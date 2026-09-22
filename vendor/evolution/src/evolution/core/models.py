"""Pydantic models for skills, evals, lineage, and evolution results."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500

SkillStatus = Literal["active", "candidate", "retired", "archived", "rejected"]
LineageOrigin = Literal["manual", "mutation", "crossover", "speciation", "import", "fork"]

# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------


class SkillFrontmatter(BaseModel):
    """YAML frontmatter from SKILL.md — matches Agent Skills spec."""

    name: str
    description: str
    license: str | None = None
    compatibility: Any | None = None  # str or dict (agentskills.io allows both)
    metadata: dict[str, str] | None = None
    allowed_tools: str | None = None  # space-delimited (experimental)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) > NAME_MAX:
            raise ValueError(f"name must be ≤{NAME_MAX} chars, got {len(v)}")
        if "--" in v:
            raise ValueError("name must not contain consecutive hyphens")
        if not NAME_RE.match(v):
            raise ValueError(
                "name must be lowercase alphanumeric + hyphens, must not start/end with hyphen"
            )
        return v

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata_values(cls, v: Any) -> Any:
        """Coerce non-string metadata values to strings.

        SkillsBench/agentskills SKILL.md files routinely express metadata
        values as YAML lists (e.g. ``dependencies: [duckdb, sqlalchemy]``)
        or scalars. The Agent Skills spec treats metadata as string-valued,
        so normalize here rather than rejecting upstream data: lists/tuples
        become comma-joined strings, other non-str scalars are str()'d.
        """
        if not isinstance(v, dict):
            return v
        out: dict[str, str] = {}
        for key, val in v.items():
            if isinstance(val, str):
                out[key] = val
            elif isinstance(val, (list, tuple)):
                out[key] = ", ".join(str(x) for x in val)
            elif val is None:
                out[key] = ""
            else:
                out[key] = str(val)
        return out

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must not be empty")
        if len(v) > DESCRIPTION_MAX:
            raise ValueError(f"description must be ≤{DESCRIPTION_MAX} chars, got {len(v)}")
        return v

    @field_validator("compatibility")
    @classmethod
    def validate_compatibility(cls, v: Any | None) -> Any | None:
        if v is None:
            return v
        # Accept both string and dict formats
        if isinstance(v, dict):
            return v
        if isinstance(v, str) and len(v) > COMPATIBILITY_MAX:
            raise ValueError(f"compatibility must be ≤{COMPATIBILITY_MAX} chars, got {len(v)}")
        return v


class Skill(BaseModel):
    """A fully loaded skill with parsed content and resolved paths."""

    frontmatter: SkillFrontmatter
    body: str  # Markdown content after frontmatter
    path: Path  # Absolute path to skill directory
    skill_md_path: Path  # Absolute path to SKILL.md

    model_config = {"arbitrary_types_allowed": True}

    # --- Convenience accessors ---

    @property
    def name(self) -> str:
        return self.frontmatter.name

    @property
    def description(self) -> str:
        return self.frontmatter.description

    @property
    def metadata(self) -> dict[str, str]:
        return self.frontmatter.metadata or {}

    @property
    def fitness(self) -> float | None:
        raw = self.metadata.get("evolution-fitness")
        if raw is None:
            return None
        try:
            return float(raw)
        except (ValueError, TypeError):
            return None

    @property
    def generation(self) -> int | None:
        raw = self.metadata.get("evolution-generation")
        if raw is None:
            return None
        try:
            return int(raw)
        except (ValueError, TypeError):
            return None

    @property
    def scripts(self) -> list[str]:
        return self._list_subdir("scripts")

    @property
    def references(self) -> list[str]:
        return self._list_subdir("references")

    @property
    def assets(self) -> list[str]:
        return self._list_subdir("assets")

    @property
    def all_resources(self) -> list[str]:
        return self.scripts + self.references + self.assets

    def _list_subdir(self, name: str) -> list[str]:
        d = self.path / name
        if not d.is_dir():
            return []
        return sorted(str(p.relative_to(self.path)) for p in d.rglob("*") if p.is_file())


class SkillCatalogEntry(BaseModel):
    """Lightweight entry for skill discovery (tier 1)."""

    name: str
    description: str
    path: Path
    fitness: float | None = None
    generation: int | None = None
    status: SkillStatus = "active"

    model_config = {"arbitrary_types_allowed": True}


class PopulationStatus(BaseModel):
    """Aggregate stats across all skills in a store."""

    total: int
    active: int
    retired: int
    archived: int
    mean_fitness: float | None = None
    median_fitness: float | None = None
    best: tuple[str, float] | None = None
    worst: tuple[str, float] | None = None
    total_generations: int = 0


# ---------------------------------------------------------------------------
# Eval
# ---------------------------------------------------------------------------


class EvalCase(BaseModel):
    """A single test case from evals/evals.json."""

    id: int
    prompt: str
    expected_output: str
    files: list[str] = Field(default_factory=list)
    assertions: list[str] = Field(default_factory=list)


class EvalSuite(BaseModel):
    """Full eval suite for a skill."""

    skill_name: str
    evals: list[EvalCase]


# ---------------------------------------------------------------------------
# Lineage
# ---------------------------------------------------------------------------


class LineageEntry(BaseModel):
    """One version in a skill's evolutionary history."""

    version: str
    timestamp: datetime
    origin: LineageOrigin
    parent: str | None = None
    mutation_type: str | None = None
    fitness: float | None = None
    status: SkillStatus = "candidate"


class SkillLineage(BaseModel):
    """Complete lineage record for a skill (.evolution/lineage.json)."""

    skill_id: str
    current_version: str
    created_at: datetime
    lineage: list[LineageEntry] = Field(default_factory=list)

    def get_entry(self, version: str) -> LineageEntry:
        for entry in self.lineage:
            if entry.version == version:
                return entry
        raise KeyError(f"Version {version!r} not found in lineage")


# ---------------------------------------------------------------------------
# Skill Containers
# ---------------------------------------------------------------------------


class ContainerSkillRef(BaseModel):
    """Canonical reference to one skill in a frozen container selection."""

    name: str
    version: str | None = None
    sha256: str | None = None

    @model_validator(mode="after")
    def validate_pin(self) -> ContainerSkillRef:
        if self.sha256 is not None:
            self.sha256 = self.sha256.lower()
            if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
                raise ValueError("sha256 must be a 64-character hexadecimal digest")
            if self.version is None:
                raise ValueError("sha256 requires a pinned version")
        return self

    def __str__(self) -> str:
        return f"{self.name}@{self.version}" if self.version else self.name


class SkillContainer(BaseModel):
    """Named group of skills used together when solving a task."""

    name: str
    description: str
    skills: list[str]  # ordered list; first = primary
    metadata: dict[str, str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) > NAME_MAX:
            raise ValueError(f"name must be ≤{NAME_MAX} chars, got {len(v)}")
        if "--" in v:
            raise ValueError("name must not contain consecutive hyphens")
        if not NAME_RE.match(v):
            raise ValueError(
                "name must be lowercase alphanumeric + hyphens, must not start/end with hyphen"
            )
        return v

    @field_validator("skills")
    @classmethod
    def validate_skills(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("container must have at least one skill")
        return v


# ---------------------------------------------------------------------------
# Skill Traces
# ---------------------------------------------------------------------------


class SkillTrace(BaseModel):
    """Record of a single skill usage."""

    id: str
    skill_name: str
    skill_version: str
    model: str
    task: str
    timestamp: datetime
    passed: int = 0
    total: int = 0
    pass_rate: float = 0.0
    success: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    time_ms: int = 0
    errors: list[str] = Field(default_factory=list)
    # Split manifest identity. Recorded so report tooling cannot silently mix
    # runs from different train/val/test partitions. Populated when the
    # solver is given a manifest via `solve_task(manifest=...)`.
    manifest_name: str | None = None
    manifest_sha: str | None = None
    manifest_scope: str | None = None  # "skill_evolution" | "dev" | "reporting"
    # Structured produce provenance (see CLAUDE.md Evidence & Reflection Contract).
    trace_context: dict | None = None
