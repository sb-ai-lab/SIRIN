"""Cold-start helpers: scaffold a task, preflight a run, and bootstrap a full demo loop.

A fresh clone ships no tasks (`tasks/` is gitignored) and no skills (`.agents/` is
gitignored), so these commands let a newcomer or an agent go from nothing to one
solve->reflect->rewrite->commit loop on a task of their own.
"""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from evolution.cli.json_contract import emit_json, fail_json
from evolution.core.models import NAME_MAX, NAME_RE
from evolution.eval.paths import resolve_tasks_root
from evolution.eval.python_env import expected_role_python
from evolution.llm.proxy_env import is_local_api_base

console = Console()

_TASK_TOML = """version = "1.0"

[metadata]
name = "{name}"
difficulty = "easy"
category = "custom"
origin = "custom"

[skills]
required = ["{skill}"]

[evaluation]
timeout_sec = "120"
test_file = "tests/test_outputs.py"
"""

_INSTRUCTION = """# {name}

Write a Python script that creates a file `output.txt` in the current directory
whose entire contents are exactly:

```
hello
```

Save it to the workspace root as `output.txt`.
"""

_TEST = """import os
from pathlib import Path


def _workspace() -> Path:
    return Path(os.environ.get("TASK_WORKSPACE") or os.environ.get("WORKSPACE_DIR") or ".")


def test_output_exists():
    assert (_workspace() / "output.txt").is_file(), "expected output.txt in the workspace"


def test_output_content():
    assert (_workspace() / "output.txt").read_text().strip() == "hello"
"""


def _scaffold_task(name: str, root: Path, skill: str, force: bool) -> Path:
    _validate_id(name, "task")
    _validate_id(skill, "skill")
    root = root.resolve()
    task_dir = root / name
    planned_paths = (
        task_dir,
        task_dir / "inputs",
        task_dir / "tests",
        task_dir / "task.toml",
        task_dir / "instruction.md",
        task_dir / "tests" / "test_outputs.py",
        task_dir / "inputs" / ".gitkeep",
    )
    for path in planned_paths:
        if path.is_symlink() or not path.resolve(strict=False).is_relative_to(root):
            raise ValueError(f"Task destination escapes the tasks root: {path}")
    if task_dir.exists() and not task_dir.is_dir():
        raise ValueError(f"Task destination is not a directory: {task_dir}")
    if task_dir.exists() and not force:
        raise FileExistsError(f"{task_dir} already exists (use --force to overwrite)")
    (task_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (task_dir / "tests").mkdir(parents=True, exist_ok=True)
    (task_dir / "task.toml").write_text(_TASK_TOML.format(name=name, skill=skill), encoding="utf-8")
    (task_dir / "instruction.md").write_text(_INSTRUCTION.format(name=name), encoding="utf-8")
    (task_dir / "tests" / "test_outputs.py").write_text(_TEST, encoding="utf-8")
    (task_dir / "inputs" / ".gitkeep").write_text("", encoding="utf-8")
    from evolution.eval.task import load_task

    load_task(task_dir)  # self-validate: fail loudly if the scaffold doesn't load
    return task_dir


def _validate_id(value: str, kind: str) -> None:
    if len(value) > NAME_MAX or "--" in value or not NAME_RE.fullmatch(value):
        raise ValueError(
            f"Invalid {kind} id {value!r}: use at most {NAME_MAX} lowercase letters, "
            "digits, and single hyphens"
        )


def task_new(
    name: str = typer.Argument(help="Task name (lowercase, hyphens ok)"),
    tasks_dir: Path | None = typer.Option(
        None, "--dir", "--tasks-dir", help="Tasks root (default: ./tasks)"
    ),
    skill: str = typer.Option("my-skill", "--skill", "-s", help="Skill this task requires"),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing task dir"),
) -> None:
    """Scaffold a minimal, loadable evo-native task (task.toml + instruction.md + tests/)."""
    root = resolve_tasks_root(tasks_dir, project_dir=Path.cwd())
    try:
        task_dir = _scaffold_task(name, root, skill, force)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)
    console.print(f"[green]Created task[/green] {name} at {task_dir}")
    console.print(
        f"  requires skill: [cyan]{skill}[/cyan]  (create it: evo skill create {skill} -d '...')"
    )
    console.print(
        "  edit instruction.md + tests/test_outputs.py, then: evo run solve "
        f"{name} -m <model> --dir {root}"
    )


def _model_credential(model: str, api_base: str | None) -> tuple[bool, str, str]:
    m = (model or "").lower()
    if m == "mock":
        return True, "mock backend (offline)", ""
    if is_local_api_base(api_base):
        return True, f"local endpoint {api_base} (api_key=EMPTY)", ""
    table = [
        (("openrouter/",), "OPENROUTER_API_KEY"),
        (("anthropic/", "claude-sonnet", "claude-opus", "claude-haiku"), "ANTHROPIC_API_KEY"),
        (("openai/", "gpt-"), "OPENAI_API_KEY"),
        (("gigachat",), "GIGACHAT_CREDENTIALS"),
    ]
    for prefixes, env in table:
        if any(m.startswith(p) or p in m for p in prefixes):
            return bool(os.environ.get(env)), env, f"export {env}=..."
    if m.startswith(("codex", "claude-code", "hermes")):
        return True, "agent CLI backend (file-based auth)", ""
    return True, "unknown provider (litellm resolves credentials from env)", ""


def _local_reachable(api_base: str, timeout: float = 4.0) -> bool:
    url = api_base.rstrip("/") + "/models"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (local only)
            return resp.status == 200
    except Exception:
        return False


def doctor(
    model: str | None = typer.Option(None, "--model", "-m", help="Model to check credentials for"),
    api_base: str | None = typer.Option(
        None, "--api-base", help="Local OpenAI-compatible base URL"
    ),
    task: str | None = typer.Option(None, "--task", "-t", help="Validate this task loads"),
    tasks_dir: Path | None = typer.Option(None, "--dir", "--tasks-dir", help="Tasks root"),
    skill: str | None = typer.Option(None, "--skill", "-s", help="Check this skill resolves"),
    as_json: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Preflight a run: credentials, model reachability, task validity, skills, writability."""
    from evolution.core.store import SkillStore
    from evolution.workflow import get_task, list_tasks

    project = Path.cwd()
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str, fix: str = "") -> None:
        checks.append({"check": name, "ok": bool(ok), "detail": detail, "fix": fix})

    try:
        store = SkillStore(project_dir=project, user_dir=Path.home())
        n_skills = len(store.list())
    except Exception as exc:
        if as_json:
            fail_json("command_failed", str(exc))
        raise
    add(
        "skills available",
        n_skills > 0,
        f"{n_skills} skill(s) under .agents/skills",
        "evo quickstart  (or: evo skill create <name> -d '...')",
    )

    try:
        n_tasks = len(list_tasks(tasks_dir, project_dir=project))
    except Exception as exc:
        n_tasks = 0
        add("tasks discoverable", False, str(exc), "evo task new <name>  (or: evo quickstart)")
    else:
        add(
            "tasks available",
            n_tasks > 0,
            f"{n_tasks} task(s) under {tasks_dir or 'tasks/'}",
            "evo task new <name>  (or: evo quickstart)",
        )

    if task:
        try:
            t = get_task(task, tasks_dir=tasks_dir, project_dir=project)
            add(
                f"task '{task}' loads",
                True,
                f"{t.difficulty}/{t.category}, skills={t.skills_required}",
            )
            if t.role:
                role_py = expected_role_python(t.role) or f"<no env mapped for role {t.role!r}>"
                add(
                    f"role env for '{t.role}'",
                    Path(role_py).exists(),
                    role_py,
                    f"set EVO_ROLE_PYTHON_{t.role.upper()}=/path/to/python (evo-native tasks need no role)",
                )
        except Exception as exc:
            add(f"task '{task}' loads", False, str(exc), "evo task new " + task)

    if skill:
        add(
            f"skill '{skill}' resolves",
            store.has(skill),
            "found" if store.has(skill) else "not found",
            f"evo skill create {skill} -d '...'",
        )

    if model:
        ok, detail, fix = _model_credential(model, api_base)
        add("model credential", ok, detail, fix)
        if api_base:
            reachable = _local_reachable(api_base)
            add(
                "model endpoint reachable",
                reachable,
                api_base.rstrip("/") + "/models",
                "start your local server / check the port",
            )

    try:
        probe = project / ".evo_doctor_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        add("workspace writable", True, str(project))
    except Exception as exc:
        add("workspace writable", False, str(exc), "run from a writable directory")

    failed = [c for c in checks if not c["ok"]]
    if as_json:
        if failed:
            for check in failed:
                typer.echo(f"FAIL {check['check']}: {check['detail']}", err=True)
            fail_json("doctor_checks_failed", f"{len(failed)} doctor check(s) failed.")
        emit_json({"ok": True, "checks": checks})
        return

    tbl = Table(title="evo doctor")
    tbl.add_column("")
    tbl.add_column("check", style="cyan")
    tbl.add_column("detail")
    for c in checks:
        tbl.add_row("[green]OK[/green]" if c["ok"] else "[red]FAIL[/red]", c["check"], c["detail"])
    console.print(tbl)
    for c in failed:
        if c["fix"]:
            console.print(f"  [yellow]fix[/yellow] {c['check']}: {c['fix']}")
    if failed:
        raise typer.Exit(1)


def quickstart(
    model: str = typer.Option("mock", "--model", "-m", help="Model (default: mock, offline)"),
    api_base: str | None = typer.Option(
        None, "--api-base", help="Local OpenAI-compatible base URL"
    ),
    tasks_dir: Path | None = typer.Option(
        None, "--dir", "--tasks-dir", help="Tasks root (default: ./tasks)"
    ),
    skill: str = typer.Option("hello-skill", "--skill", "-s", help="Demo skill name"),
    task: str = typer.Option("hello-evolution", "--task", "-t", help="Demo task name"),
    permission: str = typer.Option(
        "safe", "--permission", help="Agent CLI permissions: safe or unsafe."
    ),
    pass_env: list[str] | None = typer.Option(
        None,
        "--pass-env",
        help="Pass this environment variable to generated code and the verifier (repeatable).",
    ),
) -> None:
    """Bootstrap a skill + task from nothing and run one full evolve loop end-to-end."""
    from evolution.core.store import SkillStore
    from evolution.evolve.rewrite_outcome import PROMOTED_ELIGIBLE
    from evolution.workflow import commit_skill, reflect, rewrite, solve

    project = Path.cwd()
    root = resolve_tasks_root(tasks_dir, project_dir=project)

    store = SkillStore(project_dir=project, user_dir=Path.home())
    if not store.has(skill):
        store.create(
            name=skill, description="Demo skill: write a small text file with exact contents."
        )
        console.print(f"[green]1/5 created skill[/green] {skill}")
    else:
        console.print(f"[green]1/5 skill exists[/green] {skill}")

    if not (root / task / "task.toml").exists():
        _scaffold_task(task, root, skill, force=False)
        console.print(f"[green]2/5 scaffolded task[/green] {task} (--dir {root})")
    else:
        console.print(f"[green]2/5 task exists[/green] {task}")

    console.print(f"[cyan]3/5 solve[/cyan] {task} with {model} ...")
    res = solve(
        task,
        model=model,
        project_dir=project,
        tasks_dir=root,
        skill_name=skill,
        api_base=api_base,
        agent_permission=permission,
        pass_env=pass_env or (),
    )
    ev = res.eval_result
    passed = getattr(ev, "passed", 0) if ev else 0
    total = getattr(ev, "total_tests", 0) if ev else 0
    console.print(f"    -> passed {passed}/{total}; errors={res.errors or 'none'}")

    if ev and ev.success:
        console.print(
            "[green]done[/green] task already passes; nothing to evolve. "
            "Edit the task/skill to make it harder, or point at your own task."
        )
        return

    console.print("[cyan]4/5 reflect[/cyan] on failing trace ...")
    try:
        refl = reflect(
            skill,
            model=model,
            project_dir=project,
            task=task,
            tasks_dir=root,
            api_base=api_base,
            agent_permission=permission,
            strict=False,
        )
    except Exception as exc:
        console.print(f"    [yellow]reflect skipped[/yellow]: {exc}")
        return
    usable = [r for r in refl if r.get("root_cause") and "error" not in r]
    console.print(f"    -> {len(usable)} usable reflection(s) (of {len(refl)})")
    if not usable:
        console.print(
            "[yellow]done[/yellow] no usable diagnosis this round "
            "(expected with -m mock — it can't emit real reflection JSON). "
            "Re-run with a real model to see rewrite+commit, e.g.\n"
            "    evo quickstart -m openai/openai/gpt-oss-120b --api-base http://localhost:30004/v1"
        )
        return

    console.print("[cyan]5/5 rewrite + commit[/cyan] ...")
    try:
        outcome = rewrite(
            skill,
            model=model,
            project_dir=project,
            task=task,
            tasks_dir=root,
            api_base=api_base,
            agent_permission=permission,
            apply=True,
        )
    except Exception as exc:
        console.print(f"    [yellow]rewrite skipped[/yellow]: {exc}")
        return
    if outcome.candidate_status == PROMOTED_ELIGIBLE:
        version = commit_skill(skill, project_dir=project)
        console.print(
            f"[green]done[/green] committed evolved skill {skill} -> {version}. "
            "Inspect: evo skill history " + skill
        )
    else:
        console.print(
            f"[green]done[/green] kept parent skill (rewrite status={outcome.candidate_status}: "
            f"{outcome.reason}). This is a valid no-op, not an error."
        )
