"""Materialize a task workspace from a task dir, in one of two contracts.

``contract="agent"`` (the AFTER/native-framework harness): flatten
``environment/data/*`` to the workspace root, rewrite ``solve.sh`` to run
``solution.py`` from ``<ws>/output``, and home-isolate ``data_generator.py``.

``contract="core"`` (the ``SbBenchTaskLayout`` eval path): mirror the task tree
keeping ``environment/data/`` nested, keep the original ``solve.sh``, and
regenerate ``environment/data/`` in place only when it is empty.

The two contracts are kept behaviorally distinct on purpose — they feed
different downstream verifiers — so this module dispatches to a preserved code
path per contract rather than blending them.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

from evolution.eval.child_env import minimal_child_env
from evolution.eval.proc import run_capture
from evolution.eval.python_env import resolve_python_for_role
from evolution.eval.workspace_guard import isolate_home_env

# Agent contract: filenames never carried into the flattened agent workspace.
_NEW_CORPUS_SKIP = {
    "solution.py",
    "source_artifacts",
    "_test_adapted.py",
    ".git",
    "output",
    "tests",
    "__pycache__",
}

# Core contract: filenames never carried into the mirrored eval workspace.
_COPY_IGNORE = shutil.ignore_patterns(
    "output",
    "solution.py",
    "_solve.py",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "_solve_output.txt",
    "_pytest_output.txt",
)

_CORE_ORACLE_DIRS = {"tests", "source_artifacts", "solution"}
_CORE_ORACLE_FILES = {
    "data_generator.py",
    "solution.py",
    "_solve.py",
    "_test_adapted.py",
    "_prep_manifest.json",
}

# data_generator.py uses Path("environment/data") relative to cwd; cap it so a
# misbehaving generator can't wedge the whole pipeline.
_DATA_GEN_TIMEOUT_S = float(os.environ.get("EVO_SB_DATA_GEN_TIMEOUT_S", "120") or "120")


def _ignore_dangling_symlinks(dir_: str, names: list[str]) -> list[str]:
    """copytree ignore-hook: skip symlinks whose target no longer exists.

    Provenance dirs (``source_artifacts/``) can carry links into other users'
    home trees (e.g. AFTER ds/protein-expression-analysis has
    ``source_task/inputs`` pointing at an absent checkout). With
    ``symlinks=False`` copytree follows links, so a dangling one raises and
    kills workspace staging even when nothing downstream needs it.
    """
    d = Path(dir_)
    return [n for n in names if (d / n).is_symlink() and not (d / n).exists()]


def _core_copy_ignore(dir_: str, names: list[str]) -> set[str]:
    """Core-contract ignore: `_COPY_IGNORE` patterns plus dangling symlinks."""
    ignored = set(_COPY_IGNORE(dir_, names))
    ignored.update(_ignore_dangling_symlinks(dir_, names))
    return ignored


log = logging.getLogger(__name__)


class WorkspaceMaterializationError(RuntimeError):
    """Raised when a task workspace cannot be prepared faithfully."""


def validated_verifier_source(task_dir: Path, test_file: object | None = None) -> tuple[Path, Path]:
    """Return a contained, symlink-free verifier source and relative path."""

    if test_file is None:
        try:
            with (task_dir / "task.toml").open("rb") as stream:
                verification = tomllib.load(stream).get("verification", {})
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise WorkspaceMaterializationError("could not read task verifier config") from exc
        if not isinstance(verification, dict):
            raise WorkspaceMaterializationError("task verification config must be a table")
        test_file = verification.get("verifier_entrypoint", "tests/test_outputs.py")

    if not isinstance(test_file, str) or not test_file.strip():
        raise WorkspaceMaterializationError("verifier entrypoint must be a relative file path")
    relative = Path(test_file)
    if relative == Path(".") or relative.is_absolute() or ".." in relative.parts:
        raise WorkspaceMaterializationError(f"unsafe verifier entrypoint: {test_file}")

    source = task_dir
    for part in relative.parts:
        source /= part
        if source.is_symlink():
            raise WorkspaceMaterializationError(f"verifier path contains a symlink: {relative}")
    try:
        resolved = source.resolve(strict=True)
        task_root = task_dir.resolve(strict=True)
    except OSError as exc:
        raise WorkspaceMaterializationError(f"verifier file not found: {relative}") from exc
    if not resolved.is_relative_to(task_root) or not resolved.is_file():
        raise WorkspaceMaterializationError(f"unsafe verifier entrypoint: {relative}")

    if relative.parent != Path("."):
        try:
            if any(path.is_symlink() for path in source.parent.rglob("*")):
                raise WorkspaceMaterializationError(
                    f"verifier directory contains a symlink: {relative.parent}"
                )
        except OSError as exc:
            raise WorkspaceMaterializationError(
                f"could not inspect verifier directory: {relative.parent}"
            ) from exc
    return source, relative


def _has_materialized_env_data(ws: Path) -> bool:
    env_data = ws / "environment" / "data"
    if not env_data.is_dir():
        return False
    ignored = {"README.md", "source_manifest.json"}
    return any(
        path.is_file() and not path.name.startswith(".") and path.name not in ignored
        for path in env_data.rglob("*")
    )


def _task_role(task_dir: Path) -> str | None:
    task_toml = task_dir / "task.toml"
    if not task_toml.is_file():
        return None
    try:
        data = tomllib.loads(task_toml.read_text(encoding="utf-8"))
    except Exception:
        return None
    role = ((data.get("task") or {}).get("role") or "").strip()
    return role or None


def resolve_experiment_python(role: str | None = None) -> str:
    """Return the Python executable all generated solve.sh files should use."""
    override = os.environ.get("EVO_PYTHON")
    if override:
        return override
    if os.environ.get("EVO_DISABLE_ROLE_PYTHON", "0") != "1" and role:
        try:
            return resolve_python_for_role(role)
        except Exception:
            pass
    return sys.executable


def _canonical_solution_args(solve_sh_text: str) -> str:
    """Trailing CLI args a task's own solve.sh passes to ``solution.py`` (relative
    to ``output/``, the wrapper's cwd, so they transplant directly). Empty for the
    common no-arg contract. Fixes tasks whose instruction mandates a CLI signature."""
    joined = re.sub(r"\\\s*\n", " ", solve_sh_text)
    for line in joined.splitlines():
        s = line.strip()
        if s.startswith("#") or "solution.py" not in s:
            continue
        # require a real interpreter invocation (not a comment mentioning solution.py)
        m = re.search(r"\bpython[0-9.]*\b[^\n]*?solution\.py[\"']?\s+(.+)", s)
        if not m:
            continue
        tail = re.split(r"\s+(?:#|2?>|\||;|&&)", m.group(1).strip())[0].strip()
        if tail:
            return tail
    return ""


def write_agent_solve_sh(path: Path, *, python: str | None = None, solution_args: str = "") -> None:
    """Write the canonical sb-bench solve.sh wrapper.

    The agent code lives at ``<workspace>/solution.py``. The wrapper executes
    it from ``<workspace>/output`` so verifier paths like ``output/foo`` map to
    cwd-relative writes of ``foo`` inside the script.
    """
    python = shlex.quote(python or resolve_experiment_python())
    args = (" " + solution_args.strip()) if solution_args.strip() else ""
    body = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'WS="$(cd "$(dirname "$0")" && pwd)"\n'
        'mkdir -p "$WS/output"\n'
        'cd "$WS/output"\n'
        'if [ -f "$WS/solution.py" ]; then\n'
        f'  exec {python} "$WS/solution.py"{args}\n'
        "fi\n"
        "exit 0\n"
    )
    path.write_text(body, encoding="utf-8")
    try:
        path.chmod(0o755)
    except OSError:
        pass


def _remove_existing_workspace(ws: Path) -> None:
    """Move stale workspace aside before deletion so retries get a clean path."""
    if not ws.exists():
        return
    stale = ws.with_name(f"{ws.name}.stale-{os.getpid()}-{time.time_ns()}")
    try:
        ws.rename(stale)
    except FileNotFoundError:
        return
    except OSError:
        for attempt, delay_s in enumerate((0.05, 0.1, 0.2, 0.5, 1.0), start=1):
            try:
                shutil.rmtree(ws)
                return
            except FileNotFoundError:
                return
            except OSError:
                if attempt == 5:
                    raise
                time.sleep(delay_s)
        return

    for delay_s in (0.05, 0.1, 0.2):
        try:
            shutil.rmtree(stale)
            return
        except FileNotFoundError:
            return
        except OSError:
            time.sleep(delay_s)


def _regenerate_environment_data(workspace: Path, role: str | None) -> None:
    """Run ``data_generator.py`` from the workspace if present (core contract).

    Tasks like the AFTER benchmark ship raw inputs in ``source_artifacts/`` and
    rebuild ``environment/data/`` at solve time. Pre-populated ``environment/data/``
    tasks ship without a generator — that's fine; we only fire when the script
    exists and the data dir is empty. Runs under the role interpreter.
    """
    gen = workspace / "data_generator.py"
    if not gen.is_file():
        return
    if (workspace / "environment" / "data").is_dir() and any(
        (workspace / "environment" / "data").iterdir()
    ):
        return
    try:
        run_capture(
            [resolve_python_for_role(role), "data_generator.py"],
            cwd=str(workspace),
            text=True,
            timeout=_DATA_GEN_TIMEOUT_S,
            env=minimal_child_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def _materialize_core(task_dir: Path, workspace: Path) -> None:
    """Mirror the task tree into ``workspace`` (core eval contract).

    Keeps ``environment/data/`` nested and the original ``solve.sh``; the
    sb-bench verifier resolves ``environment/data/foo`` from the workspace root.
    """
    if workspace.exists() and workspace.is_dir() and any(workspace.iterdir()):
        # Fresh-start an existing workspace dir.
        for child in workspace.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            else:
                shutil.rmtree(child)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    if not workspace.exists():
        shutil.copytree(task_dir, workspace, ignore=_core_copy_ignore)
    else:
        # ``copytree`` insists the target not exist; we manually copy.
        for item in task_dir.iterdir():
            if item.name in {"output", "__pycache__", ".pytest_cache"}:
                continue
            dest = workspace / item.name
            if item.is_file():
                shutil.copy2(item, dest)
            elif item.is_dir():
                shutil.copytree(item, dest, ignore=_ignore_dangling_symlinks)
    (workspace / "output").mkdir(exist_ok=True)
    _regenerate_environment_data(workspace, _task_role(task_dir))


def _scrub_core_oracle(workspace: Path, verifier: Path) -> None:
    """Remove verifier/oracle material after public inputs have been generated."""

    configured = workspace / (verifier if verifier.parent == Path(".") else verifier.parent)
    if configured.is_dir() and not configured.is_symlink():
        shutil.rmtree(configured)
    else:
        configured.unlink(missing_ok=True)

    for path in sorted(workspace.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        private = (
            (path.is_dir() and path.name in _CORE_ORACLE_DIRS)
            or "ground_truth" in path.name.lower()
            or path.name in _CORE_ORACLE_FILES
        )
        if not private:
            continue
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        except OSError as exc:
            raise WorkspaceMaterializationError(
                f"could not remove oracle path {path.relative_to(workspace)}: {exc}"
            ) from exc

    output = workspace / "output"
    if output.is_dir():
        for child in output.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink(missing_ok=True)


def _materialize_agent(task_dir: Path, ws: Path, *, agent_solve_sh: bool = True) -> None:
    """Flatten the task tree into ``ws`` and pre-run any data_generator.py.

    Supports both legacy SkillsBench (``inputs/``) and the new sb-bench layout
    (whole-tree copy with environment/data staging). ``solve.sh`` is rewritten
    to execute ``solution.py`` from ``<ws>/output`` so tests measure agent
    output rather than the oracle.
    """
    _remove_existing_workspace(ws)
    ws.mkdir(parents=True, exist_ok=True)
    role = _task_role(task_dir)
    role_python = resolve_experiment_python(role)

    inputs = task_dir / "inputs"
    if inputs.is_dir():
        for item in inputs.iterdir():
            if item.name.startswith("."):
                continue
            target = ws / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        if agent_solve_sh and (ws / "solve.sh").is_file():
            sh = ws / "solve.sh"
            write_agent_solve_sh(
                sh,
                python=role_python,
                solution_args=_canonical_solution_args(sh.read_text(errors="replace")),
            )
        return

    for item in task_dir.iterdir():
        if item.name in _NEW_CORPUS_SKIP or item.name.startswith("."):
            continue
        target = ws / item.name
        if item.is_dir():
            shutil.copytree(item, target, symlinks=False)
        else:
            shutil.copy2(item, target)
    (ws / "output").mkdir(exist_ok=True)

    dg = ws / "data_generator.py"
    if dg.is_file():
        (ws / "tests").mkdir(exist_ok=True)
        # data_generators may stage visible inputs from source_artifacts (skipped
        # above for oracle hygiene); stage it transiently then remove before agent runs.
        staged_sa = None
        src_artifacts = task_dir / "source_artifacts"
        if src_artifacts.is_dir() and not (ws / "source_artifacts").exists():
            staged_sa = ws / "source_artifacts"
            shutil.copytree(
                src_artifacts,
                staged_sa,
                symlinks=False,
                ignore=_ignore_dangling_symlinks,
            )
        try:
            proc = run_capture(
                [role_python, "data_generator.py"],
                cwd=str(ws),
                env=isolate_home_env(minimal_child_env(), ws.parent / ".datagen_home"),
                text=True,
                timeout=120,
            )
            if proc.returncode != 0:
                if _has_materialized_env_data(ws):
                    log.warning(
                        "data_generator.py failed for %s; using pre-materialized "
                        "environment/data. stderr_tail=%r",
                        task_dir,
                        (proc.stderr or "")[-1000:],
                    )
                else:
                    raise WorkspaceMaterializationError(
                        "data_generator.py failed for "
                        f"{task_dir}: rc={proc.returncode}\n"
                        f"stdout:\n{(proc.stdout or '')[-4000:]}\n"
                        f"stderr:\n{(proc.stderr or '')[-4000:]}"
                    )
        except WorkspaceMaterializationError:
            raise
        except Exception as exc:
            raise WorkspaceMaterializationError(
                f"data_generator.py failed for {task_dir}: {type(exc).__name__}: {exc}"
            ) from exc
        if staged_sa is not None and staged_sa.is_dir():
            shutil.rmtree(staged_sa, ignore_errors=True)
        shutil.rmtree(ws / "tests", ignore_errors=True)

    env_data = ws / "environment" / "data"
    if env_data.is_dir():
        for item in env_data.iterdir():
            if item.name.startswith("_"):
                continue
            target = ws / item.name
            if target.exists():
                continue
            try:
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
            except Exception:
                continue

    if agent_solve_sh:
        sh = ws / "solve.sh"
        canon_args = (
            _canonical_solution_args(sh.read_text(errors="replace")) if sh.is_file() else ""
        )
        write_agent_solve_sh(sh, python=role_python, solution_args=canon_args)


def materialize_workspace(
    task_dir: Path,
    ws: Path,
    *,
    agent_solve_sh: bool = True,
    contract: str = "agent",
) -> None:
    """Materialize ``task_dir`` into ``ws`` under the chosen ``contract``.

    ``contract="agent"`` (default) preserves the AFTER/native-framework harness
    behavior; ``contract="core"`` preserves ``SbBenchTaskLayout.stage_workspace``.

    When EVO_CORPUS_BASE_ROOT + EVO_CORPUS_WRITE_CENSUS are set and the task is
    census-vetted, the workspace is hardlink-staged from a once-built base
    instead of byte-copied (same paths, same bytes, zero new file inodes).
    """
    if contract not in ("core", "agent"):
        raise ValueError(f"unknown materialize contract {contract!r} (expected 'agent' or 'core')")
    from evolution.eval.corpus_base import maybe_stage_workspace_from_base

    verifier = validated_verifier_source(task_dir)[1] if contract == "core" else None
    staged_from_base = maybe_stage_workspace_from_base(
        task_dir, ws, contract=contract, agent_solve_sh=agent_solve_sh
    )
    if contract == "core":
        if not staged_from_base:
            _materialize_core(task_dir, ws)
        assert verifier is not None
        _scrub_core_oracle(ws, verifier)
        return
    if staged_from_base:
        return
    _materialize_agent(task_dir, ws, agent_solve_sh=agent_solve_sh)


__all__ = [
    "WorkspaceMaterializationError",
    "materialize_workspace",
    "resolve_experiment_python",
    "validated_verifier_source",
    "write_agent_solve_sh",
]
