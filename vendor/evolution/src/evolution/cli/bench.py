"""``evo run bench`` — benchmark runner subcommand.

Replaces the legacy ``runs/*.sh`` wrappers with two pure-Python commands:

* ``evo run bench run`` — solve a list of tasks with one model, optionally
  across multiple trials and conditions, writing one CSV per invocation.
* ``evo run bench matrix`` — cartesian product over models × conditions ×
  tasks, reusing the same per-cell logic.

Each ``bench run`` invocation writes a fresh
``results/<model_tag>/results-<condition>-<timestamp>.csv`` (so runs don't
accumulate into a shared file) plus per-run workspaces under
``results/<model_tag>/<task>/<timestamp>/``. The whole ``results/`` tree is
gitignored.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from evolution.config import llm_max_tokens
from evolution.eval.paths import resolve_tasks_root
from evolution.eval.trace_cleanup import purge_workspace_bulk
from evolution.eval.volume_guard import InodeFloorError, assert_inode_headroom, preflight_inodes

bench = typer.Typer(help="Benchmark runner")
console = Console()


CSV_FIELDS = [
    "timestamp",
    "model",
    "task",
    "condition",
    "trial",
    "passed",
    "total",
    "exit_code",
    "tokens_in",
    "tokens_out",
    "tokens_total",
    "time_ms",  # LLM generation call time
    "exec_ms",  # solution execution (solve.sh / python)
    "eval_ms",  # pytest evaluation
    "completion_ms",  # full task wall time = time_ms + exec_ms + eval_ms
    "skill_version",
    "workspace",
]


def _model_tag(model: str) -> str:
    """Slugify a model id for use as a results subdirectory name."""
    return model.replace("/", "__").replace(":", "-").replace(" ", "-")


def _condition_label(no_skill: bool, skill_version: Optional[str]) -> str:
    if no_skill:
        return "no-skill"
    if skill_version:
        return skill_version
    return "latest"


def _ensure_csv_header(csv_path: Path) -> None:
    if csv_path.exists():
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow(CSV_FIELDS)


def _append_row(csv_path: Path, row: dict) -> None:
    with csv_path.open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=CSV_FIELDS).writerow(row)


def _solve_one(
    task,
    *,
    model: str,
    api_base: Optional[str],
    max_tokens: Optional[int],
    permission: str,
    pass_env: list[str],
    timeout: float,
    no_skill: bool,
    skill_version: Optional[str],
    snapshot: Optional[str],
    skills_root: Path,
    manifest_path: Optional[Path],
    manifest_scope: Optional[str],
    workspace: Path,
) -> dict:
    """Run one (task, model, condition) cell and return a CSV row dict."""
    from evolution.core.store import SkillStore
    from evolution.eval.solver import solve_task
    from evolution.eval.workspace import setup_workspace
    from evolution.llm.backend import get_backend
    from evolution.workflow import resolve_task_bindings

    workspace.mkdir(parents=True, exist_ok=True)
    setup_workspace(task, workspace)

    backend_kwargs: dict = {"max_tokens": llm_max_tokens(max_tokens)}
    if api_base:
        backend_kwargs["api_base"] = api_base
    backend = get_backend(model, agent_permission=permission, **backend_kwargs)

    bindings = []
    if not no_skill:
        store = SkillStore(project_dir=skills_root)
        bindings = resolve_task_bindings(
            task,
            store=store,
            project_dir=skills_root,
            skill_version=skill_version,
            snapshot=snapshot,
        )

    split_manifest = None
    if manifest_path is not None:
        from evolution.splits import SplitManifest

        split_manifest = SplitManifest.load(manifest_path)

    result = solve_task(
        task,
        backend,
        workspace,
        bindings=bindings,
        timeout=timeout,
        model_name=model,
        manifest=split_manifest,
        manifest_scope=manifest_scope,
        pass_env=pass_env,
    )

    er = result.eval_result
    resp = result.llm_response
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "task": task.name,
        "condition": _condition_label(no_skill, skill_version),
        "trial": 0,
        "passed": er.passed if er else 0,
        "total": er.total_tests if er else 0,
        "exit_code": result.script_exit_code,
        "tokens_in": resp.tokens_in if resp else 0,
        "tokens_out": resp.tokens_out if resp else 0,
        "tokens_total": (resp.tokens_in + resp.tokens_out) if resp else 0,
        "time_ms": resp.time_ms if resp else 0,
        "exec_ms": result.exec_ms,
        "eval_ms": result.eval_ms,
        "completion_ms": result.completion_ms,
        "skill_version": skill_version or "",
        "workspace": str(workspace),
    }
    # Must stay after the row is built — nothing re-reads the workspace below.
    purge_workspace_bulk(workspace)
    return row


def _print_summary(rows: list[dict]) -> None:
    if not rows:
        return
    table = Table(title="Benchmark summary", show_header=True)
    for col in ("model", "task", "condition", "trial", "passed", "total", "exit"):
        table.add_column(col)
    for r in rows:
        passed = r["passed"]
        total = r["total"]
        marker = "[green]PASS[/green]" if total and passed == total else "[red]FAIL[/red]"
        table.add_row(
            r["model"],
            r["task"],
            r["condition"],
            str(r["trial"]),
            f"{marker} {passed}",
            str(total),
            str(r["exit_code"]),
        )
    console.print(table)


@bench.command(name="run")
def bench_run(
    model: str = typer.Option(
        ...,
        "--model",
        "-m",
        help="Model id (e.g. openrouter/anthropic/claude-sonnet-4)",
    ),
    tasks: Optional[str] = typer.Option(
        None,
        "--tasks",
        help="Comma-separated task names (default: all tasks under --dir)",
    ),
    trials: int = typer.Option(1, "--trials", help="Trials per task"),
    skill_version: Optional[str] = typer.Option(
        None,
        "--skill-version",
        help="Pin to a specific skill version (default: active version)",
    ),
    no_skill: bool = typer.Option(
        False,
        "--no-skill",
        help="Run without injecting skills (baseline)",
    ),
    api_base: Optional[str] = typer.Option(None, "--api-base"),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Max tokens for LLM response (default: EVO_LLM_MAX_TOKENS or 16384)",
    ),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to generated code and the verifier (repeatable).",
    ),
    timeout: float = typer.Option(300.0, "--timeout"),
    snapshot: Optional[str] = typer.Option(None, "--snapshot"),
    tasks_dir: Optional[Path] = typer.Option(None, "--dir", "-d"),
    results_dir: Optional[Path] = typer.Option(
        None,
        "--results-dir",
        help="Results root (default: ./results)",
    ),
    manifest: Optional[Path] = typer.Option(None, "--manifest"),
    manifest_scope: Optional[str] = typer.Option(None, "--manifest-scope"),
) -> None:
    """Benchmark one model across one or more tasks.

    Examples:

      evo run bench run -m openrouter/anthropic/claude-sonnet-4
      evo run bench run -m gigachat-pro --tasks offer-letter-generator,powerlifting-coef-calc
      evo run bench run -m openai/Qwen/Qwen3-4B --api-base http://localhost:8000/v1 --no-skill
    """
    from evolution.eval.task import discover_tasks

    cwd = Path.cwd()
    tasks_path = resolve_tasks_root(tasks_dir, project_dir=cwd)
    all_tasks = discover_tasks(tasks_path)
    by_name = {t.name: t for t in all_tasks}
    if tasks:
        wanted = [n.strip() for n in tasks.split(",") if n.strip()]
        unknown = [n for n in wanted if n not in by_name]
        if unknown:
            console.print(f"[red]Unknown task(s): {', '.join(unknown)}[/red]")
            raise typer.Exit(1)
        selected = [by_name[n] for n in wanted]
    else:
        selected = list(all_tasks)

    if not selected:
        console.print("[yellow]No tasks to run.[/yellow]")
        raise typer.Exit(1)

    results_root = results_dir or cwd / "results"
    model_dir = results_root / _model_tag(model)

    condition = _condition_label(no_skill, skill_version)
    # One CSV per bench invocation (timestamped) so successive runs don't
    # accumulate into a shared file. The condition is in the name so the
    # per-(model,condition) runs a `bench matrix` spawns are distinguishable.
    run_ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    csv_path = model_dir / f"results-{condition}-{run_ts}.csv"
    _ensure_csv_header(csv_path)

    try:
        preflight_inodes(results_root)
    except InodeFloorError as exc:
        console.print(f"[red]FATAL: {exc}[/red]")
        raise typer.Exit(2)
    os.environ.setdefault("EVO_SHARED_GUARD_DIR", str(results_root / "_sharedguard"))

    console.print(
        f"Running [cyan]{model}[/cyan] on {len(selected)} task(s), "
        f"{trials} trial(s), condition=[cyan]{condition}[/cyan]"
    )
    console.print(f"  CSV: {csv_path}")

    rows: list[dict] = []
    failure_exit_code = 0
    for task in selected:
        try:
            assert_inode_headroom(results_root, context=task.name)
        except InodeFloorError as exc:
            console.print(f"[red]FATAL: {exc}[/red]")
            raise typer.Exit(2)
        for trial in range(1, trials + 1):
            ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            ws = model_dir / task.name / ts / f"{condition}_t{trial}"
            console.print(
                f"  [{task.name}] trial={trial} → {ws.relative_to(cwd) if ws.is_relative_to(cwd) else ws}"
            )
            try:
                row = _solve_one(
                    task,
                    model=model,
                    api_base=api_base,
                    max_tokens=max_tokens,
                    permission=permission,
                    pass_env=pass_env or [],
                    timeout=timeout,
                    no_skill=no_skill,
                    skill_version=skill_version,
                    snapshot=snapshot,
                    skills_root=cwd,
                    manifest_path=manifest,
                    manifest_scope=manifest_scope,
                    workspace=ws,
                )
            except Exception as exc:
                console.print(f"    [red]error: {exc}[/red]")
                user_error = isinstance(exc, (FileNotFoundError, KeyError, ValueError))
                failure_exit_code = max(failure_exit_code, 1 if user_error else 2)
                row = {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "model": model,
                    "task": task.name,
                    "condition": condition,
                    "trial": trial,
                    "passed": 0,
                    "total": 0,
                    "exit_code": -1,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "time_ms": 0,
                    "skill_version": skill_version or "",
                    "workspace": str(ws),
                }
            row["trial"] = trial
            rows.append(row)
            _append_row(csv_path, row)

    _print_summary(rows)
    if failure_exit_code:
        raise typer.Exit(failure_exit_code)


@bench.command(name="matrix")
def bench_matrix(
    models: str = typer.Option(
        ...,
        "--models",
        help="Comma-separated model ids",
    ),
    conditions: str = typer.Option(
        "no-skill,latest",
        "--conditions",
        help="Comma-separated conditions: no-skill, latest, or a version like v1",
    ),
    tasks: Optional[str] = typer.Option(None, "--tasks"),
    trials: int = typer.Option(1, "--trials"),
    api_base: Optional[str] = typer.Option(None, "--api-base"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens"),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to generated code and the verifier (repeatable).",
    ),
    timeout: float = typer.Option(300.0, "--timeout"),
    tasks_dir: Optional[Path] = typer.Option(None, "--dir", "-d"),
    results_dir: Optional[Path] = typer.Option(None, "--results-dir"),
) -> None:
    """Run a model × condition × task matrix.

    Replaces ``runs/bench_full.sh`` and ``runs/bench_all.sh``.

    Examples:

      evo run bench matrix --models claude-sonnet-4,qwen3-27b,llama3-8b \\
                       --conditions no-skill,v1,latest \\
                       --tasks offer-letter-generator,powerlifting-coef-calc
    """
    model_list = [m.strip() for m in models.split(",") if m.strip()]
    cond_list = [c.strip() for c in conditions.split(",") if c.strip()]
    if not model_list or not cond_list:
        console.print("[red]--models and --conditions must be non-empty.[/red]")
        raise typer.Exit(1)

    for model in model_list:
        for cond in cond_list:
            no_skill = cond == "no-skill"
            skill_version = None if cond in ("no-skill", "latest") else cond
            console.print(f"\n[bold]== {model} | {cond} ==[/bold]")
            bench_run(
                model=model,
                tasks=tasks,
                trials=trials,
                skill_version=skill_version,
                no_skill=no_skill,
                api_base=api_base,
                max_tokens=max_tokens,
                permission=permission,
                pass_env=pass_env,
                timeout=timeout,
                snapshot=None,
                tasks_dir=tasks_dir,
                results_dir=results_dir,
                manifest=None,
                manifest_scope=None,
            )
