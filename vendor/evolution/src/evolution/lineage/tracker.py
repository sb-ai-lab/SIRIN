"""Read and write .evolution/lineage.json."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from evolution.core.models import LineageEntry, Skill, SkillLineage
from evolution.lineage.state_io import atomic_write_json, skill_mutation_lock, transaction_lock
from evolution.lineage.version import VersionStore


class LineageError(RuntimeError):
    """Raised when .evolution/lineage.json exists but is malformed.

    The framework deliberately fails loud rather than silently fabricating
    lineage history (a research-artifact integrity invariant). Recovery is an
    explicit, user-invoked `evo skill repair <skill>`.
    """


class LineageTracker:
    """Manages the lineage record for a single skill."""

    def __init__(self, skill: Skill) -> None:
        self._skill = skill
        self._lineage_path = skill.path / ".evolution" / "lineage.json"
        self._lock_path = skill.path / ".evolution" / "lineage.lock"
        self._lineage: SkillLineage | None = None

    @property
    def lineage_path(self) -> Path:
        return self._lineage_path

    def _load(self) -> SkillLineage:
        if self._lineage is not None:
            return self._lineage

        if not self._lineage_path.exists():
            # Initialize empty lineage
            self._lineage = SkillLineage(
                skill_id=self._skill.name,
                current_version="v0",
                created_at=datetime.now(UTC),
                lineage=[],
            )
        else:
            try:
                self._lineage = SkillLineage.model_validate_json(
                    self._lineage_path.read_text(encoding="utf-8")
                )
            except (OSError, ValidationError) as exc:
                raise LineageError(
                    f"{self._skill.name}: .evolution/lineage.json is unreadable or malformed. "
                    f"Run `evo skill repair {self._skill.name}` to rebuild it from the "
                    f"on-disk version snapshots."
                ) from exc

        return self._lineage

    def _save(self) -> None:
        lin = self._load()
        self._lineage_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self._lineage_path, lin.model_dump(mode="json"))

    # --- Read ---

    @property
    def lineage(self) -> list[LineageEntry]:
        return self._load().lineage

    @property
    def current_version(self) -> str:
        return self._load().current_version

    def get_entry(self, version: str) -> LineageEntry:
        return self._load().get_entry(version)

    def promotion_count(self, version: str | None = None) -> int:
        """Count retained parent edges from *version* to its lineage root.

        Labels are identifiers, not maturity.  This deliberately follows the
        recorded parent links and rejects corrupt graph shapes before an editor
        can use an incorrect decay step.
        """
        lineage = self._load()
        active = version or lineage.current_version
        entries: dict[str, LineageEntry] = {}
        for entry in lineage.lineage:
            if entry.version in entries:
                raise LineageError(f"{self._skill.name}: duplicate lineage label {entry.version!r}")
            entries[entry.version] = entry
        count = 0
        seen: set[str] = set()
        while active in entries:
            if active in seen:
                raise LineageError(f"{self._skill.name}: lineage cycle at {active!r}")
            seen.add(active)
            entry = entries[active]
            parent = entry.parent
            if parent is None:
                break
            if parent not in entries and parent != "v0":
                raise LineageError(
                    f"{self._skill.name}: lineage parent {parent!r} for {active!r} is missing"
                )
            if entry.status != "rejected":
                count += 1
            active = parent
        return count

    retained_promotion_count = promotion_count

    # --- Write ---

    def record(self, entry: LineageEntry) -> None:
        """Append a lineage entry and persist."""
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            self._lineage = None
            lin = self._load()
            lin.lineage.append(entry)
            self._save()

    def promote(self, version: str, fitness: float | None = None) -> None:
        """Set *version* as active. Retire the previous active version.

        Also restores the version's complete managed tree (SKILL.md, scripts,
        references, and assets) so the active version is what gets used.
        """
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            self._lineage = None
            lin = self._load()
            target = lin.get_entry(version)
            previous_version = lin.current_version
            VersionStore(self._skill).restore(version)
            try:
                for entry in lin.lineage:
                    if entry.status == "active":
                        entry.status = "retired"
                target.status = "active"
                if fitness is not None:
                    target.fitness = fitness
                lin.current_version = version
                self._save()
            except Exception:
                persisted_version: str | None = None
                try:
                    persisted_version = SkillLineage.model_validate_json(
                        self._lineage_path.read_text(encoding="utf-8")
                    ).current_version
                except (OSError, ValidationError):
                    pass
                if persisted_version != version:
                    try:
                        VersionStore(self._skill).restore(previous_version)
                    except Exception as rollback_error:
                        raise LineageError(
                            f"Promotion of {version!r} failed and the previous managed tree "
                            f"could not be restored"
                        ) from rollback_error
                self._lineage = None
                raise

    def reject(self, version: str, fitness: float | None = None) -> None:
        """Mark version as rejected (δ-gated promotion declined; stays on disk)."""
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            self._lineage = None
            entry = self._load().get_entry(version)
            entry.status = "rejected"
            if fitness is not None:
                entry.fitness = fitness
            self._save()

    def delete_version(self, version: str, force: bool = False) -> None:
        """Delete a version from lineage and disk.

        Cannot delete active version. Cannot delete versions with children
        unless force=True (reparents children to deleted entry's parent).
        """
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            self._lineage = None
            lin = self._load()

            if lin.current_version == version:
                raise ValueError(
                    f"Cannot delete active version {version!r}. Promote another first."
                )

            target = lin.get_entry(version)
            parent = target.parent

            # Check for children
            children = [e.version for e in lin.lineage if e.parent == version]
            if children and not force:
                raise ValueError(
                    f"Version {version!r} has children: {', '.join(children)}. "
                    f"Use --force to delete and reparent."
                )

            # Reparent children to deleted entry's parent
            for entry in lin.lineage:
                if entry.parent == version:
                    entry.parent = parent

            lin.lineage = [e for e in lin.lineage if e.version != version]
            self._save()

            # Remove from disk
            from evolution.lineage.version import VersionStore

            vs = VersionStore(self._skill)
            vs.delete(version)

    def next_version_label(self) -> str:
        """Generate the next version label (v1, v2, v3, ...)."""
        lin = self._load()
        max_v = 0
        for entry in lin.lineage:
            v = entry.version
            if v.startswith("v") and v[1:].isdigit():
                max_v = max(max_v, int(v[1:]))
        return f"v{max_v + 1}"


def _natural_version_key(version: str) -> tuple[int, str]:
    """Sort ``v2`` before ``v10`` (numeric, not lexicographic)."""
    m = re.match(r"v(\d+)", version)
    return (int(m.group(1)) if m else 0, version)


def _coerce_dt(value: object) -> datetime | None:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def rebuild_lineage(skill: Skill) -> tuple[SkillLineage, list[str]]:
    """Reconstruct a valid ``SkillLineage`` from on-disk version snapshots.

    Provenance-light recovery: entries are ``origin="import"`` /
    ``mutation_type="recovered-from-disk"`` because the true mutation chain is
    unknowable from snapshots alone. Returns the rebuilt lineage plus
    human-readable notes (e.g. a remapped ``current_version``) for the caller
    to surface. Does not write — callers (``evo skill repair``) persist explicitly.
    """
    notes: list[str] = []
    evo_dir = skill.path / ".evolution"
    lineage_path = evo_dir / "lineage.json"

    partial: dict = {}
    if lineage_path.exists():
        try:
            loaded = json.loads(lineage_path.read_text(encoding="utf-8"))
            partial = loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, OSError):
            notes.append("existing lineage.json was unreadable; rebuilt from scratch")

    versions = sorted(VersionStore(skill).list_versions(), key=_natural_version_key)

    skill_id = partial.get("skill_id") or skill.name

    created_at = _coerce_dt(partial.get("created_at"))
    if created_at is None:
        if versions:
            first = evo_dir / "versions" / versions[0]
            created_at = datetime.fromtimestamp(first.stat().st_mtime, tz=UTC)
        else:
            created_at = datetime.now(UTC)

    requested = partial.get("current_version")
    if versions:
        if requested in versions:
            current = requested
        else:
            current = versions[-1]
            if requested:
                notes.append(
                    f"current_version {requested!r} has no snapshot on disk; "
                    f"remapped to {current!r}"
                )
            else:
                notes.append(f"no current_version recorded; set to {current!r}")
    else:
        current = requested or "v0"
        notes.append("no version snapshots on disk; lineage rebuilt empty")

    entries: list[LineageEntry] = []
    prev: str | None = None
    for v in versions:
        vdir = evo_dir / "versions" / v
        ts = datetime.fromtimestamp(vdir.stat().st_mtime, tz=UTC)
        entries.append(
            LineageEntry(
                version=v,
                timestamp=ts,
                origin="import",
                parent=prev,
                mutation_type="recovered-from-disk",
                status="active" if v == current else "retired",
            )
        )
        prev = v

    lineage = SkillLineage(
        skill_id=skill_id,
        current_version=current,
        created_at=created_at,
        lineage=entries,
    )
    return lineage, notes
