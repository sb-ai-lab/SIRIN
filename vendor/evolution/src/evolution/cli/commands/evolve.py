"""Reflect + rewrite commands (the evolve loop).

Callbacks are registered once under ``evo evolve`` by :mod:`evolution.cli.main`.
"""

from __future__ import annotations

import asyncio
import contextlib
import difflib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NoReturn

import typer

from evolution.cli.app import (
    _get_store,
    _skill_cli_lock,
    _task_instruction_for_cli_task,
    _task_obj_for_cli_task,
    console,
)
from evolution.cli.json_contract import emit_json, fail_json
from evolution.config import llm_max_tokens
from evolution.core.models import SkillFrontmatter
from evolution.core.parser import parse_skill_md, write_skill_md
from evolution.evolve.edit_brake import resolve_base_budget
from evolution.evolve.optimizer import (
    OptimizationRunError,
    load_optimization_status,
    optimize_skill,
)
from evolution.evolve.reflect import (
    REWRITE_MODE_NAMES,
    collect_reflections,
    normalize_rewrite_mode,
    reflect_failing_traces,
    rewrite_skill_with_audit,
)
from evolution.evolve.rewrite_outcome import (
    CONTROLLED_STATUSES,
    PROMOTED_ELIGIBLE,
    REWRITE_ERROR_INTERNAL,
)
from evolution.lineage.version import hash_managed_tree
from evolution.llm.backend import get_backend
from evolution.splits import SplitManifest

_REWRITE_MODES = REWRITE_MODE_NAMES


def _exit_optimizer_error(exc: Exception, json_output: bool) -> NoReturn:
    message = str(exc.args[0]) if isinstance(exc, KeyError) and exc.args else str(exc)
    if isinstance(exc, OptimizationRunError):
        kind, code = "command_failed", 2
    elif isinstance(exc, KeyError):
        kind = "skill_not_found" if message.startswith("Skill ") else "task_not_found"
        code = 1
    elif isinstance(exc, ValueError):
        state_error = any(
            marker in message.lower()
            for marker in (
                "optimizer state",
                "optimizer run state",
                "resume identity",
                "has no snapshot",
            )
        )
        kind = "command_failed" if state_error else "invalid_arguments"
        code = 2 if state_error else 1
    elif isinstance(exc, FileNotFoundError):
        kind, code = "command_failed", 1
    else:
        kind, code = "command_failed", 2
        message = "Optimizer command failed."
    if json_output:
        fail_json(kind, message, code)
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code)


def _resolve_cli_rewrite_mode(option: str | None) -> tuple[str, str]:
    source = (
        "option"
        if option is not None
        else "environment"
        if os.environ.get("EVO_REWRITE_MODE")
        else "default"
    )
    raw = option if option is not None else os.environ.get("EVO_REWRITE_MODE", "text-return")
    return normalize_rewrite_mode(raw or "text-return"), source


def _rewrite_error_fields(reason: str) -> dict[str, Any]:
    return {
        "candidate_status": REWRITE_ERROR_INTERNAL,
        "gate_reason": REWRITE_ERROR_INTERNAL,
        "reason": reason,
        "parent_preservation": None,
        "codex_usage": None,
        "codex_diagnostics": None,
        "tokens_used": None,
        "candidate_debug_dir": None,
        "parent_skill_path": None,
        "parent_body_sha256": None,
        "candidate_body_sha256": None,
        "computed_churn": None,
        "new_headings": None,
        "edit_budget_frac": None,
        "edit_brake": None,
        "rewrite_attempts": [],
    }


def reflect_cmd(
    skill_name: str = typer.Argument(help="Skill name"),
    model: str = typer.Option(
        "openrouter/anthropic/claude-sonnet-4",
        "--model",
        "-m",
        help="Model for analysis",
    ),
    task: str | None = typer.Option(
        None,
        "--task",
        "-t",
        help="Filter traces by task name",
    ),
    limit: int | None = typer.Option(
        None,
        "--limit",
        help="Max traces to analyze (default: no cap — reflect ALL eligible failing traces)",
    ),
    trace_model: str | None = typer.Option(
        None,
        "--trace-model",
        help="Filter traces by model (substring match, e.g. 'sonnet', 'llama')",
    ),
    api_base: str | None = typer.Option(
        None,
        "--api-base",
        help="API base URL",
    ),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help=(
            "Split manifest JSON. When set, only traces from the skill-"
            "evolution scope (train) are analyzed."
        ),
    ),
    tasks_dir: Path | None = typer.Option(
        None,
        "--tasks-dir",
        "--dir",
        help=(
            "Tasks directory for task-instruction lookup (default: $EVO_TASKS_ROOT or <repo>/tasks)."
        ),
    ),
) -> None:
    """Analyze failing traces with an LLM and save reflections.

    When `--manifest` is set, reflections are restricted to train-scope
    traces; a `LeakageError` fails the run if a val/test trace is about to
    influence skill content.
    """
    store = _get_store()
    if not store.has(skill_name):
        console.print(f"[red]Skill {skill_name!r} not found.[/red]")
        raise typer.Exit(1)
    skill = store.get(skill_name)

    split_manifest = None
    if manifest is not None:
        split_manifest = SplitManifest.load(manifest)
        console.print(
            f"  manifest: {split_manifest.name} ({split_manifest.sha256[:12]}) "
            "scope=skill_evolution (train-only)"
        )

    # Get task instruction if task filter is set
    task_instruction = ""
    if task:
        task_instruction = _task_instruction_for_cli_task(task, tasks_dir)

    backend_kwargs: dict[str, Any] = {"max_tokens": llm_max_tokens(max_tokens)}
    if api_base:
        backend_kwargs["api_base"] = api_base
    backend = get_backend(model, agent_permission=permission, **backend_kwargs)

    console.print(f"Analyzing failing traces for [cyan]{skill_name}[/cyan]...")
    if task:
        console.print(f"  Task filter: {task}")
    if trace_model:
        console.print(f"  Trace model: {trace_model}")
    _require_v3 = bool(split_manifest is not None or os.environ.get("EVO_REQUIRE_V3_EVIDENCE"))
    try:
        reflections = reflect_failing_traces(
            backend,
            skill,
            task_instruction,
            task_filter=task,
            trace_model=trace_model,
            limit=limit,
            manifest=split_manifest,
            scope="skill_evolution",
            strict=True,
            require_v3_evidence=_require_v3,
        )
    except Exception as exc:
        console.print(f"[red]Reflect failed:[/red] {exc}")
        raise typer.Exit(1)

    if not reflections:
        console.print("[yellow]No failing traces without reflections found.[/yellow]")
        return

    for r in reflections:
        if "error" in r:
            console.print(f"  [red]✗[/red] {r['trace_id']}: {r['error']}")
        else:
            severity = r.get("severity", "?")
            pattern = r.get("pattern", "?")
            colors = {"critical": "red", "major": "yellow", "minor": "dim"}
            color = colors.get(severity, "white")
            console.print(
                f"  [{color}]●[/{color}] {r.get('model', '?')} — "
                f"{severity}/{pattern}: {r.get('root_cause', '?')[:80]}"
            )

    console.print(f"\n[green]{len(reflections)} reflections saved.[/green]")


def rewrite_cmd(
    skill_name: str = typer.Argument(help="Skill name"),
    model: str = typer.Option(
        "openrouter/anthropic/claude-sonnet-4",
        "--model",
        "-m",
        help="Model for rewriting",
    ),
    task: str | None = typer.Option(
        None,
        "--task",
        "-t",
        help="Filter reflections by task",
    ),
    trace_model: str | None = typer.Option(
        None,
        "--trace-model",
        help="Filter reflections by model (substring match)",
    ),
    skill_version: str | None = typer.Option(
        None,
        "--skill-version",
        help="Filter reflections by skill version (e.g. v4)",
    ),
    api_base: str | None = typer.Option(
        None,
        "--api-base",
        help="API base URL",
    ),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print rewritten skill without saving",
    ),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        help=(
            "Split manifest JSON. When set, only reflections from train-"
            "scope tasks are used; passing a val/test task via --task fails."
        ),
    ),
    tasks_dir: Path | None = typer.Option(
        None,
        "--tasks-dir",
        "--dir",
        help=(
            "Tasks directory for task-instruction lookup (default: $EVO_TASKS_ROOT or <repo>/tasks)."
        ),
    ),
    include_best_trace_code: bool = typer.Option(
        False,
        "--include-best-trace-code",
        help="Force raw best trace code into the rewrite prompt.",
    ),
    no_best_trace_code: bool = typer.Option(
        False,
        "--no-best-trace-code",
        help=(
            "Force raw best trace code out of the rewrite prompt. Default: yes "
            "without --manifest, no with --manifest."
        ),
    ),
    rewrite_audit_out: Path | None = typer.Option(
        None,
        "--rewrite-audit-out",
        help=(
            "Write structured rewrite audit JSON to this path. Default: "
            "<skill_dir>/.evolution/last_rewrite_audit.json."
        ),
    ),
    rewrite_mode: str | None = typer.Option(
        None,
        "--rewrite-mode",
        help="text-return (default) | file-edit | agentic-session (needs --task) | edit-ops.",
    ),
    rewrite_row_id: str = typer.Option(
        "",
        "--rewrite-row-id",
        help=(
            "Row identifier used for the candidate-debug archive path when "
            "EVO_DEBUG_C1=1. Adapter sets this from the row it is producing."
        ),
    ),
    version_decay: bool = typer.Option(
        True,
        "--version-decay/--no-version-decay",
        help="Decay the edit budget after retained promotions.",
    ),
    max_rewrite_attempts: int = typer.Option(
        1,
        "--max-rewrite-attempts",
        min=1,
        help="Total editor calls; retry only after an edit-brake rejection.",
    ),
) -> None:
    """Rewrite a skill based on collected reflections.

    When `--manifest` is provided, only reflections from train-scope tasks
    are fed into the rewrite prompt. Passing a val/test task via `--task`
    fails with `LeakageError`.

    Always writes a ``rewrite-audit-v1`` JSON sidecar to
    ``--rewrite-audit-out`` (or the default path) so the adapter can read
    the structured candidate status without parsing stdout.
    """
    store = _get_store()
    if not store.has(skill_name):
        console.print(f"[red]Skill {skill_name!r} not found.[/red]")
        raise typer.Exit(1)
    skill = store.get(skill_name)
    parent_sha256 = hash_managed_tree(skill.path)
    try:
        base_budget = resolve_base_budget()
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc

    audit_path = rewrite_audit_out or (
        skill.skill_md_path.parent / ".evolution" / "last_rewrite_audit.json"
    )

    try:
        rewrite_mode, rewrite_mode_source = _resolve_cli_rewrite_mode(rewrite_mode)
    except ValueError as exc:
        raw_mode = rewrite_mode if rewrite_mode is not None else os.environ.get("EVO_REWRITE_MODE")
        rewrite_mode_source = (
            "option" if rewrite_mode is not None else "environment" if raw_mode else "default"
        )
        error_audit = {
            "schema": "rewrite-audit-v1",
            "rewrite_mode": raw_mode or "text-return",
            "rewrite_mode_source": rewrite_mode_source,
            "model_id": model,
            "timestamp": datetime.now(UTC).isoformat(),
            **_rewrite_error_fields(f"invalid --rewrite-mode: {raw_mode!r}"),
        }
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.write_text(json.dumps(error_audit, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    split_manifest = None
    if manifest is not None:
        split_manifest = SplitManifest.load(manifest)
        console.print(
            f"  manifest: {split_manifest.name} ({split_manifest.sha256[:12]}) "
            "scope=skill_evolution (train-only)"
        )
        if task:
            split_manifest.assert_no_leakage(
                [task],
                scope="skill_evolution",
                context="rewrite --task",
            )

    reflections = collect_reflections(
        skill,
        task_filter=task,
        trace_model=trace_model,
        skill_version=skill_version,
        manifest=split_manifest,
        scope="skill_evolution",
    )
    if not reflections and rewrite_mode != "agentic-session":
        console.print("[yellow]No reflections found. Run 'evo evolve reflect' first.[/yellow]")
        raise typer.Exit(1)

    # Get task instruction
    task_instruction = ""
    if task:
        task_instruction = _task_instruction_for_cli_task(task, tasks_dir)

    console.print(
        f"Rewriting [cyan]{skill_name}[/cyan] based on "
        f"[green]{len(reflections)}[/green] reflections (mode={rewrite_mode})..."
    )
    if task:
        console.print(f"  Task: {task}")
    backend_kwargs: dict[str, Any] = {"max_tokens": llm_max_tokens(max_tokens)}
    if api_base:
        backend_kwargs["api_base"] = api_base
    backend = get_backend(model, agent_permission=permission, **backend_kwargs)
    if include_best_trace_code and no_best_trace_code:
        console.print(
            "[red]Use only one of --include-best-trace-code or --no-best-trace-code.[/red]"
        )
        raise typer.Exit(1)
    best_trace_enabled = (
        True if include_best_trace_code else False if no_best_trace_code else split_manifest is None
    )

    audit: dict = {
        "schema": "rewrite-audit-v1",
        "rewrite_mode": rewrite_mode,
        "rewrite_mode_source": rewrite_mode_source,
        "model_id": model,
        "timestamp": datetime.now(UTC).isoformat(),
        "edit_brake_policy": {
            "base_budget_frac": base_budget,
            "version_decay_enabled": version_decay,
            "max_rewrite_attempts": max_rewrite_attempts,
        },
    }
    exit_nonzero = False
    new_body = skill.body  # falls back to parent on rejection or error

    session_mode = rewrite_mode == "agentic-session"
    invalid_reason: str | None = None
    if rewrite_mode not in _REWRITE_MODES:
        invalid_reason = f"invalid --rewrite-mode: {rewrite_mode!r}"
    elif session_mode and not task:
        invalid_reason = "agentic-session requires --task to build the session workspace"

    try:
        if invalid_reason is not None:
            audit.update(_rewrite_error_fields(invalid_reason))
            exit_nonzero = True
        else:
            if session_mode:
                assert task is not None
                session_task = _task_obj_for_cli_task(task, tasks_dir)
            else:
                session_task = None
            outcome = asyncio.run(
                rewrite_skill_with_audit(
                    backend,
                    skill,
                    reflections,
                    task_instruction=task_instruction,
                    task_filter=task,
                    manifest=split_manifest,
                    include_best_trace_code=best_trace_enabled,
                    rewrite_mode=rewrite_mode,
                    task=session_task,
                    audit_root=audit_path.parent,
                    row_id=rewrite_row_id,
                    debug_archive=os.environ.get("EVO_DEBUG_C1") == "1",
                    version_decay=version_decay,
                    max_rewrite_attempts=max_rewrite_attempts,
                    base_budget=base_budget,
                )
            )
            new_body = outcome.body
            audit.update(
                {
                    "candidate_status": outcome.candidate_status,
                    "gate_reason": outcome.candidate_status,
                    "reason": outcome.reason,
                    "parent_preservation": outcome.preservation,
                    "codex_usage": outcome.codex_usage,
                    "codex_diagnostics": outcome.codex_diagnostics,
                    "tokens_used": outcome.tokens_used,
                    "candidate_debug_dir": outcome.candidate_debug_dir,
                    "parent_skill_path": outcome.parent_skill_path,
                    "parent_body_sha256": outcome.parent_body_sha256,
                    "candidate_body_sha256": outcome.candidate_body_sha256,
                    "computed_churn": outcome.computed_churn,
                    "new_headings": outcome.new_headings,
                    "edit_budget_frac": outcome.edit_budget_frac,
                    "edit_brake": outcome.edit_brake,
                    "rewrite_attempts": outcome.rewrite_attempts,
                }
            )
            if outcome.candidate_status not in CONTROLLED_STATUSES:
                # Contract violation: callee returned an unknown status.
                audit["candidate_status"] = REWRITE_ERROR_INTERNAL
                audit["gate_reason"] = REWRITE_ERROR_INTERNAL
                exit_nonzero = True
    except Exception as exc:
        audit.update(_rewrite_error_fields(f"{type(exc).__name__}: {exc!s}"[:500]))
        exit_nonzero = True
    finally:
        try:
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
        except Exception:
            # If the audit JSON cannot be written, that IS the contract failure.
            exit_nonzero = True
        # Reviewer-facing sidecars next to the audit JSON (see docs/codex_usage.md,
        # docs/codex_usage.md). Best-effort: a sidecar write failure must not
        # promote-or-fail the rewrite outcome itself.
        sidecar_stem = audit_path.parent / audit_path.stem
        last_message_text = (audit.get("codex_diagnostics") or {}).get("last_message") or ""
        if last_message_text:
            with contextlib.suppress(OSError):
                sidecar_stem.with_name(sidecar_stem.name + ".last_message.txt").write_text(
                    last_message_text, encoding="utf-8"
                )
        diff_text = "".join(
            difflib.unified_diff(
                skill.body.splitlines(keepends=True),
                new_body.splitlines(keepends=True),
                fromfile="parent/SKILL.md",
                tofile="candidate/SKILL.md",
            )
        )
        if diff_text:
            with contextlib.suppress(OSError):
                sidecar_stem.with_name(sidecar_stem.name + ".diff.patch").write_text(
                    diff_text, encoding="utf-8"
                )

    if dry_run:
        console.print("\n[bold]Rewritten skill body:[/bold]\n")
        console.print(new_body)
        if exit_nonzero:
            raise typer.Exit(1)
        return

    if audit.get("candidate_status") == PROMOTED_ELIGIBLE:
        with _skill_cli_lock(skill.path):
            if hash_managed_tree(skill.path) != parent_sha256:
                console.print("[red]Skill changed while rewrite was running.[/red]")
                raise typer.Exit(2)
            raw_fm, _ = parse_skill_md(skill.skill_md_path)
            fm = SkillFrontmatter.model_validate(raw_fm)
            write_skill_md(skill.skill_md_path, fm, new_body)
        console.print(f"\n[green]Skill {skill_name!r} rewritten.[/green]")
        console.print(f"Review with: [cyan]evo skill diff {skill_name}[/cyan]")
    else:
        console.print(
            f"\n[yellow]No new candidate committed "
            f"(status={audit.get('candidate_status')}): {audit.get('reason')}[/yellow]"
        )
    console.print(f"  audit: {audit_path}")
    if exit_nonzero:
        raise typer.Exit(1)


def optimize_cmd(
    skill_name: str = typer.Argument(help="Skill folder ID"),
    train: list[str] | None = typer.Option(
        None, "--train", help="Required training task ID; repeatable."
    ),
    validate: list[str] | None = typer.Option(
        None, "--validate", help="Required validation task ID; repeatable."
    ),
    solver_model: str | None = typer.Option(
        None, "--solver-model", help="Required model used for task attempts."
    ),
    editor_model: str | None = typer.Option(
        None, "--editor-model", help="Model used for reflection and rewriting."
    ),
    rounds: int = typer.Option(1, "--rounds"),
    trials: int = typer.Option(4, "--trials"),
    seed: int = typer.Option(0, "--seed"),
    rewrite_mode: str = typer.Option("edit-ops", "--rewrite-mode"),
    version_decay: bool = typer.Option(True, "--version-decay/--no-version-decay"),
    max_rewrite_attempts: int = typer.Option(1, "--max-rewrite-attempts", min=1),
    manifest: Path | None = typer.Option(None, "--manifest"),
    api_base: str | None = typer.Option(None, "--api-base"),
    solver_api_base: str | None = typer.Option(None, "--solver-api-base"),
    editor_api_base: str | None = typer.Option(None, "--editor-api-base"),
    solver_temperature: float | None = typer.Option(None, "--solver-temperature"),
    editor_temperature: float | None = typer.Option(None, "--editor-temperature"),
    solver_reasoning_effort: str | None = typer.Option(None, "--solver-reasoning-effort"),
    editor_reasoning_effort: str | None = typer.Option(None, "--editor-reasoning-effort"),
    permission: str = typer.Option("safe", "--permission", help="Agent CLI permissions."),
    max_tokens: int | None = typer.Option(None, "--max-tokens"),
    timeout: float = typer.Option(300.0, "--timeout"),
    resume: str | None = typer.Option(None, "--resume", help="Resume an existing run ID."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and print the plan only."),
    tasks_dir: Path | None = typer.Option(None, "--dir", "-d", help="Tasks directory."),
    pass_env: list[str] | None = typer.Option(
        None, "--pass-env", help="Environment variable allowed in task subprocesses; repeatable."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Run resumable train/validation skill optimization."""
    try:
        result = optimize_skill(
            skill_name,
            train_tasks=train or (),
            validate_tasks=validate or (),
            solver_model=solver_model or "",
            editor_model=editor_model,
            tasks_dir=tasks_dir,
            rounds=rounds,
            trials=trials,
            seed=seed,
            rewrite_mode=rewrite_mode,
            version_decay=version_decay,
            max_rewrite_attempts=max_rewrite_attempts,
            manifest=manifest,
            api_base=api_base,
            solver_api_base=solver_api_base,
            editor_api_base=editor_api_base,
            solver_temperature=solver_temperature,
            editor_temperature=editor_temperature,
            solver_reasoning_effort=solver_reasoning_effort,
            editor_reasoning_effort=editor_reasoning_effort,
            agent_permission=permission,
            max_tokens=max_tokens,
            timeout=timeout,
            resume=resume,
            dry_run=dry_run,
            pass_env=pass_env or (),
        )
    except KeyboardInterrupt:
        if json_output:
            fail_json("command_failed", "Optimization interrupted.", 130)
        raise typer.Exit(130) from None
    except Exception as exc:
        _exit_optimizer_error(exc, json_output)

    payload = result.to_dict()
    if json_output:
        emit_json(payload)
        return
    console.print(
        f"[green]{result.status}[/green] run={result.run_id} "
        f"version={result.initial_version}->{result.final_version}"
    )
    if result.reason:
        console.print(f"  reason={result.reason}")
    if result.recommendation:
        console.print(f"  recommendation: {result.recommendation}")


def optimize_status_cmd(
    skill_name: str = typer.Argument(help="Skill folder ID"),
    run_id: str | None = typer.Option(None, "--run", help="Run ID; defaults to latest."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """Show one durable optimizer checkpoint."""
    try:
        state = load_optimization_status(skill_name, run_id)
    except Exception as exc:
        _exit_optimizer_error(exc, json_output)

    if json_output:
        emit_json(state)
        return
    console.print(
        f"[cyan]{state['run_id']}[/cyan] status={state['status']} "
        f"phase={state['phase']} version={state['initial_version']}->{state['final_version']}"
    )
    if state.get("reason"):
        console.print(f"  reason={state['reason']}")
    if state.get("recommendation"):
        console.print(f"  recommendation: {state['recommendation']}")
