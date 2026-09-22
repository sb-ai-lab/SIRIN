"""Upstream sb-bench task layout.

Reads tasks in the sb-bench native format directly (no conversion to
the evo layout). Mirrors the runtime behavior of
``test_bench_scripts/qwen35_9B_run/bench.py`` while keeping skill
management on the evo side.

Layout assumptions (sb-bench native):
    task_dir/
        task.toml          — sb-bench flavor: [task], [verification]
        instruction.md     — references paths under environment/data/
        environment/data/  — input files (NOT staged separately;
                             the safe-copy preserves them in place)
        solve.sh           — execution wrapper; cd's to output/ then runs python3 solution.py
        tests/test_outputs.py
        [.ground_truth_*]  — kept inside the safe-copy
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import tomllib
from pathlib import Path

from evolution.eval.child_env import minimal_child_env
from evolution.eval.layouts.base import (
    CollectResult,
    RunResult,
    TaskLayout,
    TaskMetadata,
    TestResult,
    collect_outputs,
    rewrite_tests_if_needed,
)
from evolution.eval.layouts.evo import _parse_pytest_summary
from evolution.eval.proc import run_capture
from evolution.eval.workspace_guard import isolate_home_env


class SbBenchTaskLayout(TaskLayout):
    """The sb-bench source format (no conversion to evo)."""

    name = "sb_bench"

    # ── metadata ────────────────────────────────────────────────────────

    def parse_metadata(self, task_dir: Path) -> TaskMetadata:
        toml_path = task_dir / "task.toml"
        instruction_path = task_dir / "instruction.md"
        if not toml_path.exists():
            raise FileNotFoundError(f"task.toml not found in {task_dir}")

        with toml_path.open("rb") as f:
            data = tomllib.load(f)
        task_block = data.get("task", {})
        verify_block = data.get("verification", {})
        instruction = (
            instruction_path.read_text(encoding="utf-8").strip()
            if instruction_path.exists()
            else ""
        )

        return TaskMetadata(
            # Identity is the directory name (== sb-bench task id), NOT the
            # human-readable [task].name title — every other part of the
            # system addresses tasks by their dir id (role/task_id splits,
            # the .txt task lists, evo run bench run --tasks). Mirrors the SkillStore
            # convention where a skill's identity is its folder, not its
            # frontmatter name. The descriptive title is intentionally
            # dropped; the raw id is preserved in source_task below.
            name=task_dir.name,
            instruction=instruction,
            role=task_block.get("role"),
            difficulty=task_block.get("difficulty", "medium"),
            category=task_block.get("role") or "",  # sb-bench has no separate category
            skills_required=[
                str(skill).replace("_", "-") for skill in task_block.get("skills") or []
            ],
            tags=list(task_block.get("tags") or []),
            timeout_sec=float(
                verify_block.get("timeout_seconds") or task_block.get("timeout_seconds") or 300
            ),
            test_file=verify_block.get("verifier_entrypoint", "tests/test_outputs.py"),
            required_outputs=[],
            source="sb-bench",
            source_task=task_block.get("id", task_dir.name),
            raw_toml=toml_path.read_text(encoding="utf-8"),
        )

    # ── staging ────────────────────────────────────────────────────────

    def stage_workspace(self, task_dir: Path, workspace: Path) -> None:
        """Mirror the task tree into ``workspace`` (sans output/, caches).

        sb-bench tasks reference paths like ``environment/data/foo.xlsx`` from
        instruction.md and solve.sh, so the workspace mirrors the task tree
        rather than flattening. Delegates to the shared core materializer.
        """
        from evolution.eval.workspace_materializer import materialize_workspace

        materialize_workspace(task_dir, workspace, contract="core")

    # ── solution placement + run ───────────────────────────────────────

    def place_solution(self, workspace: Path, code: str) -> Path:
        """Write ``solution.py`` at the workspace root (where solve.sh expects
        it). Also writes ``_solve.py`` as a debug duplicate so other
        callers can reuse a single name."""
        sol = workspace / "solution.py"
        sol.write_text(code, encoding="utf-8")
        (workspace / "_solve.py").write_text(code, encoding="utf-8")
        return sol

    def run_solution(
        self,
        workspace: Path,
        python_exe: str,
        *,
        timeout: float,
        env: dict[str, str] | None = None,
    ) -> RunResult:
        """``bash solve.sh`` with ``python3`` patched to ``python_exe``.

        Mirrors ``test_bench_scripts/.../bench.py:run_solve_sh``: the
        original solve.sh is read, its ``python3`` invocations are
        replaced with the role-specific python so the patched script
        runs in the desired conda env, and then we execute the patched
        text via ``bash -c`` so the underlying file is never mutated.
        """
        solve_sh = workspace / "solve.sh"
        if not solve_sh.is_file():
            return RunResult(ok=False, error=f"solve.sh not found in {workspace}")

        patched = solve_sh.read_text(encoding="utf-8").replace("python3", python_exe)
        start = time.time()
        try:
            proc = run_capture(
                ["bash", "-c", patched],
                cwd=str(workspace),
                text=True,
                timeout=timeout,
                env=env
                if env is not None
                else isolate_home_env(minimal_child_env(), workspace / "_solve_home"),
            )
            return RunResult(
                ok=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                elapsed_sec=time.time() - start,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                ok=False,
                returncode=-1,
                elapsed_sec=time.time() - start,
                timed_out=True,
                error=f"solve.sh timed out after {timeout}s",
            )
        except OSError as exc:
            return RunResult(
                ok=False,
                returncode=-1,
                elapsed_sec=time.time() - start,
                error=str(exc),
            )

    # ── testing ────────────────────────────────────────────────────────

    def run_tests(
        self,
        task_dir: Path,
        workspace: Path,
        python_exe: str,
        *,
        timeout: float,
        env: dict[str, str] | None = None,
        test_file: str | None = None,
    ) -> TestResult:
        """Run pytest from the workspace with TASK_WORKSPACE set.

        The authoritative test directory is staged only after the solver has
        finished, so relative ``Path(__file__)`` roots point at the evaluated
        workspace while solver-created shadow tests are replaced. Handles the
        historical sb-bench convention: tests bake in
        ``/root/`` and ``/app/`` prefixes for ground-truth files. If any
        such reference is present, we copy the tests directory into a
        sibling ``_hidden_tests__<workspace_name>/`` and rewrite paths
        there before invoking pytest. The originals are never touched.
        """
        tf = test_file or "tests/test_outputs.py"
        from evolution.eval.workspace_materializer import (
            WorkspaceMaterializationError,
            validated_verifier_source,
        )

        try:
            source_test, relative_test = validated_verifier_source(task_dir, tf)
        except WorkspaceMaterializationError as exc:
            return TestResult(error=str(exc))

        staged_dir = workspace / relative_test.parent
        if relative_test.parent == Path("."):
            test_path = workspace / relative_test.name
            if test_path.is_symlink() or test_path.is_file():
                test_path.unlink()
            shutil.copy2(source_test, test_path)
        else:
            workspace_root = workspace.resolve()
            if not staged_dir.parent.resolve(strict=False).is_relative_to(workspace_root):
                return TestResult(error=f"Unsafe staged test path: {tf}")
            if staged_dir.is_symlink() or staged_dir.is_file():
                staged_dir.unlink()
            elif staged_dir.exists():
                shutil.rmtree(staged_dir)
            staged_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_test.parent, staged_dir)
            test_path = workspace / relative_test

        # Shared /root|/app rewrite (same helper EvoTaskLayout uses).
        run_test_path, run_cwd = rewrite_tests_if_needed(test_path, workspace)

        run_env = {
            **(env or isolate_home_env(minimal_child_env(), workspace / "_solve_home")),
            "TASK_WORKSPACE": str(workspace),
        }
        # Prepend the role python's bin dir so bare ``python3`` resolves there.
        py_bin_dir = os.path.dirname(python_exe)
        if py_bin_dir:
            run_env["PATH"] = py_bin_dir + os.pathsep + run_env.get("PATH", "")

        cmd = [
            python_exe,
            "-m",
            "pytest",
            str(run_test_path),
            "-v",
            "--tb=short",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ]
        start = time.time()
        try:
            proc = run_capture(
                cmd,
                cwd=str(run_cwd),
                text=True,
                timeout=timeout,
                env=run_env,
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                elapsed_sec=time.time() - start,
                timed_out=True,
                error=f"pytest timed out after {timeout}s",
            )

        return _parse_pytest_summary(proc.stdout + proc.stderr, time.time() - start)

    # ── output collection ──────────────────────────────────────────────

    def collect_outputs(self, workspace: Path, pre_snapshot: dict[str, str]) -> CollectResult:
        """Copy produced root files into ``output/`` (the verifier's read dir)."""
        return collect_outputs(workspace, pre_snapshot)

    # ── cleanup ────────────────────────────────────────────────────────

    def cleanup_between_attempts(self, workspace: Path) -> None:
        for name in ("solution.py", "_solve.py"):
            p = workspace / name
            if p.is_file():
                p.unlink()
        out_dir = workspace / "output"
        if out_dir.is_dir():
            for child in out_dir.iterdir():
                if child.is_file() or child.is_symlink():
                    child.unlink()
                else:
                    shutil.rmtree(child)
        for cache in workspace.rglob("__pycache__"):
            if cache.is_dir():
                shutil.rmtree(cache, ignore_errors=True)
