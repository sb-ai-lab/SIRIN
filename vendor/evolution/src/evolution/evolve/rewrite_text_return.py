"""Text-return rewrite backend: the LLM returns a fenced SKILL.md body."""

from __future__ import annotations

from typing import NamedTuple

from evolution.core.models import Skill
from evolution.evolve._legacy_prompts import load_legacy_prompt
from evolution.evolve.rewrite_common import (
    _collect_scripts,
    _format_reflections,
    _format_success_preserve,
    _pattern_summary,
    _reject_leaked_rewrite,
    _sanitize_reflections_for_rewriter,
)
from evolution.evolve.rewrite_guards import (
    actionable_reflections,
    leakage_provenance_corpus,
    rewrite_size_limits,
    size_violations,
)
from evolution.evolve.rewrite_outcome import (
    LEAK_REJECTED,
    LOW_CONFIDENCE_REFLECTION,
    NO_OP_TEXT,
    PROMOTED_ELIGIBLE,
    SANITIZE_ERROR,
    SIZE_VIOLATION,
    TRUNCATED_REWRITE,
)
from evolution.evolve.rewrite_sanitize import sanitize_rewritten_body
from evolution.lineage.traces import TraceStore
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest

REWRITE_SYSTEM = load_legacy_prompt("rewrite_system")

REWRITE_PROMPT = load_legacy_prompt("rewrite_prompt")


def _find_best_trace(skill: Skill, task_filter: str | None = None) -> tuple[dict, str] | None:
    """Find the best-performing trace and return (result_dict, code)."""
    ts = TraceStore(skill)
    traces = ts.list(task=task_filter)
    if not traces:
        return None

    best = max(traces, key=lambda t: t.get("pass_rate", 0))
    if best.get("pass_rate", 0) == 0:
        return None

    code_path = ts.resolve_trace_file(best["id"], "solve.py")
    if not code_path.exists():
        return None
    return best, code_path.read_text(encoding="utf-8")


def _best_trace_section(skill: Skill, task_filter: str | None, include_code: bool) -> str:
    if not include_code:
        return ""
    best = _find_best_trace(skill, task_filter=task_filter)
    if not best:
        return ""
    result, code = best
    return (
        f"\n## Best Trace (for reference - {result.get('passed', 0)}/{result.get('total', 0)} "
        f"passed, model: {result.get('model', '?')})\n"
        "This code partially worked. Use it as a starting point for the approach.\n"
        f"```python\n{code}\n```\n"
    )


class _TextReturnResult(NamedTuple):
    body: str
    candidate_status: str
    reason: str
    tokens_used: int


async def _rewrite_skill_text_return_impl(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict],
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    include_best_trace_code: bool,
) -> _TextReturnResult:
    """Run the historical text-return rewrite path and classify the outcome.

    May raise on backend failure; :func:`rewrite_skill_with_audit` is responsible
    for catching those and mapping them to ``rewrite_error_backend``.
    """
    parent_body = skill.body

    if manifest is not None and task_filter:
        manifest.assert_no_leakage(
            [task_filter],
            scope="skill_evolution",
            context="rewrite_skill(task_filter)",
        )

    success_preserve = _format_success_preserve(reflections)
    selected = actionable_reflections(reflections)
    if selected is None:
        return _TextReturnResult(
            parent_body,
            LOW_CONFIDENCE_REFLECTION,
            "fewer than half of reflections were actionable",
            0,
        )
    reflections = _sanitize_reflections_for_rewriter(selected)

    reflection_text = _format_reflections(reflections)
    if not reflection_text.strip():
        return _TextReturnResult(
            parent_body,
            LOW_CONFIDENCE_REFLECTION,
            "no valid reflections to use for rewriting",
            0,
        )

    limits = rewrite_size_limits(skill, skill.body)
    prompt = REWRITE_PROMPT.format(
        skill_body=skill.body,
        task_instruction=task_instruction or "(not provided)",
        scripts_section=_collect_scripts(skill),
        n_reflections=len(reflections),
        reflections=reflection_text,
        pattern_summary=_pattern_summary(reflections),
        success_preserve_section=success_preserve,
        best_trace_section=_best_trace_section(
            skill,
            task_filter=task_filter,
            include_code=include_best_trace_code,
        ),
        max_chars=limits["max_chars"],
        max_lines=limits["max_lines"],
    )

    resp = await backend.complete([{"role": "user", "content": prompt}], system=REWRITE_SYSTEM)
    tokens_used = int(
        getattr(resp, "total_tokens", 0)
        or ((getattr(resp, "tokens_in", 0) or 0) + (getattr(resp, "tokens_out", 0) or 0))
        or 0
    )
    if (getattr(resp, "finish_reason", "") or "").lower() == "length":
        return _TextReturnResult(
            parent_body,
            TRUNCATED_REWRITE,
            "rewrite truncated (finish_reason=length); raise EVO_LLM_MAX_TOKENS "
            "so the model can emit the whole skill",
            tokens_used,
        )
    try:
        new_body = sanitize_rewritten_body(resp.content, skill.body)
    except ValueError as exc:
        corpus = leakage_provenance_corpus(skill, task_filter)
        if _reject_leaked_rewrite(skill, resp.content, corpus):
            return _TextReturnResult(
                parent_body,
                LEAK_REJECTED,
                "leakage scanner flagged train-specific content",
                tokens_used,
            )
        return _TextReturnResult(
            parent_body, SANITIZE_ERROR, f"sanitize: {exc!s}"[:300], tokens_used
        )

    corpus = leakage_provenance_corpus(skill, task_filter)
    if _reject_leaked_rewrite(skill, new_body, corpus):
        return _TextReturnResult(
            parent_body,
            LEAK_REJECTED,
            "leakage scanner flagged train-specific content",
            tokens_used,
        )

    issues = size_violations(new_body, limits)
    if issues:
        return _TextReturnResult(
            parent_body,
            SIZE_VIOLATION,
            "exceeds absolute size ceiling: " + "; ".join(issues),
            tokens_used,
        )

    if new_body == parent_body:
        return _TextReturnResult(
            parent_body, NO_OP_TEXT, "rewrite returned a body byte-equal to parent", tokens_used
        )

    return _TextReturnResult(
        new_body, PROMOTED_ELIGIBLE, "text-return rewrite produced a candidate", tokens_used
    )
