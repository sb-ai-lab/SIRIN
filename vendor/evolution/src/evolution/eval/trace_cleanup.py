"""Path-scoped bulk purge + debug-text archive for solve/eval leaf dirs.

A per-solve/per-eval leaf directory splits into reproducible BULK (the
materialized corpus ``workspace`` + FS-guard scaffolding + native eval-home
copies) and a small keep-set (``prompt.md``/``response.md``/``solve.py``/
``pytest.log`` debug text, ``result.json``, ``bundle.json``). Deleting only the
BULK after a solve's outputs are captured reclaims the inodes that exhaust the
shared NFS volume, while leaving every machine-read and human-debug artifact
intact.

The purge is strictly PATH-SCOPED to the named direct children of a leaf, so a
directory named ``workspace`` nested inside kept state (e.g. Memento's evolved
skill at ``native_state/.../memento_s/workspace/``) is never touched.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path

log = logging.getLogger(__name__)

# Direct children of a solve/eval leaf that hold reproducible BULK.
BULK_LEAF_DIRS = (
    "workspace",
    "_workspace_guard_bin",
    "_workspace_guard_py",
    "_solve_home",
    ".datagen_home",
    "_memento_eval_home",
    "_memp_eval_memory",
    "_hermes_home",
)

# Corpus + scaffolding subdirs of a solve WORKSPACE whose debug keep-set
# (prompt/response/solve/pytest logs), produced ``output/``, and test files all
# sit at the workspace root — so only these named bulk subdirs are reclaimed,
# never the workspace root itself.
WORKSPACE_BULK_DIRS = (
    "environment",
    "inputs",
    "source_artifacts",
    ".venv",
    "_solve_home",
    "_workspace_guard_bin",
    "_workspace_guard_py",
)

_rmtree_failures = 0


def keep_cell_traces() -> bool:
    """Opt-out switch: ``EVO_KEEP_CELL_TRACES=1`` disables all bulk purging."""
    return os.environ.get("EVO_KEEP_CELL_TRACES", "0") == "1"


def rmtree_failure_count() -> int:
    """Total NFS-remnant rmtree failures observed this process (observability)."""
    return _rmtree_failures


def _rmtree_onerror(func, failed_path, _exc_info) -> None:
    """Make read-only entries (e.g. quarantined corpus bases) deletable, then retry."""
    os.chmod(failed_path, 0o700)
    parent = os.path.dirname(failed_path)
    if parent:
        os.chmod(parent, 0o700)
    func(failed_path)


def _rmtree_counted(path: Path) -> bool:
    global _rmtree_failures
    for attempt in range(1, 6):
        try:
            shutil.rmtree(path, onerror=_rmtree_onerror)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            if attempt == 5:
                _rmtree_failures += 1
                log.warning(
                    "trace_cleanup: rmtree failed (NFS remnant?) total_failures=%d path=%s",
                    _rmtree_failures,
                    path,
                )
                return False
            time.sleep(0.1 * attempt)
    return False


def purge_leaf_bulk(cache_dir: Path | str | None) -> int:
    """Delete the reproducible BULK dirs directly under one solve/eval leaf.

    Removes only the :data:`BULK_LEAF_DIRS` direct children of ``cache_dir`` —
    never recursing by name — so kept state trees that happen to contain a
    ``workspace`` dir are untouched. No-op when ``EVO_KEEP_CELL_TRACES=1`` or
    ``cache_dir`` is falsy/missing. Returns the count of dirs removed.
    """
    if not cache_dir or keep_cell_traces():
        return 0
    leaf = Path(cache_dir)
    if not leaf.is_dir():
        return 0
    removed = 0
    for name in BULK_LEAF_DIRS:
        target = leaf / name
        if target.is_dir() and _rmtree_counted(target):
            removed += 1
    return removed


# Human-debug TEXT filenames collapsed into the per-cell archive. Machine-read
# artifacts (bundle.json, cell_metrics.json, native_state/, …) are never listed.
_DEBUG_TEXT_NAMES = frozenset(
    {
        "prompt.md",
        "response.md",
        "response_retry.md",
        "solve.py",
        "prompt_audit.json",
        "_prompt.md",
        "_response.md",
        "_response_retry.md",
        "_solve.py",
        "pytest_output.txt",
        "_pytest_output.txt",
        "solve_run.log",
        "solve_output.txt",
        "_solve_output.txt",
        "workspace_guard.jsonl",
        ".workspace_guard.jsonl",
    }
)
# Subtrees never walked for debug text: evolved-skill state + kept rollup trees.
_ARCHIVE_EXCLUDE_DIRS = frozenset(
    {"native_state", "native_state_versions", "skills", "rounds", ".git"}
)


def _is_debug_text(name: str) -> bool:
    return name in _DEBUG_TEXT_NAMES or (name.startswith("pytest") and name.endswith(".log"))


def _iter_debug_text_files(cell_dir: Path):
    for root, dirs, files in os.walk(cell_dir):
        dirs[:] = [d for d in dirs if d not in _ARCHIVE_EXCLUDE_DIRS]
        for name in files:
            if _is_debug_text(name):
                yield Path(root) / name


def _archive_member_names(archive: Path, use_zstd: bool) -> set[str]:
    import tarfile

    if use_zstd:
        import zstandard

        with open(archive, "rb") as raw:
            with zstandard.ZstdDecompressor().stream_reader(raw) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as tar:
                    return {m.name for m in tar}
    with tarfile.open(archive, mode="r:gz") as tar:
        return set(tar.getnames())


def archive_cell_debug_text(cell_dir: Path | str | None) -> Path | None:
    """Collapse per-solve human-debug TEXT under ``cell_dir`` into one tarball.

    Walks ``cell_dir`` (skipping :data:`_ARCHIVE_EXCLUDE_DIRS`), tars the
    :func:`_is_debug_text` files into ``cell_traces.tar.zst`` (zstd; ``.tar.gz``
    fallback), verifies the member set round-trips, then deletes the originals —
    turning many tiny debug inodes into one. Machine-read artifacts
    (``bundle.json``, rollups, ``native_state/``) are never touched. No-op under
    ``EVO_KEEP_CELL_TRACES=1``, a missing dir, or nothing to archive. Returns the
    archive path or ``None``.
    """
    if not cell_dir or keep_cell_traces():
        return None
    cell = Path(cell_dir)
    if not cell.is_dir():
        return None
    files = sorted(_iter_debug_text_files(cell))
    if not files:
        return None

    import tarfile

    try:
        import zstandard
    except Exception:
        use_zstd = False
    else:
        use_zstd = True

    archive = cell / ("cell_traces.tar.zst" if use_zstd else "cell_traces.tar.gz")
    rels = [str(f.relative_to(cell)) for f in files]
    try:
        if use_zstd:
            import zstandard

            cctx = zstandard.ZstdCompressor(level=10)
            with open(archive, "wb") as raw, cctx.stream_writer(raw) as comp:
                with tarfile.open(fileobj=comp, mode="w|") as tar:
                    for f, rel in zip(files, rels, strict=True):
                        tar.add(f, arcname=rel)
        else:
            with tarfile.open(archive, mode="w:gz") as tar:
                for f, rel in zip(files, rels, strict=True):
                    tar.add(f, arcname=rel)
        verified = _archive_member_names(archive, use_zstd) == set(rels)
    except OSError as exc:
        log.warning("archive_cell_debug_text: write/verify failed; keeping originals: %s", exc)
        verified = False

    if not verified:
        try:
            archive.unlink()
        except OSError:
            pass
        return None

    for f in files:
        try:
            f.unlink()
        except OSError:
            pass
    return archive


def purge_workspace_bulk(workspace: Path | str | None) -> int:
    """Reclaim reproducible corpus + scaffolding from a solve workspace in place.

    Deletes only the :data:`WORKSPACE_BULK_DIRS` subdirs (the staged corpus, the
    overlay ``.venv``, and the FS-guard scaffolding) plus any ``__pycache__`` and
    the ``_hidden_tests__<ws>`` sibling — while keeping the debug keep-set
    (``_prompt.md``/``_response.md``/``_solve.py``/``pytest_output.txt``/
    ``prompt_audit.json``/``.workspace_guard.jsonl``), the produced ``output/``,
    and ``tests/`` intact. Unlike :func:`purge_leaf_bulk`, the keep-set lives
    INSIDE the workspace, so the workspace root is never removed. No-op under
    ``EVO_KEEP_CELL_TRACES=1`` or a falsy/missing path. Returns dirs removed.
    """
    if not workspace or keep_cell_traces():
        return 0
    ws = Path(workspace)
    if not ws.is_dir():
        return 0
    removed = 0
    for name in WORKSPACE_BULK_DIRS:
        target = ws / name
        if target.is_dir() and _rmtree_counted(target):
            removed += 1
    for cache in ws.rglob("__pycache__"):
        if cache.is_dir():
            _rmtree_counted(cache)
    hidden = ws.parent / f"_hidden_tests__{ws.name}"
    if hidden.is_dir():
        _rmtree_counted(hidden)
    return removed


__all__ = [
    "BULK_LEAF_DIRS",
    "WORKSPACE_BULK_DIRS",
    "archive_cell_debug_text",
    "keep_cell_traces",
    "purge_leaf_bulk",
    "purge_workspace_bulk",
    "rmtree_failure_count",
]
