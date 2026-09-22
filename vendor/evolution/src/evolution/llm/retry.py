"""Shared async retry helper for LLM backends.

Both LiteLLM and GigaChat backends face transient 429s, 5xx, and network
blips. ``retry_async`` runs a coroutine factory with exponential backoff +
full jitter, asking a caller-supplied ``classify`` function whether each
exception should be retried or raised.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

Classify = Callable[[BaseException], bool]
"""Returns True if the exception is retryable, False to raise immediately."""


async def retry_async(
    factory: Callable[[], Awaitable[T]],
    *,
    classify: Classify,
    max_attempts: int = 8,
    base_delay_s: float = 4.0,
    cap_delay_s: float = 60.0,
) -> T:
    """Run ``factory()`` with exponential backoff on retryable errors.

    Delay schedule: ``min(base_delay_s * 2**attempt + uniform(0, 1), cap_delay_s)``.
    Default 8 attempts × 4s base ≈ 5 minutes of coverage, which spans two
    OpenRouter free-tier reset windows.
    """
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return await factory()
        except BaseException as exc:
            last_exc = exc
            if not classify(exc) or attempt + 1 == max_attempts:
                raise
            delay = min(
                base_delay_s * (2**attempt) + random.uniform(0, 1.0),
                cap_delay_s,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
