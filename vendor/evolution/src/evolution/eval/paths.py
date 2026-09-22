"""Core filesystem locations for the evaluation pipeline and CLI.

Kept tiny and dependency-free so both the ``evo`` CLI and the eval runner can
resolve the tasks directory with the same explicit/environment/project order.
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_tasks_root(
    explicit: str | Path | None = None,
    *,
    project_dir: str | Path | None = None,
) -> Path:
    """Resolve tasks as explicit path, ``EVO_TASKS_ROOT``, or project ``tasks/``."""
    selected = explicit or os.environ.get("EVO_TASKS_ROOT")
    return Path(selected or Path(project_dir or Path.cwd()) / "tasks").expanduser().resolve()


def tasks_root() -> str:
    """Backward-compatible string form of :func:`resolve_tasks_root`."""
    return str(resolve_tasks_root())
