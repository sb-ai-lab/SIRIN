"""Build the rich scratch workspace an agentic-session rewrite explores.

The ``agentic-session`` rewrite mode (see ``reflect.py``) runs ONE genuine
coding-agent session per evolve round instead of the two-step
reflect→single-shot-edit path. The agent needs a workspace it can actually
explore: the parent ``SKILL.md`` it edits in place, the raw train traces it
diagnoses, the real task inputs so it can write+run a candidate solve, and an
aggregate self-validation score — all WITHOUT any oracle (verifier source,
expected values, ground truth) under its working directory.

This module constructs that workspace and, just as importantly, *proves* the
oracle is absent before any tool is granted:

    SESSION/                 <- the agent's cwd (work_dir)
        SKILL.md             <- the file it edits; the only output we keep
        solve.sh             <- run wrapper (role-python patched / synthesized)
        measure.sh           <- aggregate-only self-validation score
        environment/ ...     <- real task inputs (so a candidate solve can run)
        traces/<id>/         <- solve.py + curated result.json + evidence.md
    _verifier/               <- SIBLING, OUTSIDE the agent cwd
        tests/               <- verifier source + co-located ground truth

The split is the integrity boundary on this host (no OS sandbox): the oracle
source simply never sits under the agent cwd. ``measure.sh`` runs the verifier
out-of-cwd and emits ONLY ``passed/total`` (``--tb=no`` so blind-mode
tracebacks cannot leak expected values). The leak scanner on the lifted
``SKILL.md`` remains the final backstop downstream.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path

from evolution import config
from evolution.core.models import Skill
from evolution.eval.python_env import resolve_python_for_role
from evolution.eval.task import Task
from evolution.evolve.reflection import scoped_trace_dirs
from evolution.evolve.reflection_evidence import (
    render_failure_evidence,
    render_oracle_sections,
)
from evolution.lineage.traces import load_trace_evidence, resolve_trace_artifact
from evolution.splits import SplitManifest

# Names that must never remain under the agent cwd. Checked post-prune.
_ORACLE_DIR_NAMES = {"tests"}
_ORACLE_FILE_TOKENS = ("ground_truth", "_prep_manifest.json")


class SessionWorkspaceError(RuntimeError):
    """Raised when the session workspace cannot be built oracle-free.

    A hard failure here aborts the session build rather than handing the agent
    a cwd that still contains verifier source / ground truth.
    """


@dataclass
class SessionWorkspace:
    """Paths + metadata for one built agentic-session workspace."""

    root: Path
    """Parent temp dir; delete this to clean up the whole session."""

    session_dir: Path
    """The agent's working directory (``work_dir`` for ``complete_agent_session``)."""

    verifier_dir: Path
    """Out-of-cwd sibling holding the verifier ``tests/`` + ground truth."""

    skill_path: Path
    """``session_dir/SKILL.md`` — lifted out after the session."""

    measure_sh: Path
    solve_sh: Path
    trace_ids: list[str] = field(default_factory=list)
    role: str | None = None
    source_models: list[str] = field(default_factory=list)
    blind: bool = True


def _make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _session_root() -> Path:
    """Temp root for session workspaces (shares the C1 candidate root knob)."""
    return Path(os.environ.get("EVO_C1_CANDIDATE_ROOT") or "/tmp")


def _copy_tests_to_verifier(src_tests: Path, dst_tests: Path, session_dir: Path) -> None:
    """Copy the verifier ``tests/`` tree into the out-of-cwd verifier dir.

    Mirrors :func:`rewrite_tests_if_needed`'s ``/root``→workspace substitution
    so tests that bake in ``/root/`` or ``/app/`` prefixes read the agent's
    produced outputs. ``__pycache__`` is dropped; ground-truth blobs copy
    verbatim.
    """
    dst_tests.mkdir(parents=True, exist_ok=True)
    sub = (f"{session_dir}/", f"{session_dir}/")
    for entry in src_tests.iterdir():
        if entry.name == "__pycache__":
            continue
        dst = dst_tests / entry.name
        if entry.is_file():
            if entry.suffix == ".py":
                body = entry.read_text(encoding="utf-8", errors="replace")
                body = body.replace("/root/", sub[0]).replace("/app/", sub[1])
                dst.write_text(body, encoding="utf-8")
            else:
                shutil.copy2(entry, dst)
        elif entry.is_dir():
            shutil.copytree(entry, dst, ignore=shutil.ignore_patterns("__pycache__"))


def _prune_oracle(session_dir: Path) -> None:
    """Remove verifier source / ground truth / prep manifest from the agent cwd.

    Load-bearing: ``SbBenchTaskLayout.stage_workspace`` copies the oracle into
    the workspace by default (its ``_COPY_IGNORE`` excludes only
    output/solution/caches). ``EvoTaskLayout`` never stages an oracle, so this
    is a no-op there. Either way, after this runs no oracle path exists under
    ``session_dir``.
    """
    for path in sorted(session_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        name = path.name
        try:
            if path.is_dir() and name in _ORACLE_DIR_NAMES:
                shutil.rmtree(path, ignore_errors=True)
            elif "ground_truth" in name.lower() or name == "_prep_manifest.json":
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
        except OSError:
            continue
    out_dir = session_dir / "output"
    if out_dir.is_dir():
        for child in out_dir.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            else:
                shutil.rmtree(child, ignore_errors=True)


def _assert_no_oracle(session_dir: Path) -> None:
    """Hard-fail the build if any oracle path survives under the agent cwd."""
    offenders: list[str] = []
    for path in session_dir.rglob("*"):
        name = path.name
        if path.is_dir() and name in _ORACLE_DIR_NAMES:
            offenders.append(str(path.relative_to(session_dir)))
        elif "ground_truth" in name.lower() or name == "_prep_manifest.json":
            offenders.append(str(path.relative_to(session_dir)))
    if offenders:
        raise SessionWorkspaceError(
            "oracle still present under agent cwd after prune: " + ", ".join(offenders[:10])
        )


def _write_solve_sh(session_dir: Path, role_python: str) -> Path:
    """Patch an existing ``solve.sh`` (python3→role python) or synthesize one.

    sb-bench tasks ship a ``solve.sh`` that cd's into ``output/`` then runs
    ``python3 solution.py``; we patch the interpreter in place so the agent's
    ``bash solve.sh`` uses the role env. Evolution-native tasks ship no ``solve.sh``; we
    synthesize the minimal ``python solution.py`` at the workspace root, which
    matches ``EvoTaskLayout.run_solution``'s outputs-at-root contract.
    """
    solve_sh = session_dir / "solve.sh"
    if solve_sh.is_file():
        patched = solve_sh.read_text(encoding="utf-8").replace("python3", role_python)
        solve_sh.write_text(patched, encoding="utf-8")
    else:
        solve_sh.write_text(
            f'#!/usr/bin/env bash\ncd "$(dirname "$0")"\nexec "{role_python}" solution.py\n',
            encoding="utf-8",
        )
    _make_executable(solve_sh)
    return solve_sh


def _write_measure_sh(session_dir: Path, verifier_test_path: Path, role_python: str) -> Path:
    """Write the aggregate-only self-validation wrapper.

    Runs the out-of-cwd verifier with ``TASK_WORKSPACE=session_dir`` and
    ``--tb=no`` so only the pass/fail counts surface — no per-test names,
    tracebacks, or expected values (blind-safe). Never re-enters ``solve.sh``
    (avoids the known solve.sh↔solution.py recursion bomb); the agent runs the
    solve itself, ``measure.sh`` only scores.
    """
    measure_sh = session_dir / "measure.sh"
    measure_sh.write_text(
        "#!/usr/bin/env bash\n"
        "# Aggregate self-validation score (diagnostic only; the real δ-gate\n"
        "# re-scores independently on a held-back spec the agent never sees).\n"
        "set -u\n"
        f'SESSION_DIR="{session_dir}"\n'
        f'VERIFIER_TEST="{verifier_test_path}"\n'
        f'PY="{role_python}"\n'
        "# Flatten an accidental output/output nest so the verifier sees one output/.\n"
        'if [ -d "$SESSION_DIR/output/output" ]; then\n'
        '  cp -a "$SESSION_DIR/output/output/." "$SESSION_DIR/output/" 2>/dev/null || true\n'
        "fi\n"
        'out=$(cd "$SESSION_DIR" && TASK_WORKSPACE="$SESSION_DIR" "$PY" -m pytest '
        '"$VERIFIER_TEST" --tb=no -q -p no:cacheprovider 2>&1)\n'
        "passed=$(printf '%s' \"$out\" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1)\n"
        "failed=$(printf '%s' \"$out\" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' | head -1)\n"
        "errors=$(printf '%s' \"$out\" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' | head -1)\n"
        "passed=${passed:-0}; failed=${failed:-0}; errors=${errors:-0}\n"
        "total=$((passed + failed + errors))\n"
        'echo "SELF_VALIDATE passed=${passed}/${total}"\n',
        encoding="utf-8",
    )
    _make_executable(measure_sh)
    return measure_sh


def _seed_traces(
    session_dir: Path,
    pairs: list[tuple[dict, Path]],
    *,
    blind: bool,
    max_traces: int,
) -> tuple[list[str], list[str]]:
    """Write ``traces/<id>/`` from the train-scoped (trace, dir) pairs.

    Each seeded trace carries the agent's own ``solve.py`` (allowed), a curated
    ``result.json`` scalar subset, and ``evidence.md`` rendered through the
    sanitizing renderers (failure evidence always; oracle sections only when
    not blind). Returns ``(trace_ids, source_models)``.
    """
    traces_root = session_dir / "traces"
    traces_root.mkdir(parents=True, exist_ok=True)
    trace_ids: list[str] = []
    source_models: list[str] = []
    for trace, trace_dir in pairs[:max_traces]:
        tid = str(trace.get("id") or "")
        if not tid:
            continue
        dst = traces_root / tid
        dst.mkdir(parents=True, exist_ok=True)

        solve_src = resolve_trace_artifact(trace_dir, "solve.py")
        if solve_src.is_file():
            shutil.copy2(solve_src, dst / "solve.py")

        evidence = load_trace_evidence(trace_dir)
        fe = (evidence or {}).get("failure_evidence") or {}
        vr = fe.get("verifier_result") or {}
        model = str(trace.get("model") or "?")
        pass_rate = trace.get("pass_rate")
        passed = trace.get("passed", vr.get("passed"))
        total = trace.get("total", vr.get("total"))

        (dst / "result.json").write_text(
            json.dumps(
                {
                    "trace_id": tid,
                    "task": trace.get("task"),
                    "model": model,
                    "pass_rate": pass_rate,
                    "passed": passed,
                    "total": total,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        pr_str = f"{pass_rate:.0%}" if isinstance(pass_rate, (int, float)) else "?"
        parts = [
            f"# Trace {tid}",
            f"- model: {model}",
            f"- pass_rate: {pr_str}",
            "",
            "## Failure evidence (sanitized, execution-observable)",
            render_failure_evidence(evidence),
        ]
        if not blind:
            oracle = render_oracle_sections(evidence)
            if oracle:
                parts += ["", oracle]
        (dst / "evidence.md").write_text("\n".join(parts) + "\n", encoding="utf-8")

        trace_ids.append(tid)
        if model not in source_models:
            source_models.append(model)
    return trace_ids, source_models


def build_session_workspace(
    skill: Skill,
    task: Task,
    *,
    task_filter: str | None = None,
    trace_model: str | None = None,
    skill_version: str | None = None,
    manifest: SplitManifest | None = None,
    max_traces: int | None = None,
) -> SessionWorkspace:
    """Construct the oracle-free scratch workspace for one agentic session.

    Stages the real task into ``session_dir`` (its layout decides what lands
    there), copies the verifier ``tests/`` to an out-of-cwd ``_verifier/`` with
    ground truth, prunes any oracle from ``session_dir`` and asserts none
    remains, then seeds ``SKILL.md`` + ``solve.sh`` + ``measure.sh`` +
    ``traces/``. Raises :class:`SessionWorkspaceError` if the oracle cannot be
    removed from the agent cwd.
    """
    blind = config.reflect_blind()
    if max_traces is None:
        max_traces = int(os.environ.get("EVO_SESSION_MAX_TRACES", "8") or "8")

    import uuid

    root = _session_root() / f"evo_sess_{uuid.uuid4().hex}"
    session_dir = root / "session"
    verifier_dir = root / "_verifier"
    session_dir.mkdir(parents=True, exist_ok=False)
    verifier_dir.mkdir(parents=True, exist_ok=False)

    # 1. Stage the real task into the agent cwd (layout-specific).
    task.resolve_layout().stage_workspace(task.path, session_dir)

    # 2. Copy the verifier tests (source of truth) out-of-cwd, with the
    #    /root|/app → session_dir rewrite so produced outputs are read.
    test_rel = Path(task.test_file or "tests/test_outputs.py")
    src_tests_dir = task.path / (test_rel.parent if str(test_rel.parent) != "." else "tests")
    verifier_test_path = verifier_dir / test_rel
    if src_tests_dir.is_dir():
        _copy_tests_to_verifier(src_tests_dir, verifier_test_path.parent, session_dir)
    if not verifier_test_path.exists():
        raise SessionWorkspaceError(
            f"verifier test not found after copy: {verifier_test_path} "
            f"(source tests dir: {src_tests_dir})"
        )

    # 3. Prune oracle from the agent cwd, then PROVE none remains.
    _prune_oracle(session_dir)
    _assert_no_oracle(session_dir)

    # 4. Place the parent SKILL.md the agent edits in place.
    skill_path = session_dir / "SKILL.md"
    shutil.copy2(skill.skill_md_path, skill_path)

    # 5. Run + measure scripts (role interpreter resolved at build time).
    role_python = resolve_python_for_role(task.role)
    solve_sh = _write_solve_sh(session_dir, role_python)
    measure_sh = _write_measure_sh(session_dir, verifier_test_path, role_python)

    # 6. Seed raw train traces (same scope collect_reflections uses).
    pairs = scoped_trace_dirs(
        skill,
        task_filter=task_filter,
        trace_model=trace_model,
        skill_version=skill_version,
        manifest=manifest,
    )
    trace_ids, source_models = _seed_traces(session_dir, pairs, blind=blind, max_traces=max_traces)

    return SessionWorkspace(
        root=root,
        session_dir=session_dir,
        verifier_dir=verifier_dir,
        skill_path=skill_path,
        measure_sh=measure_sh,
        solve_sh=solve_sh,
        trace_ids=trace_ids,
        role=task.role,
        source_models=source_models,
        blind=blind,
    )


def cleanup_session_workspace(ws: SessionWorkspace) -> None:
    """Remove the whole session tree (call after lifting ``SKILL.md``)."""
    shutil.rmtree(ws.root, ignore_errors=True)
