#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import sys


def _exec_real() -> None:
    cmd = Path(sys.argv[0]).name
    real = shutil.which(cmd, path=os.environ.get("EVOLUTION_WORKSPACE_GUARD_ORIG_PATH", ""))
    if not real:
        print(f"workspace guard: real command not found for {cmd}", file=sys.stderr)
        sys.exit(127)
    os.execv(real, [real, *sys.argv[1:]])


src = os.environ.get("EVOLUTION_WORKSPACE_GUARD_SRC")
if src:
    sys.path.insert(0, src)

try:
    from evolution.eval.workspace_guard import make_workspace_guard

    log = os.environ.get("EVOLUTION_WORKSPACE_GUARD_LOG") or ""
    guard = make_workspace_guard(
        framework=os.environ.get("EVOLUTION_WORKSPACE_GUARD_FRAMEWORK", "subprocess"),
        workspace_dir=Path(os.environ["EVOLUTION_WORKSPACE_GUARD_WORKSPACE"]),
        audit_log_path=Path(log) if log else None,
    )
    rendered = " ".join(shlex.quote(arg) for arg in [Path(sys.argv[0]).name, *sys.argv[1:]])
    reason = guard.terminal_command_block_reason(rendered)
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(126)
except Exception:
    # Preserve framework functionality if guard bootstrap fails.
    pass

_exec_real()
