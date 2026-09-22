"""Edit-ops rewrite backend: the LLM proposes structured edits; the harness applies them.

The propose -> select -> apply -> repair engine (:func:`propose_and_apply_edits`)
is the reusable core: it drives the ``edit_ops`` rewrite mode here and the
iterative-evolution experiment editors. Unusable proposals are an honest no-op
(:data:`EDIT_OPS_PARSE_ERROR`), never a silent fallback to a full-body rewrite.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable
from typing import Any, NamedTuple

from evolution import config, prompts
from evolution.config import train_optimization_enabled
from evolution.core.models import Skill
from evolution.evolve.edit_brake import (
    effective_budget,
    format_effective_budget,
    resolve_base_budget,
)
from evolution.evolve.edit_ops import (
    EditOp,
    apply_edits,
    edit_budget,
    edit_dedup_body_threshold,
    edit_repair_insert_enabled,
    parse_edits,
    select_edits,
)
from evolution.evolve.rewrite_common import (
    _format_reflections,
    _pattern_summary,
    _reject_leaked_rewrite,
    _sanitize_reflections_for_rewriter,
)
from evolution.evolve.rewrite_guards import (
    actionable_reflections,
    hard_size_violations,
    leakage_provenance_corpus,
    rewrite_size_limits,
    size_violations,
)
from evolution.evolve.rewrite_outcome import (
    EDIT_OPS_PARSE_ERROR,
    LEAK_REJECTED,
    LOW_CONFIDENCE_REFLECTION,
    NO_OP_TEXT,
    PROMOTED_ELIGIBLE,
    SANITIZE_ERROR,
    SIZE_VIOLATION,
)
from evolution.evolve.rewrite_sanitize import sanitize_rewritten_body
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest

logger = logging.getLogger(__name__)

_PROPOSAL_LENSES: tuple[str, ...] = (
    "### Proposal lens\nFor this proposal set, prioritize edits that add one concrete, copyable code idiom the evidence shows the solver lacked — a short GENERIC pattern (e.g. bulk replace across document parts, safe low-level element removal, clone-and-fill expansion) as a fenced snippet. Never copy task-specific literals, filenames, or values from the evidence.",
    "### Proposal lens\nFor this proposal set, prioritize replace or delete edits that tighten or generalize existing sections the evidence shows are misleading, redundant, or too narrow — prefer restructuring over appending.",
)


def edit_ops_churn_limit() -> float:
    """Compatibility accessor for the common brake base budget."""
    from evolution.evolve.edit_brake import resolve_base_budget

    return resolve_base_budget()


def edit_proposals() -> int:
    """Independent proposal calls per round.

    `EVO_EDIT_PROPOSALS` overrides the default, which is 3 for train
    optimization and 1 otherwise. n>1 diversifies the propose step with lensed
    re-asks (see `_PROPOSAL_LENSES`) before a merge pass reconciles them into
    one budget-bounded edit list.
    """
    raw = os.environ.get("EVO_EDIT_PROPOSALS")
    if raw is None or raw == "":
        return 3 if train_optimization_enabled() else 1
    try:
        proposals = int(raw)
    except ValueError as exc:
        raise ValueError(f"EVO_EDIT_PROPOSALS {raw!r} is not an integer") from exc
    if proposals < 1:
        raise ValueError(f"EVO_EDIT_PROPOSALS must be positive, got {proposals}")
    return proposals


def propose_prompt_name() -> str:
    return "propose_edits_train" if train_optimization_enabled() else "propose_edits"


def size_budget_text(body: str) -> str:
    max_chars = int(os.environ.get("EVO_REWRITE_MAX_CHARS", "120000") or "120000")
    max_lines = int(os.environ.get("EVO_REWRITE_MAX_LINES", "4000") or "4000")
    return (
        f"the absolute ceilings of {max_chars} characters and {max_lines} non-empty lines "
        f"(the current body is {len(body)} characters)"
    )


def edit_brake_policy_text(*, promotion_count: int = 0, version_decay: bool = True) -> str:
    """Render the shared admission limit for an editor prompt."""
    budget = effective_budget(resolve_base_budget(), promotion_count, version_decay=version_decay)
    return (
        "Make the smallest sufficient edit. The system rejects finalized normalized line churn "
        f"above the exact effective edit-brake budget of {format_effective_budget(budget)}."
    )


def evidence_policy_text(blind: bool) -> str:
    return prompts.load_prompt("_blocks/blind_evidence" if blind else "_blocks/oracle_evidence")


async def propose_and_apply_edits(
    backend: LLMBackend,
    *,
    body: str,
    evidence: str,
    blind: bool,
    task_context: str = "",
    runtime_contract: str = "",
    round_memory: str = "",
    rejected_attempts: str = "",
    edit_brake_policy: str = "",
    budget: int | None = None,
    repair: bool = True,
    record_call: Callable[..., None] | None = None,
    record_metadata: dict[str, Any] | None = None,
) -> tuple[str, dict]:
    """Propose edits against ``body``, select under budget, apply, repair once.

    When `edit_proposals()` > 1, runs that many independent propose calls (the
    first with no lens, for a byte-identical default path when n==1; the rest
    cycling `_PROPOSAL_LENSES` through the `apply_feedback` slot with a stable
    derived seed) and, if the mechanical dedup+clip pass over-budgets, resolves
    them with one `merge_edits` call. A proposal set is never discarded: if the
    merge call is unusable, the mechanical selection is applied instead.

    Returns ``(new_body, telemetry)``; ``new_body == body`` with
    ``telemetry["error_noop"]`` set when no usable edit survived across any
    call. ``record_call``, when given, is invoked ``(call_type, rendered_prompt,
    raw_response)`` after each backend response for external audit logging
    (every proposal call reports "propose" regardless of lens, the
    reconciliation call reports "merge", the post-apply retry reports
    "repair"); it does no filesystem I/O itself here.
    """
    policy = evidence_policy_text(blind)
    budget = budget if budget is not None else edit_budget()
    dedup_threshold = edit_dedup_body_threshold()
    system_edit = prompts.render("system_edit", evidence_policy=policy)
    tel: dict = {"edit_budget": budget, "tokens_in": 0, "tokens_out": 0}

    def _record(
        call_type: str, prompt: str, response: str, metadata: dict[str, Any] | None = None
    ) -> None:
        if record_call is None:
            return
        if record_metadata is None:
            record_call(call_type, prompt, response)
            return
        merged = {**(record_metadata or {}), **(metadata or {})}
        record_call(call_type, prompt, response, merged)

    async def _propose(
        apply_feedback: str,
        *,
        current_body: str,
        call_budget: int,
        seed: int | None = None,
        call_type: str = "propose",
    ):
        prompt = prompts.render(
            propose_prompt_name(),
            task_context=task_context,
            runtime_contract=runtime_contract,
            skill_body=current_body,
            evidence_policy=policy,
            evidence=evidence,
            round_memory=round_memory,
            rejected_attempts=rejected_attempts,
            apply_feedback=apply_feedback,
            edit_budget=str(call_budget),
            size_budget=size_budget_text(current_body),
            edit_brake_policy=edit_brake_policy or edit_brake_policy_text(),
        )
        resp = await backend.complete(
            [{"role": "user", "content": prompt}],
            system=system_edit,
            seed=seed,
        )
        tel["tokens_in"] += int(getattr(resp, "tokens_in", 0) or 0)
        tel["tokens_out"] += int(getattr(resp, "tokens_out", 0) or 0)
        _record(
            call_type,
            prompt,
            str(resp.content),
            {
                "system": system_edit,
                "template": propose_prompt_name(),
                "evidence_mode": "blind" if blind else "train_oracle",
                "seed": seed,
            },
        )
        if (getattr(resp, "finish_reason", "") or "").lower() == "length":
            return [], [
                {
                    "raw": str(resp.content)[:500],
                    "reason": "propose response truncated (finish_reason=length); "
                    "raise EVO_LLM_MAX_TOKENS",
                }
            ]
        return parse_edits(resp.content)

    n = edit_proposals()
    ops_per_call = []
    all_errors = []
    for i in range(n):
        if i == 0:
            feedback, seed = "", None
        else:
            feedback = _PROPOSAL_LENSES[(i - 1) % len(_PROPOSAL_LENSES)]
            seed = 1000 + i
        call_ops, call_errors = await _propose(
            feedback,
            current_body=body,
            call_budget=budget,
            seed=seed,
        )
        ops_per_call.append(call_ops)
        all_errors.extend(call_errors)

    all_ops = [op for call_ops in ops_per_call for op in call_ops]
    tel["edit_parse_errors"] = len(all_errors)
    tel["n_proposal_calls"] = n
    tel["n_proposed_total"] = len(all_ops)
    if not all_ops:
        tel.update(n_proposed=0, error_noop=bool(all_errors))
        if all_errors:
            tel["error_noop_reason"] = str(all_errors[0].get("reason", ""))[:300]
        return body, tel

    selected, sel_report = select_edits(all_ops, budget, body=body)
    tel["n_unique"] = len(selected) + sum(
        1 for e in sel_report if e["status"] == "skipped_over_budget"
    )
    n_final_proposed = len(all_ops)
    merge_used = False

    if n > 1 and any(e["status"] == "skipped_over_budget" for e in sel_report):
        proposals_payload = [
            [
                {
                    "op": op.op,
                    "target": op.target,
                    "content": op.content,
                    "rationale": op.rationale,
                    "evidence_refs": op.evidence_refs,
                }
                for op in call_ops
            ]
            for call_ops in ops_per_call
        ]
        merge_prompt = prompts.render(
            "merge_edits",
            task_context=task_context,
            runtime_contract=runtime_contract,
            skill_body=body,
            evidence_policy=policy,
            proposals=json.dumps(proposals_payload),
            edit_budget=str(budget),
            edit_brake_policy=edit_brake_policy or edit_brake_policy_text(),
        )
        resp = await backend.complete(
            [{"role": "user", "content": merge_prompt}],
            system=system_edit,
        )
        tel["tokens_in"] += int(getattr(resp, "tokens_in", 0) or 0)
        tel["tokens_out"] += int(getattr(resp, "tokens_out", 0) or 0)
        _record(
            "merge",
            merge_prompt,
            str(resp.content),
            {
                "system": system_edit,
                "template": "merge_edits",
                "evidence_mode": "blind" if blind else "train_oracle",
            },
        )
        merged_ops, merge_errors = parse_edits(resp.content)
        tel["edit_parse_errors"] += len(merge_errors)
        allowed = {(op.op, op.target, op.content, tuple(op.evidence_refs)) for op in all_ops}
        admitted = [
            op
            for op in merged_ops
            if (op.op, op.target, op.content, tuple(op.evidence_refs)) in allowed
        ]
        if admitted:
            selected, sel_report = select_edits(admitted, budget, body=body)
            merge_used = True
            tel["n_merged"] = len(admitted)
            tel["n_merge_rejected"] = len(merged_ops) - len(admitted)
            n_final_proposed = len(admitted)
        else:
            tel["merge_parse_error"] = bool(merge_errors)
            tel["n_merge_rejected"] = len(merged_ops)

    tel["merge_used"] = merge_used

    new_body, initial_apply_report = apply_edits(
        body, selected, insert_fallback=not (repair and edit_repair_insert_enabled())
    )
    successful = [
        op
        for op, report in zip(selected, initial_apply_report, strict=True)
        if report["status"].startswith(("applied", "fallback"))
    ]
    repairable_statuses = {
        "skipped_target_not_found",
        "skipped_duplicate_topic",
    }
    skipped = [e for e in initial_apply_report + sel_report if e["status"] in repairable_statuses]
    tel["final_source"] = "merge" if merge_used else "propose"
    repair_apply_report: list[dict] = []
    repair_sel_report: list[dict] = []
    repair_selected: list[EditOp] = []
    remaining_budget = max(0, budget - len(successful))
    if skipped and repair and remaining_budget:
        feedback = "### Apply feedback (previous proposal)\n" + "\n".join(
            (
                f"- {e['op']} target not found in the body: {e['target_head']!r} — copy the "
                "anchor exactly from the Current Skill Body"
                if e["status"] == "skipped_target_not_found"
                else f"- {e['op']} {e['target_head']!r}: {e['status']} — propose a different "
                "missing procedure, or replace the existing topic instead of reinserting it."
                if e["status"] == "skipped_duplicate_topic"
                else f"- {e['op']} {e['target_head']!r}: {e['status']}"
            )
            for e in skipped
        )
        ops2, errors2 = await _propose(
            feedback,
            current_body=new_body,
            call_budget=remaining_budget,
            seed=None,
            call_type="repair",
        )
        tel["edit_repair_used"] = True
        tel["edit_parse_errors"] += len(errors2)
        if ops2:
            repair_selected, repair_sel_report = select_edits(ops2, remaining_budget, body=new_body)
            new_body, repair_apply_report = apply_edits(
                new_body,
                repair_selected,
                insert_fallback=not edit_repair_insert_enabled(),
            )
            n_final_proposed += len(ops2)
            tel["final_source"] = "repair"

    final_report = initial_apply_report + sel_report + repair_apply_report + repair_sel_report
    tel.update(
        n_proposed=n_final_proposed,
        n_selected=len(successful) + len(repair_selected),
        n_applied=sum(1 for e in final_report if e["status"].startswith(("applied", "fallback"))),
        n_skipped=sum(1 for e in final_report if e["status"].startswith("skipped")),
        edit_apply_report=final_report,
    )
    if dedup_threshold is not None:
        tel["n_skipped_duplicate_content"] = sum(
            1 for e in final_report if e["status"] == "skipped_duplicate_content"
        )
    return new_body, tel


class _EditOpsResult(NamedTuple):
    body: str
    candidate_status: str
    reason: str
    tokens_used: int
    telemetry: dict


async def _rewrite_skill_edit_ops_impl(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict],
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    *,
    edit_brake_policy: str = "",
    rejected_attempts: str = "",
) -> _EditOpsResult:
    """Run the edit-ops rewrite path and classify the outcome."""
    parent_body = skill.body

    if manifest is not None and task_filter:
        manifest.assert_no_leakage(
            [task_filter],
            scope="skill_evolution",
            context="rewrite_skill(task_filter)",
        )

    selected = actionable_reflections(reflections)
    if selected is None:
        return _EditOpsResult(
            parent_body,
            LOW_CONFIDENCE_REFLECTION,
            "fewer than half of reflections were actionable",
            0,
            {},
        )
    reflections = _sanitize_reflections_for_rewriter(selected)
    reflection_text = _format_reflections(reflections)
    if not reflection_text.strip():
        return _EditOpsResult(
            parent_body,
            LOW_CONFIDENCE_REFLECTION,
            "no valid reflections to use for editing",
            0,
            {},
        )

    blind = config.reflect_blind()
    evidence = (
        f"## Failure Reflections (from {len(reflections)} failing traces)\n{reflection_text}\n\n"
        f"## Failure Pattern Summary\n{_pattern_summary(reflections)}"
    )
    new_body, tel = await propose_and_apply_edits(
        backend,
        body=parent_body,
        evidence=evidence,
        blind=blind,
        task_context=task_instruction or "(not provided)",
        runtime_contract=prompts.load_prompt("_blocks/runtime_path_contract_neutral"),
        edit_brake_policy=edit_brake_policy,
        rejected_attempts=rejected_attempts,
    )
    tokens_used = int(tel.get("tokens_in", 0)) + int(tel.get("tokens_out", 0))

    if tel.get("error_noop"):
        return _EditOpsResult(
            parent_body,
            EDIT_OPS_PARSE_ERROR,
            f"unusable edit proposals: {tel.get('error_noop_reason', '')}"[:300],
            tokens_used,
            tel,
        )
    if not tel.get("n_proposed"):
        return _EditOpsResult(
            parent_body,
            NO_OP_TEXT,
            "editor proposed no edits (no fixable gap localized)",
            tokens_used,
            tel,
        )

    try:
        new_body = sanitize_rewritten_body(new_body, parent_body)
    except ValueError as exc:
        return _EditOpsResult(
            parent_body, SANITIZE_ERROR, f"sanitize: {exc!s}"[:300], tokens_used, tel
        )

    corpus = leakage_provenance_corpus(skill, task_filter)
    if _reject_leaked_rewrite(skill, new_body, corpus):
        return _EditOpsResult(
            parent_body,
            LEAK_REJECTED,
            "leakage scanner flagged train-specific content",
            tokens_used,
            tel,
        )

    limits = rewrite_size_limits(skill, parent_body)
    issues = size_violations(new_body, limits)
    if issues:
        return _EditOpsResult(
            parent_body,
            SIZE_VIOLATION,
            "exceeds absolute size ceiling: " + "; ".join(hard_size_violations(new_body, limits)),
            tokens_used,
            tel,
        )

    if new_body == parent_body:
        return _EditOpsResult(
            parent_body,
            NO_OP_TEXT,
            "applied edits produced a body byte-equal to parent",
            tokens_used,
            tel,
        )

    return _EditOpsResult(
        new_body, PROMOTED_ELIGIBLE, "edit-ops rewrite produced a candidate", tokens_used, tel
    )


__all__ = [
    "edit_ops_churn_limit",
    "edit_proposals",
    "evidence_policy_text",
    "propose_and_apply_edits",
    "propose_prompt_name",
    "edit_brake_policy_text",
    "size_budget_text",
    "_rewrite_skill_edit_ops_impl",
]
