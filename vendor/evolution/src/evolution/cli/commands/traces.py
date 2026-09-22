"""Trace inspection commands.

Callbacks are registered once under ``evo trace`` by :mod:`evolution.cli.main`.
"""

from __future__ import annotations

import json

import typer
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from evolution.cli.app import (
    _get_store,
    console,
)
from evolution.cli.json_contract import emit_json, fail_json


def traces_cmd(
    name: str = typer.Argument(help="Skill name"),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Filter by skill version",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Filter by model name",
    ),
    task: str | None = typer.Option(
        None,
        "--task",
        "-t",
        help="Filter by task name",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of a table."),
) -> None:
    """List traces for a skill with optional filters.

    Examples:

      evo trace list docx
      evo trace list docx --version v3
      evo trace list docx --model claude-sonnet-4
      evo trace list docx --task offer-letter
    """
    from evolution.lineage.traces import TraceStore

    try:
        store = _get_store()
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
        ts = TraceStore(skill)
        traces = ts.list(skill_version=version, model=model, task=task)
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    if json_output:
        emit_json(traces)
        return

    if not traces:
        console.print("No traces found.")
        return

    table = Table(title=f"{name} -- traces ({len(traces)})")
    table.add_column("#", style="dim", justify="right")
    table.add_column("VERSION", style="cyan")
    table.add_column("MODEL")
    table.add_column("TASK")
    table.add_column("RESULT", justify="right")
    table.add_column("IN/OUT", justify="right")
    table.add_column("TIME", justify="right")

    for i, t in enumerate(traces, 1):
        passed = t.get("passed", 0)
        total = t.get("total", 0)
        success = t.get("success", False)
        result_str = f"{passed}/{total}"
        result_style = "green" if success else "red"
        tokens_in = t.get("tokens_in", 0)
        tokens_out = t.get("tokens_out", 0)
        time_ms = t.get("time_ms", 0)

        table.add_row(
            str(i),
            t.get("skill_version", ""),
            t.get("model", ""),
            t.get("task", ""),
            f"[{result_style}]{result_str}[/]",
            f"{tokens_in}+{tokens_out}",
            f"{time_ms}ms",
        )

    console.print(table)


def show_trace_cmd(
    name: str = typer.Argument(help="Skill name"),
    trace_id: str | None = typer.Argument(
        None,
        help="Trace ID, number (#1, #2, ...), or omit for --last",
    ),
    section: str | None = typer.Option(
        None,
        "--section",
        "-s",
        help="Show only one section: prompt, response, code, result",
    ),
    last: bool = typer.Option(
        False,
        "--last",
        "-l",
        help="Show the most recent trace",
    ),
) -> None:
    """Show the contents of a trace.

    Examples:

      evo trace show docx --last             # most recent trace
      evo trace show docx --last -s code     # just the code from latest
      evo trace show docx 1                  # first trace (by index)
      evo trace show docx -1                 # last trace (negative index)
      evo trace show docx <full_trace_id>    # by exact ID
    """
    from evolution.lineage.traces import TraceIndexError, TraceStore

    store = _get_store()
    try:
        skill = store.get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1)

    ts = TraceStore(skill)
    try:
        index = ts.list()
    except (TraceIndexError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None

    if not index:
        console.print("No traces found.")
        raise typer.Exit(1)

    # Resolve trace_id
    if last or trace_id is None:
        resolved_id = index[-1]["id"]
    elif trace_id.lstrip("-").isdigit():
        # Numeric index: 1-based positive, or negative from end
        idx = int(trace_id)
        if idx > 0:
            idx -= 1  # convert 1-based to 0-based
        try:
            resolved_id = index[idx]["id"]
        except IndexError:
            console.print(f"[red]Index {trace_id} out of range (1-{len(index)}).[/red]")
            raise typer.Exit(1)
    else:
        resolved_id = trace_id

    display_id = trace_id or "latest"
    try:
        trace_dir = ts.resolve_trace_dir(resolved_id)
        result_file = ts.resolve_trace_file(resolved_id, "result.json")
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None

    if not trace_dir.is_dir():
        console.print(f"[red]Trace {resolved_id!r} not found.[/red]")
        raise typer.Exit(1)

    if result_file.exists():
        result = json.loads(result_file.read_text())
    else:
        result = {}

    sections = {
        "prompt": ("prompt.md", "Prompt", "markdown"),
        "response": ("response.md", "LLM Response", "markdown"),
        "code": ("solve.py", "Extracted Code", "python"),
        "result": ("result.json", "Result", "json"),
    }

    if section:
        if section not in sections:
            console.print(
                f"[red]Unknown section: {section}. Use: prompt, response, code, result[/red]"
            )
            raise typer.Exit(1)
        to_show = {section: sections[section]}
    else:
        to_show = sections

    # Header
    success = result.get("success", False)
    passed = result.get("passed", 0)
    total = result.get("total", 0)
    status = (
        f"[green]PASS[/green] {passed}/{total}" if success else f"[red]FAIL[/red] {passed}/{total}"
    )

    console.print(
        Panel(
            f"Skill: [cyan]{name}[/cyan] {result.get('skill_version', '')}\n"
            f"Model: {result.get('model', '')}\n"
            f"Task:  {result.get('task', '')}\n"
            f"Result: {status}\n"
            f"Tokens: {result.get('tokens_in', 0)} in + {result.get('tokens_out', 0)} out\n"
            f"Time:  {result.get('time_ms', 0)}ms",
            title=f"Trace: {display_id}",
        )
    )

    try:
        section_paths = {
            key: ts.resolve_trace_file(resolved_id, filename)
            for key, (filename, _title, _lang) in to_show.items()
        }
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from None

    for key, (_filename, title, lang) in to_show.items():
        filepath = section_paths[key]
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")

        if key == "result":
            console.print(
                Panel(
                    Syntax(content, lang, theme="monokai"),
                    title=title,
                )
            )
        elif key == "code":
            console.print(
                Panel(
                    Syntax(content, lang, theme="monokai", line_numbers=True),
                    title=title,
                )
            )
        else:
            # For prompt and response, truncate if very long
            lines = content.split("\n")
            if len(lines) > 60 and section is None:
                preview = "\n".join(
                    lines[:30] + [f"\n... ({len(lines) - 60} lines omitted) ...\n"] + lines[-30:]
                )
                console.print(Panel(preview, title=f"{title} ({len(lines)} lines)"))
            else:
                console.print(Panel(content, title=title))


def repair_traces_cmd(name: str = typer.Argument(help="Skill name")) -> None:
    """Rebuild a corrupt trace index from valid on-disk trace packets."""
    from evolution.lineage.traces import TraceStore

    try:
        skill = _get_store().get(name)
    except KeyError:
        console.print(f"[red]Skill {name!r} not found.[/red]")
        raise typer.Exit(1) from None
    report = TraceStore(skill).repair_index()
    console.print(f"[green]Indexed {report.indexed} trace(s).[/green]")
    if report.skipped:
        console.print(f"[yellow]Skipped: {', '.join(report.skipped)}[/yellow]")
