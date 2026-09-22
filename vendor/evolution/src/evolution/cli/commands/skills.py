"""Skill lifecycle commands: create / list / show / validate / version / import + containers.

Callbacks are registered once under ``evo skill`` by :mod:`evolution.cli.main`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from evolution.cli.app import (
    _get_container_store,
    _get_store,
    _skill_cli_lock,
    console,
)
from evolution.cli.json_contract import emit_json, fail_json
from evolution.core._util import truncate_with_ellipsis
from evolution.core.store import SkillStore
from evolution.core.validator import validate_skill
from evolution.lineage.state_io import atomic_write_text


def init(
    path: Path = typer.Argument(Path("."), help="Project directory"),
) -> None:
    """Initialize evolution tracking for skills in this directory."""
    store = SkillStore(project_dir=path)
    entries = store.list()
    console.print(f"Discovered {len(entries)} skill(s) in {path.resolve()}")
    for entry in entries:
        evo_dir = entry.path / ".evolution"
        if not evo_dir.exists():
            console.print(f"  Initializing .evolution/ for {entry.name}...")
            evo_dir.mkdir(parents=True, exist_ok=True)
        else:
            console.print(f"  {entry.name}: already initialized")


def create(
    name: str = typer.Argument(help="Skill name (lowercase, hyphens ok)"),
    description: str = typer.Option(..., "--description", "-d", help="What the skill does"),
    license: str | None = typer.Option(None, "--license", "-l"),
    compatibility: str | None = typer.Option(None, "--compatibility"),
    scope: str = typer.Option("project", help="'project' or 'user'"),
    from_file: Path | None = typer.Option(
        None,
        "--from-file",
        "-f",
        help="Seed SKILL.md from this file instead of the blank scaffold.",
    ),
    replace: bool = typer.Option(
        False,
        "--replace",
        "--retire",
        help=(
            "If the skill already exists, rename it to "
            "<name>-deprecated-on-<YYYYMMDD-HHMM> and create a fresh one. "
            "Without this flag the command exits with an error when the skill exists."
        ),
    ),
) -> None:
    """Create a new skill scaffold.

    Examples:

      evo skill create api -d "REST API patterns"
      evo skill create api -d "REST API patterns" --from-file datasets/AFTER/skills/api/SKILL_HANDCRAFT.md
      evo skill create api -d "REST API patterns" --replace
      evo skill create api -d "REST API patterns" --from-file /path/to/SKILL.md --replace
    """
    store = _get_store()
    try:
        skill, deprecated = store.create(
            name=name,
            description=description,
            license=license,
            compatibility=compatibility,
            scope=scope,
            from_file=from_file,
            replace=replace,
        )
        if deprecated is not None:
            console.print(
                f"[yellow]Deprecated:[/yellow] previous {name!r} → "
                f"[dim]{deprecated.path.name}[/dim]"
            )
        console.print(f"[green]Created skill:[/green] {skill.name}")
        console.print(f"  Path: {skill.path}")
        console.print(f"  Edit: {skill.skill_md_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def list_skills(
    status: str | None = typer.Option(None, help="Filter: active, retired, archived"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """List all discovered skills."""
    try:
        store = _get_store()
        entries = store.list(status=status)
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    if json_output:
        emit_json(
            [
                {
                    "name": e.name,
                    "fitness": e.fitness,
                    "generation": e.generation,
                    "status": e.status,
                    "description": e.description,
                }
                for e in entries
            ]
        )
        return

    if not entries:
        console.print("No skills found.")
        return

    table = Table(title="Skills")
    table.add_column("NAME", style="cyan")
    table.add_column("FITNESS", justify="right")
    table.add_column("GEN", justify="right")
    table.add_column("STATUS")
    table.add_column("DESCRIPTION", max_width=50)

    for e in entries:
        fitness = f"{e.fitness:.2f}" if e.fitness is not None else "-"
        gen = str(e.generation) if e.generation is not None else "-"
        status_style = {
            "active": "green",
            "retired": "yellow",
            "archived": "dim",
            "candidate": "blue",
        }.get(e.status, "dim")
        desc = truncate_with_ellipsis(e.description, 50)
        table.add_row(e.name, fitness, gen, f"[{status_style}]{e.status}[/]", desc)

    console.print(table)


def show(
    name: str = typer.Argument(help="Skill name"),
    version: str | None = typer.Option(None, "--version", "-v", help="Specific version"),
    json_output: bool = typer.Option(
        False, "--json", help="Emit JSON instead of formatted output."
    ),
) -> None:
    """Show full skill content."""
    try:
        store = _get_store()
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    if version is not None:
        from evolution.lineage.version import VersionStore

        try:
            skill = store.get(name)
        except KeyError:
            message = f"Skill {name!r} not found."
            if json_output:
                fail_json("skill_not_found", message)
            console.print(f"[red]{message}[/red]")
            raise typer.Exit(1) from None
        except Exception as exc:
            if json_output:
                fail_json("command_failed", str(exc))
            raise

        try:
            saved = VersionStore(skill).load(version)
        except KeyError:
            message = f"Version {version!r} not found."
            if json_output:
                fail_json("version_not_found", message)
            console.print(f"[red]{message}[/red]")
            raise typer.Exit(1) from None
        except ValueError as exc:
            message = str(exc)
            if json_output:
                fail_json("invalid_arguments", message)
            console.print(f"[red]{message}[/red]")
            raise typer.Exit(1) from None
        except Exception as exc:
            if json_output:
                fail_json("command_failed", str(exc))
            raise

        content = saved.skill_md_path.read_text(encoding="utf-8")
        if json_output:
            emit_json({"name": name, "version": version, "content": content})
        else:
            console.print(Panel(Syntax(content, "markdown"), title=f"{name} ({version})"))
        return

    try:
        skill = store.get(name)
    except KeyError:
        message = f"Skill {name!r} not found."
        if json_output:
            fail_json("skill_not_found", message)
        console.print(f"[red]{message}[/red]")
        raise typer.Exit(1) from None
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    if json_output:
        emit_json(
            {
                "name": skill.name,
                "description": skill.description,
                "license": skill.frontmatter.license,
                "compatibility": skill.frontmatter.compatibility,
                "fitness": skill.fitness,
                "generation": skill.generation,
                "scripts": skill.scripts,
                "references": skill.references,
                "path": str(skill.path),
                "body": skill.body,
            }
        )
        return

    # Header
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Name", skill.name)
    table.add_row("Description", skill.description)
    if skill.frontmatter.license:
        table.add_row("License", skill.frontmatter.license)
    if skill.frontmatter.compatibility:
        table.add_row("Compatibility", skill.frontmatter.compatibility)
    if skill.fitness is not None:
        table.add_row("Fitness", f"{skill.fitness:.2f}")
    if skill.generation is not None:
        table.add_row("Generation", str(skill.generation))
    if skill.scripts:
        table.add_row("Scripts", ", ".join(skill.scripts))
    if skill.references:
        table.add_row("References", ", ".join(skill.references))
    table.add_row("Path", str(skill.path))
    console.print(table)
    console.print()

    # Body
    console.print(Syntax(skill.body, "markdown"))


def validate(
    name: str = typer.Argument(help="Skill name or path"),
) -> None:
    """Validate a skill against the Agent Skills specification."""
    store = _get_store()

    # Resolve to path
    if store.has(name):
        path = store._index[name].path
    else:
        path = Path(name)

    result = validate_skill(path)

    if result.errors:
        console.print("[red bold]ERRORS:[/red bold]")
        for err in result.errors:
            console.print(f"  [red]x[/red] {err}")

    if result.warnings:
        console.print("[yellow bold]WARNINGS:[/yellow bold]")
        for warn in result.warnings:
            console.print(f"  [yellow]![/yellow] {warn}")

    if result.valid:
        console.print(f"[green]v {name} is valid.[/green]")
    else:
        console.print(f"[red]x {name} has validation errors.[/red]")
        raise typer.Exit(1)


def search(
    query: str = typer.Argument(help="Search query"),
    limit: int = typer.Option(5, "--limit", "-n"),
) -> None:
    """Search skills by keyword."""
    store = _get_store()
    results = store.search(query, limit=limit)

    if not results:
        console.print("No matching skills found.")
        return

    table = Table(title=f"Search: {query!r}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("NAME", style="cyan")
    table.add_column("STATUS")
    table.add_column("DESCRIPTION", max_width=60)

    for i, entry in enumerate(results, 1):
        desc = truncate_with_ellipsis(entry.description, 60)
        table.add_row(str(i), entry.name, entry.status, desc)

    console.print(table)


def status() -> None:
    """Population overview."""
    store = _get_store()
    pop = store.population_status()

    if pop.total == 0:
        console.print("No skills found.")
        return

    table = Table(title="Population Status", show_header=False, box=None)
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Total skills", str(pop.total))
    table.add_row("Active", f"[green]{pop.active}[/green]")
    table.add_row("Retired", f"[yellow]{pop.retired}[/yellow]")
    table.add_row("Archived", f"[dim]{pop.archived}[/dim]")
    if pop.mean_fitness is not None:
        table.add_row("Mean fitness", f"{pop.mean_fitness:.2f}")
    if pop.best:
        table.add_row("Best", f"{pop.best[0]} ({pop.best[1]:.2f})")
    if pop.worst:
        table.add_row("Worst", f"{pop.worst[0]} ({pop.worst[1]:.2f})")
    table.add_row("Total generations", str(pop.total_generations))
    console.print(table)


def lineage(
    name: str = typer.Argument(help="Skill name"),
) -> None:
    """Show ancestry tree for a skill."""
    from evolution.lineage.tracker import LineageTracker

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    tracker = LineageTracker(skill)
    entries = tracker.lineage

    if not entries:
        console.print("No lineage recorded.")
        return

    tree = Tree(f"[bold]{name}[/bold] lineage")
    current_node = tree
    for entry in entries:
        status_style = {
            "active": "green",
            "retired": "yellow",
            "archived": "dim",
            "candidate": "blue",
        }.get(entry.status, "dim")

        fitness_str = f"fitness={entry.fitness:.2f}" if entry.fitness is not None else "fitness=-"
        marker = " << current" if entry.status == "active" else ""
        label = (
            f"[bold]{entry.version}[/bold] -- {entry.origin} -- "
            f"{fitness_str}  [{status_style}]{entry.status}[/]{marker}"
        )
        current_node = current_node.add(label)

    console.print(tree)


def diff_cmd(
    name: str = typer.Argument(help="Skill name"),
    v1: str | None = typer.Argument(
        None, help="First version (omit both to diff working copy vs active)"
    ),
    v2: str | None = typer.Argument(None, help="Second version"),
) -> None:
    """Diff two versions, or show uncommitted changes.

    Examples:

      evo skill diff docx            # working copy vs last committed version
      evo skill diff docx v1 v2      # compare two versions
    """
    from evolution.lineage.diff import skill_diff
    from evolution.lineage.tracker import LineageTracker
    from evolution.lineage.version import VersionStore

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    vs = VersionStore(skill)

    if v1 is None and v2 is None:
        # Diff working copy vs active version
        tracker = LineageTracker(skill)
        active_ver = tracker.current_version
        if not active_ver or not vs.exists(active_ver):
            console.print("[yellow]No committed version to compare against.[/yellow]")
            raise typer.Exit(1)
        old = vs.load(active_ver)
        new = skill  # working copy
        console.print(f"Comparing [cyan]{active_ver}[/cyan] (committed) vs working copy\n")
    elif v1 is not None and v2 is not None:
        try:
            old = vs.load(v1)
        except KeyError:
            console.print(f"[red]Version {v1!r} not found.[/red]")
            raise typer.Exit(1)
        try:
            new = vs.load(v2)
        except KeyError:
            console.print(f"[red]Version {v2!r} not found.[/red]")
            raise typer.Exit(1)
    else:
        console.print(
            "[red]Provide both versions (evo skill diff name v1 v2) or none (evo skill diff name).[/red]"
        )
        raise typer.Exit(1)

    d = skill_diff(old, new)

    if not d.text_diff and not d.frontmatter_changes:
        console.print("[dim]No changes.[/dim]")
        return

    console.print(f"[bold]Summary:[/bold] {d.summary}\n")

    if d.text_diff:
        console.print(Syntax(d.text_diff, "diff"))
    else:
        console.print("[dim]No text changes.[/dim]")


def history(
    name: str = typer.Argument(help="Skill name"),
) -> None:
    """Show fitness trajectory over versions."""
    from evolution.lineage.traces import TraceStore
    from evolution.lineage.tracker import LineageTracker

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    tracker = LineageTracker(skill)
    entries = tracker.lineage
    ts = TraceStore(skill)

    table = Table(title=f"{name} -- version history")
    table.add_column("VERSION", style="cyan")
    table.add_column("FITNESS", justify="right")
    table.add_column("DELTA", justify="right")
    table.add_column("TRACES", justify="right")
    table.add_column("ORIGIN")
    table.add_column("STATUS")
    table.add_column("DATE")

    prev_fitness: float | None = None
    for entry in entries:
        # Prefer real fitness from traces; fall back to lineage metadata
        trace_fitness = ts.fitness(entry.version)
        trace_count = ts.count(skill_version=entry.version)
        fitness = trace_fitness if trace_fitness is not None else entry.fitness

        fitness_str = f"{fitness:.1%}" if fitness is not None else "-"
        if fitness is not None and prev_fitness is not None:
            delta = fitness - prev_fitness
            delta_str = f"[green]+{delta:.1%}[/]" if delta > 0 else f"[red]{delta:.1%}[/]"
        else:
            delta_str = "-"

        status_style = {
            "active": "green",
            "retired": "yellow",
            "archived": "dim",
        }.get(entry.status, "dim")
        date_str = entry.timestamp.strftime("%Y-%m-%d") if entry.timestamp else "-"

        table.add_row(
            entry.version,
            fitness_str,
            delta_str,
            str(trace_count) if trace_count > 0 else "-",
            entry.origin,
            f"[{status_style}]{entry.status}[/]",
            date_str,
        )
        if fitness is not None:
            prev_fitness = fitness

    console.print(table)


def promote(
    name: str = typer.Argument(help="Skill name"),
    version: str = typer.Argument(help="Version to promote (e.g. v1, v2)"),
) -> None:
    """Switch a skill to a specific version."""
    from evolution.lineage.tracker import LineageTracker

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    tracker = LineageTracker(skill)

    try:
        tracker.promote(version)
    except KeyError:
        console.print(f"[red]Version {version!r} not found for {name}.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]{name}[/green] switched to [cyan]{version}[/cyan]")


def commit(
    name: str = typer.Argument(help="Skill name"),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help="Description of changes",
    ),
    no_promote: bool = typer.Option(
        False,
        "--no-promote",
        help="Save version but don't make it active",
    ),
) -> None:
    """Snapshot the current skill state as a new version.

    Examples:

      evo skill commit docx -m "fixed conditional handling"
      evo skill commit docx --no-promote
    """

    from evolution.core.models import LineageEntry
    from evolution.core.validator import validate_skill
    from evolution.lineage.diff import skill_diff
    from evolution.lineage.tracker import LineageTracker
    from evolution.lineage.version import VersionStore

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    with _skill_cli_lock(skill.path):
        # Validate first
        vr = validate_skill(skill.path)
        if not vr.valid:
            for err in vr.errors:
                console.print(f"  [red]x[/red] {err}")
            console.print("[red]Fix validation errors before committing.[/red]")
            raise typer.Exit(1)

        vs = VersionStore(skill)
        tracker = LineageTracker(skill)

        # Check for changes vs active version
        active_ver = tracker.current_version
        if active_ver and vs.exists(active_ver):
            old = vs.load(active_ver)
            d = skill_diff(old, skill)
            if not d.text_diff and not d.frontmatter_changes:
                console.print("[yellow]No changes to commit.[/yellow]")
                raise typer.Exit(0)

        # Auto-increment version
        new_ver = tracker.next_version_label()

        # Snapshot
        vs.save(new_ver)

        # Record lineage
        entry = LineageEntry(
            version=new_ver,
            parent=active_ver or None,
            timestamp=datetime.now(),
            origin="manual",
            mutation_type="manual-edit",
            status="candidate",
        )
        tracker.record(entry)

        if not no_promote:
            tracker.promote(new_ver)
            console.print(f"[green]{name}[/green] committed as [cyan]{new_ver}[/cyan] (active)")
        else:
            console.print(f"[green]{name}[/green] committed as [cyan]{new_ver}[/cyan] (candidate)")

        if message:
            console.print(f"  {message}")


def discard(
    name: str = typer.Argument(help="Skill name"),
) -> None:
    """Discard uncommitted changes, restoring the last committed version.

    Examples:

      evo skill discard docx
    """
    from evolution.lineage.diff import skill_diff
    from evolution.lineage.tracker import LineageTracker
    from evolution.lineage.version import VersionStore

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    with _skill_cli_lock(skill.path):
        vs = VersionStore(skill)
        tracker = LineageTracker(skill)
        active_ver = tracker.current_version

        if not active_ver or not vs.exists(active_ver):
            console.print("[yellow]No committed version to restore.[/yellow]")
            raise typer.Exit(1)

        old = vs.load(active_ver)
        d = skill_diff(old, skill)
        if not d.text_diff and not d.frontmatter_changes:
            console.print("[dim]No uncommitted changes.[/dim]")
            return

        tracker.promote(active_ver)
        console.print(f"[green]{name}[/green] restored to [cyan]{active_ver}[/cyan]")


def repair_cmd(
    name: str = typer.Argument(help="Skill name"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the rebuilt lineage.json without writing it",
    ),
) -> None:
    """Rebuild a skill's .evolution/lineage.json from on-disk version snapshots.

    Use when `evo skill lineage|history|commit|promote` fails because lineage.json is
    malformed. Recovery is provenance-light: entries are marked
    origin=import / mutation_type=recovered-from-disk.

    Examples:

      evo skill repair docx
      evo skill repair docx --dry-run
    """
    from evolution.lineage.tracker import rebuild_lineage

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    lineage, notes = rebuild_lineage(skill)
    for note in notes:
        console.print(f"[yellow]note:[/yellow] {note}")

    payload = json.dumps(lineage.model_dump(mode="json"), indent=2, default=str)

    if dry_run:
        console.print(payload)
        console.print("[dim](dry run — lineage.json not written)[/dim]")
        return

    with _skill_cli_lock(skill.path):
        lineage, _ = rebuild_lineage(skill)
        payload = json.dumps(lineage.model_dump(mode="json"), indent=2, default=str)
        path = skill.path / ".evolution" / "lineage.json"
        atomic_write_text(path, payload + "\n")
    console.print(
        f"[green]{name}[/green] lineage repaired: {len(lineage.lineage)} version(s), "
        f"active [cyan]{lineage.current_version}[/cyan]."
    )


def delete_version_cmd(
    name: str = typer.Argument(help="Skill name"),
    version: str = typer.Argument(help="Version to delete (e.g. v4)"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Delete even if version has children (reparents them)",
    ),
) -> None:
    """Delete a skill version from lineage and disk.

    Cannot delete the active version — promote another first.
    Cannot delete versions with children unless --force is used.

    Examples:

      evo skill delete-version docx v4
      evo skill delete-version docx v2 --force
    """
    from evolution.lineage.tracker import LineageTracker

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    tracker = LineageTracker(skill)

    try:
        tracker.delete_version(version, force=force)
    except KeyError:
        console.print(f"[red]Version {version!r} not found for {name}.[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]{name}[/green] version [cyan]{version}[/cyan] deleted")


def import_cmd(
    source: Path = typer.Argument(help="Path to skill directory or SKILL.md"),
    name: str | None = typer.Option(None, "--name", "-n", help="Override skill name"),
) -> None:
    """Import an existing skill into the store."""
    store = _get_store()
    try:
        skill = store.import_skill(source, name=name)
        console.print(f"[green]Imported:[/green] {skill.name}")
        console.print(f"  Path: {skill.path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def import_skillsbench(
    repo: Path = typer.Argument(help="Path to SkillsBench repository"),
    skills: str | None = typer.Option(
        None,
        "--skills",
        "-s",
        help="Comma-separated skill names to import (default: all)",
    ),
    theme: str = typer.Option("", "--theme", "-t", help="Theme prefix for metadata"),
) -> None:
    """Bulk import skills from a SkillsBench repository."""
    from evolution.importers.skillsbench import discover_skills, import_skills

    store = _get_store()

    names = [n.strip() for n in skills.split(",")] if skills else None

    # Show what we'll import
    entries = discover_skills(repo)
    if names:
        entries = [e for e in entries if e.name in set(names)]

    console.print(f"Found {len(entries)} skill(s) to import from {repo}")

    imported = import_skills(store, repo, names=names, theme_prefix=theme)

    if imported:
        table = Table(title=f"Imported {len(imported)} skill(s)")
        table.add_column("NAME", style="cyan")
        table.add_column("STATUS", style="green")
        for n in imported:
            table.add_row(n, "imported")
        console.print(table)
    else:
        console.print("[yellow]No new skills imported.[/yellow]")


def list_containers() -> None:
    """List all skill containers."""
    cstore = _get_container_store()
    containers = cstore.list()

    if not containers:
        console.print("[yellow]No containers found.[/yellow]")
        return

    table = Table(title=f"Skill Containers ({len(containers)})")
    table.add_column("NAME", style="cyan")
    table.add_column("SKILLS", style="green")
    table.add_column("DESCRIPTION")

    for c in containers:
        table.add_row(c.name, ", ".join(c.skills), c.description[:60])
    console.print(table)


def show_container(
    name: str = typer.Argument(help="Container name"),
) -> None:
    """Show details of a skill container."""
    cstore = _get_container_store()
    try:
        c = cstore.get(name)
    except (KeyError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    console.print(Panel(f"[bold]{c.name}[/bold]\n{c.description}", title="Container"))
    console.print(f"\n[bold]Skills ({len(c.skills)}):[/bold]")

    store = _get_store()
    for i, sname in enumerate(c.skills, 1):
        marker = "[bold green]primary[/bold green]" if i == 1 else ""
        found = "[green]✓[/green]" if store.has(sname) else "[red]✗[/red]"
        console.print(f"  {i}. {found} {sname} {marker}")

    if c.metadata:
        console.print("\n[bold]Metadata:[/bold]")
        for k, v in c.metadata.items():
            console.print(f"  {k}: {v}")


def create_container(
    name: str = typer.Argument(help="Container name"),
    description: str = typer.Option(
        ...,
        "--description",
        "-d",
        help="Description of the container",
    ),
    skills: str = typer.Option(
        ...,
        "--skills",
        help="Comma-separated skill names",
    ),
) -> None:
    """Create a new skill container."""
    cstore = _get_container_store()
    skill_list = [s.strip() for s in skills.split(",")]

    try:
        c = cstore.create(name=name, description=description, skills=skill_list)
        console.print(f"[green]Created container:[/green] {c.name}")
        console.print(f"  Skills: {', '.join(c.skills)}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def delete_container(
    name: str = typer.Argument(help="Container name"),
) -> None:
    """Delete a skill container."""
    cstore = _get_container_store()
    try:
        cstore.delete(name)
        console.print(f"[green]Deleted container:[/green] {name}")
    except KeyError:
        console.print(f"[red]Container {name!r} not found.[/red]")
        raise typer.Exit(1)


def snapshot_container_cmd(
    name: str = typer.Argument(help="Container name"),
    message: str = typer.Option(
        ...,
        "--message",
        "-m",
        help="Snapshot message",
    ),
) -> None:
    """Record which skill versions this container currently uses."""
    cstore = _get_container_store()
    store = _get_store()
    try:
        label = cstore.snapshot(name, message, skill_store=store)
        entries = cstore.snapshots(name)
        last = entries[-1]
        console.print(f"[green]Snapshot {label}:[/green] {name}")
        for ref in last["skill_refs"]:
            console.print(f"  {ref['name']} @ {ref['version']}")
    except KeyError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)


def container_snapshots_cmd(
    name: str = typer.Argument(help="Container name"),
) -> None:
    """Show snapshot history for a container."""
    cstore = _get_container_store()
    try:
        entries = cstore.snapshots(name)
    except KeyError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if not entries:
        console.print(f"[yellow]No snapshots for {name!r}.[/yellow]")
        return

    table = Table(title=f"Container Snapshots: {name}")
    table.add_column("LABEL", style="cyan")
    table.add_column("SKILLS")
    table.add_column("MESSAGE")
    table.add_column("TIMESTAMP")

    for snapshot_entry in entries:
        refs = snapshot_entry.get("skill_refs")
        skills_str = (
            ", ".join(f"{ref['name']}@{ref['version']}" for ref in refs)
            if isinstance(refs, list)
            else ", ".join(
                f"{name}@{version}" for name, version in snapshot_entry.get("skills", {}).items()
            )
        )
        table.add_row(
            snapshot_entry["label"],
            skills_str,
            snapshot_entry.get("message", ""),
            snapshot_entry.get("timestamp", "")[:19],
        )
    console.print(table)
