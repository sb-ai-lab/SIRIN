"""Free-inode tripwire for shared run volumes.

The run volume is shared and unquota'd: other writers can exhaust its inode
pool regardless of what this harness does. ``preflight_inodes`` refuses to
start a run near the floor; ``assert_inode_headroom`` aborts a run that would
otherwise stall every session on the volume mid-flight.

Thresholds (free-inode counts, ``0`` disables the check):
    EVO_MIN_FREE_INODES    preflight refuse threshold (default 500000)
    EVO_ABORT_FREE_INODES  mid-run abort floor (default 100000)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

log = logging.getLogger(__name__)

_PREFLIGHT_DEFAULT = 500_000
_ABORT_DEFAULT = 100_000
_LOG_INTERVAL_S = 300.0
_last_status_log: dict[str, float] = {}


class InodeFloorError(RuntimeError):
    """Free inodes on the run volume fell below a configured floor."""


def free_inodes(path: Path | str) -> int | None:
    """Free inodes available to this process on ``path``'s volume, or None."""
    try:
        return int(os.statvfs(str(path)).f_favail)
    except (OSError, ValueError):
        return None


def _threshold(env: str, default: int) -> int:
    raw = os.environ.get(env, "").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def preflight_inodes(run_root: Path | str) -> int | None:
    """Refuse to start when the volume is already near inode exhaustion."""
    floor = _threshold("EVO_MIN_FREE_INODES", _PREFLIGHT_DEFAULT)
    free = free_inodes(run_root)
    if floor and free is not None and free < floor:
        raise InodeFloorError(
            f"free inodes on {run_root} = {free} < EVO_MIN_FREE_INODES={floor}; "
            "refusing to start (reclaim with scripts/clean_run_cache.py or raise the threshold)"
        )
    if free is not None:
        log.info("volume preflight: %s free inodes on %s", free, run_root)
    return free


def assert_inode_headroom(run_root: Path | str, *, context: str = "") -> int | None:
    """Mid-run tripwire: abort below the hard floor, else rate-limited status log."""
    floor = _threshold("EVO_ABORT_FREE_INODES", _ABORT_DEFAULT)
    free = free_inodes(run_root)
    if free is None:
        return None
    if floor and free < floor:
        raise InodeFloorError(
            f"free inodes on {run_root} = {free} < EVO_ABORT_FREE_INODES={floor}"
            f"{f' ({context})' if context else ''}; aborting before the volume stalls"
        )
    key = str(run_root)
    now = time.monotonic()
    if now - _last_status_log.get(key, 0.0) >= _LOG_INTERVAL_S:
        _last_status_log[key] = now
        log.info(
            "volume headroom: %s free inodes on %s%s",
            free,
            run_root,
            f" ({context})" if context else "",
        )
    return free
