"""Agentic-session rewrite backend: unified diagnose-and-edit session."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

from evolution import config
from evolution.core.models import Skill, SkillFrontmatter
from evolution.core.parser import parse_skill_md, write_skill_md
from evolution.evolve._legacy_prompts import load_legacy_prompt
from evolution.evolve.preservation import score_preservation
from evolution.evolve.rewrite_common import (
    _SEVERITY_RANK,
    _candidate_added_new_heading,
    _candidate_root,
    _cleanup_candidate,
    _non_empty_line_churn,
    _parent_top_headings,
    _reject_leaked_rewrite,
    _rewrite_provenance,
)
from evolution.evolve.rewrite_guards import (
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
    REWRITE_ERROR_BACKEND,
    REWRITE_ERROR_CODEX,
    SANITIZE_ERROR,
    SIZE_VIOLATION,
    RewriteOutcome,
)
from evolution.evolve.rewrite_sanitize import sanitize_rewritten_body
from evolution.evolve.session_workspace import (
    SessionWorkspaceError,
    build_session_workspace,
    cleanup_session_workspace,
)
from evolution.llm.agent_backend import AgentBackend, AgentBackendError
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest

if TYPE_CHECKING:
    from evolution.eval.task import Task
    from evolution.evolve.session_workspace import SessionWorkspace

logger = logging.getLogger(__name__)


SESSION_SYSTEM_BLIND = load_legacy_prompt("session_system_blind")

SESSION_SYSTEM_ORACLE = load_legacy_prompt("session_system_oracle")

SESSION_PROMPT = load_legacy_prompt("session_prompt")


def _parse_diagnosis_json(session_dir: Path) -> dict | None:
    """Read the agent-written ``DIAGNOSIS.json``; ``None`` if missing/malformed.

    Missing or malformed is treated by the caller as ``insufficient`` →
    conservative no-op (safe default).
    """
    p = session_dir / "DIAGNOSIS.json"
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return raw if isinstance(raw, dict) else None


def _session_has_progress(ws: SessionWorkspace, parent_body: str) -> bool:
    """True if an errored/timed-out session left salvageable on-disk output.

    Either a written ``DIAGNOSIS.json`` or an edited ``SKILL.md`` counts; the
    downstream lift->gate path re-validates whatever is salvaged, so an
    unparseable edit is still progress (the gate rejects it cleanly).
    """
    if (ws.session_dir / "DIAGNOSIS.json").is_file():
        return True
    try:
        _fm, body = parse_skill_md(ws.skill_path)
    except Exception as exc:
        logger.debug(
            "_session_has_progress: unparseable SKILL.md, treating existence as progress: %s",
            exc,
        )
        return ws.skill_path.exists()
    return body != parent_body


def _diagnosis_to_reflection(diag: dict) -> dict:
    """Map a session ``DIAGNOSIS.json`` into a reflection-shaped audit record."""
    sev = str(diag.get("severity") or "info").lower()
    if sev not in _SEVERITY_RANK:
        sev = "info"
    suff = str(diag.get("evidence_sufficiency") or "insufficient").lower()
    if suff not in ("sufficient", "insufficient"):
        suff = "insufficient"
    return {
        "pattern": str(diag.get("consensus_pattern") or ""),
        "root_cause": str(diag.get("root_cause") or ""),
        "skill_gap": str(diag.get("skill_gap") or ""),
        "suggested_fix": str(diag.get("suggested_fix") or ""),
        "severity": sev,
        "evidence_sufficiency": suff,
        "rewrite_recommended": bool(diag.get("rewrite_recommended", False)),
    }


def _session_round_banner(row_id: str) -> str:
    """Cosmetic ` (round N)` suffix parsed from ``row{N}__…`` row ids."""
    m = re.match(r"row(\d+)", row_id or "")
    return f" — round {m.group(1)}" if m else ""


async def _rewrite_skill_agentic_session_impl(
    backend: LLMBackend,
    skill: Skill,
    task: Task | None,
    task_instruction: str,
    task_filter: str | None,
    manifest: SplitManifest | None,
    *,
    audit_root: Path | None,
    row_id: str,
    debug_archive: bool,
    model_id: str,
) -> RewriteOutcome:
    """Run ONE multi-turn agentic session per evolve round (EVO_REWRITE_MODE=agentic-session).

    The agent explores raw train traces in a rich scratch workspace, diagnoses
    the recurring procedural gap, edits SKILL.md in place, and self-validates by
    writing+running a candidate solve. We lift ONLY the edited SKILL.md, then run
    the SAME post-exit validators as the file-edit path. Selection authority stays
    with the downstream δ-gate; the session's self-score is diagnostic only.
    """
    parent_body = skill.body
    _budget_frac, base_prov = _rewrite_provenance(skill)

    # 0. Fail-fast on misconfiguration (no silent degrade).
    if not isinstance(backend, AgentBackend):
        raise RuntimeError(
            "EVO_REWRITE_MODE=agentic-session requires an AgentBackend; "
            f"got {type(backend).__name__}"
        )
    if task is None:
        return RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_BACKEND,
            reason="agentic-session requires a Task to build the workspace; got None",
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            **base_prov,
        )

    # 1. Same leakage assertion as file-edit; the train/test split is the boundary.
    if manifest is not None and task_filter:
        manifest.assert_no_leakage(
            [task_filter],
            scope="skill_evolution",
            context="rewrite_skill_with_audit(agentic_session,task_filter)",
        )

    limits = rewrite_size_limits(skill, skill.body)
    parent_headings = _parent_top_headings(skill.body)
    preserve_text = "\n".join(f"- {h}" for h in parent_headings) if parent_headings else "(none)"

    # 2. Build the rich, oracle-pruned scratch workspace.
    try:
        ws = build_session_workspace(skill, task, task_filter=task_filter, manifest=manifest)
    except SessionWorkspaceError as exc:
        return RewriteOutcome(
            body=parent_body,
            candidate_status=REWRITE_ERROR_BACKEND,
            reason=f"session workspace build failed: {exc!s}"[:500],
            preservation=None,
            codex_usage=None,
            candidate_debug_dir=None,
            model_id=model_id,
            parent_body=parent_body,
            candidate_body_raw=None,
            **base_prov,
        )

    # 3. Compose the round-protocol prompt; blind/oracle system per EVO_REFLECT_BLIND.
    blind = config.reflect_blind()
    system = SESSION_SYSTEM_BLIND if blind else SESSION_SYSTEM_ORACLE
    prompt = SESSION_PROMPT.format(
        round_banner=_session_round_banner(row_id),
        round_context="",
        rejected_context="",
        task_instruction=task_instruction or "(not provided)",
        preserve_headings=preserve_text,
        n_traces=len(ws.trace_ids),
        source_models=", ".join(ws.source_models) if ws.source_models else "(unknown)",
        max_chars=limits["max_chars"],
        max_lines=limits["max_lines"],
    )
    try:
        (ws.session_dir / "TASK.md").write_text(prompt, encoding="utf-8")
    except OSError:
        pass

    # 3b. Read-only fallback: EVO_SESSION_SELF_VALIDATE=0 strips the run scripts.
    self_validate = os.environ.get("EVO_SESSION_SELF_VALIDATE", "1") != "0"
    if not self_validate:
        for f in (ws.solve_sh, ws.measure_sh):
            try:
                Path(f).unlink()
            except OSError:
                pass

    def _env_float(name: str) -> float | None:
        v = os.environ.get(name)
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    budget = _env_float("EVO_SESSION_BUDGET_USD")
    timeout = _env_float("EVO_SESSION_TIMEOUT_S")

    # 4. Run the session. Non-zero rc is captured, not raised — the agent may
    #    have made useful partial progress; we decide from the SKILL.md on disk.
    codex_usage: dict | None = None
    codex_diag: dict | None = None
    try:
        await backend.complete_agent_session(
            ws.session_dir, prompt, system, budget_usd=budget, timeout_s=timeout
        )
        codex_usage = dict(getattr(backend, "last_usage", {}) or {})
        codex_diag = dict(getattr(backend, "last_codex_diagnostics", {}) or {})
    except AgentBackendError as exc:
        codex_usage = dict(getattr(backend, "last_usage", {}) or {})
        codex_diag = dict(getattr(backend, "last_codex_diagnostics", {}) or {})
        # Salvage on-disk progress: a timeout/error mid-session may still leave an
        # edited SKILL.md or a written DIAGNOSIS.json. The lift->gate path below
        # (isolation/leak/size/churn/delta-gate) protects integrity, so we only
        # bail outright when the agent left nothing to gate.
        codex_diag["session_error"] = str(exc)[:300]
        codex_diag["session_timed_out"] = "timed out" in str(exc).lower()
        if not _session_has_progress(ws, parent_body):
            cleanup_session_workspace(ws)
            return RewriteOutcome(
                body=parent_body,
                candidate_status=REWRITE_ERROR_CODEX,
                reason=f"agentic session failed: {exc!s}"[:500],
                preservation=None,
                codex_usage=codex_usage or None,
                candidate_debug_dir=None,
                model_id=model_id,
                parent_body=parent_body,
                candidate_body_raw=None,
                codex_diagnostics=codex_diag or None,
                **base_prov,
            )

    # 5. Parse the agent's DIAGNOSIS.json (the reflection-contract bridge) and
    #    attach it to the audit diagnostics so every outcome below carries it.
    diag = _parse_diagnosis_json(ws.session_dir)
    reflection_record = _diagnosis_to_reflection(diag) if diag else None
    if codex_diag is None:
        codex_diag = {}
    codex_diag["session_diagnosis"] = diag
    codex_diag["session_reflection_record"] = reflection_record
    codex_diag["session_trace_ids"] = list(ws.trace_ids)
    codex_diag["session_source_models"] = list(ws.source_models)
    codex_diag["session_self_validate"] = self_validate
    if diag is not None:
        codex_diag["session_best_self_score"] = diag.get("best_self_score")
        codex_diag["session_rounds_self_run"] = diag.get("rounds_self_run")

    # 6. Lift ONLY the edited SKILL.md into a clean candidate dir, drop the rest.
    candidate_dir = _candidate_root() / f"evo_sess_c_{uuid.uuid4().hex}"
    candidate_dir.mkdir(parents=True, exist_ok=False)
    candidate_skill_path = candidate_dir / "SKILL.md"
    try:
        shutil.copy2(ws.skill_path, candidate_skill_path)
    finally:
        cleanup_session_workspace(ws)

    # 7. Hard isolation validator (candidate dir holds exactly SKILL.md).
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

    # 8. Parse candidate, reattach parent frontmatter (runtime safety net).
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

    parent_fm_raw, _ = parse_skill_md(skill.skill_md_path)
    parent_fm_validated = SkillFrontmatter.model_validate(parent_fm_raw)
    write_skill_md(candidate_skill_path, parent_fm_validated, candidate_body_raw)
    _re_fm, candidate_body = parse_skill_md(candidate_skill_path)

    _new_added, _new_headings_list = _candidate_added_new_heading(parent_body, candidate_body)
    cand_prov: dict[str, Any] = {
        **base_prov,
        "candidate_body_sha256": hashlib.sha256(candidate_body.encode("utf-8")).hexdigest(),
        "computed_churn": _non_empty_line_churn(parent_body, candidate_body),
        "new_headings": list(_new_headings_list),
    }

    # 9. No-op: the agent concluded the parent already handles the gap.
    if candidate_body == parent_body:
        preservation = score_preservation(
            parent_body, candidate_body, parent_fm_raw, candidate_fm_raw
        )
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=NO_OP_FILE_EDIT,
            reason="candidate SKILL.md body byte-equal to parent (session made no edit)",
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

    # 10. Low-confidence gate — DIAGNOSIS.json is the authoritative signal for
    #     this mode (the agent diagnoses from raw traces, not pre-digested
    #     reflections). Missing/insufficient/not-recommended ⇒ conservative no-op
    #     restoring the parent (safe default).
    rr = reflection_record or {}
    if (
        diag is None
        or not rr.get("rewrite_recommended")
        or rr.get("evidence_sufficiency") == "insufficient"
    ):
        if diag is None:
            reason = "no/malformed DIAGNOSIS.json from session ⇒ treated as insufficient"
        elif not rr.get("rewrite_recommended"):
            # Section 9 already returned on byte-equal, so a real edit exists here:
            # the agent edited SKILL.md yet set rewrite_recommended=false. Flag the
            # contradiction (outcome stays the conservative no-op).
            codex_diag["session_recommend_edit_contradiction"] = True
            reason = "session edited SKILL.md but set rewrite_recommended=false; keeping parent"
        else:
            reason = "session reported evidence_sufficiency=insufficient; keeping parent"
        outcome = RewriteOutcome(
            body=parent_body,
            candidate_status=LOW_CONFIDENCE_REFLECTION,
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

    # 11. No-new-heading guard skipped in session mode: the agent's focused
    #     sub-section for a diagnosed gap is a valid minimal fix; leak + size cap
    #     + δ-gate (held-back train_b) are the integrity boundary. _new_headings
    #     stays in cand_prov for audit telemetry.

    # 12. Sanitize + leak guard + size cap (reuse text-return validators).
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

    # 13. Promote-eligible candidate; downstream δ-gate is the selection authority.
    preservation = score_preservation(parent_body, candidate_body, parent_fm_raw, candidate_fm_raw)
    outcome = RewriteOutcome(
        body=candidate_body,
        candidate_status=PROMOTED_ELIGIBLE,
        reason="agentic-session rewrite produced a candidate",
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
