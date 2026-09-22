"""Task layout abstraction.

A `TaskLayout` encapsulates everything that differs between task layouts
the evolution pipeline can drive (the evo native format and the upstream
sb-bench format): metadata parsing, workspace staging, solution placement,
execution, and test running. See ``plans/layout_abstraction.md``.

The eval pipeline (`workspace.py`, `runner.py`, `solver.py`) always routes
through ``Task.resolve_layout()``; ``detect_layout`` picks the layout at
``load_task`` time (task.toml ``[layout].kind`` wins, else a file-presence
heuristic).
"""

from evolution.eval.layouts.base import (
    RunResult,
    TaskLayout,
    TaskMetadata,
    TestResult,
)
from evolution.eval.layouts.detect import detect_layout
from evolution.eval.layouts.evo import EvoTaskLayout
from evolution.eval.layouts.sb_bench import SbBenchTaskLayout

__all__ = [
    "EvoTaskLayout",
    "RunResult",
    "SbBenchTaskLayout",
    "TaskLayout",
    "TaskMetadata",
    "TestResult",
    "detect_layout",
]
