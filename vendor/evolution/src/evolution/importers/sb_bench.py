"""Import tasks and skills from sb-bench (Sber Agent Onboarding Benchmark)."""

from __future__ import annotations

import logging
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# sb-bench layout:
#   tasks/{role}/{difficulty}-{name}/
#     task.toml, instruction.md, environment/data/, environment/skills/,
#     data_generator.py, solve.sh, tests/test_outputs.py,
#     .ground_truth_*

_ROLE_CATEGORY = {
    "ds": "data-science",
    "de": "data-engineering",
    "infra": "infrastructure",
}


@dataclass
class SbBenchTask:
    """A discovered task in sb-bench."""

    task_id: str  # e.g. "de/E1-duckdb-assembly"
    name: str  # e.g. "DuckDB Dataset Assembly"
    role: str  # ds, de, infra
    difficulty: str  # easy, medium, hard, extra-hard
    tools: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    timeout_sec: int = 300
    path: Path = field(default_factory=lambda: Path("."))
    skill_names: list[str] = field(default_factory=list)


def discover_tasks(
    repo_path: str | Path,
    role: str | None = None,
    difficulty: str | None = None,
) -> list[SbBenchTask]:
    """Scan sb-bench repo and return all tasks.

    Args:
        repo_path: Path to sb-bench repository root.
        role: Filter by role (ds, de, infra).
        difficulty: Filter by difficulty (easy, medium, hard).
    """
    repo = Path(repo_path).resolve()
    tasks_dir = repo / "tasks"
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"No tasks/ directory at {tasks_dir}")

    tasks: list[SbBenchTask] = []

    for role_dir in sorted(tasks_dir.iterdir()):
        if not role_dir.is_dir() or role_dir.name.startswith("."):
            continue
        if role and role_dir.name != role:
            continue

        for task_dir in sorted(role_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            toml_path = task_dir / "task.toml"
            if not toml_path.exists():
                continue

            task = _parse_sb_task(toml_path, role_dir.name)
            if difficulty and task.difficulty != difficulty:
                continue

            tasks.append(task)

    return tasks


def import_task(
    sb_task: SbBenchTask,
    evolution_tasks_dir: Path,
    *,
    force: bool = False,
    regenerate_data: bool = True,
) -> str:
    """Import a single sb-bench task into Evolution format.

    Args:
        regenerate_data: If True, run data_generator.py before copying
            (ensures fresh, unmodified input data).

    Returns the new task name (e.g. "sb-de-duckdb-assembly").
    """
    # Regenerate data to ensure it hasn't been modified by a prior oracle run
    if regenerate_data:
        gen_script = sb_task.path / "data_generator.py"
        if gen_script.exists():
            import subprocess
            import sys

            proc = subprocess.run(
                [sys.executable, str(gen_script)],
                capture_output=True,
                text=True,
                cwd=str(sb_task.path),
                timeout=120,
            )
            if proc.returncode != 0:
                logger.warning(
                    "data_generator.py failed for %s: %s",
                    sb_task.task_id,
                    proc.stderr[-300:],
                )

    # Derive evolution task name: sb-{role}-{short_name}
    short_name = _short_name(sb_task.task_id)
    evo_name = f"sb-{sb_task.role}-{short_name}"

    dest = Path(evolution_tasks_dir) / evo_name
    if dest.exists():
        if not force:
            logger.info("Skipping %s (already exists at %s)", evo_name, dest)
            return evo_name
        shutil.rmtree(dest)

    dest.mkdir(parents=True)

    # 1. Convert task.toml
    _write_task_toml(dest, sb_task, evo_name)

    # 2. Copy and rewrite instruction.md
    _copy_instruction(sb_task.path, dest)

    # 3. Copy input data: environment/data/* → inputs/
    _copy_inputs(sb_task.path, dest)

    # 4. Copy and adapt tests
    _copy_tests(sb_task.path, dest)

    # 5. Copy ground truth files into tests/
    _copy_ground_truth(sb_task.path, dest)

    logger.info("Imported %s → %s", sb_task.task_id, evo_name)
    return evo_name


def import_tasks(
    repo_path: str | Path,
    evolution_tasks_dir: str | Path,
    *,
    role: str | None = None,
    difficulty: str | None = None,
    task_ids: list[str] | None = None,
    force: bool = False,
) -> list[str]:
    """Import multiple tasks from sb-bench.

    Returns list of imported task names.
    """
    tasks = discover_tasks(repo_path, role=role, difficulty=difficulty)

    if task_ids:
        id_set = set(task_ids)
        # Allow partial match (e.g. "de/E1" matches "de/E1-duckdb-assembly")
        tasks = [
            t
            for t in tasks
            if t.task_id in id_set or any(t.task_id.startswith(prefix) for prefix in id_set)
        ]

    dest = Path(evolution_tasks_dir)
    dest.mkdir(parents=True, exist_ok=True)

    imported = []
    for task in tasks:
        try:
            name = import_task(task, dest, force=force)
            imported.append(name)
        except Exception as exc:
            logger.warning("Failed to import %s: %s", task.task_id, exc)

    return imported


def discover_skills(repo_path: str | Path) -> list[dict]:
    """Discover all skills across sb-bench tasks.

    Returns list of dicts with: name, task_id, skill_dir, role.
    Deduplicates by skill name (first occurrence wins).
    """
    repo = Path(repo_path).resolve()
    tasks_dir = repo / "tasks"
    seen: dict[str, dict] = {}
    results: list[dict] = []

    for role_dir in sorted(tasks_dir.iterdir()):
        if not role_dir.is_dir() or role_dir.name.startswith("."):
            continue
        for task_dir in sorted(role_dir.iterdir()):
            skills_dir = task_dir / "environment" / "skills"
            if not skills_dir.is_dir():
                continue
            task_id = f"{role_dir.name}/{task_dir.name}"

            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.is_file():
                    continue

                name = skill_dir.name
                if name in seen:
                    continue

                entry = {
                    "name": name,
                    "task_id": task_id,
                    "skill_dir": skill_dir,
                    "role": role_dir.name,
                }
                seen[name] = entry
                results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_sb_task(toml_path: Path, role: str) -> SbBenchTask:
    """Parse sb-bench task.toml into SbBenchTask."""
    text = toml_path.read_text(encoding="utf-8")
    task_dir = toml_path.parent

    task_id = _toml_value(text, "id") or f"{role}/{task_dir.name}"
    name = _toml_value(text, "name") or task_dir.name
    difficulty = _toml_value(text, "difficulty") or "medium"
    tools = _toml_list(text, "tools")
    tags = _toml_list(text, "tags")
    timeout = int(_toml_value(text, "timeout_seconds") or "300")

    # Discover skill names
    skills_dir = task_dir / "environment" / "skills"
    skill_names = []
    if skills_dir.is_dir():
        skill_names = sorted(
            d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
        )

    return SbBenchTask(
        task_id=task_id,
        name=name,
        role=role,
        difficulty=difficulty,
        tools=tools,
        tags=tags,
        timeout_sec=timeout,
        path=task_dir,
        skill_names=skill_names,
    )


def _short_name(task_id: str) -> str:
    """Extract short name from task_id.

    "de/E1-duckdb-assembly" → "duckdb-assembly"
    "infra/H2-terraform-migration" → "terraform-migration"
    """
    # Take the part after role/, then strip the difficulty prefix (E1-, M2-, etc.)
    part = task_id.split("/", 1)[-1]  # "E1-duckdb-assembly"
    m = re.match(r"^[A-Z]\d+-(.+)$", part)
    return m.group(1) if m else part


def _write_task_toml(dest: Path, task: SbBenchTask, evo_name: str) -> None:
    """Write Evolution-format task.toml."""
    category = _ROLE_CATEGORY.get(task.role, task.role)
    # Combine tools into tags
    all_tags = list(set(task.tags + task.tools))

    # Use container name (matches evo_name) so all 3 skills are injected
    skill_ref = evo_name if task.skill_names else ""

    lines = [
        'version = "1.0"',
        "",
        "[metadata]",
        f'name = "{evo_name}"',
        f'difficulty = "{task.difficulty}"',
        f'category = "{category}"',
        f"tags = [{', '.join(f'{t!r}' for t in sorted(all_tags))}]",
        "",
        "[source]",
        'origin = "sb-bench"',
        f'task_id = "{task.task_id}"',
        f'role = "{task.role}"',
        "",
        "[skills]",
        f'required = ["{skill_ref}"]' if skill_ref else "required = []",
        "",
        "[evaluation]",
        f'timeout_sec = "{task.timeout_sec}"',
        'test_file = "tests/test_outputs.py"',
        'grading = "pytest"',
        "",
    ]
    (dest / "task.toml").write_text("\n".join(lines), encoding="utf-8")


def _copy_instruction(src_task: Path, dest: Path) -> None:
    """Copy instruction.md, rewriting environment/data/ paths to ./."""
    text = (src_task / "instruction.md").read_text(encoding="utf-8")

    # Rewrite paths: ./environment/data/foo → ./foo
    text = re.sub(r"\./environment/data/", "./", text)
    # Also catch without leading ./ : environment/data/foo
    text = re.sub(r"(?<!\.)environment/data/", "./", text)

    (dest / "instruction.md").write_text(text, encoding="utf-8")


def _copy_inputs(src_task: Path, dest: Path) -> None:
    """Copy environment/data/* → inputs/."""
    data_dir = src_task / "environment" / "data"
    inputs_dir = dest / "inputs"

    if not data_dir.is_dir():
        return

    inputs_dir.mkdir(parents=True, exist_ok=True)

    for item in data_dir.iterdir():
        dst = inputs_dir / item.name
        if item.is_file():
            shutil.copy2(item, dst)
        elif item.is_dir():
            shutil.copytree(item, dst)


def _copy_tests(src_task: Path, dest: Path) -> None:
    """Copy and adapt test_outputs.py for Evolution runner."""
    src_tests = src_task / "tests"
    if not src_tests.is_dir():
        return

    dest_tests = dest / "tests"
    dest_tests.mkdir(parents=True, exist_ok=True)

    for f in src_tests.iterdir():
        if not f.is_file():
            continue

        text = f.read_text(encoding="utf-8")
        text = _adapt_test(text)
        (dest_tests / f.name).write_text(text, encoding="utf-8")


def _adapt_test(text: str) -> str:
    """Rewrite sb-bench test code for Evolution compatibility."""
    # 1. Replace SB_OUTPUT env var with TASK_WORKSPACE
    text = text.replace(
        'os.environ.get("SB_OUTPUT", "/root")',
        'os.environ.get("TASK_WORKSPACE", "/root")',
    )
    text = text.replace("SB_OUT", "WORKSPACE")

    # 2. Fix ground truth path: parent.parent → parent
    #    sb-bench: Path(__file__).parent.parent / ".ground_truth_*"
    #    evolution: Path(__file__).parent / ".ground_truth_*"
    #    (because we copy ground truth into tests/ directory)
    text = text.replace(
        "Path(__file__).parent.parent",
        "Path(__file__).parent",
    )

    # 3. Rewrite bare relative paths to environment/data/
    #    e.g. Path("environment/data/myproject/...") → Path(f"{WORKSPACE}/myproject/...")
    text = re.sub(
        r'Path\("environment/data/([^"]+)"\)',
        r'Path(f"{WORKSPACE}/\1")',
        text,
    )

    return text


def _copy_ground_truth(src_task: Path, dest: Path) -> None:
    """Copy .ground_truth_* files from task root into tests/ directory."""
    dest_tests = dest / "tests"
    dest_tests.mkdir(parents=True, exist_ok=True)

    for f in src_task.iterdir():
        if f.is_file() and f.name.startswith(".ground_truth"):
            shutil.copy2(f, dest_tests / f.name)


# ---------------------------------------------------------------------------
# TOML helpers (same pattern as other importers)
# ---------------------------------------------------------------------------


def _toml_value(text: str, key: str) -> str:
    m = re.search(rf'^{key}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return m.group(1) if m else ""


def _toml_list(text: str, key: str) -> list[str]:
    m = re.search(rf"^{key}\s*=\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    return re.findall(r'"([^"]*)"', m.group(1))
