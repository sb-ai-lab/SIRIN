"""Protocol and shared dataclasses for the task layout abstraction.

Two concrete implementations live alongside this module:
``EvoTaskLayout`` (evo native) and ``SbBenchTaskLayout`` (upstream
sb-bench). The eval pipeline (`workspace.py`, `runner.py`,
`solver.py`) will, once Phase 3 lands, dispatch through this Protocol
instead of branching inline on file presence.
"""

from __future__ import annotations

import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from evolution.eval.evidence import produced_paths


class TaskTomlError(ValueError):
    """Raised when a task.toml cannot be read as a TOML document."""


def read_task_toml(task_dir: Path) -> tuple[dict, str]:
    """Read and parse ``task.toml`` with a path-specific error."""
    path = Path(task_dir) / "task.toml"
    try:
        text = path.read_text(encoding="utf-8")
        return tomllib.loads(text), text
    except tomllib.TOMLDecodeError as exc:
        raise TaskTomlError(f"{path}: invalid TOML: {exc}") from exc
    except OSError as exc:
        raise TaskTomlError(f"{path}: cannot read TOML: {exc}") from exc


@dataclass
class TaskMetadata:
    """Parsed metadata from a task.toml. Layout-agnostic representation.

    Fields not present in a given layout's toml are left at their defaults.
    """

    name: str
    """Task identifier; defaults to the directory name if no name field exists."""

    instruction: str = ""
    """Raw instruction text (after any layout-internal path rewriting)."""

    role: str | None = None
    """sb-bench role (de / ds / genai / infra / pm / swe). None for Evolution-native tasks."""

    difficulty: str = "medium"

    category: str = ""

    skills_required: list[str] = field(default_factory=list)
    """Skill names the task asks for. Evolution-native tasks use
    ``[skills].required``; SB-Bench and AFTER tasks use ``[task].skills``."""

    tags: list[str] = field(default_factory=list)

    timeout_sec: float = 600.0
    """Per-attempt wall-clock budget. evo: ``[evaluation].timeout_sec``;
    sb-bench: ``[verification].timeout_seconds``."""

    test_file: str = "tests/test_outputs.py"
    """Relative path from the task dir (and from the workspace) to the
    pytest entry."""

    required_outputs: list[str] = field(default_factory=list)
    """Public declared outputs. Never reads tests/expected/oracle."""

    source: str = ""
    """Origin tag (``skillsbench``, ``sb-bench``, ``""``)."""

    source_task: str = ""

    raw_toml: str = ""
    """Verbatim task.toml text. Layouts may stash this for downstream callers."""


@dataclass
class RunResult:
    """Outcome of executing a placed solution (solve.sh, python, …)."""

    ok: bool
    """Whether the run completed and returned 0."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    elapsed_sec: float = 0.0
    timed_out: bool = False
    error: str | None = None
    """Free-form summary when ``ok`` is False (timeout / exception text)."""


@dataclass
class TestResult:
    """Outcome of running the task's tests against a workspace."""

    collected: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errored: int = 0
    stdout: str = ""
    elapsed_sec: float = 0.0
    timed_out: bool = False
    error: str | None = None


@dataclass
class CollectResult:
    """Outcome of placing solver-produced files into ``output/``."""

    copied: int = 0
    flattened: int = 0
    error: str | None = None
    """Set on a copy/move IOError — fail loud, never a silent score of 0."""


def collect_outputs(workspace: Path, pre_snapshot: dict[str, str]) -> CollectResult:
    """COPY solver-produced root files into ``workspace/output/`` and flatten an
    accidental ``output/output/`` nest, so the ``output/``-reading verifier sees
    them no matter where the agent wrote.

    COPY (never move): SWE in-place tasks deliver at the root and their verifier
    reads the root; copying satisfies both root- and ``output/``-readers and
    leaves root state intact. No-clobber: a file already under ``output/`` (a
    correct ``solve.sh`` delivery) wins over a same-named root scratch. Fail
    loud: a copy/move ``OSError`` sets ``error`` rather than silently leaving
    ``output/`` empty. Idempotent; a strict no-op when nothing was produced.
    """
    workspace = Path(workspace)
    output_dir = workspace / "output"
    res = CollectResult()
    try:
        nested = output_dir / "output"
        if nested.is_dir():
            for src in sorted(p for p in nested.rglob("*") if p.is_file()):
                dst = output_dir / src.relative_to(nested)
                if dst.exists():
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                res.flattened += 1
            shutil.rmtree(nested, ignore_errors=True)

        output_dir.mkdir(parents=True, exist_ok=True)
        for rel in produced_paths(workspace, pre_snapshot):
            if Path(rel).parts[:1] == ("output",):
                continue
            dst = output_dir / rel
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(workspace / rel, dst)
            res.copied += 1
    except OSError as exc:
        res.error = f"{type(exc).__name__}: {exc}"
    return res


def rewrite_tests_if_needed(test_path: Path, workspace: Path) -> tuple[Path, Path]:
    """Mirror the legacy ``runner.run_task`` ``/root`` / ``/app`` handling.

    Some imported sb-bench tests bake in ``/root/`` and ``/app/`` path
    prefixes that the bundled ground-truth scripts use. Without rewriting
    them to the actual workspace the tests fail for path reasons rather
    than solver-quality reasons.

    If ``test_path`` contains either prefix, copy the *entire* tests
    directory into a hidden sibling of the workspace
    (``_hidden_tests__<workspace_name>``) with the prefixes rewritten to
    the workspace path, and return ``(run_test_path, run_cwd)`` pointing
    there. Otherwise return ``(test_path, workspace)`` unchanged. The
    original tests directory is never modified.

    Shared by both ``EvoTaskLayout`` and ``SbBenchTaskLayout`` so the
    layout path is a strict superset of the legacy runner behavior.
    """
    test_dir = test_path.parent
    try:
        text = test_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return test_path, workspace
    if "/root/" not in text and "/app/" not in text:
        return test_path, workspace

    hidden = workspace.parent / f"_hidden_tests__{workspace.name}"
    hidden.mkdir(parents=True, exist_ok=True)
    for entry in test_dir.iterdir():
        dst = hidden / entry.name
        if entry.is_file():
            body = entry.read_text(encoding="utf-8", errors="replace")
            body = body.replace("/root/", f"{workspace}/").replace("/app/", f"{workspace}/")
            dst.write_text(body, encoding="utf-8")
        elif entry.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(entry, dst)
    return hidden / test_path.name, hidden


class TaskLayout(Protocol):
    """The methods a layout must provide to drive one task end-to-end.

    Implementations are stateless and cheap to instantiate; the eval
    pipeline keeps one instance per `Task`. See module docstring + the
    plan document at ``plans/layout_abstraction.md`` for the contract.
    """

    name: str
    """Short identifier (``"evo"`` / ``"sb_bench"``) used in audit logs."""

    def parse_metadata(self, task_dir: Path) -> TaskMetadata:
        """Read the task's task.toml + instruction.md into a layout-neutral struct."""
        ...

    def stage_workspace(self, task_dir: Path, workspace: Path) -> None:
        """Populate ``workspace`` with the files needed to run a solve attempt.

        evo: copy ``task_dir/inputs/*`` into ``workspace/``.
        sb-bench: copy the entire task tree into ``workspace/`` (sans output/, caches).
        """
        ...

    def place_solution(self, workspace: Path, code: str) -> Path:
        """Write the LLM-produced code where the run step expects it.

        Returns the canonical script path so the caller can log it.
        Both layouts today write ``workspace/solution.py`` (sb-bench's
        solve.sh expects that name) and optionally ``workspace/_solve.py``
        as a debug copy.
        """
        ...

    def run_solution(
        self,
        workspace: Path,
        python_exe: str,
        *,
        timeout: float,
        env: dict[str, str] | None = None,
    ) -> RunResult:
        """Execute the placed solution.

        evo: ``python workspace/_solve.py``.
        sb-bench: ``bash solve.sh`` with ``python3`` patched to ``python_exe``.

        ``env`` is the base environment to run under. The layout may add
        layout-specific variables (e.g. ``TASK_WORKSPACE``) before calling
        subprocess.
        """
        ...

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
        """Run pytest against the staged workspace.

        ``test_file`` defaults to whatever ``parse_metadata`` returned for
        this task. The layout decides cwd, extra env vars, and any
        per-task path rewriting (e.g. sb-bench's ``/root`` -> ``workspace``
        substitution in tests).
        """
        ...

    def collect_outputs(self, workspace: Path, pre_snapshot: dict[str, str]) -> CollectResult:
        """Place solver-produced files where the verifier reads them.

        Runs after ``run_solution`` and before ``run_tests``. sb-bench copies
        produced root files into ``output/`` (its verifier's read location) and
        flattens ``output/output/``; evo is a strict no-op (its verifiers read
        the workspace root). Returns a ``CollectResult`` whose ``error`` is set
        on a copy failure so the caller can fail loud instead of scoring 0.
        """
        ...

    def cleanup_between_attempts(self, workspace: Path) -> None:
        """Reset workspace state between solve attempts.

        Wipes ``solution.py`` / ``_solve.py`` / ``output/*`` /
        ``__pycache__`` so the next attempt starts clean. Does NOT touch
        input files, test files, or the layout-managed ``environment/``.
        """
        ...
