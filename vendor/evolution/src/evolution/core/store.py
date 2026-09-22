"""Skill registry — discovers, indexes, and manages skills on disk."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import stat
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from evolution.core.models import (
    PopulationStatus,
    Skill,
    SkillCatalogEntry,
    SkillFrontmatter,
    SkillStatus,
)
from evolution.core.parser import load_skill, parse_skill_md, write_skill_md
from evolution.lineage.state_io import fsync_directory, skill_mutation_lock

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".evolution"}
_MAX_DEPTH = 4
SkillCatalog = list[SkillCatalogEntry]

logger = logging.getLogger(__name__)


class SkillStore:
    """Discover, index, and manage Agent Skills on the file system.

    Scan order (project-level overrides user-level):
      1. <project_dir>/.agents/skills/
      2. <user_dir>/.agents/skills/
      3. Any extra_dirs
    """

    def __init__(
        self,
        project_dir: str | Path | None = None,
        user_dir: str | Path | None = None,
        extra_dirs: list[Path] | None = None,
    ) -> None:
        self._scan_roots: list[Path] = []

        if project_dir is not None:
            p = Path(project_dir).resolve() / ".agents" / "skills"
            self._scan_roots.append(p)

        if user_dir is not None:
            u = Path(user_dir).expanduser().resolve() / ".agents" / "skills"
            self._scan_roots.append(u)

        if extra_dirs:
            self._scan_roots.extend(Path(d).resolve() for d in extra_dirs)

        # In-memory index: name -> catalog entry
        self._index: dict[str, SkillCatalogEntry] = {}

        self.discover()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self) -> SkillCatalog:
        """Scan all configured directories for skills. Rebuild index."""
        self._index.clear()

        for root in self._scan_roots:
            if not self._root_is_safe(root) or not root.is_dir():
                continue
            self._scan_dir(root, depth=0)

        return list(self._index.values())

    def _scan_dir(self, directory: Path, depth: int) -> None:
        if depth > _MAX_DEPTH or directory.is_symlink():
            return

        skill_md = directory / "SKILL.md"
        if skill_md.exists() or skill_md.is_symlink():
            try:
                _validate_skill_tree(directory)
            except ValueError as exc:
                logger.warning("Skipping unsafe skill at %s: %s", directory, exc)
                return
            self._index_skill(skill_md)
            return  # skill dirs aren't recursed further

        try:
            children = sorted(directory.iterdir())
        except PermissionError:
            return

        for child in children:
            if (
                not child.name.startswith(".")
                and not child.is_symlink()
                and child.is_dir()
                and child.name not in _SKIP_DIRS
            ):
                self._scan_dir(child, depth + 1)

    @staticmethod
    def _root_is_safe(root: Path) -> bool:
        return not root.is_symlink() and root.resolve(strict=False) == root

    def _index_skill(self, skill_md: Path) -> None:
        """Read frontmatter only (tier 1) and add to index."""
        try:
            raw_fm, _ = parse_skill_md(skill_md)
            fm = SkillFrontmatter.model_validate(raw_fm)
        except Exception as exc:
            # Loud-but-resilient: a malformed SKILL.md is dropped from the index
            # rather than aborting discovery, but never silently (repo rule).
            logger.warning("Skipping unparseable skill at %s: %s", skill_md.parent, exc)
            return

        # The skill's identity is its directory name, not the frontmatter
        # `name:`. import_skill writes each skill to ``root / skill_name`` and
        # callers/tasks address skills by that id. SB-Bench handcraft bodies
        # carry an unrelated upstream `name:` (e.g. ``sqlite-map-parser`` in
        # the ``sql`` skill dir); keying the index off the folder keeps the
        # store addressable by the id everything else uses, without rewriting
        # the canonical file (which would break base-seed hash integrity).
        name = skill_md.parent.name

        # Project-level (earlier in scan_roots) wins on collision
        if name in self._index:
            return

        fitness: float | None = None
        generation: int | None = None
        status: SkillStatus = "active"

        if fm.metadata:
            # Absent keys are normal (not every skill is evolved) and stay
            # silent; a present-but-malformed value is loud — it signals a
            # hand-edit that violated the "metadata values are strings" rule.
            if "evolution-fitness" in fm.metadata:
                try:
                    fitness = float(fm.metadata["evolution-fitness"])
                except (ValueError, TypeError):
                    logger.warning(
                        "Skill %s: ignoring malformed evolution-fitness %r",
                        name,
                        fm.metadata["evolution-fitness"],
                    )
            if "evolution-generation" in fm.metadata:
                try:
                    generation = int(fm.metadata["evolution-generation"])
                except (ValueError, TypeError):
                    logger.warning(
                        "Skill %s: ignoring malformed evolution-generation %r",
                        name,
                        fm.metadata["evolution-generation"],
                    )

        # Check lineage for status
        lineage_path = skill_md.parent / ".evolution" / "lineage.json"
        if lineage_path.exists():
            try:
                lin_data = json.loads(lineage_path.read_text())
                for entry in reversed(lin_data.get("lineage", [])):
                    if entry.get("status") == "active":
                        status = "active"
                        break
                    if entry.get("status") in ("retired", "archived"):
                        status = cast(SkillStatus, entry["status"])
                        break
            except Exception as exc:
                logger.warning(
                    "Skill %s: could not read lineage status from %s (defaulting to active): %s",
                    name,
                    lineage_path,
                    exc,
                )

        self._index[name] = SkillCatalogEntry(
            name=name,
            description=fm.description,
            path=skill_md.parent,
            fitness=fitness,
            generation=generation,
            status=status,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self, status: str | None = None) -> SkillCatalog:
        """Return catalog entries, optionally filtered by status."""
        entries = list(self._index.values())
        if status is not None:
            entries = [e for e in entries if e.status == status]
        return sorted(entries, key=lambda e: e.name)

    def get(self, name: str) -> Skill:
        """Load full skill by name. Raises KeyError if not found."""
        if name not in self._index:
            raise KeyError(f"Skill {name!r} not found in store")
        entry = self._index[name]
        return load_skill(entry.path)

    def has(self, name: str) -> bool:
        return name in self._index

    def search(self, query: str, limit: int = 5) -> SkillCatalog:
        """Keyword search over skill names and descriptions.

        Simple TF scoring: tokenize query -> count matches in name+description.
        """
        query_tokens = set(_tokenize(query.lower()))
        if not query_tokens:
            return []

        scored: list[tuple[float, SkillCatalogEntry]] = []
        for entry in self._index.values():
            doc_tokens = Counter(_tokenize(f"{entry.name} {entry.description}".lower()))
            score = sum(doc_tokens.get(t, 0) for t in query_tokens)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:limit]]

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        description: str,
        license: str | None = None,
        compatibility: str | None = None,
        metadata: dict[str, str] | None = None,
        scope: str = "project",
        from_file: Path | None = None,
        replace: bool = False,
    ) -> tuple[Skill, Skill | None]:
        """Scaffold a new skill directory with SKILL.md, evals/, and .evolution/.

        Args:
            from_file: Path to an existing SKILL.md to seed the new skill from.
                       When omitted a blank scaffold is written instead.
            replace:   When True and the skill directory already exists, rename
                       the old directory to ``{name}-deprecated-on-{YYYYMMDD-HHMM}``
                       before creating the new one. The deprecated copy is
                       re-indexed so it remains accessible via ``evo skill list``.
                       When False (default) a ``FileExistsError`` is raised if
                       the directory already exists.

        Returns:
            ``(new_skill, deprecated_skill)`` — ``deprecated_skill`` is ``None``
            when no existing directory was found.
        """
        # Determine root
        if scope == "user" and len(self._scan_roots) >= 2:
            root = self._scan_roots[1]
        elif self._scan_roots:
            root = self._scan_roots[0]
        else:
            raise RuntimeError("No scan roots configured — set project_dir or user_dir")
        if not self._root_is_safe(root):
            raise ValueError(f"Skill root must not contain symlinks: {root}")

        # Validate name via the model
        fm = SkillFrontmatter(
            name=name,
            description=description,
            license=license,
            compatibility=compatibility,
            metadata=metadata,
        )

        seed_file: Path | None = None
        if from_file is not None:
            seed_file = Path(from_file)
            if seed_file.is_symlink():
                raise ValueError(f"--from-file must not be a symlink: {seed_file}")
            if not seed_file.is_file():
                raise FileNotFoundError(f"--from-file path not found: {seed_file}")
            load_skill(seed_file, validate_dir_name=False)

        skill_dir = root / name
        deprecated_skill: Skill | None = None
        with skill_mutation_lock(skill_dir):
            if skill_dir.is_symlink():
                raise ValueError(f"Skill directory must not be a symlink: {skill_dir}")
            if skill_dir.exists():
                if not replace:
                    raise FileExistsError(f"Skill directory already exists: {skill_dir}")

            root.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=root))
            deprecated_dir: Path | None = None
            try:
                for subdir in ("scripts", "references", "assets"):
                    (staging / subdir).mkdir()

                if seed_file is not None:
                    shutil.copy2(seed_file, staging / "SKILL.md")
                else:
                    title = name.replace("-", " ").title()
                    body = (
                        f"# {title}\n\n"
                        f"## When to use this skill\n\n"
                        f"TODO: Describe when to use this skill.\n\n"
                        f"## Steps\n\n"
                        f"1. TODO: First step\n"
                        f"2. TODO: Second step\n"
                    )
                    write_skill_md(staging / "SKILL.md", fm, body)

                evals_dir = staging / "evals"
                evals_dir.mkdir()
                evals_data = {"skill_name": name, "evals": []}
                (evals_dir / "evals.json").write_text(
                    json.dumps(evals_data, indent=2), encoding="utf-8"
                )
                self._init_evolution(
                    staging,
                    name,
                    origin="import" if seed_file is not None else "manual",
                )

                if skill_dir.exists():
                    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M")
                    deprecated_dir = root / f"{name}-deprecated-on-{ts}"
                    skill_dir.rename(deprecated_dir)
                try:
                    staging.rename(skill_dir)
                    fsync_directory(root)
                except Exception:
                    if deprecated_dir is not None and not skill_dir.exists():
                        deprecated_dir.rename(skill_dir)
                        fsync_directory(root)
                    raise
                if deprecated_dir is not None:
                    deprecated_skill = load_skill(deprecated_dir)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)

        # Re-index
        self.discover()

        return load_skill(skill_dir), deprecated_skill

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_skill(
        self,
        source: str | Path,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
        scope: str = "project",
    ) -> Skill:
        """Import an existing skill from a directory or SKILL.md path.

        Copies SKILL.md + scripts/ + references/ + assets/ into the store,
        initializes .evolution/ with origin="import", and snapshots v1.

        Args:
            source: Path to a skill directory or SKILL.md file.
            name: Override skill name (default: use name from frontmatter).
            metadata: Extra metadata to merge into frontmatter.
            scope: 'project' or 'user'.

        Returns:
            The imported Skill.

        Raises:
            FileNotFoundError: if source SKILL.md doesn't exist.
            FileExistsError: if a skill with that name already exists.
        """
        source = Path(os.path.abspath(Path(source).expanduser()))
        if source.is_symlink():
            raise ValueError(f"Skill source must not be a symlink: {source}")
        if source.is_file():
            source_dir = source.parent
        else:
            source_dir = source

        skill_md_path = source_dir / "SKILL.md"
        if not skill_md_path.exists():
            raise FileNotFoundError(f"SKILL.md not found at {skill_md_path}")
        _validate_skill_tree(source_dir)

        # Parse source
        raw_fm, body = parse_skill_md(skill_md_path)
        if name is not None:
            raw_fm["name"] = name
        fm = SkillFrontmatter.model_validate(raw_fm)

        # Merge extra metadata
        if metadata:
            existing = fm.metadata or {}
            merged = {**existing, **metadata}
            fm = fm.model_copy(update={"metadata": merged})

        skill_name = fm.name

        # Determine destination root
        if scope == "user" and len(self._scan_roots) >= 2:
            root = self._scan_roots[1]
        elif self._scan_roots:
            root = self._scan_roots[0]
        else:
            raise RuntimeError("No scan roots configured — set project_dir or user_dir")
        if not self._root_is_safe(root):
            raise ValueError(f"Skill root must not contain symlinks: {root}")

        dest_dir = root / skill_name
        if dest_dir.exists():
            raise FileExistsError(f"Skill {skill_name!r} already exists at {dest_dir}")

        with skill_mutation_lock(dest_dir):
            if dest_dir.exists() or dest_dir.is_symlink():
                raise FileExistsError(f"Skill {skill_name!r} already exists at {dest_dir}")
            root.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=f".{skill_name}-", dir=root))
            try:
                write_skill_md(staging / "SKILL.md", fm, body)
                for subdir in ("scripts", "references", "assets"):
                    src_sub = source_dir / subdir
                    if src_sub.is_dir() and any(src_sub.iterdir()):
                        shutil.copytree(src_sub, staging / subdir)

                evals_dir = staging / "evals"
                evals_dir.mkdir()
                (evals_dir / "evals.json").write_text(
                    json.dumps({"skill_name": skill_name, "evals": []}, indent=2),
                    encoding="utf-8",
                )
                self._init_evolution(staging, skill_name, origin="import")
                staging.rename(dest_dir)
                fsync_directory(root)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)

        # Re-index
        self.discover()

        return load_skill(dest_dir)

    def _init_evolution(
        self,
        skill_dir: Path,
        skill_name: str,
        origin: str = "manual",
    ) -> None:
        """Create .evolution/ with lineage.json and a v1 snapshot."""
        evo_dir = skill_dir / ".evolution"
        evo_dir.mkdir(exist_ok=True)

        now = datetime.now(UTC).isoformat()
        lineage_data = {
            "skill_id": skill_name,
            "current_version": "v1",
            "created_at": now,
            "lineage": [
                {
                    "version": "v1",
                    "timestamp": now,
                    "origin": origin,
                    "parent": None,
                    "fitness": None,
                    "status": "active",
                }
            ],
        }
        (evo_dir / "lineage.json").write_text(json.dumps(lineage_data, indent=2), encoding="utf-8")
        # Snapshot v1
        v1_dir = evo_dir / "versions" / "v1"
        v1_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_dir / "SKILL.md", v1_dir / "SKILL.md")
        for subdir in ("scripts", "references", "assets"):
            src_sub = skill_dir / subdir
            if src_sub.is_dir() and any(src_sub.iterdir()):
                shutil.copytree(src_sub, v1_dir / subdir)

    def population_status(self) -> PopulationStatus:
        """Aggregate stats across all skills."""
        entries = list(self._index.values())
        if not entries:
            return PopulationStatus(total=0, active=0, retired=0, archived=0)

        active = [e for e in entries if e.status == "active"]
        retired = [e for e in entries if e.status == "retired"]
        archived = [e for e in entries if e.status == "archived"]

        fitnesses = sorted([e.fitness for e in entries if e.fitness is not None])

        mean_f = sum(fitnesses) / len(fitnesses) if fitnesses else None
        median_f = fitnesses[len(fitnesses) // 2] if fitnesses else None

        best = (
            max(
                ((e.name, e.fitness) for e in entries if e.fitness is not None),
                key=lambda x: x[1],
            )
            if fitnesses
            else None
        )
        worst = (
            min(
                ((e.name, e.fitness) for e in entries if e.fitness is not None),
                key=lambda x: x[1],
            )
            if fitnesses
            else None
        )

        total_gens = sum(e.generation or 0 for e in entries)

        return PopulationStatus(
            total=len(entries),
            active=len(active),
            retired=len(retired),
            archived=len(archived),
            mean_fitness=mean_f,
            median_fitness=median_f,
            best=best,
            worst=worst,
            total_generations=total_gens,
        )


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase tokens (alphanumeric + hyphens)."""
    return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", text)


def _validate_skill_tree(skill_dir: Path) -> None:
    """Reject links and special files from the managed part of a skill."""

    try:
        root_mode = skill_dir.lstat().st_mode
    except OSError as exc:
        raise ValueError(f"Cannot inspect skill directory: {skill_dir}") from exc
    if stat.S_ISLNK(root_mode) or not stat.S_ISDIR(root_mode):
        raise ValueError(f"Skill directory must be a real directory: {skill_dir}")

    stack = [skill_dir / "SKILL.md"]
    stack.extend(skill_dir / name for name in ("scripts", "references", "assets"))

    while stack:
        path = stack.pop()
        if not path.exists() and not path.is_symlink():
            continue
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise ValueError(f"Cannot inspect managed skill path: {path}") from exc
        if stat.S_ISLNK(mode):
            raise ValueError(f"Managed skill path must not be a symlink: {path}")
        if stat.S_ISDIR(mode):
            try:
                stack.extend(path.iterdir())
            except OSError as exc:
                raise ValueError(f"Cannot inspect managed skill directory: {path}") from exc
        elif not stat.S_ISREG(mode):
            raise ValueError(f"Managed skill path must be a regular file or directory: {path}")
