#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


def _exec_real() -> None:
    cmd = Path(sys.argv[0]).name
    real = shutil.which(cmd, path=os.environ.get("EVOLUTION_WORKSPACE_GUARD_ORIG_PATH", ""))
    if not real:
        print(f"workspace guard: real command not found for {cmd}", file=sys.stderr)
        sys.exit(127)
    os.execv(real, [real, *sys.argv[1:]])


def _allowed_roots() -> list[Path]:
    roots: list[Path] = []
    for key in ("EVOLUTION_WORKSPACE_GUARD_WORKSPACE", "EVOLUTION_WORKSPACE_GUARD_RUN_HOME"):
        val = os.environ.get(key)
        if val:
            try:
                roots.append(Path(val).resolve())
            except (OSError, RuntimeError, ValueError):
                pass
    import tempfile
    try:
        roots.append(Path(tempfile.gettempdir()).resolve())
    except (OSError, RuntimeError, ValueError):
        pass
    return roots


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _candidate_paths(arg: str):
    if not arg or arg.startswith("-"):
        return
    yield arg
    if "=" in arg:
        tail = arg.split("=", 1)[1]
        if tail:
            yield tail


def _blocked(arg: str, roots: list[Path]) -> bool:
    if not roots:
        return False
    for cand in _candidate_paths(arg):
        try:
            p = Path(cand).expanduser()
        except (TypeError, ValueError):
            continue
        if not p.is_absolute():
            p = Path.cwd() / p
        resolved = p.resolve(strict=False)
        if not any(resolved == r or _is_relative_to(resolved, r) for r in roots):
            return True
    return False


try:
    _roots = _allowed_roots()
    _bad = [a for a in sys.argv[1:] if _blocked(a, _roots)]
    if _bad:
        print(
            "BLOCKED: "
            + Path(sys.argv[0]).name
            + " target(s) outside the task workspace are disabled: "
            + repr(_bad),
            file=sys.stderr,
        )
        sys.exit(126)
except Exception:
    pass

_exec_real()
