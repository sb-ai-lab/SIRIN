"""Layout detection: pick the right ``TaskLayout`` for a given task dir.

Order of decision:
    1. If ``task.toml`` has ``[layout].kind = "evo"`` (or ``"sb-bench"``),
       honor that.
    2. Otherwise, look at the filesystem: presence of ``solve.sh`` AND
       ``environment/`` ⇒ sb-bench layout. Anything else ⇒ evo layout.

Returns an *instance* (not a class) so callers can stash it on ``Task``
without repeated construction.
"""

from __future__ import annotations

from pathlib import Path

from evolution.eval.layouts.base import TaskLayout, read_task_toml
from evolution.eval.layouts.evo import EvoTaskLayout
from evolution.eval.layouts.sb_bench import SbBenchTaskLayout

# Singletons — layouts are stateless.
_EVO = EvoTaskLayout()
_SB_BENCH = SbBenchTaskLayout()

# Public mapping in case callers want to look it up by name.
LAYOUTS: dict[str, TaskLayout] = {
    "evo": _EVO,
    "sb-bench": _SB_BENCH,
    "sb_bench": _SB_BENCH,
}


def detect_layout(task_dir: Path) -> TaskLayout:
    """Return the appropriate layout for ``task_dir``.

    See module docstring for the decision order. An explicit layout kind is
    authoritative; malformed or unknown declarations fail closed.
    """
    data, _ = read_task_toml(task_dir)
    layout = data.get("layout")
    kind = layout.get("kind") if isinstance(layout, dict) else None
    if kind is None:
        kind = data.get("kind")
    if kind is not None:
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError(f"{task_dir / 'task.toml'}: layout kind must be a non-empty string")
        normalized = kind.lower()
        if normalized not in LAYOUTS:
            raise ValueError(
                f"{task_dir / 'task.toml'}: unknown task layout kind {kind!r}; "
                f"expected one of {sorted(LAYOUTS)}"
            )
        return LAYOUTS[normalized]

    if (task_dir / "solve.sh").is_file() and (task_dir / "environment").is_dir():
        return _SB_BENCH
    return _EVO
