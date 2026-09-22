"""Parse and load SKILL.md files following the Agent Skills spec."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

import yaml

from evolution.core.models import EvalSuite, Skill, SkillFrontmatter

# Regex: opening --- must be at the very start of the file
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\n(.*?\n)---[ \t]*\n",
    re.DOTALL,
)


def parse_skill_md(path: str | Path) -> tuple[dict, str]:
    """Parse a SKILL.md file into (frontmatter_dict, body_string).

    Handles:
    - Standard YAML frontmatter between ``---`` delimiters.
    - Lenient recovery: if YAML fails, retry with common fixups
      (unquoted colons wrapped in quotes).
    - Missing closing ``---``: treat everything after first ``---`` as YAML
      and return empty body.

    Raises:
        FileNotFoundError: if *path* does not exist.
        ValueError: if YAML is completely unparseable even after fixups.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    text = path.read_text(encoding="utf-8")

    m = _FRONTMATTER_RE.match(text)
    if m is None:
        # Fallback: try to find opening --- and treat rest as YAML
        if text.startswith("---"):
            yaml_text = text[4:]  # skip opening ---\n
            body = ""
        else:
            raise ValueError(f"No YAML frontmatter found in {path}")
    else:
        yaml_text = m.group(1)
        body = text[m.end() :]

    frontmatter = _parse_yaml_lenient(yaml_text, path)
    return frontmatter, body.strip()


def _parse_yaml_lenient(yaml_text: str, source: Path) -> dict:
    """Parse YAML with fallback for common cross-client issues."""
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        # Common fixup: wrap description value containing unquoted colons
        fixed = _fix_unquoted_colons(yaml_text)
        try:
            data = yaml.safe_load(fixed)
        except yaml.YAMLError as e:
            raise ValueError(f"Unparseable YAML in {source}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Frontmatter must be a YAML mapping, got {type(data).__name__}")

    return data


def _fix_unquoted_colons(yaml_text: str) -> str:
    """Wrap values containing colons in double quotes."""
    lines = []
    for line in yaml_text.splitlines():
        # Match top-level key: value lines (not indented, not part of a block)
        m = re.match(r"^(\w[\w-]*):\s+(.+)$", line)
        if m and ":" in m.group(2) and not m.group(2).startswith(("'", '"', "|", ">")):
            key, val = m.group(1), m.group(2)
            escaped = val.replace('"', '\\"')
            lines.append(f'{key}: "{escaped}"')
        else:
            lines.append(line)
    return "\n".join(lines)


def load_skill(path: str | Path, *, validate_dir_name: bool = True) -> Skill:
    """Load a Skill from a directory path or SKILL.md file path.

    Steps:
    1. Resolve to directory (if file given, use parent).
    2. Read and parse SKILL.md.
    3. Validate frontmatter via SkillFrontmatter model.
    4. Warn (don't fail) if name != directory name unless disabled.
    5. Return Skill instance.

    Raises:
        FileNotFoundError: if SKILL.md does not exist.
        ValueError: if YAML is unparseable.
        pydantic.ValidationError: if frontmatter is invalid.
    """
    path = Path(path).resolve()

    if path.is_file():
        skill_md_path = path
        skill_dir = path.parent
    else:
        skill_dir = path
        skill_md_path = path / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md_path}")

    raw_fm, body = parse_skill_md(skill_md_path)

    # Validate frontmatter
    frontmatter = SkillFrontmatter.model_validate(raw_fm)

    # Warn if name doesn't match directory. Version snapshots live under
    # .evolution/versions/vN, so callers loading those pass validate_dir_name=False.
    if validate_dir_name and frontmatter.name != skill_dir.name:
        warnings.warn(
            f"Skill name {frontmatter.name!r} does not match directory name {skill_dir.name!r}",
            stacklevel=2,
        )

    return Skill(
        frontmatter=frontmatter,
        body=body,
        path=skill_dir,
        skill_md_path=skill_md_path,
    )


def load_eval_suite(skill_path: str | Path) -> EvalSuite | None:
    """Load evals/evals.json from a skill directory. Return None if absent."""
    skill_path = Path(skill_path)
    if skill_path.is_file():
        skill_path = skill_path.parent

    evals_path = skill_path / "evals" / "evals.json"
    if not evals_path.exists():
        return None

    data = json.loads(evals_path.read_text(encoding="utf-8"))
    return EvalSuite.model_validate(data)


def write_skill_md(
    path: Path,
    frontmatter: SkillFrontmatter,
    body: str,
) -> None:
    """Write a SKILL.md file with YAML frontmatter + markdown body."""
    fm_dict = frontmatter.model_dump(exclude_none=True)
    yaml_str = yaml.dump(fm_dict, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_str}---\n\n{body}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
