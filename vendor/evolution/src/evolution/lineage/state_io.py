"""Crash-safe, process-safe primitives for persisted lineage state."""

from __future__ import annotations

import errno
import fcntl
import json
import os
import stat
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class LockTimeoutError(TimeoutError):
    """Raised when a transaction lock cannot be acquired before its deadline."""


class LockOrderError(RuntimeError):
    """Raised when nested locks are requested out of canonical path order."""


_LOCK_STACK = threading.local()


def fsync_directory(path: Path) -> None:
    """Flush directory-entry changes for *path* to stable storage."""

    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Durably replace *path* with *data* using a same-directory temp file."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
    fd, raw_tmp = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=target.parent,
    )
    tmp = Path(raw_tmp)
    try:
        if mode is not None:
            os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
        fsync_directory(target.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Durably replace a text file."""

    atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: Path, value: object) -> None:
    """Durably replace a JSON file using the repository's readable format."""

    payload = json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n"
    atomic_write_text(path, payload)


def _held_lock_keys() -> list[str]:
    stack = getattr(_LOCK_STACK, "keys", None)
    if stack is None:
        stack = []
        _LOCK_STACK.keys = stack
    return stack


@contextmanager
def transaction_lock(
    path: Path,
    *,
    timeout: float = 30.0,
    poll_interval: float = 0.01,
) -> Iterator[None]:
    """Hold an exclusive POSIX advisory lock for a state transaction.

    Nested locks must be acquired in canonical path order. This makes callers
    that need more than one state lock deterministic and prevents AB/BA
    deadlocks between threads or processes.
    """

    lock_path = Path(path).resolve(strict=False)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    key = str(lock_path)
    held = _held_lock_keys()
    if held and key <= held[-1]:
        raise LockOrderError(
            f"Lock {lock_path} must be acquired after {held[-1]!r}; "
            "nested transaction locks use canonical path order"
        )

    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + max(0.0, timeout)
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if time.monotonic() >= deadline:
                    raise LockTimeoutError(
                        f"Timed out after {timeout:g}s acquiring transaction lock {lock_path}"
                    ) from exc
                time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

        held.append(key)
        try:
            yield
        finally:
            held.pop()
    finally:
        if acquired:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


@contextmanager
def skill_mutation_lock(skill_path: Path, *, timeout: float = 0.0) -> Iterator[None]:
    """Serialize mutations of one skill, allowing same-thread nesting."""

    skill = Path(skill_path)
    lock_path = (skill.parent / f".{skill.name}.mutation.lock").resolve(strict=False)
    held = getattr(_LOCK_STACK, "skill_mutations", None)
    if held is None:
        held = set()
        _LOCK_STACK.skill_mutations = held

    key = str(lock_path)
    if key in held:
        yield
        return

    with transaction_lock(lock_path, timeout=timeout):
        held.add(key)
        try:
            yield
        finally:
            held.remove(key)
