"""Central, read-on-access accessors for Evolution's environment configuration.

Every accessor reads ``os.environ`` on **each call** — it never caches at import
time — so runtime overrides and tests that set ``EVO_*`` mid-run take effect
immediately. This module is the canonical home for the env flags that are read
in more than one place; the full environment surface (every ``EVO_*`` /
framework variable) is documented in ``docs/configuration.md``.

Add an accessor here when a flag starts being read from more than one module, so
its name and semantics live in exactly one place.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _int_env(name: str, default: int) -> int:
    """Read an integer ``EVO_*`` flag on each call; log and fall back on bad input."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("config: %s=%r is not an integer; using default %d", name, raw, default)
        return default


def reflect_blind() -> bool:
    """Whether the reflector must run *blind* (``EVO_REFLECT_BLIND=1``).

    Blind mode hides detailed train verifier evidence (test source and failed-test
    detail) from the reflector. Default (unset/``0``) exposes that train evidence; the integrity
    boundary is the split/provenance gate that keeps held-out validation/test
    evidence out of evolution.
    """
    return os.environ.get("EVO_REFLECT_BLIND") == "1"


def llm_reasoning_effort() -> str | None:
    """Reasoning-effort override for LLM backends (``EVO_LLM_REASONING_EFFORT``).

    Returns the raw value (e.g. ``"low"``/``"medium"``/``"high"``/``"xhigh"``)
    or ``None`` when unset. Backends treat this as authoritative over their own
    defaults.
    """
    return os.environ.get("EVO_LLM_REASONING_EFFORT")


def llm_max_tokens(explicit: int | None = None) -> int:
    """Resolve the output budget: explicit value, environment, then 16384."""
    raw: int | str = (
        explicit if explicit is not None else os.environ.get("EVO_LLM_MAX_TOKENS", "16384")
    )
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"EVO_LLM_MAX_TOKENS must be a positive integer, got {raw!r}") from exc
    if value < 1:
        raise ValueError(f"EVO_LLM_MAX_TOKENS must be a positive integer, got {raw!r}")
    return value


def reflect_drop_mixed() -> bool:
    """Whether reflection drops mixed-signal failing traces (``EVO_REFLECT_DROP_MIXED=1``).

    When enabled, a failing trace is skipped if the same ``(task, skill_version)``
    also has a passing trace — the skill *can* pass it, so the failure is treated
    as verifier noise rather than a skill deficiency. Default (unset/``0``) keeps
    every failing trace, byte-identical to historical behaviour.
    """
    return os.environ.get("EVO_REFLECT_DROP_MIXED") == "1"


def optimization_target() -> str:
    """Experiment objective (``EVO_OPTIMIZATION_TARGET``).

    ``"general"`` preserves the default anti-overfit behavior. ``"train"`` is an
    explicitly labeled train-optimization mode: train metrics may drive
    promotion/selection, while held-out test metrics remain a control only.
    """
    raw = (os.environ.get("EVO_OPTIMIZATION_TARGET", "general") or "general").strip().lower()
    if raw in {"", "general", "heldout", "held-out"}:
        return "general"
    if raw == "train":
        return "train"
    raise ValueError(f"unknown EVO_OPTIMIZATION_TARGET {raw!r}; expected 'general' or 'train'")


def train_optimization_enabled() -> bool:
    """Whether the current run explicitly optimizes train performance."""
    return optimization_target() == "train"


def reflect_success_k() -> int:
    """Passing sibling traces sampled into reflection (``EVO_REFLECT_SUCCESS_K``, default 3)."""
    return _int_env("EVO_REFLECT_SUCCESS_K", 3)


def reflect_meta_skill_chars() -> int:
    """Char cap for the cross-round meta-skill digest in the reflect prompt
    (``EVO_REFLECT_META_SKILL_CHARS``, default 4000)."""
    return _int_env("EVO_REFLECT_META_SKILL_CHARS", 4000)


def leak_ngram_min_chars() -> int:
    """Minimum line length the leak scanner checks for verbatim trace copies
    (``EVO_LEAK_NGRAM_MIN_CHARS``, default 50)."""
    return _int_env("EVO_LEAK_NGRAM_MIN_CHARS", 50)
