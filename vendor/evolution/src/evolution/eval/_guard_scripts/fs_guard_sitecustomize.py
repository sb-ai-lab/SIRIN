from __future__ import annotations

import glob as _glob
import json as _json
import os as _os
from pathlib import Path as _Path
import time as _time
from typing import Any as _Any


_WORKSPACE = _Path(_os.environ.get("EVOLUTION_WORKSPACE_GUARD_WORKSPACE", ".")).resolve()
_RUN_HOME_RAW = _os.environ.get("EVOLUTION_WORKSPACE_GUARD_RUN_HOME", "")
_RUN_HOME = _Path(_RUN_HOME_RAW).resolve() if _RUN_HOME_RAW else None
_LOG = _os.environ.get("EVOLUTION_WORKSPACE_GUARD_LOG") or ""
_FRAMEWORK = _os.environ.get("EVOLUTION_WORKSPACE_GUARD_FRAMEWORK", "python")
_MAX_DEPTH_UNDER_BASE = int(_os.environ.get("EVO_GUARD_MAX_DEPTH", "20") or "20")
_RAISE_ON_DEPTH = _os.environ.get("EVO_GUARD_MAX_DEPTH_RAISE", "") == "1"
_PROTECTED_ROOTS = tuple(_Path(p) for p in (
    "/home",
    "/root",
    "/tmp",
    "/data",
    "/workspace",
    "/mnt",
    "/media",
    "/proc",
    "/sys",
    "/etc",
))
_WORKSPACE_ALIAS = "/workspace"


def _translate_workspace_alias(path: _Any) -> _Any:
    if isinstance(path, int):
        return path
    if not isinstance(path, (str, bytes, _os.PathLike)):
        return path
    try:
        raw_obj = _os.fspath(path)
        raw = _os.fsdecode(raw_obj) if isinstance(raw_obj, bytes) else raw_obj
    except (TypeError, ValueError):
        return path
    if not isinstance(raw, str):
        return path
    if raw == _WORKSPACE_ALIAS:
        translated = str(_WORKSPACE)
    elif raw.startswith(_WORKSPACE_ALIAS + "/"):
        translated = str(_WORKSPACE) + raw[len(_WORKSPACE_ALIAS):]
    else:
        return path
    if isinstance(path, bytes):
        return _os.fsencode(translated)
    return translated


def _is_relative_to(path: _Path, root: _Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _log(action: str, subject: object, reason: str) -> None:
    if not _LOG:
        return
    try:
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(
                _json.dumps(
                    {
                        "ts": round(_time.time(), 3),
                        "framework": _FRAMEWORK,
                        "event": "python_fs_check",
                        "decision": "block",
                        "action": action,
                        "subject": str(subject)[:1000],
                        "reason": reason[:1000],
                        "workspace": str(_WORKSPACE),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass


def _outside_workspace(path: object) -> bool:
    try:
        p = _Path(_translate_workspace_alias(path)).expanduser()
    except TypeError:
        return False
    if not p.is_absolute():
        return False
    resolved = p.resolve(strict=False)
    if resolved == _WORKSPACE or _is_relative_to(resolved, _WORKSPACE):
        return False
    if _RUN_HOME is not None and (resolved == _RUN_HOME or _is_relative_to(resolved, _RUN_HOME)):
        return False
    if not any(resolved == root or _is_relative_to(resolved, root) for root in _PROTECTED_ROOTS):
        return False
    return True


def _glob_root(pattern: object) -> _Path | None:
    if not isinstance(pattern, (str, bytes, _os.PathLike)):
        return None
    text = _os.fsdecode(_translate_workspace_alias(pattern))
    if not text.startswith("/"):
        return None
    cut = len(text)
    for marker in ("*", "?", "["):
        pos = text.find(marker)
        if pos >= 0:
            cut = min(cut, pos)
    prefix = text[:cut] or "/"
    return _Path(prefix).resolve(strict=False)


_orig_os_walk = _os.walk


def _guarded_os_walk(top, *args, **kwargs):
    if _outside_workspace(top):
        _log("os.walk", top, "recursive host-root traversal is disabled")
        return iter(())
    return _orig_os_walk(top, *args, **kwargs)


_os.walk = _guarded_os_walk

_orig_glob = _glob.glob
_orig_iglob = _glob.iglob


def _glob_blocked(pattern) -> bool:
    root = _glob_root(pattern)
    if root is None:
        return False
    protected = any(root == protected_root or _is_relative_to(root, protected_root) for protected_root in _PROTECTED_ROOTS)
    blocked = protected and root != _WORKSPACE and not _is_relative_to(root, _WORKSPACE)
    if blocked and _RUN_HOME is not None:
        blocked = root != _RUN_HOME and not _is_relative_to(root, _RUN_HOME)
    if blocked:
        _log("glob", pattern, "absolute glob outside task workspace is disabled")
    return blocked


def _guarded_glob(pathname, *args, **kwargs):
    if _glob_blocked(pathname):
        return []
    return _orig_glob(pathname, *args, **kwargs)


def _guarded_iglob(pathname, *args, **kwargs):
    if _glob_blocked(pathname):
        return iter(())
    return _orig_iglob(pathname, *args, **kwargs)


_glob.glob = _guarded_glob
_glob.iglob = _guarded_iglob

_orig_path_glob = _Path.glob
_orig_path_rglob = _Path.rglob


def _guarded_path_glob(self, pattern, *args, **kwargs):
    if _outside_workspace(self):
        _log("Path.glob", self, "path glob outside task workspace is disabled")
        return iter(())
    return _orig_path_glob(self, pattern, *args, **kwargs)


def _guarded_path_rglob(self, pattern, *args, **kwargs):
    if _outside_workspace(self):
        _log("Path.rglob", self, "path rglob outside task workspace is disabled")
        return iter(())
    return _orig_path_rglob(self, pattern, *args, **kwargs)


_Path.glob = _guarded_path_glob  # type: ignore[reportAttributeAccessIssue]
_Path.rglob = _guarded_path_rglob  # type: ignore[reportAttributeAccessIssue]


import builtins as _builtins
import io as _io
import shutil as _shutil
import tempfile as _tempfile


def _mutate_roots() -> list:
    roots = [_WORKSPACE]
    if _RUN_HOME is not None:
        roots.append(_RUN_HOME)
    try:
        roots.append(_Path(_tempfile.gettempdir()).resolve())
    except Exception:
        pass
    return roots


_MUTATE_ROOTS = _mutate_roots()

_SAFE_DEVICE_FILES = frozenset({
    "/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom",
    "/dev/tty", "/dev/stdin", "/dev/stdout", "/dev/stderr",
})


def _is_safe_special(p) -> bool:
    try:
        s = p.as_posix()
    except Exception:
        return False
    if s in _SAFE_DEVICE_FILES:
        return True
    return s.startswith("/dev/fd/") or s.startswith("/proc/self/fd/") or (
        s.startswith("/proc/") and "/fd/" in s
    )


def _mutation_blocked(path) -> bool:
    if isinstance(path, int):
        return False
    try:
        raw = _translate_workspace_alias(path)
        raw = _os.fsdecode(bytes(raw) if isinstance(raw, bytearray) else raw) if isinstance(raw, (bytes, bytearray)) else raw
        p = _Path(raw).expanduser()
    except (TypeError, ValueError):
        return False
    if not p.is_absolute():
        try:
            p = _Path.cwd() / p
        except (OSError, ValueError):
            return False
    if _is_safe_special(p):
        return False
    try:
        resolved = p.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        return False
    if _is_safe_special(resolved):
        return False
    return not any(resolved == r or _is_relative_to(resolved, r) for r in _MUTATE_ROOTS)


def _is_log_path(file) -> bool:
    if not _LOG:
        return False
    try:
        raw = _os.fsdecode(bytes(file) if isinstance(file, bytearray) else file) if isinstance(file, (bytes, bytearray)) else file
        return _Path(raw) == _Path(_LOG)
    except (TypeError, ValueError):
        return False


def _refuse(action: str, target) -> None:
    _log(action, target, "mutation outside task workspace is disabled")
    raise PermissionError(
        "workspace guard: refusing " + action + " outside the task workspace: " + str(target)[:200]
    )


def _log_depth(action: str, subject: object, depth: int) -> None:
    if not _LOG:
        return
    try:
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(
                _json.dumps(
                    {
                        "ts": round(_time.time(), 3),
                        "framework": _FRAMEWORK,
                        "event": "python_fs_depth",
                        "decision": "block" if _RAISE_ON_DEPTH else "record",
                        "action": action,
                        "subject": str(subject)[:1000],
                        "depth": depth,
                        "workspace": str(_WORKSPACE),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass


def _depth_tripwire(action: str, path) -> None:
    base = _RUN_HOME if _RUN_HOME is not None else _WORKSPACE
    try:
        resolved = _Path(_translate_workspace_alias(path)).expanduser().resolve(strict=False)
    except (TypeError, OSError, RuntimeError, ValueError):
        return
    if not _is_relative_to(resolved, base):
        return
    depth = len(resolved.relative_to(base).parts)
    if depth <= _MAX_DEPTH_UNDER_BASE:
        return
    _log_depth(action, resolved, depth)
    if _RAISE_ON_DEPTH:
        raise PermissionError(
            "workspace guard: refusing "
            + action
            + " at nesting depth "
            + str(depth)
            + " under "
            + str(base)[:120]
        )


_orig_os_remove = _os.remove
_orig_os_unlink = _os.unlink
_orig_os_rmdir = _os.rmdir
_orig_os_mkdir = _os.mkdir
_orig_os_makedirs = _os.makedirs
_orig_os_rename = _os.rename
_orig_os_replace = _os.replace
_orig_os_chdir = _os.chdir


def _guarded_os_remove(path, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _mutation_blocked(path_t):
        _refuse("os.remove", path)
    return _orig_os_remove(path_t, *args, **kwargs)


def _guarded_os_unlink(path, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _mutation_blocked(path_t):
        _refuse("os.unlink", path)
    return _orig_os_unlink(path_t, *args, **kwargs)


def _guarded_os_rmdir(path, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _mutation_blocked(path_t):
        _refuse("os.rmdir", path)
    return _orig_os_rmdir(path_t, *args, **kwargs)


def _guarded_os_mkdir(path, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _mutation_blocked(path_t):
        _refuse("os.mkdir", path)
    _depth_tripwire("os.mkdir", path_t)
    return _orig_os_mkdir(path_t, *args, **kwargs)


def _guarded_os_makedirs(name, *args, **kwargs):
    name_t = _translate_workspace_alias(name)
    if _mutation_blocked(name_t):
        _refuse("os.makedirs", name)
    _depth_tripwire("os.makedirs", name_t)
    return _orig_os_makedirs(name_t, *args, **kwargs)


def _guarded_os_rename(src, dst, *args, **kwargs):
    src_t = _translate_workspace_alias(src)
    dst_t = _translate_workspace_alias(dst)
    if _mutation_blocked(src_t) or _mutation_blocked(dst_t):
        _refuse("os.rename", dst)
    return _orig_os_rename(src_t, dst_t, *args, **kwargs)


def _guarded_os_replace(src, dst, *args, **kwargs):
    src_t = _translate_workspace_alias(src)
    dst_t = _translate_workspace_alias(dst)
    if _mutation_blocked(src_t) or _mutation_blocked(dst_t):
        _refuse("os.replace", dst)
    return _orig_os_replace(src_t, dst_t, *args, **kwargs)


def _guarded_os_chdir(path):
    return _orig_os_chdir(_translate_workspace_alias(path))


_os.remove = _guarded_os_remove
_os.unlink = _guarded_os_unlink
_os.rmdir = _guarded_os_rmdir
_os.mkdir = _guarded_os_mkdir
_os.makedirs = _guarded_os_makedirs
_os.rename = _guarded_os_rename
_os.replace = _guarded_os_replace
_os.chdir = _guarded_os_chdir


_orig_shutil_rmtree = _shutil.rmtree


def _guarded_shutil_rmtree(path, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _mutation_blocked(path_t):
        _refuse("shutil.rmtree", path)
    return _orig_shutil_rmtree(path_t, *args, **kwargs)


_shutil.rmtree = _guarded_shutil_rmtree


_orig_path_unlink = _Path.unlink
_orig_path_rmdir = _Path.rmdir
_orig_path_mkdir = _Path.mkdir


def _guarded_path_unlink(self, *args, **kwargs):
    self_t = _Path(_translate_workspace_alias(self))
    if _mutation_blocked(self_t):
        _refuse("Path.unlink", self)
    return _orig_path_unlink(self_t, *args, **kwargs)


def _guarded_path_rmdir(self, *args, **kwargs):
    self_t = _Path(_translate_workspace_alias(self))
    if _mutation_blocked(self_t):
        _refuse("Path.rmdir", self)
    return _orig_path_rmdir(self_t, *args, **kwargs)


def _guarded_path_mkdir(self, *args, **kwargs):
    self_t = _Path(_translate_workspace_alias(self))
    if _mutation_blocked(self_t):
        _refuse("Path.mkdir", self)
    _depth_tripwire("Path.mkdir", self_t)
    return _orig_path_mkdir(self_t, *args, **kwargs)


_Path.unlink = _guarded_path_unlink
_Path.rmdir = _guarded_path_rmdir
_Path.mkdir = _guarded_path_mkdir


def _is_write_mode(mode) -> bool:
    if not isinstance(mode, str):
        return False
    return any(ch in mode for ch in ("w", "a", "x", "+"))


_orig_builtins_open = _builtins.open


def _guarded_open(file, mode="r", *args, **kwargs):
    file_t = _translate_workspace_alias(file)
    if _is_write_mode(mode) and not _is_log_path(file_t) and _mutation_blocked(file_t):
        _refuse("open", file)
    return _orig_builtins_open(file_t, mode, *args, **kwargs)


_builtins.open = _guarded_open
_io.open = _guarded_open


_orig_os_open = _os.open

_WRITE_OPEN_FLAGS = (
    _os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_APPEND | getattr(_os, "O_TRUNC", 0)
)


def _is_write_flags(flags) -> bool:
    try:
        return bool(int(flags) & _WRITE_OPEN_FLAGS)
    except (TypeError, ValueError):
        return False


def _guarded_os_open(path, flags, *args, **kwargs):
    path_t = _translate_workspace_alias(path)
    if _is_write_flags(flags) and not _is_log_path(path_t) and _mutation_blocked(path_t):
        _refuse("os.open", path)
    return _orig_os_open(path_t, flags, *args, **kwargs)


_os.open = _guarded_os_open


try:
    _marker_dir = _RUN_HOME if _RUN_HOME is not None else (_Path(_LOG).parent if _LOG else None)
    if _marker_dir is not None:
        _marker_dir.mkdir(parents=True, exist_ok=True)
        (_marker_dir / ("_fs_guard_active.%d" % _os.getpid())).write_text("1", encoding="utf-8")
except Exception:
    pass
