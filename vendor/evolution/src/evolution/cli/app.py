"""Shared CLI app objects and helpers for the ``evo`` command modules.

The command bodies live in the topic modules under
:mod:`evolution.cli.commands` (``skills``, ``tasks``, ``traces``, ``evolve``,
``solve``) that decorate the single ``app`` defined here. The entry module
:mod:`evolution.cli.main` imports those modules and wires the grouped
``task``/``skill``/``run``/``trace``/
``evolve``/``split`` sub-apps. Keeping ``app`` and the shared helpers here
avoids an import cycle between ``main`` and the command modules.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console

from evolution.core.store import SkillStore
from evolution.eval.paths import tasks_root
from evolution.eval.task import Task
from evolution.lineage.state_io import LockTimeoutError, skill_mutation_lock
from evolution.workflow import get_task, skill_store

app = typer.Typer(
    name="evo",
    help="Evolution: trace-driven skill lifecycle for LLM agents.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
console = Console()

task_app = typer.Typer(help="Create, list, prepare, and evaluate task corpora.")
skill_app = typer.Typer(help="Create, inspect, validate, and version skills.")
container_app = typer.Typer(help="Create, inspect, and snapshot skill containers.")
run_app = typer.Typer(help="Run task attempts and benchmark loops.")
trace_app = typer.Typer(help="List and inspect recorded task traces.")
evolve_app = typer.Typer(help="Reflect on traces and rewrite candidate skills.")
split_app = typer.Typer(help="Inspect train/test split manifests.")

app.add_typer(task_app, name="task")
app.add_typer(skill_app, name="skill")
skill_app.add_typer(container_app, name="container")
app.add_typer(run_app, name="run")
app.add_typer(trace_app, name="trace")
app.add_typer(evolve_app, name="evolve")
app.add_typer(split_app, name="split")


def _get_store(project_dir: Path | None = None) -> SkillStore:
    return skill_store(project_dir=project_dir, user_dir=Path.home())


def _get_container_store(project_dir: Path | None = None):
    from evolution.core.containers import ContainerStore

    project = project_dir or Path.cwd()
    return ContainerStore(project_dir=project, user_dir=Path.home())


@contextmanager
def _skill_cli_lock(skill_path: Path) -> Iterator[None]:
    try:
        with skill_mutation_lock(skill_path):
            yield
    except LockTimeoutError:
        console.print(
            f"[red]Skill {skill_path.name!r} is busy; retry after the active mutation.[/red]"
        )
        raise typer.Exit(2) from None


def _task_instruction_for_cli_task(task: str, tasks_dir: Path | None) -> str:
    """Resolve a task filter to non-empty task instructions or fail loudly."""
    task_obj = _task_obj_for_cli_task(task, tasks_dir)
    if not str(task_obj.instruction or "").strip():
        tasks_path = Path(tasks_dir or tasks_root()).resolve()
        console.print(f"[red]Task {task!r} in {tasks_path} has an empty instruction.[/red]")
        raise typer.Exit(1)
    return task_obj.instruction


def _task_obj_for_cli_task(task: str, tasks_dir: Path | None) -> Task:
    """Resolve a task filter to its full Task object (agentic-session workspace)."""
    tasks_path = Path(tasks_dir or tasks_root()).resolve()
    try:
        return get_task(task, tasks_dir=tasks_path)
    except KeyError:
        console.print(f"[red]Task {task!r} not found in tasks directory {tasks_path}.[/red]")
        raise typer.Exit(1) from None
