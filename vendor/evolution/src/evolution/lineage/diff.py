"""Compute meaningful diffs between skill versions."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from evolution.core.models import Skill


@dataclass
class SkillDiff:
    """Structured diff between two skill versions."""

    summary: str = ""
    text_diff: str = ""
    frontmatter_changes: dict[str, tuple] = field(default_factory=dict)
    sections_added: list[str] = field(default_factory=list)
    sections_removed: list[str] = field(default_factory=list)
    sections_modified: list[str] = field(default_factory=list)
    scripts_added: list[str] = field(default_factory=list)
    scripts_removed: list[str] = field(default_factory=list)


def skill_diff(old: Skill, new: Skill) -> SkillDiff:
    """Compute a diff between two skill versions."""
    result = SkillDiff()

    # --- Text diff ---
    old_lines = old.body.splitlines(keepends=True)
    new_lines = new.body.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{old.name} (old)",
            tofile=f"{new.name} (new)",
        )
    )
    result.text_diff = "".join(diff_lines)

    # --- Frontmatter changes ---
    old_fm = old.frontmatter.model_dump(exclude_none=True)
    new_fm = new.frontmatter.model_dump(exclude_none=True)
    all_keys = set(old_fm) | set(new_fm)
    for key in all_keys:
        old_val = old_fm.get(key)
        new_val = new_fm.get(key)
        if old_val != new_val:
            result.frontmatter_changes[key] = (old_val, new_val)

    # --- Section changes ---
    old_sections = _extract_sections(old.body)
    new_sections = _extract_sections(new.body)
    old_headings = set(old_sections.keys())
    new_headings = set(new_sections.keys())

    result.sections_added = sorted(new_headings - old_headings)
    result.sections_removed = sorted(old_headings - new_headings)
    result.sections_modified = sorted(
        h for h in old_headings & new_headings if old_sections[h] != new_sections[h]
    )

    # --- Scripts diff ---
    old_scripts = set(old.scripts)
    new_scripts = set(new.scripts)
    result.scripts_added = sorted(new_scripts - old_scripts)
    result.scripts_removed = sorted(old_scripts - new_scripts)

    # --- Summary ---
    parts = []
    if result.sections_added:
        parts.append(f"added sections: {', '.join(result.sections_added)}")
    if result.sections_removed:
        parts.append(f"removed sections: {', '.join(result.sections_removed)}")
    if result.sections_modified:
        parts.append(f"modified sections: {', '.join(result.sections_modified)}")
    if result.frontmatter_changes:
        changed = ", ".join(result.frontmatter_changes.keys())
        parts.append(f"frontmatter changes: {changed}")
    if result.scripts_added:
        parts.append(f"added scripts: {', '.join(result.scripts_added)}")
    if result.scripts_removed:
        parts.append(f"removed scripts: {', '.join(result.scripts_removed)}")
    if not parts:
        parts.append("no changes detected")
    result.summary = "; ".join(parts)

    return result


def _extract_sections(body: str) -> dict[str, str]:
    """Parse markdown into {heading: content} pairs."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections
