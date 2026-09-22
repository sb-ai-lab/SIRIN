"""Workspace setup — prepare input files for task evaluation."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from evolution.eval.task import Task
from evolution.paths import account_home


def setup_workspace(
    task: Task,
    workspace: Path | None = None,
    *,
    project_dir: Path | None = None,
) -> Path:
    """Stage a task's input files into a fresh workspace directory.

    Delegates to the task's layout: the evo native layout copies
    ``inputs/*`` into the workspace root; the sb-bench native layout
    mirrors the task tree (``environment/``, ``solve.sh``, …). Returns the
    workspace path.
    """
    if workspace is None:
        target = Path(tempfile.mkdtemp(prefix=f"evo-{task.path.name}-"))
    else:
        requested = Path(workspace).expanduser()
        if requested.is_symlink():
            raise ValueError(f"Workspace must not be a symlink: {requested}")
        target = requested.resolve()
        _validate_cleanup_target(task, target, project_dir)
        if target.exists():
            if not target.is_dir():
                raise NotADirectoryError(f"Workspace is not a directory: {target}")
            shutil.rmtree(target)
        target.mkdir(parents=True)

    task.resolve_layout().stage_workspace(task.path, target)
    return target


def _validate_cleanup_target(task: Task, target: Path, project_dir: Path | None) -> None:
    task_dir = task.path.resolve()
    cwd = Path.cwd().resolve()
    protected = {Path.home().resolve(), account_home().resolve(), cwd}
    if project_dir is not None:
        protected.add(Path(project_dir).resolve())

    if target.parent == target or any(
        target == path or target in path.parents for path in protected
    ):
        raise ValueError(f"Refusing unsafe workspace cleanup target: {target}")
    if target == task_dir or target in task_dir.parents or task_dir in target.parents:
        raise ValueError(f"Workspace must not overlap task source {task_dir}: {target}")
