"""Proxy environment helpers for LLM clients."""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from urllib.parse import urlparse

_PROXY_ENV_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)
_NO_PROXY_ENV_VARS = ("NO_PROXY", "no_proxy")
_LOCAL_API_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_LOCAL_NO_PROXY_ENTRIES = ("localhost", "127.0.0.1", "::1", "0.0.0.0")

# Refcount+lock: outermost scope snapshots+strips, last exit restores — no cross-scope clobber.
_proxy_lock = threading.Lock()
_proxy_depth = 0
_proxy_saved: dict[str, str | None] = {}


def is_local_api_base(api_base: str | None) -> bool:
    """Return True when *api_base* points to a local OpenAI-compatible server."""
    if not api_base:
        return False
    raw = str(api_base).strip()
    if not raw:
        return False
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    host = (parsed.hostname or "").lower()
    return host in _LOCAL_API_HOSTS


def env_without_proxy_for_local_model(
    api_base: str | None,
    env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an env copy with proxy vars removed only for local model endpoints."""
    source = os.environ if env is None else env
    copied = dict(source)
    if not is_local_api_base(api_base):
        return copied
    for key in _PROXY_ENV_VARS:
        copied.pop(key, None)
    _add_local_no_proxy(copied)
    return copied


@contextmanager
def without_proxy_env(*, add_local_no_proxy: bool = False) -> Iterator[None]:
    """Temporarily remove process proxy env vars; refcounted+lock-guarded so concurrent/nested scopes restore exactly once."""
    global _proxy_depth
    with _proxy_lock:
        if _proxy_depth == 0:
            _proxy_saved.clear()
            _proxy_saved.update(
                {key: os.environ.get(key) for key in (*_PROXY_ENV_VARS, *_NO_PROXY_ENV_VARS)}
            )
            for key in _PROXY_ENV_VARS:
                os.environ.pop(key, None)
        if add_local_no_proxy:
            _add_local_no_proxy(os.environ)
        _proxy_depth += 1
    try:
        yield
    finally:
        with _proxy_lock:
            _proxy_depth -= 1
            if _proxy_depth == 0:
                for key, value in _proxy_saved.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
                _proxy_saved.clear()


@contextmanager
def without_proxy_for_local_model(api_base: str | None) -> Iterator[None]:
    """Temporarily remove process proxy env vars for local model calls only."""
    if not is_local_api_base(api_base):
        yield
        return

    with without_proxy_env(add_local_no_proxy=True):
        yield


def _add_local_no_proxy(env: MutableMapping[str, str]) -> None:
    existing: list[str] = []
    for key in _NO_PROXY_ENV_VARS:
        existing.extend(part.strip() for part in env.get(key, "").split(",") if part.strip())
    merged = sorted({*existing, *_LOCAL_NO_PROXY_ENTRIES})
    value = ",".join(merged)
    env["NO_PROXY"] = value
    env["no_proxy"] = value
