"""Timeout-safe subprocess capture.

``subprocess.run(capture_output=True, timeout=...)`` does not reliably enforce
the timeout: on expiry CPython kills only the direct child, then blocks in
``communicate()`` on the stdout/stderr pipe whose write end is still held by
surviving grandchildren — so ``TimeoutExpired`` is never raised and the calling
thread wedges forever (this deadlocked a whole anchor in t34v7). Running the
child in its own session and killing the entire process group on timeout closes
those pipes and makes the timeout real.
"""

from __future__ import annotations

import locale
import os
import signal
import subprocess
import threading
import time

_DEFAULT_MAX_OUTPUT_BYTES = 1024 * 1024
_PIPE_DRAIN_GRACE_SECONDS = 5.0


class _BoundedCapture:
    """Drain a byte stream while retaining bounded head-and-tail evidence."""

    def __init__(self, limit: int) -> None:
        self.limit = max(0, limit)
        self.total = 0
        self.head = bytearray()
        self.tail = bytearray()

    def feed(self, chunk: bytes) -> None:
        self.total += len(chunk)
        if len(self.head) < self.limit:
            self.head.extend(chunk[: self.limit - len(self.head)])
        if self.limit:
            self.tail.extend(chunk)
            if len(self.tail) > self.limit:
                del self.tail[: len(self.tail) - self.limit]

    def value(self) -> bytes:
        if self.total <= self.limit:
            return bytes(self.head)
        marker = f"\n...[output truncated; {self.total} bytes total]...\n".encode("ascii")
        if len(marker) >= self.limit:
            return marker[: self.limit]
        payload_budget = self.limit - len(marker)
        head_size = payload_budget // 2
        tail_size = payload_budget - head_size
        tail = bytes(self.tail[-tail_size:]) if tail_size else b""
        return bytes(self.head[:head_size]) + marker + tail


def _kill_group(proc: subprocess.Popen, process_group: int) -> None:
    try:
        os.killpg(process_group, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


def _drain(pipe, capture: _BoundedCapture) -> None:
    try:
        for chunk in iter(lambda: pipe.read(64 * 1024), b""):
            capture.feed(chunk)
    finally:
        pipe.close()


def _render(capture: _BoundedCapture, *, text: bool) -> str | bytes:
    value = capture.value()
    if not text:
        return value
    return value.decode(locale.getpreferredencoding(False), errors="replace")


def run_capture(
    cmd: list[str],
    *,
    timeout: float,
    cwd: str | None = None,
    env: dict | None = None,
    text: bool = True,
    max_output_bytes: int = _DEFAULT_MAX_OUTPUT_BYTES,
) -> subprocess.CompletedProcess:
    """Like ``subprocess.run(capture_output=True, timeout=...)`` but the
    timeout is actually enforced: the whole process group is killed on expiry.

    Raises ``subprocess.TimeoutExpired`` (with whatever output was captured) so
    existing callers' ``except subprocess.TimeoutExpired`` paths are unchanged.
    """

    started = time.monotonic()
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        cwd=cwd,
        env=env,
        start_new_session=True,
    ) as proc:
        process_group = proc.pid
        stdout_capture = _BoundedCapture(max_output_bytes)
        stderr_capture = _BoundedCapture(max_output_bytes)
        assert proc.stdout is not None
        assert proc.stderr is not None
        readers = [
            threading.Thread(target=_drain, args=(proc.stdout, stdout_capture), daemon=True),
            threading.Thread(target=_drain, args=(proc.stderr, stderr_capture), daemon=True),
        ]
        for reader in readers:
            reader.start()

        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(proc, process_group)
            try:
                proc.wait(timeout=_PIPE_DRAIN_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        drain_budget = (
            _PIPE_DRAIN_GRACE_SECONDS
            if timed_out
            else max(0.0, timeout - (time.monotonic() - started))
        )
        drain_deadline = time.monotonic() + drain_budget
        for reader in readers:
            reader.join(timeout=max(0.0, drain_deadline - time.monotonic()))
            if reader.is_alive():
                timed_out = True
                _kill_group(proc, process_group)
        if timed_out:
            final_deadline = time.monotonic() + _PIPE_DRAIN_GRACE_SECONDS
            for reader in readers:
                reader.join(timeout=max(0.0, final_deadline - time.monotonic()))

        out = _render(stdout_capture, text=text)
        err = _render(stderr_capture, text=text)
        if timed_out:
            raise subprocess.TimeoutExpired(cmd, timeout, output=out, stderr=err)
        return subprocess.CompletedProcess(cmd, proc.returncode, out, err)
