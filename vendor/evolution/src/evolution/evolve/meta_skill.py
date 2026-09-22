"""Cross-round optimizer memory distilled from prior δ-gate records.

Each completed round of ``evolve_skills_one_round`` writes a
``round_record_<timestamp>.json`` into ``<skill_path>/.evolution/`` capturing
the promotion-gate outcome plus a summary of the reflections that informed
the rewrite. At the start of the next round's reflect call,
:func:`build_meta_skill` reads every record on disk and renders a compact
text blob that the reflector includes in its prompt as
``## Cross-Round Learning``.

The blob is template-rendered (no extra LLM call) and tail-bounded to
``char_cap`` so prompt-budget stays predictable.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "evolution-round-record-v1"

_ROUND_RECORD_GLOB = "round_record_*.json"

PROMOTED_ELIGIBLE = "promoted_eligible"

# Canonical, status-derived rejection vocabulary (rev F1). The raw rewrite-guard
# message can embed train-specific literals (a leaked identifier, an expected
# value), so the buffer never echoes it back to the next reflector — only this
# fixed string keyed off ``candidate_status``.
_REJECT_REASON = {
    "leak_rejected": "candidate copied train-specific literals (leak scanner)",
    "size_violation": "candidate exceeded the skill size ceiling",
    "low_confidence_reflection": "fewer than half the reflections were actionable",
    "no_op_text": "rewrite returned the parent body unchanged",
    "no_op_file_edit": "file-edit rewrite made no change",
    "sanitize_error": "candidate body failed sanitization",
    "candidate_invalid_extra_files": "candidate added disallowed files",
    "candidate_invalid_symlink": "candidate introduced a symlink",
    "candidate_invalid_hidden_file": "candidate added a hidden file",
    "candidate_invalid_path_escape": "candidate wrote outside the skill dir",
    "candidate_invalid_frontmatter_corrupt": "candidate frontmatter was corrupt",
    "candidate_invalid_new_heading": "candidate introduced a disallowed new heading",
    "candidate_edit_budget_exceeded": "candidate edited more than the budget allowed",
    "rewrite_error_codex": "rewriter (codex) errored",
    "rewrite_error_backend": "rewriter backend errored",
}

_REJECTED_FOOTER = (
    "These are prior-round rejections; the current evidence may demand similar "
    "edits if circumstances differ — diagnose from evidence first, the buffer "
    "second."
)


def round_records_dir(skill_path: Path) -> Path:
    return skill_path / ".evolution"


def write_round_record(skill_path: Path, record: dict[str, Any]) -> Path:
    """Atomically write one round record under ``<skill>/.evolution/``."""
    out_dir = round_records_dir(skill_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = record.get("timestamp") or ""
    fname = f"round_record_{ts or 'unknown'}.json"
    target = out_dir / fname
    payload = dict(record)
    payload.setdefault("schema", SCHEMA)
    data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=".round_record_", dir=str(out_dir))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return target


def load_round_records(skill_path: Path) -> list[dict[str, Any]]:
    out_dir = round_records_dir(skill_path)
    if not out_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for p in sorted(out_dir.glob(_ROUND_RECORD_GLOB)):
        try:
            records.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return records


def build_meta_skill(skill_path: Path, *, char_cap: int = 4000) -> str:
    """Render prior-round PROMOTE/ROLLBACK history into a reflector-prompt blob."""
    records = load_round_records(skill_path)
    if not records:
        return ""

    lines: list[str] = []
    for idx, rec in enumerate(records, 1):
        status = str(rec.get("gate_status") or "unknown")
        parent = str(rec.get("parent_version") or "?")
        candidate = str(rec.get("candidate_version") or "?")
        delta = rec.get("delta")
        try:
            delta_str = "Δ=?" if delta is None else f"Δ={float(delta):+.3f}"
        except (TypeError, ValueError):
            delta_str = "Δ=?"
        pat_f = rec.get("dominant_failure_pattern") or "-"
        pat_s = rec.get("dominant_success_pattern") or "-"
        n_f = int(rec.get("n_failure_reflections") or 0)
        n_s = int(rec.get("n_success_reflections") or 0)
        reason_lines = str(rec.get("reason") or "").splitlines()
        reason = reason_lines[0][:120] if reason_lines else ""
        head = f"- R{idx}: {status} {parent}->{candidate} ({delta_str})"
        body = f"failures={n_f} (top: {pat_f}); successes={n_s} (top: {pat_s})"
        line = f"{head}; {body}"
        if reason:
            line = f"{line}; reason: {reason}"
        lines.append(line)

    n_promote = sum(1 for r in records if r.get("gate_status") == "promoted")
    n_rollback = sum(
        1 for r in records if str(r.get("gate_status") or "").startswith("rolled_back")
    )
    n_noop = sum(1 for r in records if r.get("gate_status") == "no_op")
    summary = (
        f"Prior rounds: {len(records)} total — "
        f"{n_promote} PROMOTE, {n_rollback} ROLLBACK, {n_noop} NO_OP."
    )

    header = f"{summary}\nRound-by-round outcome:"
    blob = "\n".join([header, *lines]).strip()

    if len(blob) <= char_cap:
        return blob
    keep_lines = lines
    while keep_lines and len("\n".join([header, *keep_lines])) > char_cap:
        keep_lines = keep_lines[1:]
    if not keep_lines:
        return summary[:char_cap]
    elided = len(lines) - len(keep_lines)
    note = f"(earliest {elided} round(s) elided to fit char_cap={char_cap})"
    return "\n".join([header, note, *keep_lines])


def summarize_reflection_audit(audit: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce a ``reflection_audit.reflections`` list to round-record fields."""
    n_f = 0
    n_s = 0
    fail_patterns: dict[str, int] = {}
    succ_patterns: dict[str, int] = {}
    for r in audit or []:
        kind = str(r.get("kind") or "failure")
        pat = str(r.get("pattern") or "unknown")
        if kind == "success":
            n_s += 1
            succ_patterns[pat] = succ_patterns.get(pat, 0) + 1
        else:
            n_f += 1
            fail_patterns[pat] = fail_patterns.get(pat, 0) + 1

    def _top(d: dict[str, int]) -> str | None:
        if not d:
            return None
        return max(d.items(), key=lambda kv: kv[1])[0]

    return {
        "n_failure_reflections": n_f,
        "n_success_reflections": n_s,
        "dominant_failure_pattern": _top(fail_patterns),
        "dominant_success_pattern": _top(succ_patterns),
    }


def canonical_reject_reason(candidate_status: str | None) -> str:
    if not candidate_status:
        return "rewrite rejected"
    return _REJECT_REASON.get(candidate_status, f"rewrite rejected ({candidate_status})")


def build_rejected_entry(
    *,
    row_id: str,
    candidate_status: str,
    computed_churn: float | None = None,
    new_headings: list[str] | None = None,
    n_actionable: int = 0,
    n_low_confidence: int = 0,
) -> dict[str, Any]:
    """One ``rejected`` sub-record persisted when a rewrite did not promote."""
    return {
        "row_id": row_id,
        "candidate_status": candidate_status,
        "reason": canonical_reject_reason(candidate_status),
        "computed_churn": computed_churn,
        "new_headings": list(new_headings or []),
        "counts": {
            "n_actionable": int(n_actionable),
            "n_low_confidence": int(n_low_confidence),
            "leak_rejected": candidate_status == "leak_rejected",
        },
    }


def build_rejected_edits_context(
    skill_path: Path,
    *,
    k: int | None = None,
    char_cap: int | None = None,
    window: int | None = None,
    row_id: str | None = None,
) -> str:
    """Render prior-round rewrite *rejections* into a reflector-prompt blob.

    Fixed-schema bullets only (``round``/``status``/``churn``/``new_headings``/
    ``counts`` — rev F2); the free-text reason never reaches the prompt. Returns
    ``""`` on round 1 or when no rejection lies inside the freshness window.
    """
    if k is None:
        k = int(os.environ.get("EVO_REFLECT_REJECTED_K", "5") or "5")
    if char_cap is None:
        char_cap = int(os.environ.get("EVO_REFLECT_REJECTED_CHARS", "3000") or "3000")
    if window is None:
        window = int(os.environ.get("EVO_REFLECT_REJECTED_WINDOW", "3") or "3")
    if row_id is None:
        row_id = os.environ.get("EVO_REFLECT_ROW_ID") or ""

    rejected: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for rec in load_round_records(skill_path):
        rj = rec.get("rejected")
        if not isinstance(rj, dict):
            continue
        if row_id and rj.get("row_id") and rj.get("row_id") != row_id:
            continue
        rejected.append((rec, rj))
    if not rejected:
        return ""
    if window > 0:
        rejected = rejected[-window:]
    if k > 0:
        rejected = rejected[-k:]

    header = "Prior-round rewrite rejections (most recent last):"
    lines: list[str] = []
    for rec, rj in rejected:
        rnd = rec.get("round")
        rnd_str = f"R{rnd}" if rnd else "R?"
        status = rj.get("candidate_status") or "?"
        churn = rj.get("computed_churn")
        churn_str = f"{float(churn):.2f}" if isinstance(churn, (int, float)) else "?"
        heads = rj.get("new_headings") or []
        heads_str = ", ".join(str(h) for h in heads[:6]) if heads else "(none)"
        counts = rj.get("counts") or {}
        c_str = (
            f"actionable={counts.get('n_actionable', '?')}, "
            f"low_conf={counts.get('n_low_confidence', '?')}, "
            f"leak={int(bool(counts.get('leak_rejected')))}"
        )
        lines.append(
            f"- {rnd_str}: status={status}; churn={churn_str}; "
            f"new_headings=[{heads_str}]; counts({c_str})"
        )

    def _assemble(keep: list[str]) -> str:
        return "\n".join([header, *keep]) + "\n\n" + _REJECTED_FOOTER

    blob = _assemble(lines)
    if len(blob) <= char_cap:
        return blob
    keep = lines
    while keep and len(_assemble(keep)) > char_cap:
        keep = keep[1:]
    if not keep:
        return (header + "\n\n" + _REJECTED_FOOTER)[:char_cap]
    return _assemble(keep)
