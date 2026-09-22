"""Once-per-task read-only corpus base + hardlink staging (opt-in).

Root cause of the inode blow-up: ``materialize_workspace`` byte-copies the
task corpus into every solve (``16*n_train + 30`` per cell). With a base, the
corpus is materialized ONCE per (contract, task) under ``EVO_CORPUS_BASE_ROOT``
and each solve mirrors it with HARDLINKS — dentries to the shared inodes, zero
new file inodes — at the exact same paths, so every traversal (prompt
``iterdir``, ``rglob``/``walk``, wrapped ``find``, the fs guard) sees ordinary
in-workspace files. Files a solve may WRITE are listed in the census
(``EVO_CORPUS_WRITE_CENSUS``) and are copied, not linked; tasks without a
census entry keep today's full copy. Wholly inert unless BOTH env vars are set.

Build protocol (shared NFS — no flock reliance, no ``chmod a-w``): build TWICE
into private temp dirs and require byte-identical trees (catches
nondeterministic data generators), refuse bases that embed their own build
path (catches ``__file__``-keyed generators), write ``manifest.json``
(relpath -> sha256), then one atomic ``os.rename`` into place; a losing
concurrent builder discards its temp and revalidates the winner. A base whose
sampled hashes stop matching is quarantined and rebuilt — never trusted.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.json"
_SAMPLE_HASHES = 8
_CENSUS_CACHE: dict[str, dict] = {}

# In-place mutation hazards: DB engines write THROUGH an open handle, so a
# hardlinked db would poison the shared base. Always copied, never linked.
_ALWAYS_COPY_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".duckdb", ".mdb")


def _env_base_root() -> Path | None:
    raw = os.environ.get("EVO_CORPUS_BASE_ROOT", "").strip()
    return Path(raw) if raw else None


def load_write_census() -> dict | None:
    """Per-task write-relpath census from ``EVO_CORPUS_WRITE_CENSUS`` (cached)."""
    raw = os.environ.get("EVO_CORPUS_WRITE_CENSUS", "").strip()
    if not raw:
        return None
    cached = _CENSUS_CACHE.get(raw)
    if cached is not None:
        return cached
    try:
        data = json.loads(Path(raw).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("corpus_base: unreadable census %s: %s", raw, exc)
        return None
    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        return None
    _CENSUS_CACHE[raw] = tasks
    return tasks


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_digest(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): _sha256_file(p) for p in sorted(root.rglob("*")) if p.is_file()
    }


def _load_manifest(base_dir: Path) -> dict | None:
    try:
        manifest = json.loads((base_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        return None
    return manifest


def _manifest_valid(base_dir: Path, *, sample: int | None = _SAMPLE_HASHES) -> bool:
    manifest = _load_manifest(base_dir)
    if manifest is None:
        return False
    items = sorted(manifest["files"].items())
    for rel, _sha in items:
        if not (base_dir / rel).is_file():
            return False
    checked = items if sample is None else items[:sample]
    for rel, sha in checked:
        try:
            if _sha256_file(base_dir / rel) != sha:
                return False
        except OSError:
            return False
    return True


def _quarantine(base_dir: Path) -> None:
    target = base_dir.parent / f".quarantine.{base_dir.name}.{os.getpid()}"
    try:
        os.rename(base_dir, target)
        log.warning("corpus_base: base %s failed validation; quarantined to %s", base_dir, target)
    except OSError:
        log.warning("corpus_base: base %s failed validation and could not be quarantined", base_dir)


def _embeds_build_path(root: Path, needles: tuple[str, ...]) -> bool:
    encoded = tuple(n.encode() for n in needles)
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        try:
            blob = p.read_bytes()
        except OSError:
            return True
        if any(n in blob for n in encoded):
            return True
    return False


def _materialize_into(task_dir: Path, ws: Path, *, contract: str, agent_solve_sh: bool) -> None:
    from evolution.eval import workspace_materializer as wm

    if contract == "core":
        wm._materialize_core(task_dir, ws)
    else:
        wm._materialize_agent(task_dir, ws, agent_solve_sh=agent_solve_sh)


def _variant(contract: str, agent_solve_sh: bool) -> str:
    return contract if agent_solve_sh else f"{contract}-nosh"


def ensure_base(task_dir: Path, *, contract: str, agent_solve_sh: bool = True) -> Path | None:
    """Return a validated base dir for (contract, task), building it if needed."""
    base_root = _env_base_root()
    if base_root is None:
        return None
    variant_dir = base_root / _variant(contract, agent_solve_sh)
    base_dir = variant_dir / task_dir.name
    marker = variant_dir / f".{task_dir.name}.nondeterministic"
    if marker.exists():
        return None
    if base_dir.is_dir():
        if _manifest_valid(base_dir):
            return base_dir
        _quarantine(base_dir)

    builds: list[Path] = []
    try:
        for n in (1, 2):
            parent = variant_dir / f".build.{task_dir.name}.{os.getpid()}.{n}"
            ws = parent / task_dir.name
            ws.parent.mkdir(parents=True, exist_ok=True)
            _materialize_into(task_dir, ws, contract=contract, agent_solve_sh=agent_solve_sh)
            builds.append(ws)
        d1, d2 = _tree_digest(builds[0]), _tree_digest(builds[1])
        if d1 != d2 or _embeds_build_path(
            builds[0], (str(builds[0].parent), str(builds[1].parent))
        ):
            marker.write_text("datagen output differs across builds or embeds its build path\n")
            log.warning(
                "corpus_base: %s is not base-safe; falling back to per-solve copies", task_dir.name
            )
            return None
        # Provenance by content, layout-agnostic (the agent contract flattens):
        # bytes not present in the source task = generated/rewritten at
        # materialize time -> copied per solve, never linked.
        source_hashes = set(_tree_digest(task_dir).values())
        copy_rels = sorted(
            rel
            for rel, sha in d1.items()
            if sha not in source_hashes or rel.lower().endswith(_ALWAYS_COPY_SUFFIXES)
        )
        (builds[0] / MANIFEST_NAME).write_text(
            json.dumps({"files": d1, "copy": copy_rels}, indent=0, sort_keys=True),
            encoding="utf-8",
        )
        try:
            os.rename(builds[0], base_dir)
        except OSError:
            pass
    except Exception as exc:
        log.warning("corpus_base: build failed for %s: %s", task_dir.name, exc)
        return None
    finally:
        for ws in builds:
            shutil.rmtree(ws.parent, ignore_errors=True)
    return base_dir if _manifest_valid(base_dir) else None


def stage_from_base(base_dir: Path, ws: Path, *, copy_relpaths: set[str]) -> None:
    """Mirror the base into ``ws``: hardlink read-only files, copy write-census ones."""
    ws.mkdir(parents=True, exist_ok=True)
    for src in sorted(base_dir.rglob("*")):
        rel = src.relative_to(base_dir)
        dst = ws / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        if src.name == MANIFEST_NAME and rel.parent == Path("."):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if str(rel) in copy_relpaths:
            shutil.copy2(src, dst)
            continue
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)


def maybe_stage_workspace_from_base(
    task_dir: Path, ws: Path, *, contract: str, agent_solve_sh: bool = True
) -> bool:
    """Stage ``ws`` from a hardlink base when this task is census-vetted.

    False (caller falls back to today's full copy) unless EVO_CORPUS_BASE_ROOT
    is set, the census lists this task, and a validated base exists/builds.
    """
    census = load_write_census()
    if census is None:
        return False
    entry = census.get(task_dir.name)
    if not isinstance(entry, dict):
        return False
    base_dir = ensure_base(task_dir, contract=contract, agent_solve_sh=agent_solve_sh)
    if base_dir is None:
        return False
    manifest = _load_manifest(base_dir)
    if manifest is None:
        return False
    if ws.exists():
        shutil.rmtree(ws)
    writes = {str(r) for r in (entry.get("writes") or [])}
    writes.update(str(r) for r in (manifest.get("copy") or []))
    stage_from_base(base_dir, ws, copy_relpaths=writes)
    return True
