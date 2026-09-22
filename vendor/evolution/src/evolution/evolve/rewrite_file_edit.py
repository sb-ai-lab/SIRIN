"""Codex file-edit rewrite backend: the agent edits SKILL.md on disk."""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import subprocess
import uuid
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from evolution.core.models import Skill, SkillFrontmatter
from evolution.core.parser import parse_skill_md, write_skill_md
from evolution.evolve._legacy_prompts import load_legacy_prompt
from evolution.evolve.preservation import score_preservation
from evolution.evolve.rewrite_common import (
    _SEVERITY_RANK,
    _candidate_added_new_heading,
    _candidate_root,
    _cleanup_candidate,
    _collect_scripts,
    _format_reflections,
    _format_success_preserve,
    _non_empty_line_churn,
    _parent_top_headings,
    _pattern_summary,
    _reject_leaked_rewrite,
    _rewrite_provenance,
    _sanitize_reflections_for_rewriter,
)
from evolution.evolve.rewrite_guards import (
    actionable_reflections,
    hard_size_violations,
    leakage_provenance_corpus,
    rewrite_size_limits,
    validate_candidate_isolation,
)
from evolution.evolve.rewrite_outcome import (
    CANDIDATE_INVALID_FRONTMATTER_CORRUPT,
    LEAK_REJECTED,
    LOW_CONFIDENCE_REFLECTION,
    NO_OP_FILE_EDIT,
    PROMOTED_ELIGIBLE,
    REWRITE_ERROR_CODEX,
    SANITIZE_ERROR,
    SIZE_VIOLATION,
    RewriteOutcome,
)
from evolution.evolve.rewrite_sanitize import sanitize_rewritten_body
from evolution.llm.agent_backend import AgentBackend, AgentBackendError
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


CODEX_FILE_EDIT_SYSTEM = load_legacy_prompt("codex_file_edit_system")

CODEX_FILE_EDIT_PROMPT = load_legacy_prompt("codex_file_edit_prompt")


def _consensus_reflection(reflections: list[dict]) -> dict:
    """Pick the reflection representing the most common (pattern) cluster.

    Ranking: frequency of same `pattern` > severity > original trace order.
    Memory feedback_evolve_signal_per_family — one idiosyncratic critical
    reflection should not dominate the rewrite when 3/3 traces share a
    different repeated pattern.
    """
    if not reflections:
        return {}
    pattern_counts: Counter[str] = Counter(str(r.get("pattern") or "unknown") for r in reflections)

    def _key(idx_r: tuple[int, dict]) -> tuple[int, int, int]:
        idx, r = idx_r
        pat = str(r.get("pattern") or "unknown")
        sev = str(r.get("severity") or "minor").lower()
        return (-pattern_counts[pat], _SEVERITY_RANK.get(sev, 99), idx)

    return sorted(enumerate(reflections), key=_key)[0][1]


def _consensus_summary(reflections: list[dict]) -> str:
    """One-paragraph 'N/M traces failed because <pattern>' summary."""
    if not reflections:
        return "(no actionable reflections)"
    n = len(reflections)
    patterns: Counter[str] = Counter(str(r.get("pattern") or "unknown") for r in reflections)
    top_pattern, top_count = patterns.most_common(1)[0]
    rep = _consensus_reflection(reflections)
    root_cause = str(rep.get("root_cause") or "(no root_cause)")
    skill_gap = str(rep.get("skill_gap") or "(no skill_gap)")
    suggested_fix = str(rep.get("suggested_fix") or "(no suggested_fix)")
    if top_count == n and n > 1:
        head = f"All {n}/{n} traces share pattern `{top_pattern}`."
    elif top_count > 1:
        head = f"{top_count}/{n} traces share pattern `{top_pattern}`; the rest differ."
    else:
        head = f"Each of {n} traces failed differently; representative pattern `{top_pattern}`."
    return (
        f"{head}\n"
        f"- Representative root_cause: {root_cause}\n"
        f"- Skill gap to close: {skill_gap}\n"
        f"- Suggested fix: {suggested_fix}"
    )


def _format_all_actionable_reflections(reflections: list[dict]) -> str:
    """Render every actionable reflection in full (root_cause + skill_gap + suggested_fix)."""
    if not reflections:
        return "(none)"
    lines: list[str] = []
    for i, r in enumerate(reflections, 1):
        sev = r.get("severity", "?")
        pat = r.get("pattern", "?")
        lines.append(f"### Reflection {i}  (severity: {sev}, pattern: `{pat}`)")
        lines.append(f"- root_cause: {r.get('root_cause', '?')}")
        lines.append(f"- skill_gap: {r.get('skill_gap', '?')}")
        lines.append(f"- suggested_fix: {r.get('suggested_fix', '?')}")
    return "\n".join(lines)


def _source_models_summary(reflections: list[dict]) -> str:
    """Dedup'd source_model_id list pulled from each reflection's trace_context."""
    models: list[str] = []
    for r in reflections:
        ctx = r.get("trace_context") or {}
        mid = ctx.get("source_model_id") or r.get("model")
        if mid and mid not in models:
            models.append(str(mid))
    return ", ".join(models) if models else "(unknown)"


def _git_init_candidate(work_dir: Path, *, timeout_s: float = 10.0) -> bool:
    """Best-effort: initialise candidate dir as a tiny git repo so codex's
    in-loop ``git diff`` self-review works.  Failures are non-fatal
    (returns False); codex's git diff just exits non-zero as before.
    """
    if not shutil.which("git"):
        return False
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    cmds = (
        ["git", "init", "-q", "-b", "baseline"],
        ["git", "-c", "user.email=evo@local", "-c", "user.name=evo", "add", "SKILL.md"],
        [
            "git",
            "-c",
            "user.email=evo@local",
            "-c",
            "user.name=evo",
            "commit",
            "-q",
            "-m",
            "baseline",
        ],
    )
    try:
        for cmd in cmds:
            r = subprocess.run(
                cmd,
                cwd=str(work_dir),
                env=env,
                capture_output=True,
                timeout=timeout_s,
                check=False,
            )
            if r.returncode != 0:
                logger.debug(
                    "git init candidate failed at %s: rc=%s stderr=%s",
                    cmd[1] if len(cmd) > 1 else cmd[0],
                    r.returncode,
                    (r.stderr or b"")[:200],
                )
                return False
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("git init candidate exception: %s", exc)
        return False
    return True


_FENCE_RE = re.compile(r"```[\w+-]*[ \t]*\n(.*?)\n```", re.DOTALL)


def _extract_fenced_candidate(last_message: str, parent_body: str) -> str | None:
    """Recover a candidate body when codex answered in chat-mode.

    Mirrors the ``fenced_candidate.SKILL.md`` workflow (docs/codex_usage.md):
    when codex returns a fenced markdown block instead
    of editing the workspace file, the largest block usually IS the intended
    candidate. Strips an optional YAML frontmatter so the returned string is
    a pure body. Returns ``None`` when no usable candidate is recoverable.
    """
    if not last_message:
        return None
    blocks = _FENCE_RE.findall(last_message)
    if not blocks:
        return None
    payload = max(blocks, key=len).strip("\n")
    if payload.startswith("---\n") or payload.startswith("---\r\n"):
        end = payload.find("\n---", 4)
        if end != -1:
            payload = payload[end + 4 :].lstrip("\n")
    payload = payload.strip()
    if not payload or payload == parent_body.strip():
        return None
    return payload


async def _rewrite_skill_file_edit_impl(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict],
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    include_best_trace_code: bool,
    *,
    audit_root: Path | None,
    row_id: str,
    debug_archive: bool,
    model_id: str,
) -> RewriteOutcome:
    """Run the C1 file-edit rewrite path and return a full RewriteOutcome.

    Per plan §1.5 — flow numbered to match the plan steps in order.
    """

    parent_body = skill.body
    _budget_frac, base_prov = _rewrite_provenance(skill)

    # 0. Fail-fast if backend is not an agent CLI.  Memory feedback_no_silent_fallbacks:
    #    file-edit mode requires an AgentBackend; we do not silently degrade.
    if not isinstance(backend, AgentBackend):
        raise RuntimeError(
            f"EVO_REWRITE_MODE=file-edit requires an AgentBackend; got {type(backend).__name__}"
        )

    # 1. low-confidence check (same threshold as text-return).
    if manifest is not None and task_filter:
        manifest.assert_no_leakage(
            [task_filter],
            scope="skill_evolution",
            context="rewrite_skill_with_audit(file_edit,task_filter)",
        )
    success_preserve = _format_success_preserve(reflections)
    selected = actionable_reflections(reflections)
    if selected is None:
        return RewriteOutcome(
            body=parent_body,
            candidate_status=LOW_CONFIDENCE_REFLECTION,
            reason="fewer than half of reflections were actionable",
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            **base_prov,
        )
    reflections = _sanitize_reflections_for_rewriter(selected)

    reflection_text = _format_reflections(reflections)
    if not reflection_text.strip():
        return RewriteOutcome(
            body=parent_body,
            candidate_status=LOW_CONFIDENCE_REFLECTION,
            reason="no valid reflections to use for rewriting",
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            **base_prov,
        )

    # 2. Candidate workspace seeded with parent SKILL.md.
    candidate_dir = _candidate_root() / f"evo_c1_{uuid.uuid4().hex}"
    candidate_dir.mkdir(parents=True, exist_ok=False)
    candidate_skill_path = candidate_dir / "SKILL.md"
    shutil.copy2(skill.skill_md_path, candidate_skill_path)

    # 2b. Best-effort git init so codex can use `git diff` to self-review.
    _git_init_candidate(candidate_dir)

    # 3. Build prompt — consensus-first ranking + full reflections + parent
    #    headings as preserve list (memories feedback_evolve_signal_per_family,
    #    project_evolution_regenerates_not_refines).
    limits = rewrite_size_limits(skill, skill.body)
    parent_headings = _parent_top_headings(skill.body)
    preserve_text = "\n".join(f"- {h}" for h in parent_headings) if parent_headings else "(none)"
    prompt = CODEX_FILE_EDIT_PROMPT.format(
        skill_body=skill.body,
        preserve_headings=preserve_text,
        task_instruction=task_instruction or "(not provided)",
        source_models=_source_models_summary(reflections),
        n_traces=len(reflections),
        scripts_section=_collect_scripts(skill),
        consensus_summary=_consensus_summary(reflections),
        # Keep the historical prompt contract: the count includes the
        # synthesized consensus context alongside the raw reflections.
        n_reflections=len(reflections) + 1,
        all_reflections=_format_all_actionable_reflections(reflections),
        pattern_summary=_pattern_summary(reflections),
        success_preserve_section=success_preserve,
        max_chars=limits["max_chars"],
        max_lines=limits["max_lines"],
    )
    # _best_trace_section() / include_best_trace_code is intentionally unused
    # here — file-edit mode hides raw best-trace code from the prompt to keep
    # the leak surface minimal.
    if include_best_trace_code:
        logger.debug("file-edit mode ignores include_best_trace_code=True (leak surface)")

    # 4. codex exec in a caller-seeded candidate dir.  The backend chooses
    #    the Codex sandbox/bypass mode; Evolution's safety boundary is still
    #    the temp workspace plus post-exit validators below.
    codex_usage: dict | None = None
    codex_diag: dict | None = None
    try:
        await backend.complete_file_edit(candidate_dir, prompt, CODEX_FILE_EDIT_SYSTEM)
        codex_usage = dict(getattr(backend, "last_usage", {}) or {})
        codex_diag = dict(getattr(backend, "last_codex_diagnostics", {}) or {})
    except AgentBackendError as exc:
        codex_usage = dict(getattr(backend, "last_usage", {}) or {})
        codex_diag = dict(getattr(backend, "last_codex_diagnostics", {}) or {})
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_CODEX,
            reason=f"codex file-edit failed: {exc!s}"[:500],
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            codex_diagnostics=codex_diag or None,
            **base_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 4b. Strip the harness-seeded .git dir before isolation check — git was
    #     only for codex's `git diff` self-review and is not part of the
    #     candidate. Keeps `_ALLOWED_HIDDEN_NAMES` strict.
    git_dir = candidate_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)

    # 5. Hard isolation validators (post-exit only).
    ok, iso_status, iso_reason = validate_candidate_isolation(candidate_dir)
    if not ok:
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=iso_status,
            reason=iso_reason,
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            codex_diagnostics=codex_diag or None,
            **base_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 6. Parse the candidate, capture frontmatter BEFORE reattach.
    try:
        candidate_fm_raw, candidate_body_raw = parse_skill_md(candidate_skill_path)
    except Exception as exc:
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=CANDIDATE_INVALID_FRONTMATTER_CORRUPT,
            reason=f"parse_skill_md: {exc!s}"[:300],
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            codex_diagnostics=codex_diag or None,
            **base_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 7. Frontmatter reattach (runtime safety net, independent of metric).
    parent_fm_raw, _ = parse_skill_md(skill.skill_md_path)
    parent_fm_validated = SkillFrontmatter.model_validate(parent_fm_raw)
    write_skill_md(candidate_skill_path, parent_fm_validated, candidate_body_raw)
    _re_fm, candidate_body = parse_skill_md(candidate_skill_path)

    # 7a. Compute candidate-derived provenance eagerly so every post-parse
    #     outcome (including silent paths like no-op and sandbox-fail) lands
    #     a self-describing audit record. Memory
    #     feedback_diagnose_runtime_contracts_not_just_prompt.
    _, _new_headings_list = _candidate_added_new_heading(parent_body, candidate_body)
    cand_prov: dict[str, Any] = {
        **base_prov,
        "candidate_body_sha256": hashlib.sha256(candidate_body.encode("utf-8")).hexdigest(),
        "computed_churn": _non_empty_line_churn(parent_body, candidate_body),
        "new_headings": list(_new_headings_list),
    }

    # 7b. Sandbox-failure classifier (t34v10): codex exits 0 even when
    #     `bwrap` aborts inside `-s workspace-write` on this host (memory
    #     reference_codex_workspace_write_broken_bwrap). With `--json`
    #     diagnostics, the bwrap line lands in `sandbox_errors`. Unchanged
    #     candidate + sandbox failure → rewrite_error_codex, not a silent
    #     no_op_file_edit.
    sandbox_errors = (codex_diag or {}).get("sandbox_errors") or []
    cmd_failures = (codex_diag or {}).get("command_failures") or []
    sandbox_failed = bool(sandbox_errors) or any(
        "permission denied" in (cf.get("stderr") or "").lower() for cf in cmd_failures
    )
    if sandbox_failed and candidate_body == parent_body:
        reason = (
            "sandbox failure under -s "
            + ((codex_diag or {}).get("sandbox") or "?")
            + ": "
            + "; ".join(sandbox_errors[:2] or ["see codex_diagnostics"])
        )[:300]
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_CODEX,
            reason=reason,
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=candidate_body_raw,
            codex_diagnostics=codex_diag or None,
            **cand_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 7c. Fenced-candidate fallback (see docs/codex_usage.md):
    #     when the file is unchanged but codex returned a chat-mode reply with
    #     a fenced markdown block, treat the block as the candidate body. The
    #     reattach + parse cycle is re-run so downstream guards see the same
    #     shape they would for a file-edit candidate.
    if candidate_body == parent_body and not sandbox_failed:
        fenced_body = _extract_fenced_candidate(
            (codex_diag or {}).get("last_message") or "", parent_body
        )
        if fenced_body is not None:
            write_skill_md(candidate_skill_path, parent_fm_validated, fenced_body)
            _re_fm, candidate_body = parse_skill_md(candidate_skill_path)
            candidate_body_raw = fenced_body
            _, _new_headings_list = _candidate_added_new_heading(parent_body, candidate_body)
            cand_prov = {
                **base_prov,
                "candidate_body_sha256": hashlib.sha256(candidate_body.encode("utf-8")).hexdigest(),
                "computed_churn": _non_empty_line_churn(parent_body, candidate_body),
                "new_headings": list(_new_headings_list),
            }
            if codex_diag is None:
                codex_diag = {}
            codex_diag["fenced_fallback"] = True

    # 8. no-op file edit (codex chose not to change the body).
    if candidate_body == parent_body:
        preservation = score_preservation(
            parent_body, candidate_body, parent_fm_raw, candidate_fm_raw
        )
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=NO_OP_FILE_EDIT,
            reason="candidate SKILL.md body byte-equal to parent",
            preservation=preservation,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=candidate_body_raw,
            codex_diagnostics=codex_diag or None,
            **cand_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 9. Sanitize + leak guard + size cap (reuse text-return validators).
    try:
        candidate_body = sanitize_rewritten_body(candidate_body, parent_body)
    except ValueError as exc:
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=SANITIZE_ERROR,
            reason=f"sanitize_rewritten_body: {exc!s}"[:300],
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=candidate_body_raw,
            codex_diagnostics=codex_diag or None,
            **cand_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome
    corpus = leakage_provenance_corpus(skill, task_filter)
    if _reject_leaked_rewrite(skill, candidate_body, corpus):
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=LEAK_REJECTED,
            reason="leakage scanner flagged train-specific content",
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=candidate_body_raw,
            codex_diagnostics=codex_diag or None,
            **cand_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome
    hard = hard_size_violations(candidate_body, limits)
    if hard:
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=SIZE_VIOLATION,
            reason="exceeds absolute size ceiling: " + "; ".join(hard),
            preservation=None,
            codex_usage=codex_usage or None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=candidate_body_raw,
            codex_diagnostics=codex_diag or None,
            **cand_prov,
        )
        _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
        return outcome

    # 10. Preservation score (measured against candidate_fm BEFORE reattach).
    preservation = score_preservation(parent_body, candidate_body, parent_fm_raw, candidate_fm_raw)

    # 12. Build final outcome before cleanup; let cleanup attach debug_dir.
    outcome = RewriteOutcome(
        body=candidate_body,
        candidate_status=PROMOTED_ELIGIBLE,
        reason="file-edit rewrite produced a candidate",
        preservation=preservation,
        codex_usage=codex_usage or None,
        candidate_debug_dir=None,
        model_id=model_id,
        parent_body=parent_body,
        candidate_body_raw=candidate_body_raw,
        codex_diagnostics=codex_diag or None,
        **cand_prov,
    )
    _cleanup_candidate(candidate_dir, audit_root, row_id, debug_archive, outcome)
    return outcome
