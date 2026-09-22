"""Small shared helpers used across packages."""

from __future__ import annotations

import time


def ms_since(start: float) -> int:
    """Milliseconds elapsed since a ``time.monotonic()`` reading."""
    return int((time.monotonic() - start) * 1000)


def truncate_with_ellipsis(text: str, max_len: int) -> str:
    """Truncate ``text`` to ``max_len`` chars, appending ``...`` when shortened."""
    return text[:max_len] + ("..." if len(text) > max_len else "")
