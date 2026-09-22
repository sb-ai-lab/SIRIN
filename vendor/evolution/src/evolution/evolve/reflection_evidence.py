"""Prompt-safe rendering and provenance checks for trace evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path

from evolution.eval.evidence import TRAIN_EVIDENCE_SCHEMA, TRAIN_EVIDENCE_SCOPES
from evolution.splits import SplitManifest

EVIDENCE_UNAVAILABLE = "(unavailable: no evidence packet)"

# Provenance gate accepts v3 (legacy), v4 (split-controlled feedback), and v5
# (optional oracle_evidence). build_evidence always emits the newest; old
# traces stay reflectable ad-hoc.
_ACCEPTED_SCHEMAS = (
    "evolution-trace-evidence-v3",
    "evolution-trace-evidence-v4",
    "evolution-trace-evidence-v5",
    TRAIN_EVIDENCE_SCHEMA,
)

TRAIN_EVIDENCE_MAX_CHARS = int(os.environ.get("EVO_TRAIN_EVIDENCE_MAX_CHARS", "200000") or "200000")
_EDITOR_CONTROL_FIELDS = frozenset({"task", "task_id", "score", "delta", "gate_reason", "memory"})

ORACLE_TOTAL_CHARS = int(os.environ.get("EVO_REFLECT_ORACLE_TOTAL_CHARS", "12000") or "12000")

# Guardrail rendered immediately above the oracle blocks so the split boundary
# sits next to the tempting literals (weak local models under-weight the system
# prompt).
ORACLE_LEAD_IN = (
    "> **Training verifier evidence.** The sections below are from training "
    "traces: test source, expected values, failed-test names, and traceback may "
    "be used to localize the skill gap and improve train performance. The hard "
    "boundary is held-out validation/test evidence, which must never be used "
    "for skill evolution or stopping. Prefer a reusable procedure when the "
    "training evidence supports one."
)

# Source feedback is only rendered for collect-phase diagnosis traces.
# promotion_validation traces never surface it (see CLAUDE.md).
_FEEDBACK_PHASES = (None, "", "collect")


def normalize_train_evidence(
    evidence: dict | None,
    *,
    allow_legacy: bool = False,
) -> dict:
    """Return a train-only packet or reject it before editor rendering."""
    if not isinstance(evidence, dict):
        raise ValueError("train evidence is missing")
    packet = (
        evidence
        if evidence.get("schema") == TRAIN_EVIDENCE_SCHEMA
        else ((evidence.get("failure_evidence") or {}).get("train_evidence"))
    )
    if isinstance(packet, dict) and packet.get("schema") == TRAIN_EVIDENCE_SCHEMA:
        records = packet.get("records")
        if not isinstance(records, list):
            raise ValueError("train evidence packet records must be a list")
        for index, record in enumerate(records):
            if not isinstance(record, dict) or record.get("scope") not in TRAIN_EVIDENCE_SCOPES:
                raise ValueError(f"train evidence record {index} is outside train scope")
        return packet
    if not allow_legacy:
        raise ValueError("editor requires a train-evidence-v1 packet")
    phase = (evidence.get("trace_context") or {}).get("phase")
    if phase not in TRAIN_EVIDENCE_SCOPES:
        raise ValueError(f"legacy evidence has no permitted train scope: {phase!r}")
    return {
        "schema": TRAIN_EVIDENCE_SCHEMA,
        "scope": "train",
        "legacy_provenance": True,
        "records": [{"scope": phase, "legacy_record": evidence}],
    }


def render_train_evidence(evidence: dict | None) -> str:
    """Render bounded train evidence without gate/control metadata."""
    packet = normalize_train_evidence(evidence)

    def without_editor_controls(value):
        if isinstance(value, dict):
            return {
                key: without_editor_controls(item)
                for key, item in value.items()
                if key not in _EDITOR_CONTROL_FIELDS
            }
        if isinstance(value, list):
            return [without_editor_controls(item) for item in value]
        return value

    records = [without_editor_controls(record) for record in packet["records"]]
    return json.dumps(
        {"schema": TRAIN_EVIDENCE_SCHEMA, "scope": "train", "records": records},
        ensure_ascii=False,
        indent=2,
        default=str,
    )[:TRAIN_EVIDENCE_MAX_CHARS]


def render_solve_diag(evidence: dict | None) -> tuple[str, str, str]:
    if not evidence:
        return (EVIDENCE_UNAVAILABLE, EVIDENCE_UNAVAILABLE, EVIDENCE_UNAVAILABLE)
    diag = evidence.get("agent_solve")
    if not isinstance(diag, dict):
        return (EVIDENCE_UNAVAILABLE, EVIDENCE_UNAVAILABLE, EVIDENCE_UNAVAILABLE)
    return (
        str(diag.get("exit_code", EVIDENCE_UNAVAILABLE)),
        str(diag.get("timeout", EVIDENCE_UNAVAILABLE)),
        str(diag.get("diagnostic", EVIDENCE_UNAVAILABLE)),
    )


def render_artifacts(evidence: dict | None) -> str:
    if not evidence or "produced_artifacts" not in evidence:
        return EVIDENCE_UNAVAILABLE
    artifacts = evidence.get("produced_artifacts")
    if isinstance(artifacts, str):
        if artifacts.startswith("(unavailable:"):
            return artifacts
        return "(artifact metadata withheld: invalid v3 shape)"
    if not artifacts:
        return EVIDENCE_UNAVAILABLE

    lines: list[str] = []
    for entry in artifacts:
        if not isinstance(entry, dict):
            continue
        if "note" in entry and "path" not in entry:
            note = str(entry["note"])
            if note.startswith("(artifact list capped at "):
                lines.append(f"- {note}")
            else:
                lines.append("- (artifact note withheld: invalid v3 shape)")
            continue
        lines.append(
            f"- status={entry.get('status', '?')}, "
            f"size={entry.get('size', '?')}, "
            f"suffix={entry.get('suffix', '?')}"
        )
    return "\n".join(lines) if lines else EVIDENCE_UNAVAILABLE


def render_failure_evidence(evidence: dict | None) -> str:
    if not evidence or not isinstance(evidence.get("failure_evidence"), dict):
        return EVIDENCE_UNAVAILABLE
    fe = evidence["failure_evidence"]
    lines: list[str] = []
    cats = fe.get("failure_categories") or []
    lines.append(f"categories: {', '.join(cats) if cats else '(none)'}")
    lines.append(f"code_generation: {fe.get('code_generation_status', '?')}")
    vr = fe.get("verifier_result") or {}
    lines.append(
        f"verification: {vr.get('verification_category', '?')} "
        f"(passed={vr.get('passed', '?')}/{vr.get('total', '?')})"
    )
    se = fe.get("solve_exception")
    if isinstance(se, dict):
        lines.append(f"solve_exception: {se.get('type', '?')} (frame: {se.get('frame', '?')})")
    else:
        lines.append("solve_exception: (none)")
    lines.append(
        f"required_outputs: count={fe.get('required_output_count', 0)} "
        f"suffixes={fe.get('required_output_suffixes', [])} "
        f"missing={fe.get('missing_declared_output_count', '(n/a)')}"
    )
    pos = fe.get("produced_outputs") or []
    if pos:
        lines.append("produced_outputs (shape only):")
        for po in pos:
            if isinstance(po, dict):
                lines.append(f"- suffix={po.get('suffix', '?')} shape={po.get('shape')}")
    sf = fe.get("source_feedback")
    phase = (evidence.get("trace_context") or {}).get("phase")
    if isinstance(sf, dict) and phase in _FEEDBACK_PHASES:
        lines.append("source execution feedback (sanitized; source/local task only):")
        if sf.get("exception_class"):
            lines.append(f"- exception_class: {sf.get('exception_class')}")
        lines.append(f"- exit_code={sf.get('exit_code')} timeout={sf.get('timeout')}")
        for key in ("stderr_tail", "pytest_error_tail"):
            val = (sf.get(key) or "").strip()
            if val:
                lines.append(f"- {key}:\n{val}")
    return "\n".join(lines)


def _oracle_evidence(evidence: dict | None) -> dict | None:
    fe = (evidence or {}).get("failure_evidence")
    if not isinstance(fe, dict):
        return None
    oe = fe.get("oracle_evidence")
    return oe if isinstance(oe, dict) else None


def render_test_source(evidence: dict | None) -> str:
    """Oracle-visible test source; ``""`` when blind/absent."""
    oe = _oracle_evidence(evidence)
    src = (oe or {}).get("tests_source") or ""
    if not src.strip():
        return ""
    return f"```python\n{src}\n```"


def render_failed_tests(evidence: dict | None) -> str:
    oe = _oracle_evidence(evidence)
    failed = (oe or {}).get("failed_tests") or []
    lines: list[str] = []
    for ft in failed:
        if not isinstance(ft, dict):
            continue
        nodeid = ft.get("nodeid", "?")
        tail = (ft.get("message_tail") or "").strip()
        lines.append(f"- {nodeid}" + (f" — {tail}" if tail else ""))
    return "\n".join(lines)


def render_pytest_traceback(evidence: dict | None) -> str:
    oe = _oracle_evidence(evidence)
    tb = (oe or {}).get("pytest_traceback") or ""
    if not tb.strip():
        return ""
    return f"```\n{tb}\n```"


def render_source_artifacts(evidence: dict | None) -> str:
    oe = _oracle_evidence(evidence)
    arts = (oe or {}).get("source_artifacts") or []
    lines: list[str] = []
    for a in arts:
        if not isinstance(a, dict):
            continue
        if "note" in a and "path" not in a:
            lines.append(f"- {a['note']}")
            continue
        lines.append(
            f"- {a.get('path', '?')} (size={a.get('size', '?')}, suffix={a.get('suffix', '?')})"
        )
        content = a.get("content")
        if content:
            lines.append(f"  ```\n  {content}\n  ```")
    return "\n".join(lines)


def render_oracle_sections(evidence: dict | None) -> str:
    """Fold the four oracle blocks under headings, aggregate char-capped (rev C1).

    Returns ``""`` when the trace carries no ``oracle_evidence`` (blind mode or
    legacy v3/v4 packet), so existing call sites are unaffected.
    """
    if _oracle_evidence(evidence) is None:
        return ""
    blocks = [
        ("Test Source", render_test_source(evidence)),
        ("Failed Tests", render_failed_tests(evidence)),
        ("Pytest Traceback", render_pytest_traceback(evidence)),
        ("Source Artifacts", render_source_artifacts(evidence)),
    ]
    out: list[str] = []
    total = 0
    for title, body in blocks:
        if not body:
            continue
        if total + len(body) > ORACLE_TOTAL_CHARS:
            out.append(f"## {title}\n(omitted: oracle render budget exceeded)")
            continue
        out.append(f"## {title}\n{body}")
        total += len(body)
    if not out:
        return ""
    return ORACLE_LEAD_IN + "\n\n" + "\n\n".join(out)


def validate_trace_provenance(
    *,
    trace: dict,
    trace_dir: Path,
    evidence: dict | None,
    manifest: SplitManifest | None,
    scope: str,
    require_v3_evidence: bool,
) -> None:
    if require_v3_evidence and (
        not evidence
        or evidence.get("schema") not in _ACCEPTED_SCHEMAS
        or not evidence.get("failure_evidence")
        or not evidence.get("trace_context")
    ):
        raise ValueError(
            f"provenance gate: failing trace {trace['id']!r} lacks a v3+ "
            f"evidence packet (expected {trace_dir / 'evidence.json'} "
            f"schema in {_ACCEPTED_SCHEMAS} with non-empty failure_evidence + "
            "trace_context). Reflection must consume only fresh "
            "current-run solves; refusing to reflect on a stale/preloaded/"
            "sparse trace."
        )

    if manifest is None:
        return

    trace_name = trace.get("manifest_name")
    trace_sha = trace.get("manifest_sha")
    trace_scope = trace.get("manifest_scope")
    if trace_sha != manifest.sha256 or trace_scope != scope:
        raise ValueError(
            f"provenance gate: failing trace {trace['id']!r} was not generated "
            "under the active reflection manifest "
            f"{manifest.name!r} ({manifest.sha256[:12]}) scope={scope!r}; "
            f"trace has manifest_name={trace_name!r}, "
            f"manifest_sha={(str(trace_sha)[:12] if trace_sha else None)!r}, "
            f"manifest_scope={trace_scope!r}. Refusing to reflect on a stale/"
            "cross-run/unscoped trace."
        )
