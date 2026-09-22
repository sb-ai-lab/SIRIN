"""Task-corpus commands: list / setup / eval, sb-bench import, and split checks.

Callbacks are registered once under ``evo task`` and ``evo split`` by
:mod:`evolution.cli.main`.
"""

from __future__ import annotations

import re
from pathlib import Path

import typer
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from evolution.cli.app import (
    _get_container_store,
    _get_store,
    console,
)
from evolution.eval.paths import resolve_tasks_root
from evolution.eval.task import discover_tasks
from evolution.splits import LeakageError, SplitManifest


def import_sb_bench(
    repo: Path = typer.Argument(help="Path to sb-bench repository"),
    role: str | None = typer.Option(
        None,
        "--role",
        "-r",
        help="Filter by role: ds, de, infra",
    ),
    difficulty: str | None = typer.Option(
        None,
        "--difficulty",
        help="Filter by difficulty: easy, medium, hard",
    ),
    tasks_filter: str | None = typer.Option(
        None,
        "--tasks",
        "-t",
        help="Comma-separated task IDs (e.g. de/E1,infra/E2)",
    ),
    with_skills: bool = typer.Option(
        False,
        "--with-skills",
        help="Also import skills into the skill store",
    ),
    with_containers: bool = typer.Option(
        False,
        "--with-containers",
        help="Also create skill containers for each task",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing tasks",
    ),
    tasks_dir: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Destination tasks dir (default: ./tasks)",
    ),
) -> None:
    """Import tasks (and optionally skills) from sb-bench repository."""
    from evolution.importers.sb_bench import (
        discover_skills as sb_discover_skills,
    )
    from evolution.importers.sb_bench import (
        discover_tasks as sb_discover,
    )
    from evolution.importers.sb_bench import (
        import_tasks as sb_import_tasks,
    )

    dest = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    task_ids = [t.strip() for t in tasks_filter.split(",")] if tasks_filter else None

    # Show what we'll import
    found = sb_discover(repo, role=role, difficulty=difficulty)
    if task_ids:
        id_set = set(task_ids)
        found = [
            t for t in found if t.task_id in id_set or any(t.task_id.startswith(p) for p in id_set)
        ]

    if not found:
        console.print("[yellow]No matching tasks found.[/yellow]")
        raise typer.Exit(0)

    console.print(f"Found [bold]{len(found)}[/bold] task(s) to import from {repo}\n")
    for t in found:
        console.print(f"  {t.task_id:<30} {t.difficulty:<8} skills: {', '.join(t.skill_names)}")
    console.print()

    # Import tasks
    imported = sb_import_tasks(
        repo,
        dest,
        role=role,
        difficulty=difficulty,
        task_ids=task_ids,
        force=force,
    )

    if imported:
        table = Table(title=f"Imported {len(imported)} task(s)")
        table.add_column("TASK", style="cyan")
        table.add_column("STATUS", style="green")
        for name in imported:
            table.add_row(name, "imported")
        console.print(table)
    else:
        console.print("[yellow]No new tasks imported.[/yellow]")

    # Import skills if requested
    if with_skills and imported:
        store = _get_store()
        all_skills = sb_discover_skills(repo)

        # Filter to skills used by imported tasks
        imported_set = set(imported)
        task_skill_map: dict[str, list[str]] = {}
        for t in found:
            evo_name = f"sb-{t.role}-{t.task_id.split('/', 1)[-1]}"
            m = re.match(r"^[A-Z]\d+-(.+)$", t.task_id.split("/", 1)[-1])
            short = m.group(1) if m else t.task_id.split("/", 1)[-1]
            evo_name = f"sb-{t.role}-{short}"
            if evo_name in imported_set:
                task_skill_map[t.task_id] = t.skill_names

        skill_names_needed = set()
        for names in task_skill_map.values():
            skill_names_needed.update(names)

        relevant = [s for s in all_skills if s["name"] in skill_names_needed]
        skill_count = 0
        for s in relevant:
            if store.has(s["name"]):
                continue
            try:
                store.import_skill(
                    source=s["skill_dir"],
                    metadata={
                        "source": "sb-bench",
                        "source-task": s["task_id"],
                        "role": s["role"],
                    },
                )
                skill_count += 1
                console.print(f"  Imported skill: [green]{s['name']}[/green]")
            except Exception as exc:
                console.print(f"  [red]Failed: {s['name']}: {exc}[/red]")

        console.print(f"\n[green]{skill_count} skill(s) imported.[/green]")

    # Create containers if requested
    if with_containers and imported:
        cstore = _get_container_store()

        for t in found:
            m = re.match(r"^[A-Z]\d+-(.+)$", t.task_id.split("/", 1)[-1])
            short = m.group(1) if m else t.task_id.split("/", 1)[-1]
            evo_name = f"sb-{t.role}-{short}"

            if evo_name not in set(imported):
                continue
            if not t.skill_names:
                continue

            container_name = evo_name
            if cstore.has(container_name):
                console.print(
                    f"  Container [yellow]{container_name}[/yellow] already exists, skipping"
                )
                continue

            try:
                cstore.create(
                    name=container_name,
                    description=f"Skills for {t.name} ({t.task_id})",
                    skills=t.skill_names,
                    metadata={
                        "source": "sb-bench",
                        "source-task": t.task_id,
                        "role": t.role,
                    },
                )
                console.print(
                    f"  Created container: [green]{container_name}[/green] ({', '.join(t.skill_names)})"
                )
            except Exception as exc:
                console.print(f"  [red]Failed container {container_name}: {exc}[/red]")


def list_tasks(
    tasks_dir: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Tasks directory (default: ./tasks)",
    ),
) -> None:
    """List available evaluation tasks."""

    tasks_path = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    tasks = discover_tasks(tasks_path)

    if not tasks:
        console.print("No tasks found.")
        return

    table = Table(title=f"Evaluation Tasks ({len(tasks)})")
    table.add_column("NAME", style="cyan")
    table.add_column("DIFFICULTY")
    table.add_column("SKILLS", style="green")
    table.add_column("SOURCE")
    table.add_column("CATEGORY")

    for t in tasks:
        diff_style = {
            "easy": "green",
            "medium": "yellow",
            "hard": "red",
        }.get(t.difficulty, "dim")
        table.add_row(
            escape(t.name),
            f"[{diff_style}]{escape(t.difficulty)}[/]",
            escape(", ".join(t.skills_required)),
            escape(t.source),
            escape(t.category),
        )

    console.print(table)


def setup_task_cmd(
    name: str = typer.Argument(help="Task name"),
    workspace: Path = typer.Option(
        ...,
        "--workspace",
        "-w",
        help="Workspace directory to prepare",
    ),
    tasks_dir: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Tasks directory (default: ./tasks)",
    ),
) -> None:
    """Set up a workspace with task input files."""
    from evolution.eval.workspace import setup_workspace

    tasks_path = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    tasks = discover_tasks(tasks_path)
    by_name = {t.name: t for t in tasks}

    if name not in by_name:
        console.print(f"[red]Task {name!r} not found.[/red]")
        raise typer.Exit(1)

    task = by_name[name]
    ws = setup_workspace(task, workspace)

    console.print(f"[green]Workspace ready:[/green] {ws}")
    console.print(f"  Task: {task.name}")
    console.print(f"  Skills: {', '.join(task.skills_required)}")
    console.print("\n[bold]Instruction:[/bold]")
    console.print(Panel(task.instruction, title=task.name))
    console.print("\nWhen done, evaluate with:")
    console.print(f"  [cyan]evo task eval {task.name} -w {ws}[/cyan]")


def split_check_cmd(
    manifest: Path = typer.Argument(
        help="Path to a split manifest JSON file",
    ),
    evolution_tasks: str | None = typer.Option(
        None,
        "--evolution-tasks",
        help="Comma-separated task ids that will be fed to the skill-evolution loop",
    ),
    dev_tasks: str | None = typer.Option(
        None,
        "--dev-tasks",
        help="Comma-separated task ids used for selection/stopping (train+val allowed)",
    ),
    reporting_tasks: str | None = typer.Option(
        None,
        "--reporting-tasks",
        help="Comma-separated task ids used for final reporting (test only)",
    ),
) -> None:
    """Preflight: fail if any task id falls outside its allowed scope.

    Run this once at the start of every split-aware run to guarantee that the
    evolution loop, selection loop, and reporting pipeline each see only the
    slice the manifest permits.

    Examples:

      evo split check /path/to/manifest.json \
        --evolution-tasks xlsx-recover-data,offer-letter-generator \
        --dev-tasks xlsx-recover-data,offer-letter-generator,pdf-excel-diff
    """
    try:
        m = SplitManifest.load(manifest)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    console.print(f"Manifest [cyan]{m.name}[/cyan] ({m.sha256[:12]})")
    counts = m.counts
    console.print(
        f"  train={counts.get('train', '?')}  "
        f"val={counts.get('val', '?')}  "
        f"test={counts.get('test', '?')}  "
        f"(eligible={counts.get('eligible', '?')}, all_repo={counts.get('all_repo', '?')})"
    )

    def _split_ids(csv: str | None) -> list[str]:
        if not csv:
            return []
        return [x.strip() for x in csv.split(",") if x.strip()]

    checks = [
        ("skill_evolution", _split_ids(evolution_tasks), "evolution loop"),
        ("dev", _split_ids(dev_tasks), "selection/stopping"),
        ("reporting", _split_ids(reporting_tasks), "reporting"),
    ]

    had_error = False
    for scope, ids_, context in checks:
        if not ids_:
            continue
        try:
            m.assert_no_leakage(ids_, scope=scope, context=context)
            console.print(f"  [green]OK[/green] scope={scope} ({len(ids_)} tasks) -- no leakage")
        except LeakageError as exc:
            had_error = True
            console.print(f"  [red]LEAK[/red] {exc}")

    if had_error:
        raise typer.Exit(1)

    if not any(ids_ for _, ids_, _ in checks):
        console.print(
            "[yellow]No task lists supplied; manifest loaded but nothing to check.[/yellow]"
        )


def split_list_cmd(
    manifest: Path = typer.Argument(help="Path to split manifest JSON"),
    scope: str = typer.Option(
        "all",
        "--scope",
        "-s",
        help="One of: skill_evolution, dev, reporting, all",
    ),
) -> None:
    """Print the task ids in a given scope of a manifest.

    Examples:

      evo split list /path/to/manifest.json -s skill_evolution
      evo split list /path/to/manifest.json -s reporting
    """
    try:
        m = SplitManifest.load(manifest)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    try:
        ids = m.tasks(scope=scope)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    for tid in ids:
        typer.echo(tid)


def run_task_cmd(
    name: str = typer.Argument(help="Task name"),
    workspace: Path = typer.Option(
        ...,
        "--workspace",
        "-w",
        help="Workspace directory with agent output",
    ),
    tasks_dir: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Tasks directory (default: ./tasks)",
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to the verifier (repeatable).",
    ),
) -> None:
    """Run a task's evaluation tests against a workspace."""
    from evolution.eval.runner import run_task

    tasks_path = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    tasks = discover_tasks(tasks_path)
    by_name = {t.name: t for t in tasks}

    if name not in by_name:
        console.print(f"[red]Task {name!r} not found.[/red]")
        available = ", ".join(sorted(by_name.keys()))
        console.print(f"Available: {available}")
        raise typer.Exit(1)

    task = by_name[name]
    console.print(f"Running [cyan]{task.name}[/cyan] against {workspace}...")

    result = run_task(task, workspace, pass_env=pass_env or ())

    # Display result
    if result.success:
        console.print(f"\n[green]PASS[/green] {result.passed}/{result.total_tests} tests passed")
    else:
        console.print(
            f"\n[red]FAIL[/red] {result.passed}/{result.total_tests} passed, {result.failed} failed"
        )
        for err in result.errors:
            console.print(f"  [red]x[/red] {err}")
        raise typer.Exit(1)


def run_tasks_cmd(
    workspace: Path = typer.Option(
        ...,
        "--workspace",
        "-w",
        help="Workspace directory with agent output",
    ),
    tasks_dir: Path = typer.Option(
        None,
        "--dir",
        "-d",
        help="Tasks directory (default: ./tasks)",
    ),
    skill: str | None = typer.Option(
        None,
        "--skill",
        "-s",
        help="Only run tasks requiring this skill",
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to the verifier (repeatable).",
    ),
) -> None:
    """Run all task evaluations against a workspace."""
    from evolution.eval.runner import run_task

    tasks_path = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    tasks = discover_tasks(tasks_path)

    if skill:
        tasks = [t for t in tasks if skill in t.skills_required]

    if not tasks:
        console.print("No matching tasks found.")
        return

    console.print(f"Running {len(tasks)} task(s) against {workspace}...\n")

    results = []
    for task in tasks:
        result = run_task(task, workspace, pass_env=pass_env or ())
        results.append(result)

        status = "[green]PASS[/green]" if result.success else "[red]FAIL[/red]"
        console.print(f"  {status} {task.name}: {result.passed}/{result.total_tests}")

    # Summary
    total_pass = sum(1 for r in results if r.success)
    console.print(f"\n{total_pass}/{len(results)} tasks passed")

    if total_pass < len(results):
        raise typer.Exit(1)
