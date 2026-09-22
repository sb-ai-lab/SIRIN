"""Task model — evaluation tasks for measuring skill effectiveness."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid runtime import cost
    from evolution.eval.layouts import TaskLayout


@dataclass
class Task:
    """An evaluation task that measures skill effectiveness.

    Tasks are adopted from benchmarks (e.g. SkillsBench) or created manually.
    Each task has an instruction, required skills, and pytest-based assertions.
    """

    name: str
    instruction: str
    difficulty: str  # easy, medium, hard
    category: str
    skills_required: list[str]
    tags: list[str] = field(default_factory=list)
    # sb-bench role (de/ds/genai/infra/pm/swe); selects the interpreter the
    # solution + tests run under (see eval/python_env.py). None for Evolution-native tasks.
    role: str | None = None
    source: str = ""  # e.g. "skillsbench"
    source_task: str = ""  # original task id
    timeout_sec: float = 600.0
    test_file: str = "tests/test_outputs.py"
    # Public declared outputs only; never tests/expected/oracle (see CLAUDE.md).
    required_outputs: list[str] = field(default_factory=list)
    path: Path = field(default_factory=lambda: Path("."))
    # Populated by ``load_task`` via ``detect_layout``. Carries the
    # layout-specific run/test semantics (evo native vs sb-bench native).
    # The eval pipeline (workspace/runner/solver) always drives a task
    # through its layout; ``resolve_layout`` defaults a directly-constructed
    # Task (layout=None) to the evo native layout for backward compatibility.
    layout: TaskLayout | None = None

    @property
    def test_path(self) -> Path:
        return self.path / self.test_file

    def resolve_layout(self) -> TaskLayout:
        """Return this task's layout, defaulting to the evo native layout."""
        if self.layout is not None:
            return self.layout
        from evolution.eval.layouts import EvoTaskLayout

        return EvoTaskLayout()


@dataclass
class TaskResult:
    """Result of running a task evaluation."""

    task_name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    # Combined pytest stdout+stderr + collected node ids for the oracle path.
    raw_stdout: str | None = None
    nodeids: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.total_tests > 0


class TaskDiscoveryError(ValueError):
    """Raised after all declared task directories have been checked."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("Invalid task(s):\n" + "\n".join(f"- {error}" for error in errors))


def load_task(task_dir: Path) -> Task:
    """Load a task from its directory.

    Detects the task layout (evo native vs sb-bench native) and sources all
    metadata through ``layout.parse_metadata``.
    """
    task_dir = Path(task_dir).resolve()

    if not task_dir.is_dir():
        raise FileNotFoundError(f"Task directory not found: {task_dir}")
    if not (task_dir / "task.toml").exists():
        raise FileNotFoundError(f"task.toml not found in {task_dir}")
    if not (task_dir / "instruction.md").exists():
        raise FileNotFoundError(f"instruction.md not found in {task_dir}")

    # Deferred import to avoid module-load circular pressure with eval.layouts.
    from evolution.eval.layouts import detect_layout

    layout = detect_layout(task_dir)
    md = layout.parse_metadata(task_dir)
    return Task(
        name=md.name,
        instruction=md.instruction,
        difficulty=md.difficulty,
        category=md.category,
        skills_required=md.skills_required,
        tags=md.tags,
        role=md.role,
        source=md.source,
        source_task=md.source_task,
        timeout_sec=md.timeout_sec,
        test_file=md.test_file,
        required_outputs=md.required_outputs,
        path=task_dir,
        layout=layout,
    )


def discover_tasks(tasks_dir: Path) -> list[Task]:
    """Discover all tasks in a directory."""
    tasks_dir = Path(tasks_dir).resolve()
    if not tasks_dir.is_dir():
        return []

    tasks: list[Task] = []
    errors: list[str] = []
    for child in sorted(tasks_dir.iterdir()):
        if child.is_dir() and (child / "task.toml").exists():
            try:
                tasks.append(load_task(child))
            except Exception as exc:
                errors.append(f"{child / 'task.toml'}: {exc}")
    if errors:
        raise TaskDiscoveryError(errors)
    return tasks
