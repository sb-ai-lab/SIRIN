"""Task evaluation runner — execute pytest assertions against a workspace."""

from __future__ import annotations

import logging
import re
from collections.abc import Collection
from pathlib import Path

from evolution.eval.child_env import minimal_child_env
from evolution.eval.python_env import resolve_python_for_role
from evolution.eval.task import Task, TaskResult
from evolution.eval.workspace_guard import build_guarded_env

_PYTEST_OUTPUT_MAX = 64 * 1024
_NODEID_LINE = re.compile(r"^(\S+::\S+)\s+(?:PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b")

logger = logging.getLogger(__name__)


def _collected_nodeids(stdout: str) -> list[str]:
    seen: list[str] = []
    for line in stdout.splitlines():
        m = _NODEID_LINE.match(line.strip())
        if m and m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def _persist_pytest_output(workspace: Path, stdout: str) -> None:
    text = stdout or ""
    if len(text) > _PYTEST_OUTPUT_MAX:
        half = _PYTEST_OUTPUT_MAX // 2
        text = f"{text[:half]}\n...[truncated]...\n{text[-half:]}"
    try:
        (workspace / "pytest_output.txt").write_text(text, encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not persist pytest output to %s: %s", workspace, exc)


def run_task(
    task: Task,
    workspace: Path,
    timeout: float | None = None,
    *,
    pass_env: Collection[str] = (),
) -> TaskResult:
    """Run a task's test suite against a workspace directory.

    Args:
        task: The task to evaluate.
        workspace: Directory where the agent produced its output.
        timeout: Override timeout in seconds (default: task.timeout_sec).

    Returns:
        TaskResult with pass/fail counts and error details.
    """
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        return TaskResult(
            task_name=task.name,
            errors=[f"Workspace not found: {workspace}"],
        )

    timeout_sec = timeout or task.timeout_sec

    # Delegate to the task's layout. The layout owns the cwd choice, env
    # extension (TASK_WORKSPACE etc.), and any per-task path rewriting
    # (the sb-bench /root|/app → workspace substitution, via the shared
    # rewrite_tests_if_needed helper). We still build the guarded env so
    # the workspace boundary is enforced and auditable.
    env = build_guarded_env(
        framework="evolution-pytest",
        workspace_dir=workspace,
        audit_log_path=workspace / ".workspace_guard.jsonl",
        base_env=minimal_child_env(allow=pass_env),
        command_wrappers=True,
    )
    result = task.resolve_layout().run_tests(
        task.path,
        workspace,
        resolve_python_for_role(task.role),
        timeout=timeout_sec,
        env=env,
        test_file=task.test_file,
    )
    _persist_pytest_output(workspace, result.stdout)
    if result.timed_out:
        return TaskResult(task_name=task.name, errors=[f"Timeout after {timeout_sec}s"])
    if result.error and result.collected == 0:
        return TaskResult(task_name=task.name, errors=[result.error])
    errors = [
        s
        for s in (line.strip() for line in result.stdout.splitlines())
        if s.startswith("FAILED ") or s.startswith("ERROR ")
    ]
    return TaskResult(
        task_name=task.name,
        total_tests=result.collected,
        passed=result.passed,
        failed=result.failed + result.errored,
        skipped=result.skipped,
        errors=errors,
        raw_stdout=result.stdout,
        nodeids=_collected_nodeids(result.stdout),
    )
