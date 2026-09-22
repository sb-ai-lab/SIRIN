"""Validate skills against the Agent Skills specification."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from evolution.core.models import SkillFrontmatter
from evolution.core.parser import load_eval_suite, parse_skill_md


@dataclass
class ValidationResult:
    """Result of validating a skill directory."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_skill(path: str | Path) -> ValidationResult:
    """Validate a skill directory against the Agent Skills spec.

    Returns ValidationResult with errors (blocking) and warnings (non-blocking).
    """
    path = Path(path).resolve()
    result = ValidationResult()

    # --- SKILL.md exists ---
    if path.is_file():
        skill_md = path
        skill_dir = path.parent
    else:
        skill_dir = path
        skill_md = path / "SKILL.md"

    if not skill_md.exists():
        result.error(f"SKILL.md not found at {skill_md}")
        return result

    # --- Frontmatter parses ---
    try:
        raw_fm, body = parse_skill_md(skill_md)
    except ValueError as e:
        result.error(f"Frontmatter parse error: {e}")
        return result

    # --- Frontmatter validates ---
    try:
        fm = SkillFrontmatter.model_validate(raw_fm)
    except ValidationError as e:
        for err in e.errors():
            field_name = ".".join(str(loc) for loc in err["loc"])
            result.error(f"frontmatter.{field_name}: {err['msg']}")
        return result

    # --- Name matches directory ---
    if fm.name != skill_dir.name:
        result.warn(f"Skill name {fm.name!r} does not match directory name {skill_dir.name!r}")

    # --- Body checks ---
    if not body.strip():
        result.warn("SKILL.md body is empty (no instructions)")

    body_lines = body.splitlines()
    if len(body_lines) > 500:
        result.warn(
            f"SKILL.md body is {len(body_lines)} lines "
            f"(spec recommends <500 for progressive disclosure)"
        )

    # --- Eval suite validates (if present) ---
    try:
        suite = load_eval_suite(skill_dir)
        if suite is not None and suite.skill_name != fm.name:
            result.warn(
                f"evals/evals.json skill_name {suite.skill_name!r} "
                f"does not match SKILL.md name {fm.name!r}"
            )
    except Exception as e:
        result.warn(f"evals/evals.json parse error: {e}")

    return result
