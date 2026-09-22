"""Container store — manages named groups of skills."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter, ValidationError

from evolution.core.models import NAME_MAX, NAME_RE, ContainerSkillRef, Skill, SkillContainer
from evolution.lineage.state_io import (
    atomic_write_json,
    atomic_write_text,
    fsync_directory,
    transaction_lock,
)

ContainerCatalog = list[SkillContainer]
ContainerLineage = list[dict[str, Any]]
SkillList = list[Skill]
SkillNames = list[str]
SkillRefs = list[ContainerSkillRef]

_CONTAINER_LINEAGE_ADAPTER = TypeAdapter(ContainerLineage)
_SKILL_REFS_ADAPTER = TypeAdapter(list[ContainerSkillRef])

logger = logging.getLogger(__name__)


class ContainerLineageError(RuntimeError):
    """Raised when persisted container snapshot history cannot be trusted."""


class ContainerStore:
    """Discover, manage, and resolve skill containers.

    Containers are YAML files in .agents/containers/ directories.
    Scan order matches SkillStore: project-level, then user-level.
    """

    def __init__(
        self,
        project_dir: str | Path | None = None,
        user_dir: str | Path | None = None,
    ) -> None:
        self._scan_roots: list[Path] = []

        if project_dir is not None:
            p = Path(project_dir).resolve() / ".agents" / "containers"
            self._scan_roots.append(p)

        if user_dir is not None:
            u = Path(user_dir).expanduser().resolve() / ".agents" / "containers"
            self._scan_roots.append(u)

        self._index: dict[str, SkillContainer] = {}
        self.discover()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self) -> ContainerCatalog:
        """Scan all configured directories for containers. Rebuild index."""
        self._index.clear()

        for root in self._scan_roots:
            if not self._root_is_safe(root) or not root.is_dir():
                continue
            for f in sorted(root.iterdir()):
                if f.suffix in (".yaml", ".yml") and f.is_file():
                    self._index_container(f)

        return list(self._index.values())

    def _index_container(self, path: Path) -> None:
        """Parse a container YAML file and add to index."""
        try:
            container = self._read_yaml(path)
        except Exception as exc:
            logger.warning("Skipping unparseable container %s: %s", path.name, exc)
            return

        # Project-level wins on name collision
        if container.name not in self._index:
            self._index[container.name] = container

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list(self) -> ContainerCatalog:
        """Return all containers sorted by name."""
        return sorted(self._index.values(), key=lambda c: c.name)

    def get(self, name: str) -> SkillContainer:
        """Get a container by name. Raises KeyError if not found."""
        if name not in self._index:
            raise KeyError(f"Container {name!r} not found")
        return self._index[name]

    def has(self, name: str) -> bool:
        return name in self._index

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        description: str,
        skills: SkillNames,
        metadata: dict[str, str] | None = None,
    ) -> SkillContainer:
        """Create a new container YAML file."""
        container = SkillContainer(
            name=name,
            description=description,
            skills=skills,
            metadata=metadata,
        )

        root = self._write_root()
        with transaction_lock(self._catalog_lock_path(root)):
            self.discover()
            paths = [root / f"{name}{extension}" for extension in (".yaml", ".yml")]
            if self.has(name) or any(path.exists() or path.is_symlink() for path in paths):
                raise FileExistsError(f"Container {name!r} already exists")
            self._write_yaml(paths[0], container)
        self.discover()
        return container

    def update(
        self,
        name: str,
        description: str | None = None,
        skills: SkillNames | None = None,
        metadata: dict[str, str] | None = None,
    ) -> SkillContainer:
        """Update an existing container."""
        path = self._find_file(name)
        with transaction_lock(self._catalog_lock_path(path.parent)):
            path = self._find_file_in_root(path.parent, name)
            container = self._read_yaml(path)
            updates: dict = {}
            if description is not None:
                updates["description"] = description
            if skills is not None:
                updates["skills"] = skills
            if metadata is not None:
                updates["metadata"] = {**(container.metadata or {}), **metadata}
            updated = SkillContainer.model_validate({**container.model_dump(), **updates})
            self._write_yaml(path, updated)
        self.discover()
        return updated

    def delete(self, name: str) -> None:
        """Delete a container YAML file."""
        path = self._find_file(name)
        with transaction_lock(self._catalog_lock_path(path.parent)):
            path = self._find_file_in_root(path.parent, name)
            path.unlink()
            fsync_directory(path.parent)
        self.discover()

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def skill_refs(
        self,
        name: str,
        snapshot_label: str | None = None,
    ) -> SkillRefs:
        """Return ordered live names or exact references from a snapshot."""

        container = self.get(name)
        if snapshot_label is None:
            return [ContainerSkillRef(name=skill_name) for skill_name in container.skills]

        for entry in self._load_lineage(name):
            if entry.get("label") != snapshot_label:
                continue
            raw_refs = entry.get("skill_refs")
            if isinstance(raw_refs, list):
                return [ContainerSkillRef.model_validate(ref) for ref in raw_refs]

            # Older snapshots stored only an insertion-ordered {name: version} map.
            versions = entry.get("skills")
            if not isinstance(versions, dict):
                raise ValueError(f"Snapshot {snapshot_label!r} has invalid skill data")
            return [
                ContainerSkillRef(
                    name=skill_name,
                    version=raw.get("version"),
                    sha256=raw.get("sha256"),
                )
                if isinstance(raw, dict)
                else ContainerSkillRef(name=skill_name, version=str(raw))
                for skill_name, raw in versions.items()
            ]
        raise KeyError(f"Snapshot {snapshot_label!r} not found for container {name!r}")

    def resolve(
        self,
        name: str,
        skill_store,
        snapshot_label: str | None = None,
    ) -> SkillList:
        """Load all skills from a container.

        Args:
            name: Container name.
            skill_store: A SkillStore instance to load skills from.
            snapshot_label: If given, load skill versions from this snapshot
                instead of current active versions.

        Returns:
            Ordered list of Skill objects.

        Raises:
            KeyError: if container, snapshot, or any skill not found.
        """
        from evolution.lineage.version import VersionStore

        result: SkillList = []
        for ref in self.skill_refs(name, snapshot_label=snapshot_label):
            owner = skill_store.get(ref.name)
            versions = VersionStore(owner)
            selected = versions.load(ref.version) if ref.version else owner
            if ref.sha256 is not None:
                assert ref.version is not None
                actual = versions.digest(ref.version)
                if actual != ref.sha256:
                    raise ValueError(
                        f"Skill {ref.name!r} version {ref.version!r} hash mismatch: "
                        f"expected {ref.sha256}, got {actual}"
                    )
            result.append(selected)
        return result

    def _get_snapshot_skills(self, name: str, label: str) -> dict[str, str]:
        """Get {skill_name: version} from a snapshot."""
        return {ref.name: ref.version or "" for ref in self.skill_refs(name, label)}

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def _lineage_path(self, name: str) -> Path:
        root = self._write_root()
        d = root / ".evolution"
        if d.is_symlink() or not d.resolve(strict=False).is_relative_to(root):
            raise ValueError(f"Container lineage directory escapes its root: {d}")
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{name}.json"
        if path.is_symlink() or not path.resolve(strict=False).is_relative_to(d):
            raise ValueError(f"Container lineage file escapes its root: {path}")
        return path

    def _load_lineage(self, name: str) -> ContainerLineage:
        """Load snapshot history for a container. Returns [] if none."""
        p = self._lineage_path(name)
        if not p.exists():
            return []
        try:
            entries = _CONTAINER_LINEAGE_ADAPTER.validate_json(p.read_text(encoding="utf-8"))
            for entry in entries:
                if not isinstance(entry.get("label"), str):
                    raise ValueError("snapshot label must be a string")
                refs = entry.get("skill_refs")
                legacy = entry.get("skills")
                if refs is not None:
                    _SKILL_REFS_ADAPTER.validate_python(refs)
                elif not isinstance(legacy, dict) or not all(
                    isinstance(skill_name, str)
                    and (
                        isinstance(pin, str)
                        or isinstance(pin, dict)
                        and isinstance(pin.get("version"), str)
                    )
                    for skill_name, pin in legacy.items()
                ):
                    raise ValueError("snapshot skills must be pinned by name")
            return entries
        except (OSError, ValidationError, ValueError) as exc:
            raise ContainerLineageError(
                f"Container {name!r} snapshot lineage is unreadable or malformed: {p}"
            ) from exc

    def _save_lineage(self, name: str, entries: ContainerLineage) -> None:
        atomic_write_json(self._lineage_path(name), entries)

    def _lineage_lock_path(self, name: str) -> Path:
        path = self._lineage_path(name).with_suffix(".lock")
        if path.is_symlink():
            raise ValueError(f"Container lineage lock must not be a symlink: {path}")
        return path

    def snapshots(self, name: str) -> ContainerLineage:
        """Return snapshot history for a container."""
        if not self.has(name):
            raise KeyError(f"Container {name!r} not found")
        return self._load_lineage(name)

    def snapshot(self, name: str, message: str, skill_store=None) -> str:
        """Record a snapshot of current skill versions used by this container.

        Reads each skill's current active version from LineageTracker and
        appends a timestamped entry to the snapshot log. Returns the label.
        """
        if skill_store is None:
            raise ValueError("skill_store is required to create an exact container snapshot")

        path = self._find_file(name)
        with (
            transaction_lock(self._catalog_lock_path(path.parent)),
            transaction_lock(self._lineage_lock_path(name)),
        ):
            path = self._find_file_in_root(path.parent, name)
            container = self._read_yaml(path)
            entries = self._load_lineage(name)
            max_v = max(
                (
                    int(label[1:])
                    for entry in entries
                    if (label := entry.get("label", "")).startswith("s") and label[1:].isdigit()
                ),
                default=0,
            )
            label = f"s{max_v + 1}"

            from evolution.lineage.tracker import LineageTracker
            from evolution.lineage.version import VersionStore

            skill_refs: list[dict[str, str]] = []
            for skill_name in container.skills:
                skill = skill_store.get(skill_name)
                version = LineageTracker(skill).current_version
                versions = VersionStore(skill)
                if not versions.exists(version):
                    raise KeyError(
                        f"Skill {skill_name!r} active version {version!r} has no saved snapshot"
                    )
                skill_refs.append(
                    ContainerSkillRef(
                        name=skill_name,
                        version=version,
                        sha256=versions.digest(version),
                    ).model_dump(exclude_none=True)
                )

            entries.append(
                {
                    "label": label,
                    "message": message,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "skill_refs": skill_refs,
                }
            )
            self._save_lineage(name, entries)
            return label

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_root(self) -> Path:
        """First scan root (project-level preferred)."""
        if not self._scan_roots:
            raise RuntimeError("No scan roots configured")
        root = self._scan_roots[0]
        if not self._root_is_safe(root):
            raise ValueError(f"Container root must not contain symlinks: {root}")
        return root

    def _find_file(self, name: str) -> Path:
        """Find the YAML file for a container by name."""
        for root in self._scan_roots:
            try:
                return self._find_file_in_root(root, name)
            except KeyError:
                continue
        raise KeyError(f"Container file not found for {name!r}")

    @staticmethod
    def _find_file_in_root(root: Path, name: str) -> Path:
        if len(name) > NAME_MAX or "--" in name or not NAME_RE.fullmatch(name):
            raise ValueError(f"Invalid container name: {name!r}")
        if not ContainerStore._root_is_safe(root):
            raise ValueError(f"Container root must not contain symlinks: {root}")
        for extension in (".yaml", ".yml"):
            path = root / f"{name}{extension}"
            if not path.resolve(strict=False).is_relative_to(root):
                raise ValueError(f"Container path escapes its root: {path}")
            if path.is_file() and not path.is_symlink():
                return path
        raise KeyError(f"Container file not found for {name!r}")

    @staticmethod
    def _root_is_safe(root: Path) -> bool:
        return not root.is_symlink() and root.resolve(strict=False) == root

    @staticmethod
    def _catalog_lock_path(root: Path) -> Path:
        return root / ".catalog.lock"

    @staticmethod
    def _read_yaml(path: Path) -> SkillContainer:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Container file must be a regular file: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Container file must contain a YAML mapping: {path}")
        return SkillContainer.model_validate(data)

    @staticmethod
    def _write_yaml(path: Path, container: SkillContainer) -> None:
        """Write container to YAML."""
        data: dict = {
            "name": container.name,
            "description": container.description,
            "skills": container.skills,
        }
        if container.metadata:
            data["metadata"] = container.metadata
        atomic_write_text(
            path,
            yaml.dump(data, default_flow_style=False, allow_unicode=True),
        )
