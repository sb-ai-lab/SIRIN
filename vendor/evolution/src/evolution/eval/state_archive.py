"""Pack a framework state tree into one archive + a loose reader-set.

``native_state_versions/<fw>/vN`` snapshots are consumed two ways: byte-restored
as the live framework store at final-eval/reselect time, and text-read by the
GUI diff / canonical export (``**/SKILL.md``, ``**/documents.json``). A full
``copytree`` per version costs (N+1)× the whole store in inodes; instead
``pack_state_tree`` writes ONE ``store.tar.zst`` holding the complete tree plus
loose copies of just the reader-set files, and ``unpack_state_tree`` restores
from the archive — or falls back to ``copytree`` for legacy full-copy dirs.
"""

from __future__ import annotations

import importlib.util
import logging
import shutil
import tarfile
from contextlib import contextmanager
from pathlib import Path

log = logging.getLogger(__name__)

STORE_ARCHIVE_NAMES = ("store.tar.zst", "store.tar.gz")
_LOOSE_KEEP_GLOBS = ("**/SKILL.md", "**/documents.json")


def _iter_tree_files(src: Path) -> list[Path]:
    return sorted(p for p in src.rglob("*") if p.is_file() or p.is_symlink())


@contextmanager
def _open_tar_write(archive: Path):
    if archive.name.endswith(".zst"):
        import zstandard

        cctx = zstandard.ZstdCompressor(level=10)
        with open(archive, "wb") as raw, cctx.stream_writer(raw) as comp:
            with tarfile.open(fileobj=comp, mode="w|") as tar:
                yield tar
    else:
        with tarfile.open(archive, mode="w:gz") as tar:
            yield tar


@contextmanager
def _open_tar_read(archive: Path):
    if archive.name.endswith(".zst"):
        import zstandard

        with open(archive, "rb") as raw:
            with zstandard.ZstdDecompressor().stream_reader(raw) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as tar:
                    yield tar
    else:
        with tarfile.open(archive, mode="r:gz") as tar:
            yield tar


def _archive_members(archive: Path) -> set[str]:
    with _open_tar_read(archive) as tar:
        return {m.name for m in tar if m.isfile() or m.issym()}


def find_store_archive(version_dir: Path) -> Path | None:
    for name in STORE_ARCHIVE_NAMES:
        candidate = Path(version_dir) / name
        if candidate.is_file():
            return candidate
    return None


def pack_state_tree(src: Path | str, dst_dir: Path | str) -> Path | None:
    """Snapshot ``src`` into ``dst_dir``: one store archive + loose reader-set.

    Verifies the archive member set round-trips before trusting it; on any
    failure removes partial output and returns None so the caller can fall
    back to a full copy (never silent data loss).
    """
    src = Path(src)
    dst_dir = Path(dst_dir)
    if not src.is_dir():
        return None
    files = _iter_tree_files(src)
    rels = [str(f.relative_to(src)) for f in files]

    has_zstd = importlib.util.find_spec("zstandard") is not None
    dst_dir.mkdir(parents=True, exist_ok=True)
    archive = dst_dir / (STORE_ARCHIVE_NAMES[0] if has_zstd else STORE_ARCHIVE_NAMES[1])
    try:
        with _open_tar_write(archive) as tar:
            for f, rel in zip(files, rels, strict=True):
                tar.add(f, arcname=rel)
        verified = _archive_members(archive) == set(rels)
    except Exception as exc:
        log.warning("pack_state_tree: archive of %s failed: %s", src, exc)
        verified = False

    if not verified:
        shutil.rmtree(dst_dir, ignore_errors=True)
        return None

    for pattern in _LOOSE_KEEP_GLOBS:
        for f in sorted(src.glob(pattern)):
            if not f.is_file():
                continue
            out = dst_dir / f.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out)
    return archive


def unpack_state_tree(version_dir: Path | str, dst: Path | str) -> bool:
    """Restore a state tree into ``dst`` (must not exist).

    New-format snapshot dirs restore from the store archive (byte-complete);
    legacy full-copy dirs restore via ``copytree`` — identical behavior.
    """
    version_dir = Path(version_dir)
    dst = Path(dst)
    if not version_dir.is_dir():
        return False
    archive = find_store_archive(version_dir)
    if archive is None:
        shutil.copytree(version_dir, dst, symlinks=False)
        return True

    dst.mkdir(parents=True, exist_ok=True)
    with _open_tar_read(archive) as tar:
        _extract_safe(tar, dst)
    return True


def _extract_safe(tar: tarfile.TarFile, dst: Path) -> None:
    for member in tar:
        name = member.name
        if name.startswith(("/", "..")) or ".." in Path(name).parts:
            raise ValueError(f"unsafe archive member: {name!r}")
        tar.extract(member, dst)
