"""Metadata-only execution-evidence packet for skill-evolution traces (v3)."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any

from evolution import config
from evolution.eval.artifact_shape import shape_for

logger = logging.getLogger(__name__)

ARTIFACT_MAX_FILES = int(os.environ.get("EVO_TRACE_ARTIFACT_MAX_FILES", "80") or "80")

# Harness scaffold the solver/runner writes into the workspace — not a produced
# task artifact, so excluded from the manifest.
# ``pytest_output.txt`` (runner.py) is load-bearing here: it must stay excluded
# even if the substring coincidence with ``_FORBIDDEN_SUBSTR`` ("test_") changes.
_SCAFFOLD_NAMES = {
    "solution.py",
    "solve.sh",
    "prompt_audit.json",
    ".workspace_guard.jsonl",
    "pytest_output.txt",
}
_SCAFFOLD_PREFIXES = (
    "_",
)  # any underscore-prefixed path part: _prompt.md, _solve.py, _workspace_guard_bin/
# C1 rewrite-audit sidecar (``<row_id>_rewrite_audit.json``) and codex debug
# candidates (under ``c1_candidates/``) must never leak into produced_artifacts,
# or their structured payloads end up in the next-round leakage corpus.
# Memory ``feedback_audit_files_must_not_feed_evidence``.
_SCAFFOLD_SUFFIXES = ("_rewrite_audit.json",)
# Defensive: a workspace must never carry oracle material; never surface it
# even if a task layout is unusual.
_FORBIDDEN_SUBSTR = ("test_", "expected", "golden", "answer_key", "answerkey", "oracle")
_FORBIDDEN_DIRS = (".traces", "tests", "_hidden_tests", "c1_candidates", "audit")

_VALID_DIAGNOSTICS = {"ok", "nonzero_exit", "timeout", "exception", "unknown"}


def classify_solve(exit_code: int | None, timeout: bool) -> str:
    """Map a solve outcome to a coarse diagnostic class (no text)."""
    if timeout:
        return "timeout"
    if exit_code is None:
        return "unknown"
    if exit_code == 0:
        return "ok"
    if exit_code < 0:
        return "exception"  # killed by signal
    return "nonzero_exit"


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_workspace(workspace: Path) -> dict[str, str]:
    """Map relpath -> sha256 for every pre-existing file (the 'before' state).

    Called once at solve entry, before the solver writes anything. Fail-soft.
    """
    snap: dict[str, str] = {}
    try:
        workspace = Path(workspace)
        for p in workspace.rglob("*"):
            if not p.is_file():
                continue
            try:
                snap[str(p.relative_to(workspace))] = _sha256_file(p)
            except Exception as exc:
                logger.warning("snapshot_workspace: failed to hash %s: %s", p, exc)
                continue
    except Exception as exc:
        logger.warning("snapshot_workspace: scan failed for %s: %s", workspace, exc)
        return snap
    return snap


def _is_scaffold_or_forbidden(rel: str) -> bool:
    parts = Path(rel).parts
    if any(d in _FORBIDDEN_DIRS for d in parts):
        return True
    if any(part.startswith(_SCAFFOLD_PREFIXES) for part in parts):
        return True
    name = Path(rel).name
    if name in _SCAFFOLD_NAMES:
        return True
    if name.endswith(_SCAFFOLD_SUFFIXES):
        return True
    low = rel.lower()
    return any(s in low for s in _FORBIDDEN_SUBSTR)


def _produced_manifest(workspace: Path, pre: dict[str, str]) -> list[dict[str, Any]] | str:
    """Metadata of files created/modified by the solver vs the pre-snapshot.

    Per file: path, status, size, sha256, suffix — NO content preview. Excludes
    harness scaffold, forbidden/oracle-shaped names, and byte-for-byte copies of
    pre-existing inputs (same sha256 as any snapshot entry).
    """
    try:
        pre_hashes = set(pre.values())
        out: list[dict[str, Any]] = []
        workspace = Path(workspace)
        for p in sorted(workspace.rglob("*")):
            if len(out) >= ARTIFACT_MAX_FILES:
                out.append({"note": f"(artifact list capped at {ARTIFACT_MAX_FILES})"})
                break
            if not p.is_file():
                continue
            try:
                rel = str(p.relative_to(workspace))
            except Exception as exc:
                logger.warning("produced_manifest: relpath failed for %s: %s", p, exc)
                continue
            if _is_scaffold_or_forbidden(rel):
                continue
            try:
                digest = _sha256_file(p)
            except Exception as exc:
                logger.warning("produced_manifest: failed to hash %s: %s", p, exc)
                continue
            if pre.get(rel) == digest:
                continue  # unchanged pre-existing input
            if digest in pre_hashes:
                continue  # byte-copy of a pre-existing input/expected
            out.append(
                {
                    "path": rel,
                    "status": "modified" if rel in pre else "created",
                    "size": p.stat().st_size,
                    "sha256": digest,
                    "suffix": p.suffix.lower(),
                }
            )
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("produced_manifest: manifest build failed for %s: %s", workspace, exc)
        return f"(unavailable: artifact manifest failed: {type(exc).__name__})"


def produced_paths(workspace: Path, pre: dict[str, str]) -> list[str]:
    """Rel-paths of solver-produced files vs the pre-snapshot (uncapped).

    Same exclusions as the evidence manifest (scaffold/forbidden/oracle names,
    byte-identical copies of pre-existing inputs) but without the telemetry file
    cap: output placement must be complete, not bounded. Fail-soft.
    """
    pre = pre or {}
    pre_hashes = set(pre.values())
    out: list[str] = []
    try:
        workspace = Path(workspace)
        for p in sorted(workspace.rglob("*")):
            if not p.is_file():
                continue
            try:
                rel = str(p.relative_to(workspace))
            except Exception as exc:
                logger.warning("produced_paths: relpath failed for %s: %s", p, exc)
                continue
            if _is_scaffold_or_forbidden(rel):
                continue
            try:
                digest = _sha256_file(p)
            except Exception as exc:
                logger.warning("produced_paths: failed to hash %s: %s", p, exc)
                continue
            if pre.get(rel) == digest:
                continue
            if digest in pre_hashes:
                continue
            out.append(rel)
    except Exception as exc:
        logger.warning("produced_paths: scan failed for %s: %s", workspace, exc)
        return out
    return out


SCHEMA = "evolution-trace-evidence-v5"
TRAIN_EVIDENCE_SCHEMA = "train-evidence-v1"
TRAIN_EVIDENCE_SCOPES = frozenset({"train", "collect"})

FEEDBACK_TAIL_CHARS = int(os.environ.get("EVO_FEEDBACK_TAIL_CHARS", "2000") or "2000")

# Phases that NEVER receive oracle_evidence, even when EVO_REFLECT_BLIND=0.
_NEVER_ORACLE_PHASES = {"promotion_validation", "held_out", "cross_role", "genm"}
REFLECT_TESTS_CHARS = int(os.environ.get("EVO_REFLECT_TESTS_CHARS", "4000") or "4000")
REFLECT_SRC_ARTIFACTS_MAX = int(os.environ.get("EVO_REFLECT_SRC_ARTIFACTS_MAX", "6") or "6")
REFLECT_SRC_ARTIFACTS_CHARS = int(os.environ.get("EVO_REFLECT_SRC_ARTIFACTS_CHARS", "800") or "800")
_TEXT_ARTIFACT_SUFFIXES = (".json", ".yaml", ".yml", ".toml", ".md", ".csv", ".txt")
_FAILED_LINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$")

# Lines that expose verifier intent / oracle values — dropped wholesale.
_FB_DROP_LINE = re.compile(
    r"(?:^|\s)(?:FAILED|ERROR)\s|::test_|\btests?/[\w/]*test[\w/]*\.py\b"
    r"|^E\s+(?:assert|where|and|\+|-|\?)|^\s*[+-]\s|^\s*\?\s"
)
# Literal redactions on surviving lines: long quoted strings, big numbers,
# absolute paths — anything that could carry an expected constant.
_FB_REDACT = (
    re.compile(r"""(['"])(?:[^'"\n]{6,})\1"""),
    re.compile(r"\b\d{4,}\b"),
    re.compile(r"(?:/[\w.\-]+){2,}"),
)


def sanitize_feedback(text: str | None, limit: int = FEEDBACK_TAIL_CHARS) -> str:
    """Drop verifier/oracle-bearing lines and redact literals; tail-bounded.

    Never emits pytest node ids, FAILED/ERROR lines, assertion-introspection
    (``E assert/where/+/-``), diff lines, long quoted strings, >=4-digit
    numbers, or absolute paths. Policy detail in CLAUDE.md.
    """
    if not text:
        return ""
    kept: list[str] = []
    for raw in str(text).splitlines():
        if _FB_DROP_LINE.search(raw):
            continue
        line = raw
        for pat in _FB_REDACT:
            line = pat.sub("<redacted>", line)
        kept.append(line)
    out = "\n".join(kept).strip()
    if len(out) > limit:
        out = out[-limit:]
    return out


def _produced_outputs(
    manifest: list[dict[str, Any]] | str, workspace: Path
) -> list[dict[str, Any]]:
    """Value-free structural shape per produced file (counts/classes only)."""
    if not isinstance(manifest, list):
        return []

    out: list[dict[str, Any]] = []
    for entry in manifest:
        rel = entry.get("path")
        if not rel:
            continue
        try:
            shape = shape_for(Path(workspace) / rel)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("produced_outputs: shape_for failed for %s: %s", rel, exc)
            shape = {"parse_ok": False, "error": type(exc).__name__}
        out.append({"path": rel, "suffix": entry.get("suffix", ""), "shape": shape})
    return out


def _required_outputs_summary(required_outputs, manifest) -> dict[str, Any]:
    """Counts/suffixes only — never literal required paths."""
    req = [str(r) for r in (required_outputs or []) if r]
    if not req:
        return {"required_output_count": 0, "required_output_suffixes": []}
    suffixes = sorted({Path(r).suffix.lower() for r in req if Path(r).suffix})
    produced = (
        {str(e.get("path", "")) for e in manifest if isinstance(e, dict)}
        if isinstance(manifest, list)
        else set()
    )
    prod_names = {Path(p).name for p in produced}
    missing = sum(1 for r in req if r not in produced and Path(r).name not in prod_names)
    return {
        "required_output_count": len(req),
        "required_output_suffixes": suffixes,
        "missing_declared_output_count": missing,
    }


def _failure_categories(
    *,
    diag: str,
    manifest,
    produced_outputs: list[dict[str, Any]],
    code_extraction_failed: bool,
    has_exception: bool,
) -> list[str]:
    cats: list[str] = []
    if diag == "timeout":
        cats.append("timeout")
    if has_exception or diag == "exception":
        cats.append("runtime_exception")
    if diag == "nonzero_exit":
        cats.append("nonzero_exit")
    if code_extraction_failed:
        cats.append("code_extraction_failed")
    if isinstance(manifest, list) and not [e for e in manifest if e.get("path")]:
        cats.append("no_artifact")
    if any(
        isinstance(po.get("shape"), dict) and po["shape"].get("parse_ok") is False
        for po in produced_outputs
        if isinstance(po, dict)
    ):
        cats.append("invalid_output_shape")
    return cats


def _oracle_visible(phase: str | None, manifest_scope: str | None) -> bool:
    """Gate for capturing oracle_evidence into the packet (rev H1)."""
    if config.reflect_blind():
        return False
    if (phase or "") in _NEVER_ORACLE_PHASES:
        return False
    if phase not in (None, "", "collect"):
        return False
    if manifest_scope is not None and manifest_scope != "skill_evolution":
        return False
    return True


def build_train_evidence_packet(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a strict train-only evidence packet.

    The packet deliberately requires an explicit record scope. Validation,
    test, promotion-gate, and cross-role records fail before an editor call.
    """
    accepted: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"train evidence record {index} must be an object")
        scope = record.get("scope")
        if scope not in TRAIN_EVIDENCE_SCOPES:
            raise ValueError(
                f"train evidence record {index} has invalid scope {scope!r}; "
                "expected explicit 'train' or 'collect'"
            )
        accepted.append(dict(record))
    return {
        "schema": TRAIN_EVIDENCE_SCHEMA,
        "scope": "train",
        "records": accepted,
    }


def _head_tail(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n...[truncated]...\n{text[-half:]}"


def _capture_tests_source(task_dir: Path | None, test_file: str) -> str:
    """Full text of the task's test file(s); head+tail char-capped."""
    if not task_dir:
        return ""
    try:
        test_path = Path(task_dir) / test_file
        tests_dir = test_path.parent
        if tests_dir.is_dir():
            files = sorted(p for p in tests_dir.glob("*.py") if p.is_file())
        elif test_path.is_file():
            files = [test_path]
        else:
            files = []
        parts: list[str] = []
        for f in files:
            try:
                parts.append(f"# {f.name}\n{f.read_text(encoding='utf-8')}")
            except OSError as exc:
                logger.warning("capture_tests_source: read failed for %s: %s", f, exc)
                continue
        return _head_tail("\n\n".join(parts), REFLECT_TESTS_CHARS)
    except Exception as exc:
        logger.warning("capture_tests_source: failed for task_dir=%s: %s", task_dir, exc)
        return ""


def _capture_source_artifacts(task_dir: Path | None) -> list[dict[str, Any]]:
    """Shallow listing under ``<task>/source_artifacts/`` with bounded content."""
    if not task_dir:
        return []
    try:
        root = Path(task_dir) / "source_artifacts"
        if not root.is_dir():
            return []
        out: list[dict[str, Any]] = []
        for p in sorted(root.rglob("*")):
            if len(out) >= REFLECT_SRC_ARTIFACTS_MAX:
                out.append({"note": f"(source_artifacts capped at {REFLECT_SRC_ARTIFACTS_MAX})"})
                break
            if not p.is_file():
                continue
            try:
                rel = str(p.relative_to(root))
            except Exception as exc:
                logger.warning("capture_source_artifacts: relpath failed for %s: %s", p, exc)
                continue
            entry: dict[str, Any] = {
                "path": rel,
                "size": p.stat().st_size,
                "suffix": p.suffix.lower(),
            }
            if p.suffix.lower() in _TEXT_ARTIFACT_SUFFIXES:
                try:
                    entry["content"] = p.read_text(encoding="utf-8")[:REFLECT_SRC_ARTIFACTS_CHARS]
                except OSError as exc:
                    logger.warning("capture_source_artifacts: read failed for %s: %s", p, exc)
            out.append(entry)
        return out
    except Exception as exc:
        logger.warning("capture_source_artifacts: failed for task_dir=%s: %s", task_dir, exc)
        return []


def _parse_failed_tests(stdout: str | None, nodeids: list[str] | None) -> list[dict[str, str]]:
    """Reconstruct ``{nodeid, message_tail}`` from pytest short-summary lines."""
    out: list[dict[str, str]] = []
    for raw in (stdout or "").splitlines():
        m = _FAILED_LINE.match(raw.strip())
        if m:
            out.append({"nodeid": m.group(1), "message_tail": (m.group(2) or "")[:300]})
    return out


def build_evidence(
    *,
    workspace: Path,
    pre_snapshot: dict[str, str],
    solve_exit_code: int | None,
    solve_timeout: bool,
    solve_diagnostic: str | None = None,
    solve_exception: str | None = None,
    solve_exception_frame: str | None = None,
    code_extraction_failed: bool = False,
    code_extraction_retried: bool = False,
    required_outputs: list[str] | None = None,
    trace_context: dict[str, Any] | None = None,
    solve_stderr_tail: str | None = None,
    feedback_enabled: bool = False,
    task_dir: Path | None = None,
    test_file: str = "tests/test_outputs.py",
    manifest_scope: str | None = None,
    evidence_policy: str | None = None,
) -> dict[str, Any]:
    """Assemble the v5 evidence packet on every exit path. Never raises.

    failure_evidence.verifier_result defaults to ``not_run``; the post-verifier
    seam (solver) overwrites it via :func:`attach_verifier_result`. When the
    oracle gate is open (rev H1) a ``oracle_evidence`` sub-dict is seeded with
    test source + source_artifacts; the dynamic failed-test/traceback fields are
    filled later by :func:`attach_verifier_result`.
    """
    diag = solve_diagnostic or classify_solve(solve_exit_code, solve_timeout)
    if diag not in _VALID_DIAGNOSTICS:
        diag = "unknown"
    manifest = _produced_manifest(Path(workspace), pre_snapshot or {})
    produced_outputs = _produced_outputs(manifest, Path(workspace))
    code_status = (
        "failed" if code_extraction_failed else ("retried" if code_extraction_retried else "ok")
    )
    failure_evidence: dict[str, Any] = {
        "failure_categories": _failure_categories(
            diag=diag,
            manifest=manifest,
            produced_outputs=produced_outputs,
            code_extraction_failed=code_extraction_failed,
            has_exception=bool(solve_exception),
        ),
        "produced_outputs": produced_outputs,
        "verifier_result": {"passed": 0, "total": 0, "verification_category": "not_run"},
        "solve_exception": (
            {"type": solve_exception, "frame": solve_exception_frame} if solve_exception else None
        ),
        "code_generation_status": code_status,
        "source_feedback_included": bool(feedback_enabled),
    }
    if feedback_enabled:
        failure_evidence["source_feedback"] = {
            "stderr_tail": sanitize_feedback(solve_stderr_tail),
            "exception_class": solve_exception,
            "exit_code": solve_exit_code if solve_exit_code is not None else None,
            "timeout": bool(solve_timeout),
        }
    failure_evidence.update(_required_outputs_summary(required_outputs, manifest))
    if evidence_policy == TRAIN_EVIDENCE_SCHEMA:
        phase = (trace_context or {}).get("phase")
        scope = "collect" if phase == "collect" else phase
        packet = build_train_evidence_packet(
            [
                {
                    "scope": scope,
                    "agent_solve": dict(
                        failure_evidence=dict(failure_evidence),
                        diagnostic={
                            "exit_code": solve_exit_code,
                            "timeout": bool(solve_timeout),
                        },
                    ),
                    "produced_artifacts": manifest,
                }
            ]
        )
        failure_evidence["train_evidence"] = packet
    elif _oracle_visible((trace_context or {}).get("phase"), manifest_scope):
        failure_evidence["oracle_evidence"] = {
            "tests_source": _capture_tests_source(task_dir, test_file),
            "source_artifacts": _capture_source_artifacts(task_dir),
            "failed_tests": [],
            "pytest_traceback": "",
        }
    return {
        "schema": SCHEMA,
        "agent_solve": {
            "exit_code": solve_exit_code if solve_exit_code is not None else "(unavailable)",
            "timeout": bool(solve_timeout),
            "diagnostic": diag,
        },
        "produced_artifacts": manifest,
        "failure_evidence": failure_evidence,
        "trace_context": dict(trace_context) if trace_context else {},
    }


def attach_verifier_result(
    evidence: dict[str, Any],
    *,
    passed: int,
    total: int,
    pytest_error_tail: str | None = None,
    pytest_stdout: str | None = None,
    nodeids: list[str] | None = None,
) -> None:
    """Phase B: fold sanitized scalar verification status into v5 evidence. Never raises.

    When the packet carries an ``oracle_evidence`` sub-dict (gate was open at
    build time) the raw failed-test list and unsanitized pytest tail are folded
    in here: the reflector is allowed to see train evidence. Held-out evidence
    remains outside this packet.
    """
    try:
        fe = evidence.get("failure_evidence")
        if not isinstance(fe, dict):
            return
        if pytest_error_tail and isinstance(fe.get("source_feedback"), dict):
            fe["source_feedback"]["pytest_error_tail"] = sanitize_feedback(pytest_error_tail)
        oe = fe.get("oracle_evidence")
        if isinstance(oe, dict) and pytest_stdout:
            oe["failed_tests"] = _parse_failed_tests(pytest_stdout, nodeids)
            tb = pytest_stdout
            if len(tb) > FEEDBACK_TAIL_CHARS:
                tb = tb[-FEEDBACK_TAIL_CHARS:]
            oe["pytest_traceback"] = tb
        manifest = evidence.get("produced_artifacts")
        has_art = isinstance(manifest, list) and any(
            isinstance(e, dict) and e.get("path") for e in manifest
        )
        if not has_art:
            cat = "no_artifact"
        elif int(total or 0) <= 0:
            cat = "no_tests_collected"
        elif int(passed or 0) >= int(total or 0):
            cat = "produced_and_passed"
        else:
            cat = "produced_but_failed_verification"
        fe["verifier_result"] = {
            "passed": int(passed or 0),
            "total": int(total or 0),
            "verification_category": cat,
        }
        packet = fe.get("train_evidence")
        if isinstance(packet, dict) and isinstance(packet.get("records"), list):
            for record in packet["records"]:
                if not isinstance(record, dict):
                    continue
                record["verifier_result"] = dict(fe["verifier_result"])
                nested_solve = record.get("agent_solve")
                nested_failure = (
                    nested_solve.get("failure_evidence") if isinstance(nested_solve, dict) else None
                )
                if isinstance(nested_failure, dict):
                    nested_failure["verifier_result"] = dict(fe["verifier_result"])
                if pytest_stdout:
                    record["verifier_output"] = str(pytest_stdout)
        if cat == "produced_but_failed_verification":
            cats = fe.setdefault("failure_categories", [])
            if "produced_but_failed_verification" not in cats:
                cats.append("produced_but_failed_verification")
    except Exception as exc:
        logger.warning("attach_verifier_result: fold failed: %s", exc)
        return
