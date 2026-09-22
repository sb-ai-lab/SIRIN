"""Turn this family's tasks into the agent seam's plain-dict cases.

The case shape is already agent-neutral on both sides: a ``dict``. That part of
the seam fits without friction, which is worth recording as clearly as the parts
that do not.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evolution.workflow import list_tasks

#: Case keys this family populates. ``expected`` has no counterpart: a pytest
#: task's oracle is its test file, not a value the corpus can carry.
CASE_KEYS = ("case_id", "task_name", "tasks_dir")


class FlatTaskCorpus:
    """Loads tasks from a task root and yields one case per task."""

    def __init__(self, tasks_dir: Path | None = None) -> None:
        self._tasks_dir = Path(tasks_dir) if tasks_dir is not None else None

    def load_cases(self, project_dir: Path | None = None) -> list[dict[str, Any]]:
        """Return one case dict per discoverable task.

        Raises when a task root resolves but holds no task: an evaluation that
        silently measures nothing is worse than one that stops, because the gate
        downstream still produces a verdict from the empty result.
        """
        tasks = list_tasks(tasks_dir=self._tasks_dir, project_dir=project_dir)
        if not tasks:
            raise ValueError(
                f"task root produced no runnable tasks: {self._tasks_dir or project_dir!r}"
            )
        return [
            {
                "case_id": task.name,
                "task_name": task.name,
                "tasks_dir": str(self._tasks_dir) if self._tasks_dir else None,
            }
            for task in tasks
        ]
