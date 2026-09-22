"""Import skills from a SkillsBench repository."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from evolution.core.parser import parse_skill_md
from evolution.core.store import SkillStore

logger = logging.getLogger(__name__)

# SkillsBench layout:
#   tasks/<task-id>/environment/skills/<skill-name>/SKILL.md
#   tasks/<task-id>/task.toml  (metadata: difficulty, category, tags)

_TASKS_DIR = "tasks"


@dataclass
class SkillsBenchEntry:
    """A discovered skill inside a SkillsBench repo."""

    name: str
    task_id: str
    skill_dir: Path
    category: str = ""
    difficulty: str = ""
    tags: list[str] = field(default_factory=list)


def discover_skills(
    repo_path: str | Path,
    deduplicate: bool = True,
) -> list[SkillsBenchEntry]:
    """Scan a SkillsBench repo and return all skill entries.

    When *deduplicate* is True (default), skills with the same name across
    different tasks are returned only once (first occurrence wins).
    """
    repo = Path(repo_path).resolve()
    tasks_dir = repo / _TASKS_DIR
    if not tasks_dir.is_dir():
        raise FileNotFoundError(f"No tasks/ directory at {tasks_dir}")

    seen: dict[str, SkillsBenchEntry] = {}
    entries: list[SkillsBenchEntry] = []

    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue

        skills_dir = task_dir / "environment" / "skills"
        if not skills_dir.is_dir():
            continue

        # Parse task metadata
        category, difficulty, tags = _parse_task_toml(task_dir / "task.toml")

        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue

            # Read the name from frontmatter
            try:
                raw_fm, _ = parse_skill_md(skill_md)
                name = raw_fm.get("name", skill_dir.name)
            except Exception:
                name = skill_dir.name

            # Normalize: SkillsBench uses underscores in some dir names
            name = name.replace("_", "-")

            if deduplicate and name in seen:
                continue

            entry = SkillsBenchEntry(
                name=name,
                task_id=task_dir.name,
                skill_dir=skill_dir,
                category=category,
                difficulty=difficulty,
                tags=tags,
            )
            entries.append(entry)
            seen[name] = entry

    return entries


def import_skills(
    store: SkillStore,
    repo_path: str | Path,
    names: list[str] | None = None,
    theme_prefix: str = "",
) -> list[str]:
    """Import skills from SkillsBench into a SkillStore.

    Args:
        store: Target SkillStore.
        repo_path: Path to the SkillsBench repository root.
        names: If given, only import skills with these names. Otherwise all.
        theme_prefix: Optional prefix for the theme metadata tag
                      (e.g. "productivity/documents").

    Returns:
        List of imported skill names.
    """
    entries = discover_skills(repo_path)

    if names is not None:
        name_set = set(names)
        entries = [e for e in entries if e.name in name_set]

    imported: list[str] = []

    for entry in entries:
        if store.has(entry.name):
            logger.info("Skipping %s (already exists)", entry.name)
            continue

        # Build metadata tags
        meta: dict[str, str] = {
            "source": "skillsbench",
            "source-task": entry.task_id,
        }
        if entry.category:
            meta["category"] = entry.category
        if entry.difficulty:
            meta["difficulty"] = entry.difficulty
        if entry.tags:
            meta["tags"] = ", ".join(entry.tags)
        if theme_prefix:
            meta["theme"] = theme_prefix

        try:
            store.import_skill(
                source=entry.skill_dir,
                metadata=meta,
            )
            imported.append(entry.name)
            logger.info("Imported %s (from task %s)", entry.name, entry.task_id)
        except Exception as exc:
            logger.warning("Failed to import %s: %s", entry.name, exc)

    return imported


def _parse_task_toml(path: Path) -> tuple[str, str, list[str]]:
    """Extract category, difficulty, and tags from task.toml.

    Returns (category, difficulty, tags). Falls back to empty strings/list.
    """
    if not path.exists():
        return "", "", []

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return "", "", []

    # Simple TOML parsing for the fields we need — avoids adding a
    # toml dependency just for import metadata.
    category = _toml_value(text, "category")
    difficulty = _toml_value(text, "difficulty")
    tags = _toml_list(text, "tags")

    return category, difficulty, tags


def _toml_value(text: str, key: str) -> str:
    """Extract a simple key = "value" from TOML text."""
    import re

    m = re.search(rf'^{key}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return m.group(1) if m else ""


def _toml_list(text: str, key: str) -> list[str]:
    """Extract a simple key = ["a", "b"] from TOML text."""
    import re

    m = re.search(rf"^{key}\s*=\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    raw = m.group(1)
    return re.findall(r'"([^"]*)"', raw)
