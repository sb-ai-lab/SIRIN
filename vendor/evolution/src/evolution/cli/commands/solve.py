"""Single-task solve command.

The callback is registered once as ``evo run solve`` by :mod:`evolution.cli.main`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from evolution.cli.app import (
    _get_store,
    console,
)
from evolution.cli.json_contract import emit_json, fail_json
from evolution.config import llm_max_tokens
from evolution.eval.paths import resolve_tasks_root
from evolution.splits import SplitManifest
from evolution.workflow import resolve_task_bindings


def solve_cmd(
    task_name: str = typer.Argument(help="Task name"),
    model: str = typer.Option(
        ...,
        "--model",
        "-m",
        help="Model name (e.g. openai/llama3, claude, gpt-4o)",
    ),
    skill_name: str | None = typer.Option(
        None,
        "--skill",
        "-s",
        help="Skill to inject (default: auto from task requirements)",
    ),
    workspace: Path | None = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace directory (default: a fresh temporary directory)",
    ),
    api_base: str | None = typer.Option(
        None,
        "--api-base",
        help="API base URL (e.g. http://localhost:8000/v1 for vLLM)",
    ),
    max_tokens: int | None = typer.Option(
        None,
        "--max-tokens",
        help="Max tokens for LLM response (default: EVO_LLM_MAX_TOKENS or 16384)",
    ),
    seed: int | None = typer.Option(
        None,
        "--seed",
        help="Deterministic model sampling seed (default: provider behavior)",
    ),
    timeout: float = typer.Option(
        300.0,
        "--timeout",
        help="Script execution timeout in seconds",
    ),
    no_skill: bool = typer.Option(
        False,
        "--no-skill",
        help="Run without skill (baseline)",
    ),
    snapshot: str | None = typer.Option(
        None,
        "--snapshot",
        help="Use skill versions from a container snapshot (e.g. s1)",
    ),
    tasks_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Tasks directory (default: ./tasks)",
    ),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help=(
            "Split manifest JSON. If set, `--manifest-scope` must also be "
            "given and the task must fall inside that scope."
        ),
    ),
    manifest_scope: str | None = typer.Option(
        None,
        "--manifest-scope",
        help=(
            "One of skill_evolution (train), dev (train+val), reporting "
            "(test), all. Required when --manifest is set."
        ),
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the solve result as JSON (human output goes to stderr)."
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to generated code and the verifier (repeatable).",
    ),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
) -> None:
    """Solve a task with an LLM and evaluate the result.

    Examples:

      # With a vLLM server:
      evo run solve xlsx-recover-data -m openai/llama3 --api-base http://localhost:8000/v1

      # With Claude:
      evo run solve xlsx-recover-data -m claude

      # Baseline (no skill):
      evo run solve xlsx-recover-data -m claude --no-skill

      # Use a specific container snapshot:
      evo run solve sb-de-duckdb-assembly -m claude --snapshot s1

      # Scope-aware reporting run (test only):
      evo run solve sb-de-duckdb-assembly -m claude \\
         --manifest /path/to/manifest.json \\
         --manifest-scope reporting
    """
    from evolution.eval.solver import solve_task
    from evolution.eval.task import discover_tasks
    from evolution.eval.workspace import setup_workspace
    from evolution.llm.backend import get_backend, model_seed_mode

    # In --json mode, human-readable progress goes to stderr so stdout stays parseable.
    out = Console(stderr=True) if json_output else console
    if seed is not None and seed < 0:
        message = "--seed must be non-negative."
        if json_output:
            fail_json("invalid_arguments", message, 2)
        out.print(f"[red]{message}[/red]")
        raise typer.Exit(2)
    if seed is not None and model_seed_mode(model) != "forwarded":
        message = f"Model {model!r} does not support seeded completions."
        if json_output:
            fail_json("invalid_arguments", message, 2)
        out.print(f"[red]{message}[/red]")
        raise typer.Exit(2)

    try:
        tasks_path = resolve_tasks_root(tasks_dir)
        tasks = discover_tasks(tasks_path)
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise
    by_name = {t.name: t for t in tasks}

    if task_name not in by_name:
        message = f"Task {task_name!r} not found."
        if json_output:
            fail_json("task_not_found", message)
        out.print(f"[red]{message}[/red]")
        raise typer.Exit(1)

    task = by_name[task_name]

    # Set up workspace
    try:
        ws = setup_workspace(task, workspace)
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    # Build backend
    backend_kwargs: dict[str, Any] = {}
    if api_base:
        backend_kwargs["api_base"] = api_base
    try:
        backend_kwargs["max_tokens"] = llm_max_tokens(max_tokens)
        backend_kwargs["agent_permission"] = permission
        backend = get_backend(model, **backend_kwargs)
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    # Resolve skill(s)
    bindings = []
    if not no_skill:
        try:
            store = _get_store()
            bindings = resolve_task_bindings(
                task,
                store=store,
                project_dir=Path.cwd(),
                skill_name=skill_name,
                snapshot=snapshot,
            )
        except Exception as exc:
            if json_output:
                fail_json("command_failed", str(exc))
            raise
        if bindings:
            selected = ", ".join(f"{item.name}@{item.version}" for item in bindings)
            out.print(f"Using skill(s): [green]{selected}[/green]")
    else:
        out.print("Running [yellow]without skill[/yellow] (baseline)")

    split_manifest = None
    if manifest is not None:
        if not manifest_scope:
            message = (
                "--manifest-scope is required when --manifest is set "
                "(one of skill_evolution, dev, reporting, all)."
            )
            if json_output:
                fail_json("invalid_arguments", message, 2)
            out.print(f"[red]{message}[/red]")
            raise typer.Exit(2)
        try:
            split_manifest = SplitManifest.load(manifest)
        except Exception as exc:
            if json_output:
                fail_json("invalid_arguments", str(exc), 2)
            raise
        out.print(
            f"Manifest: [cyan]{split_manifest.name}[/cyan] "
            f"({split_manifest.sha256[:12]}) scope={manifest_scope}"
        )

    out.print(f"Model: [cyan]{model}[/cyan]")
    out.print(f"Task: [cyan]{task.name}[/cyan]")
    out.print(f"Workspace: {ws}\n")

    # Solve
    try:
        result = solve_task(
            task,
            backend,
            ws,
            bindings=bindings,
            timeout=timeout,
            model_name=model,
            manifest=split_manifest,
            manifest_scope=manifest_scope,
            pass_env=pass_env or (),
            attempt_seed=seed,
        )
    except Exception as exc:
        if json_output:
            fail_json("command_failed", str(exc))
        raise

    json_data = None
    if json_output:
        json_data = {
            "task": task.name,
            "model": model,
            "success": result.success,
            "script_exit_code": result.script_exit_code,
            "exec_ms": result.exec_ms,
            "eval_ms": result.eval_ms,
            "completion_ms": result.completion_ms,
            "tokens_in": result.llm_response.tokens_in if result.llm_response else None,
            "tokens_out": result.llm_response.tokens_out if result.llm_response else None,
            "passed": result.eval_result.passed if result.eval_result else None,
            "total_tests": result.eval_result.total_tests if result.eval_result else None,
            "failed": result.eval_result.failed if result.eval_result else None,
            "errors": list(result.errors),
        }

    # Report
    if result.llm_response:
        resp = result.llm_response
        total = resp.tokens_in + resp.tokens_out
        out.print(f"LLM: {resp.tokens_in} prompt + {resp.tokens_out} gen = {total} tokens")
        out.print(
            f"Timing: llm {resp.time_ms}ms | exec {result.exec_ms}ms | "
            f"eval {result.eval_ms}ms | total {result.completion_ms}ms"
        )

    if result.script_exit_code == 0:
        out.print("[green]Script executed successfully[/green]")
    elif result.script_path:
        out.print(f"[red]Script failed (exit {result.script_exit_code})[/red]")
        if result.script_output:
            # Show last 10 lines of output
            lines = result.script_output.strip().split("\n")
            for line in lines[-10:]:
                out.print(f"  {line}")

    if result.eval_result:
        er = result.eval_result
        if er.success:
            out.print(f"\n[green]PASS[/green] {er.passed}/{er.total_tests} tests")
        else:
            out.print(f"\n[red]FAIL[/red] {er.passed}/{er.total_tests} passed, {er.failed} failed")
            for err in er.errors[:5]:
                out.print(f"  [red]x[/red] {err}")

    for err in result.errors:
        out.print(f"[red]Error:[/red] {err}")

    if not result.success:
        if json_output:
            message = "; ".join(result.errors) or f"Solve failed for task {task.name!r}."
            fail_json("solve_failed", message)
        raise typer.Exit(1)
    if json_output:
        emit_json(json_data)
