"""Store and retrieve skill version snapshots."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from collections.abc import Iterable
from pathlib import Path

from evolution.core.models import Skill
from evolution.core.parser import load_skill
from evolution.lineage.state_io import fsync_directory, skill_mutation_lock, transaction_lock

_MANAGED_ENTRIES = ("SKILL.md", "scripts", "references", "assets")


class VersionIntegrityError(RuntimeError):
    """Raised when a version tree contains an unsafe or unsupported entry."""


def hash_tree(root: Path) -> str:
    """Return a deterministic SHA-256 digest of a complete directory tree.

    Relative paths, entry kinds, executable bits, and file bytes are covered.
    Symlinks and special files are rejected so a snapshot cannot hash content
    outside its own tree or change meaning when restored elsewhere.
    """

    tree = Path(root)
    if tree.is_symlink() or not tree.is_dir():
        raise VersionIntegrityError(f"Version tree must be a real directory: {tree}")
    return _hash_paths(tree, tree.rglob("*"))


def hash_managed_tree(root: Path) -> str:
    """Hash only SKILL.md and the scripts, references, and assets trees."""

    tree = Path(root)
    skill_md = tree / "SKILL.md"
    if tree.is_symlink() or not tree.is_dir() or not skill_md.is_file() or skill_md.is_symlink():
        raise VersionIntegrityError(f"Managed tree must contain a safe SKILL.md: {tree}")
    paths: list[Path] = [skill_md]
    for name in _MANAGED_ENTRIES[1:]:
        entry = tree / name
        if entry.exists() or entry.is_symlink():
            paths.append(entry)
            if entry.is_dir() and not entry.is_symlink():
                paths.extend(entry.rglob("*"))
    return _hash_paths(tree, paths)


def _hash_paths(root: Path, paths: Iterable[Path]) -> str:
    digest = hashlib.sha256(b"evolution-version-tree-v1\0")
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise VersionIntegrityError(f"Symlink is not allowed in a version tree: {path}")
        if stat.S_ISDIR(info.st_mode):
            digest.update(b"D\0" + rel + b"\0")
            continue
        if not stat.S_ISREG(info.st_mode):
            raise VersionIntegrityError(f"Special file is not allowed in a version tree: {path}")
        digest.update(b"F\0" + rel + b"\0")
        digest.update(str(info.st_mode & 0o111).encode("ascii") + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


class VersionStore:
    """Manages version snapshots in .evolution/versions/.

    Layout:
        .evolution/versions/
        ├── v1/
        │   ├── SKILL.md
        │   └── scripts/...
        ├── v2/
        │   └── SKILL.md
    """

    def __init__(self, skill: Skill) -> None:
        self._skill = skill
        self._versions_dir = skill.path / ".evolution" / "versions"
        self._lock_path = skill.path / ".evolution" / "version.lock"
        self._versions_dir.mkdir(parents=True, exist_ok=True)

    @property
    def versions_dir(self) -> Path:
        return self._versions_dir

    def save(self, version: str) -> Path:
        """Snapshot this skill under the given version label."""
        dest = self._version_dir(version)

        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            if dest.exists():
                raise FileExistsError(f"Version {version!r} already exists")

            with tempfile.TemporaryDirectory(prefix=f".{version}-", dir=self._versions_dir) as tmp:
                staging = Path(tmp)
                self._copy_managed_tree(self._skill.path, staging)
                hash_tree(staging)
                staging.rename(dest)
                fsync_directory(self._versions_dir)

        return dest

    def load(self, version: str) -> Skill:
        """Load a historical version as a Skill object.

        Raises KeyError if the version doesn't exist.
        """
        version_dir = self._version_dir(version)
        if not version_dir.exists():
            raise KeyError(f"Version {version!r} not found")
        hash_tree(version_dir)
        return load_skill(version_dir, validate_dir_name=False)

    def digest(self, version: str) -> str:
        """Return the deterministic full-tree digest for a stored version."""

        version_dir = self._version_dir(version)
        if not version_dir.exists():
            raise KeyError(f"Version {version!r} not found")
        return hash_managed_tree(version_dir)

    def restore(self, version: str) -> None:
        """Restore SKILL.md and all managed resource trees from *version*.

        Stale resource files are removed. ``.evolution``, ``.traces``, evals,
        and other live metadata remain untouched. The incoming tree is fully
        staged and verified before any live entry is swapped.
        """

        source = self._version_dir(version)
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            if not source.exists():
                raise KeyError(f"Version {version!r} not found")
            source_digest = hash_tree(source)
            evolution_dir = self._skill.path / ".evolution"
            with tempfile.TemporaryDirectory(prefix=".restore-", dir=evolution_dir) as tmp:
                transaction_dir = Path(tmp)
                incoming = transaction_dir / "incoming"
                backup = transaction_dir / "backup"
                incoming.mkdir()
                backup.mkdir()
                self._copy_managed_tree(source, incoming)
                if hash_tree(incoming) != source_digest:
                    raise VersionIntegrityError(
                        f"Staged restore of version {version!r} failed integrity verification"
                    )
                self._swap_managed_tree(incoming, backup)

    def list_versions(self) -> list[str]:
        """All stored version labels, sorted alphabetically."""
        if not self._versions_dir.exists():
            return []
        return sorted(
            d.name for d in self._versions_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
        )

    def delete(self, version: str) -> None:
        """Remove a version snapshot."""
        version_dir = self._version_dir(version)
        with skill_mutation_lock(self._skill.path), transaction_lock(self._lock_path):
            if version_dir.exists():
                shutil.rmtree(version_dir)
                fsync_directory(self._versions_dir)

    def exists(self, version: str) -> bool:
        return (self._version_dir(version) / "SKILL.md").exists()

    def _version_dir(self, version: str) -> Path:
        if not version or Path(version).name != version or version in {".", ".."}:
            raise ValueError(f"Invalid version label: {version!r}")
        return self._versions_dir / version

    @staticmethod
    def _copy_managed_tree(source: Path, destination: Path) -> None:
        skill_md = source / "SKILL.md"
        if not skill_md.is_file() or skill_md.is_symlink():
            raise VersionIntegrityError(f"Version tree has no safe SKILL.md: {source}")
        shutil.copy2(skill_md, destination / "SKILL.md")
        for subdir in _MANAGED_ENTRIES[1:]:
            src_dir = source / subdir
            if src_dir.is_symlink():
                raise VersionIntegrityError(f"Symlink is not allowed in a version tree: {src_dir}")
            if src_dir.is_dir():
                shutil.copytree(src_dir, destination / subdir, symlinks=True)

    def _swap_managed_tree(self, incoming: Path, backup: Path) -> None:
        moved_old: list[str] = []
        installed: list[str] = []
        try:
            for name in _MANAGED_ENTRIES:
                live = self._skill.path / name
                old = backup / name
                new = incoming / name
                if live.exists() or live.is_symlink():
                    os.replace(live, old)
                    moved_old.append(name)
                if new.exists():
                    os.replace(new, live)
                    installed.append(name)
            fsync_directory(self._skill.path)
        except Exception:
            for name in reversed(installed):
                live = self._skill.path / name
                if live.is_dir() and not live.is_symlink():
                    shutil.rmtree(live)
                else:
                    live.unlink(missing_ok=True)
            for name in reversed(moved_old):
                os.replace(backup / name, self._skill.path / name)
            fsync_directory(self._skill.path)
            raise
