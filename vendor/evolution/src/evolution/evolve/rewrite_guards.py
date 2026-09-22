"""Rewrite selection, size, leakage, and candidate-isolation guards.

These checks are framework safeguards for promoting skill rewrites. They are
kept separate from prompt orchestration so CLI, workflow, and research runners
can share the same rejection rules.
"""

from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path

from evolution import config
from evolution.core.models import Skill
from evolution.evolve.rewrite_outcome import (
    CANDIDATE_INVALID_EXTRA_FILES,
    CANDIDATE_INVALID_HIDDEN_FILE,
    CANDIDATE_INVALID_PATH_ESCAPE,
    CANDIDATE_INVALID_SYMLINK,
)
from evolution.lineage.traces import TraceStore, load_trace_evidence

logger = logging.getLogger(__name__)

LEAK_CORPUS_MAX_CHARS = int(os.environ.get("EVO_LEAK_CORPUS_MAX_CHARS", "200000") or "200000")

# C1 file-edit candidate isolation.  Default empty = strict: every
# ``.``-prefixed entry is rejected unless explicitly allow-listed after
# Phase 2a observation (plan §1.6).
_ALLOWED_HIDDEN_NAMES: frozenset[str] = frozenset()

_LEAK_NUM_MIN_ABS = 1000.0
_NUMERIC_TOKEN_RE = re.compile(
    r"(?<![\w.])[-+]?(?:(?:\d[\d_,]*)(?:\.\d+)?|\d*\.\d+)(?:[eE][-+]?\d+)?(?![\w.])"
)


def _ast_expected_literals(src: str) -> list[str]:
    """``repr()`` of literal comparison operands (the verifier's expected
    answers); the computed side, where path/filename tokens live, is skipped."""
    out: list[str] = []
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return out

    def _emit(v: object) -> None:
        if isinstance(v, bool):
            return
        if isinstance(v, str):
            if len(v) >= 6 and not any(ch.isspace() for ch in v):
                out.append(repr(v))
        elif isinstance(v, (int, float)) and abs(v) >= _LEAK_NUM_MIN_ABS:
            out.append(repr(v))

    def _harvest_operand(node: ast.AST) -> None:
        if isinstance(node, ast.Constant):
            _emit(node.value)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for el in node.elts:
                _harvest_operand(el)
        elif isinstance(node, ast.Dict):
            for el in node.values:
                _harvest_operand(el)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        for operand in [node.left, *node.comparators]:
            _harvest_operand(operand)
    return out


def _canonical_numeric_token(token: str) -> str | None:
    normalized = token.replace("_", "").replace(",", "")
    try:
        value = float(normalized)
    except ValueError:
        return None
    if abs(value) < _LEAK_NUM_MIN_ABS:
        return None
    if value.is_integer():
        return str(int(value))
    return f"{value:.12g}"


def _numeric_tokens(text: str) -> set[str]:
    out: set[str] = set()
    for match in _NUMERIC_TOKEN_RE.finditer(text):
        value = _canonical_numeric_token(match.group(0))
        if value is not None:
            out.add(value)
    return out


def actionable_reflections(reflections: list[dict]) -> list[dict] | None:
    failures = [
        r for r in reflections if "error" not in r and str(r.get("kind") or "failure") == "failure"
    ]
    actionable = [
        r
        for r in failures
        if r.get("evidence_sufficiency", "sufficient") != "insufficient"
        and r.get("rewrite_recommended", True) is not False
    ]
    if (
        failures
        and (not actionable or len(actionable) / len(failures) < 0.5)
        and os.environ.get("EVO_REQUIRE_HIGHCONF_REWRITE", "").lower() in ("1", "true", "yes")
    ):
        return None
    return actionable or failures or None


def actionable_success_reflections(reflections: list[dict]) -> list[dict]:
    """Filter to success-kind reflections that recommend preservation."""
    return [
        r
        for r in reflections
        if "error" not in r
        and str(r.get("kind") or "") == "success"
        and r.get("evidence_sufficiency", "sufficient") != "insufficient"
        and r.get("preserve_recommended", True) is not False
    ]


def nonempty_line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def rewrite_size_limits(skill: Skill, original_body: str) -> dict[str, int]:
    max_chars_abs = int(os.environ.get("EVO_REWRITE_MAX_CHARS", "120000") or "120000")
    max_lines_abs = int(os.environ.get("EVO_REWRITE_MAX_LINES", "4000") or "4000")
    return {
        "baseline_chars": len(original_body),
        "baseline_lines": nonempty_line_count(original_body),
        "max_chars": max_chars_abs,
        "max_lines": max_lines_abs,
        "hard_max_chars": max_chars_abs,
        "hard_max_lines": max_lines_abs,
    }


def size_violations(body: str, limits: dict[str, int]) -> list[str]:
    return hard_size_violations(body, limits)


def hard_size_violations(body: str, limits: dict[str, int]) -> list[str]:
    issues: list[str] = []
    if len(body) > limits["hard_max_chars"]:
        issues.append(f"{len(body)} chars > absolute ceiling {limits['hard_max_chars']}")
    lines = nonempty_line_count(body)
    if lines > limits["hard_max_lines"]:
        issues.append(f"{lines} non-empty lines > absolute ceiling {limits['hard_max_lines']}")
    return issues


def leakage_provenance_corpus(skill: Skill, task_filter: str | None) -> str:
    parts: list[str] = []
    try:
        store = TraceStore(skill)
        traces = store.list(task=task_filter) if task_filter else store.list()
        for t in traces:
            tdir = store.resolve_trace_dir(t.get("id", ""))
            ev = load_trace_evidence(tdir)
            if not ev:
                continue
            # Only reflection-eligible traces (exclude promotion_validation),
            # mirroring reflect_failing_traces' phase filter.
            if (ev.get("trace_context") or {}).get("phase") == "promotion_validation":
                continue
            arts = ev.get("produced_artifacts")
            if isinstance(arts, list):
                for a in arts:
                    if isinstance(a, dict):
                        parts.append(str(a.get("path", "")))
                        parts.append(str(a.get("suffix", "")))
            fe = ev.get("failure_evidence") or {}
            sf = fe.get("source_feedback")
            if isinstance(sf, dict):
                for _k in ("stderr_tail", "pytest_error_tail"):
                    if sf.get(_k):
                        parts.append(str(sf[_k]))
            # Oracle (v5): harvest only asserted expected values, not raw test
            # scaffolding, so structural tokens aren't mistaken for leaks (D3).
            oe = fe.get("oracle_evidence")
            if isinstance(oe, dict):
                src = oe.get("tests_source")
                if src:
                    parts.extend(_ast_expected_literals(str(src)))
                for ft in oe.get("failed_tests") or []:
                    if isinstance(ft, dict) and ft.get("nodeid"):
                        parts.append(str(ft["nodeid"]))
                for a in oe.get("source_artifacts") or []:
                    if isinstance(a, dict) and a.get("content"):
                        parts.append(str(a["content"]))
            if sum(len(p) for p in parts) >= LEAK_CORPUS_MAX_CHARS:
                break
    except Exception as exc:
        logger.debug("leakage_provenance_corpus: returning partial corpus after error: %s", exc)
        return "\n".join(parts)[:LEAK_CORPUS_MAX_CHARS]
    return "\n".join(parts)[:LEAK_CORPUS_MAX_CHARS]


def scan_leakage(
    body: str,
    corpus: str,
    harness_names: set[str] | None = None,
) -> list[str]:
    findings: list[str] = []
    if not body:
        return findings

    env_names = {s.strip() for s in os.environ.get("EVO_LEAK_HARNESS_NAMES", "").split(",")}
    harness = {s for s in (harness_names or set()) | env_names if s}
    for name in sorted(harness):
        if name in body:
            findings.append(f"known train-harness identifier: {name}")

    if corpus:
        corpus_lower = corpus.lower()
        body_idents = set(re.findall(r"\b(?:test_|assert_)\w+", body))
        for ident in sorted(body_idents):
            # Case-insensitive match so Test_Foo↔test_foo is still caught (rev D1).
            if (
                ident.lower() in corpus_lower
                and f"known train-harness identifier: {ident}" not in findings
            ):
                findings.append(f"verifier identifier with trace provenance: {ident}")

        ngram_min = config.leak_ngram_min_chars()
        for raw in body.splitlines():
            line = raw.strip()
            if len(line) < ngram_min:
                continue
            if line.startswith(("#", "```", "<!--", "|")):
                continue
            if line in corpus:
                snip = line if len(line) <= 80 else line[:80] + "..."
                findings.append(f"verbatim span copied from trace evidence: {snip!r}")

        quoted = set(re.findall(r"""['"]([^'"\n]{6,})['"]""", corpus))
        for lit in sorted(quoted):
            if lit in {"create", "emit", "export", "generate", "produce", "save", "write"}:
                # ponytail: conservative verb allowlist; extend only for reproduced prose collisions.
                generic_use = re.compile(
                    rf"\b{re.escape(lit)}\s+(?:(?:the|all)\s+)?"
                    r"(?:(?:required|requested|final)\s+)*(?:outputs?|artifacts?|results?|reports?|files?)\b",
                    re.IGNORECASE,
                )
                if not re.search(rf"\b{re.escape(lit)}\b", generic_use.sub("", body)):
                    continue
            if lit and lit in body:
                findings.append(f"expected-constant literal with trace provenance: {lit!r}")

        corpus_numbers = _numeric_tokens(corpus)
        body_numbers = _numeric_tokens(body)
        for value in sorted(corpus_numbers & body_numbers):
            findings.append(f"numeric expected constant with trace provenance: {value}")

    seen: set[str] = set()
    uniq: list[str] = []
    for finding in findings:
        if finding not in seen:
            seen.add(finding)
            uniq.append(finding)
    return uniq[:25]


def validate_candidate_isolation(
    candidate_dir: Path,
    *,
    allowed_extra: set[str] | None = None,
) -> tuple[bool, str, str]:
    """Walk ``candidate_dir`` and reject anything outside the isolation contract.

    Returns ``(ok, candidate_status, reason)``.  On success, ``ok=True``
    and the status / reason strings are empty.  On rejection, ``ok=False``
    and ``candidate_status`` is one of the ``CANDIDATE_INVALID_*``
    constants from :mod:`evolution.evolve.rewrite_outcome`.

    Rules (plan §1.6):

    * No symlinks (``Path.is_symlink()``).
    * No hidden files (``name.startswith(".")``) unless
      ``name in _ALLOWED_HIDDEN_NAMES``.
    * No files outside ``{"SKILL.md"} ∪ allowed_extra``.
    * No path that resolves outside ``candidate_dir.resolve()``.
    """
    allowed = {"SKILL.md"} | (allowed_extra or set())
    candidate_root = candidate_dir.resolve()
    if not candidate_root.is_dir():
        return (
            False,
            CANDIDATE_INVALID_PATH_ESCAPE,
            f"candidate_dir is not a directory: {candidate_dir}",
        )

    for entry in candidate_dir.rglob("*"):
        if entry.is_symlink():
            return (
                False,
                CANDIDATE_INVALID_SYMLINK,
                f"symlink in candidate: {entry.relative_to(candidate_dir)}",
            )
        try:
            resolved = entry.resolve()
        except (OSError, RuntimeError) as exc:
            return (
                False,
                CANDIDATE_INVALID_PATH_ESCAPE,
                f"failed to resolve {entry.relative_to(candidate_dir)}: {exc!s}",
            )
        # ``Path.is_relative_to`` is the Python 3.9+ equivalent; use string
        # prefix only as a fallback for older runtimes (project supports 3.10+).
        if candidate_root != resolved and not resolved.is_relative_to(candidate_root):
            return (
                False,
                CANDIDATE_INVALID_PATH_ESCAPE,
                f"path escapes candidate root: {entry.relative_to(candidate_dir)}",
            )
        name = entry.name
        if name.startswith("."):
            if name not in _ALLOWED_HIDDEN_NAMES:
                return (
                    False,
                    CANDIDATE_INVALID_HIDDEN_FILE,
                    f"unknown hidden entry: {entry.relative_to(candidate_dir)}",
                )
            continue
        if entry.is_file() and name not in allowed:
            return (
                False,
                CANDIDATE_INVALID_EXTRA_FILES,
                f"unexpected file in candidate: {entry.relative_to(candidate_dir)}",
            )
    return True, "", ""
