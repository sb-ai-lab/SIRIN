"""LLM-driven trace reflection and skill rewriting.

This module is the compatibility entrypoint for the core lifecycle APIs:
reflection over failed traces, rewrite generation, and audited candidate
promotion. Sibling modules keep evidence handling, sanitization, guard checks,
and preservation scoring explicit.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from evolution.core.models import Skill
from evolution.core.parser import parse_skill_md
from evolution.evolve.edit_brake import (
    analyze_edit,
    effective_budget,
    format_effective_budget,
    resolve_base_budget,
    retry_feedback,
)
from evolution.evolve.preservation import score_preservation
from evolution.evolve.reflection import (
    REFLECT_PROMPT,
    REFLECT_SUCCESS_PROMPT,
    REFLECT_SYSTEM,
    _backend_label,
    _backend_settings,
    collect_reflections,
    load_reflection,
    reflect_failing_traces,
    reflect_trace,
    save_reflection,
)
from evolution.evolve.rewrite_common import (
    _candidate_added_new_heading,
    _non_empty_line_churn,
    _parent_top_headings,
    _sanitize_reflections_for_rewriter,
)
from evolution.evolve.rewrite_file_edit import (
    CODEX_FILE_EDIT_PROMPT,
    CODEX_FILE_EDIT_SYSTEM,
    _consensus_reflection,
    _consensus_summary,
    _extract_fenced_candidate,
    _git_init_candidate,
    _rewrite_skill_file_edit_impl,
)
from evolution.evolve.rewrite_outcome import (
    CANDIDATE_EDIT_BUDGET_EXCEEDED,
    PROMOTED_ELIGIBLE,
    REWRITE_ERROR_BACKEND,
    SIZE_VIOLATION,
    RewriteOutcome,
)
from evolution.evolve.rewrite_session import (
    SESSION_PROMPT,
    SESSION_SYSTEM_BLIND,
    SESSION_SYSTEM_ORACLE,
    _rewrite_skill_agentic_session_impl,
    _session_has_progress,
)
from evolution.evolve.rewrite_text_return import (
    REWRITE_PROMPT,
    REWRITE_SYSTEM,
    _rewrite_skill_text_return_impl,
)
from evolution.lineage.state_io import atomic_write_json
from evolution.lineage.tracker import LineageTracker
from evolution.lineage.version import hash_managed_tree
from evolution.llm.agent_backend import AgentBackend
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest

if TYPE_CHECKING:
    from evolution.eval.task import Task

logger = logging.getLogger(__name__)

__all__ = [
    "REFLECT_PROMPT",
    "REFLECT_SUCCESS_PROMPT",
    "REFLECT_SYSTEM",
    "collect_reflections",
    "load_reflection",
    "normalize_rewrite_mode",
    "reflect_failing_traces",
    "reflect_trace",
    "rewrite_skill",
    "rewrite_skill_with_audit",
    "REWRITE_MODE_NAMES",
    "save_reflection",
    "CODEX_FILE_EDIT_PROMPT",
    "CODEX_FILE_EDIT_SYSTEM",
    "REWRITE_PROMPT",
    "REWRITE_SYSTEM",
    "SESSION_PROMPT",
    "SESSION_SYSTEM_BLIND",
    "SESSION_SYSTEM_ORACLE",
    "_candidate_added_new_heading",
    "_consensus_reflection",
    "_consensus_summary",
    "_extract_fenced_candidate",
    "_git_init_candidate",
    "_non_empty_line_churn",
    "_parent_top_headings",
    "_sanitize_reflections_for_rewriter",
    "_session_has_progress",
]


REWRITE_MODE_NAMES = ("text-return", "file-edit", "agentic-session", "edit-ops")


def normalize_rewrite_mode(value: str) -> str:
    mode = (value or "text-return").strip().lower().replace("_", "-")
    if mode == "session":
        mode = "agentic-session"
    if mode not in REWRITE_MODE_NAMES:
        raise ValueError(
            f"invalid rewrite mode {value!r}; expected one of {', '.join(REWRITE_MODE_NAMES)}"
        )
    return mode


async def _rewrite_skill_text_return_outcome(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict[str, Any]],
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    include_best_trace_code: bool,
    *,
    model_id: str,
) -> RewriteOutcome:
    """Run the text-return path and wrap its result in a :class:`RewriteOutcome`."""
    parent_body = skill.body
    try:
        new_body, candidate_status, reason, tokens_used = await _rewrite_skill_text_return_impl(
            backend,
            skill,
            reflections,
            task_instruction,
            task_filter,
            manifest,
            include_best_trace_code,
        )
    except Exception as exc:
        return RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_BACKEND,
            reason=f"{type(exc).__name__}: {exc!s}"[:500],
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
        )

    # Compute preservation + codex_usage even for text-return so t34v8 and
    # t34v9 mechanism numbers are comparable (review #3).  Text-return does
    # not touch frontmatter, so candidate_fm == parent_fm.
    preservation = None
    if new_body != parent_body:
        try:
            parent_fm_raw, _ = parse_skill_md(skill.skill_md_path)
            preservation = score_preservation(parent_body, new_body, parent_fm_raw, parent_fm_raw)
        except Exception as exc:
            logger.warning("preservation scoring failed for %s: %s", skill.name, exc)
            preservation = None
    codex_usage = None
    if isinstance(backend, AgentBackend):
        last = getattr(backend, "last_usage", None)
        if last:
            codex_usage = dict(last)

    return RewriteOutcome(
        body=new_body,
        candidate_status=candidate_status,
        reason=reason,
        preservation=preservation,
        codex_usage=codex_usage,
        candidate_debug_dir=None,
        model_id=model_id,
        parent_body=parent_body,
        candidate_body_raw=new_body if new_body != parent_body else None,
        tokens_used=tokens_used,
    )


async def _rewrite_skill_edit_ops_outcome(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict[str, Any]],
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    *,
    model_id: str,
    edit_brake_policy: str,
    retry_guidance: str = "",
) -> RewriteOutcome:
    """Run the edit-ops path and wrap its result in a :class:`RewriteOutcome`."""
    parent_body = skill.body
    try:
        from evolution.evolve.rewrite_edit_ops import _rewrite_skill_edit_ops_impl

        result = await _rewrite_skill_edit_ops_impl(
            backend,
            skill,
            reflections,
            task_instruction,
            task_filter,
            manifest,
            edit_brake_policy=edit_brake_policy,
            rejected_attempts=retry_guidance,
        )
    except Exception as exc:
        return RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_BACKEND,
            reason=f"{type(exc).__name__}: {exc!s}"[:500],
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
        )

    preservation = None
    if result.body != parent_body:
        try:
            parent_fm_raw, _ = parse_skill_md(skill.skill_md_path)
            preservation = score_preservation(
                parent_body, result.body, parent_fm_raw, parent_fm_raw
            )
        except Exception as exc:
            logger.warning("preservation scoring failed for %s: %s", skill.name, exc)
            preservation = None

    return RewriteOutcome(
        body=result.body,
        candidate_status=result.candidate_status,
        reason=result.reason,
        preservation=preservation,
        codex_usage=result.telemetry or None,
        candidate_debug_dir=None,
        model_id=model_id,
        parent_body=parent_body,
        candidate_body_raw=result.body if result.body != parent_body else None,
        tokens_used=result.tokens_used,
    )


async def rewrite_skill_with_audit(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict[str, Any]],
    task_instruction: str = "",
    task_filter: str | None = None,
    manifest: SplitManifest | None = None,
    include_best_trace_code: bool = True,
    *,
    rewrite_mode: str = "text-return",
    task: Task | None = None,
    audit_root: Path | None = None,
    row_id: str = "",
    debug_archive: bool = False,
    version_decay: bool = True,
    max_rewrite_attempts: int = 1,
    promotion_count: int | None = None,
    parent_version: str | None = None,
    base_budget: float | None = None,
) -> RewriteOutcome:
    """Produce a structured :class:`RewriteOutcome` for one rewrite call.

    ``rewrite_mode`` selects the implementation. Agentic sessions require ``task``.
    No branch calls the public :func:`rewrite_skill` wrapper; that
    would recurse.
    """
    if max_rewrite_attempts < 1:
        raise ValueError("max_rewrite_attempts must be at least one")
    # Resolve this before every editor implementation so invalid environment
    # configuration cannot consume a provider call.
    resolved_base_budget = resolve_base_budget() if base_budget is None else base_budget
    if promotion_count is None:
        tracker = LineageTracker(skill)
        promotion_count = tracker.promotion_count()
        parent_version = parent_version or tracker.current_version
    if promotion_count < 0:
        raise ValueError("promotion_count must be non-negative")
    model_id = _backend_label(backend)
    mode = normalize_rewrite_mode(rewrite_mode)
    parent_tree_sha256 = hash_managed_tree(skill.path)
    attempt_identity = hashlib.sha256(
        json.dumps(
            {
                "parent_tree_sha256": parent_tree_sha256,
                "rewrite_mode": mode,
                "task_instruction": task_instruction,
                "task_filter": task_filter,
                "reflections": reflections,
                "model_id": model_id,
                "backend_settings": _backend_settings(backend),
                "base_budget": resolved_base_budget,
                "promotion_count": promotion_count,
                "parent_version": parent_version,
                "version_decay": version_decay,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    attempt_log = audit_root / "rewrite_attempts.json" if audit_root is not None else None
    attempts: list[dict[str, Any]] = []
    if attempt_log is not None and attempt_log.is_file():
        try:
            saved_attempts = json.loads(attempt_log.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            saved_attempts = []
        if isinstance(saved_attempts, list):
            attempts = [
                record
                for record in saved_attempts
                if isinstance(record, dict) and record.get("attempt_identity") == attempt_identity
            ]

    def persist_attempt(record: dict[str, Any]) -> None:
        """Persist one finalized editor attempt before a possible retry."""
        if attempt_log is None:
            return
        attempt_log.parent.mkdir(parents=True, exist_ok=True)
        existing: list[dict[str, Any]] = []
        if attempt_log.is_file():
            try:
                value = json.loads(attempt_log.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                value = []
            if isinstance(value, list):
                existing = [item for item in value if isinstance(item, dict)]
        existing.append(record)
        atomic_write_json(attempt_log, existing)

    budget = effective_budget(
        resolved_base_budget,
        promotion_count,
        version_decay=version_decay,
    )
    policy_guidance = (
        f"Edit brake policy: make the smallest sufficient edit. The system rejects normalized line churn above "
        f"the exact effective budget of {format_effective_budget(budget)}."
    )
    retry_guidance = str(attempts[-1].get("retry_guidance") or "") if attempts else ""
    if attempts and attempts[-1].get("candidate_status") != CANDIDATE_EDIT_BUDGET_EXCEEDED:
        saved = attempts[-1]
        saved_body = str(saved.get("outcome_body") or saved.get("candidate_body") or skill.body)
        saved_candidate = str(saved.get("candidate_body") or saved_body)
        return RewriteOutcome(
            body=saved_body,
            candidate_status=str(saved.get("candidate_status") or REWRITE_ERROR_BACKEND),
            reason=str(saved.get("reason") or "resumed from finalized rewrite attempt"),
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=saved.get("artifact_reference"),
            model_id=model_id,
            parent_body=skill.body,
            candidate_body_raw=saved_candidate if saved_candidate != skill.body else None,
            parent_body_sha256=saved.get("parent_sha256"),
            candidate_body_sha256=saved.get("finalized_candidate_sha256"),
            computed_churn=saved.get("normalized_churn"),
            edit_budget_frac=saved.get("effective_budget_frac"),
            edit_brake=saved.get("edit_brake"),
            rewrite_attempts=attempts,
        )
    first_attempt = len(attempts) + 1
    if first_attempt > max_rewrite_attempts:
        saved = attempts[-1]
        saved_body = str(saved.get("outcome_body") or skill.body)
        saved_candidate = str(saved.get("candidate_body") or saved_body)
        return RewriteOutcome(
            body=saved_body,
            candidate_status=CANDIDATE_EDIT_BUDGET_EXCEEDED,
            reason=str(saved.get("reason") or "edit brake rejected candidate"),
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=saved.get("artifact_reference"),
            model_id=model_id,
            parent_body=skill.body,
            candidate_body_raw=saved_candidate if saved_candidate != skill.body else None,
            parent_body_sha256=saved.get("parent_sha256"),
            candidate_body_sha256=saved.get("finalized_candidate_sha256"),
            computed_churn=saved.get("normalized_churn"),
            edit_budget_frac=saved.get("effective_budget_frac"),
            edit_brake=saved.get("edit_brake"),
            rewrite_attempts=attempts,
        )
    for attempt in range(first_attempt, max_rewrite_attempts + 1):
        if hash_managed_tree(skill.path) != parent_tree_sha256:
            raise RuntimeError("skill changed before rewrite attempt")
        attempt_instruction = f"{task_instruction}\n\n{policy_guidance}"
        if retry_guidance:
            attempt_instruction += f"\n\n{retry_guidance}"
        if mode == "edit-ops":
            outcome = await _rewrite_skill_edit_ops_outcome(
                backend,
                skill,
                reflections,
                task_instruction,
                task_filter,
                manifest,
                model_id=model_id,
                edit_brake_policy=policy_guidance,
                retry_guidance=retry_guidance,
            )
        elif mode == "agentic-session":
            outcome = await _rewrite_skill_agentic_session_impl(
                backend,
                skill,
                task,
                attempt_instruction,
                task_filter,
                manifest,
                audit_root=audit_root,
                row_id=row_id,
                debug_archive=debug_archive,
                model_id=model_id,
            )
        elif mode == "file-edit":
            outcome = await _rewrite_skill_file_edit_impl(
                backend,
                skill,
                reflections,
                attempt_instruction,
                task_filter,
                manifest,
                include_best_trace_code,
                audit_root=audit_root,
                row_id=row_id,
                debug_archive=debug_archive,
                model_id=model_id,
            )
        else:
            outcome = await _rewrite_skill_text_return_outcome(
                backend,
                skill,
                reflections,
                attempt_instruction,
                task_filter,
                manifest,
                include_best_trace_code,
                model_id=model_id,
            )

        raw_body = outcome.candidate_body_raw
        if raw_body is not None and raw_body != outcome.body:
            outcome = replace(
                outcome,
                raw_body_sha256=hashlib.sha256(raw_body.encode("utf-8")).hexdigest(),
            )
        if hash_managed_tree(skill.path) != parent_tree_sha256:
            raise RuntimeError("skill changed during rewrite attempt")
        candidate_body = outcome.body
        evidence = None
        if outcome.candidate_status == PROMOTED_ELIGIBLE:
            evidence = analyze_edit(
                outcome.parent_body,
                outcome.body,
                base_budget=resolved_base_budget,
                promotion_count=promotion_count,
                version_decay=version_decay,
                parent_version=parent_version,
            )
            if not evidence.allowed:
                outcome = replace(
                    outcome,
                    body=outcome.parent_body,
                    candidate_status=CANDIDATE_EDIT_BUDGET_EXCEEDED,
                    reason=f"normalized churn {evidence.normalized_churn:.2%} exceeds budget {evidence.effective_budget_frac:.2%}",
                    parent_body_sha256=evidence.parent_sha256,
                    candidate_body_sha256=evidence.candidate_sha256,
                    computed_churn=evidence.normalized_churn,
                    edit_budget_frac=evidence.effective_budget_frac,
                )
            else:
                outcome = replace(
                    outcome,
                    parent_body_sha256=evidence.parent_sha256,
                    candidate_body_sha256=evidence.candidate_sha256,
                    computed_churn=evidence.normalized_churn,
                    edit_budget_frac=evidence.effective_budget_frac,
                )
        attempt_record = {
            "attempt": attempt,
            "parent_tree_sha256": parent_tree_sha256,
            "attempt_identity": attempt_identity,
            "rewrite_mode": mode,
            "candidate_status": outcome.candidate_status,
            "reason": outcome.reason,
            "candidate_body": candidate_body,
            "outcome_body": outcome.body,
            "parent_sha256": (evidence.parent_sha256 if evidence else outcome.parent_body_sha256),
            "finalized_candidate_sha256": hashlib.sha256(
                candidate_body.encode("utf-8")
            ).hexdigest(),
            "outcome_body_sha256": hashlib.sha256(outcome.body.encode("utf-8")).hexdigest(),
            "raw_output_sha256": outcome.raw_body_sha256
            or (
                hashlib.sha256(outcome.candidate_body_raw.encode("utf-8")).hexdigest()
                if outcome.candidate_body_raw is not None
                and outcome.candidate_body_raw != outcome.body
                else None
            ),
            "normalized_churn": evidence.normalized_churn if evidence else None,
            "effective_budget_frac": evidence.effective_budget_frac if evidence else None,
            "tokens_used": outcome.tokens_used,
            "artifact_reference": outcome.candidate_debug_dir,
        }
        if outcome.candidate_status == CANDIDATE_EDIT_BUDGET_EXCEEDED and evidence is not None:
            attempt_record["edit_brake"] = evidence.as_dict()
            attempt_record["retry_guidance"] = retry_feedback(evidence, attempt)
        attempts.append(attempt_record)
        persist_attempt(attempt_record)
        if outcome.candidate_status != CANDIDATE_EDIT_BUDGET_EXCEEDED:
            return replace(
                outcome,
                edit_brake=evidence.as_dict() if evidence else None,
                rewrite_attempts=attempts,
            )
        if attempt == max_rewrite_attempts:
            return replace(
                outcome,
                edit_brake=evidence.as_dict() if evidence else None,
                rewrite_attempts=attempts,
            )
        assert evidence is not None
        retry_guidance = retry_feedback(evidence, attempt)
    raise AssertionError("unreachable")


async def rewrite_skill(
    backend: LLMBackend,
    skill: Skill,
    reflections: list[dict[str, Any]],
    task_instruction: str = "",
    task_filter: str | None = None,
    manifest: SplitManifest | None = None,
    include_best_trace_code: bool = True,
    *,
    version_decay: bool = True,
    max_rewrite_attempts: int = 1,
    promotion_count: int | None = None,
    parent_version: str | None = None,
    base_budget: float | None = None,
) -> str:
    """Use reflections + task context to generate an improved skill body.

    Thin compatibility wrapper around :func:`rewrite_skill_with_audit`.
    Existing callers keep the historical ``str`` return type.
    """
    outcome = await rewrite_skill_with_audit(
        backend,
        skill,
        reflections,
        task_instruction=task_instruction,
        task_filter=task_filter,
        manifest=manifest,
        include_best_trace_code=include_best_trace_code,
        version_decay=version_decay,
        max_rewrite_attempts=max_rewrite_attempts,
        promotion_count=promotion_count,
        parent_version=parent_version,
        base_budget=base_budget,
    )
    if outcome.candidate_status == SIZE_VIOLATION:
        # Historical behaviour raised here; preserve for callers that don't
        # consume the structured outcome.
        raise ValueError("Rewritten skill body " + outcome.reason)
    return outcome.body
