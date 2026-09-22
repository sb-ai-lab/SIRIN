"""CLI entry point for the evo command.

This module wires the documented grouped command tree. Command bodies live in
the topic modules under :mod:`evolution.cli.commands` and are registered once
below, so flat aliases cannot drift from the public surface.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import typer

from evolution import __version__
from evolution.cli.app import (
    app,
    console,
    container_app,
    evolve_app,
    run_app,
    skill_app,
    split_app,
    task_app,
    trace_app,
)
from evolution.cli.bench import bench as _bench_app
from evolution.cli.commands.evolve import (
    optimize_cmd,
    optimize_status_cmd,
    reflect_cmd,
    rewrite_cmd,
)
from evolution.cli.commands.skills import (
    commit,
    container_snapshots_cmd,
    create,
    create_container,
    delete_container,
    delete_version_cmd,
    diff_cmd,
    discard,
    history,
    import_cmd,
    import_skillsbench,
    init,
    lineage,
    list_containers,
    list_skills,
    promote,
    repair_cmd,
    search,
    show,
    show_container,
    snapshot_container_cmd,
    status,
    validate,
)
from evolution.cli.commands.solve import solve_cmd
from evolution.cli.commands.tasks import (
    import_sb_bench,
    list_tasks,
    run_task_cmd,
    run_tasks_cmd,
    setup_task_cmd,
    split_check_cmd,
    split_list_cmd,
)
from evolution.cli.commands.traces import repair_traces_cmd, show_trace_cmd, traces_cmd
from evolution.cli.onboarding import doctor, quickstart, task_new


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"evo {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Evolution CLI."""


def gui_cmd() -> None:
    """Launch the optional Streamlit dashboard for the current project."""
    if importlib.util.find_spec("streamlit") is None:
        console.print("[red]GUI dependencies are missing; install evo-skills[gui].[/red]")
        raise typer.Exit(2)
    app_path = Path(__file__).parents[1] / "gui" / "app.py"
    completed = subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
    if completed.returncode:
        raise typer.Exit(2)


# ------------------------------------------------------------------
# Lifecycle command groups
# ------------------------------------------------------------------

app.command(name="init")(init)
app.command(name="gui")(gui_cmd)

task_app.command(name="list")(list_tasks)
task_app.command(name="setup")(setup_task_cmd)
task_app.command(name="eval")(run_task_cmd)
task_app.command(name="eval-all")(run_tasks_cmd)
task_app.command(name="import-sb-bench")(import_sb_bench)
task_app.command(name="new")(task_new)

skill_app.command(name="create")(create)
skill_app.command(name="list")(list_skills)
skill_app.command(name="show")(show)
skill_app.command(name="validate")(validate)
skill_app.command(name="search")(search)
skill_app.command(name="status")(status)
skill_app.command(name="lineage")(lineage)
skill_app.command(name="diff")(diff_cmd)
skill_app.command(name="history")(history)
skill_app.command(name="commit")(commit)
skill_app.command(name="promote")(promote)
skill_app.command(name="discard")(discard)
skill_app.command(name="repair")(repair_cmd)
skill_app.command(name="delete-version")(delete_version_cmd)
skill_app.command(name="import")(import_cmd)
skill_app.command(name="import-skillsbench")(import_skillsbench)

container_app.command(name="list")(list_containers)
container_app.command(name="show")(show_container)
container_app.command(name="create")(create_container)
container_app.command(name="delete")(delete_container)
container_app.command(name="snapshot")(snapshot_container_cmd)
container_app.command(name="snapshots")(container_snapshots_cmd)

run_app.command(name="solve")(solve_cmd)
run_app.add_typer(_bench_app, name="bench")

trace_app.command(name="list")(traces_cmd)
trace_app.command(name="show")(show_trace_cmd)
trace_app.command(name="repair")(repair_traces_cmd)

evolve_app.command(name="reflect")(reflect_cmd)
evolve_app.command(name="rewrite")(rewrite_cmd)
evolve_app.command(name="optimize")(optimize_cmd)
evolve_app.command(name="status")(optimize_status_cmd)

split_app.command(name="check")(split_check_cmd)
split_app.command(name="list")(split_list_cmd)

app.command(name="doctor")(doctor)
app.command(name="quickstart")(quickstart)


if __name__ == "__main__":  # `python -m evolution.cli.main`
    app()
