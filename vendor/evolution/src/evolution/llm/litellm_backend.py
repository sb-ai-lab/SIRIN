"""LLM backend using LiteLLM for multi-provider support."""

from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.request
from typing import Any
from urllib.parse import urlparse

from evolution import config
from evolution.core._util import ms_since
from evolution.core.models import Skill
from evolution.llm.backend import LLMResponse, SeedMode
from evolution.llm.proxy_env import (
    env_without_proxy_for_local_model,
    is_local_api_base,
    without_proxy_for_local_model,
)
from evolution.llm.retry import retry_async

_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "0.0.0.0", "::1"})


def _bypass_proxy_for_local(api_base: str | None) -> None:
    """Ensure a localhost ``api_base`` bypasses ``HTTP(S)_PROXY``.

    The OpenAI SDK transport (httpx) honors ``HTTP_PROXY`` / ``HTTPS_PROXY``
    and will route even a ``127.0.0.1`` request through the proxy unless the
    host is listed in ``NO_PROXY``. Behind a proxy that refuses localhost,
    this surfaces as a confusing ``403 Access denied`` while a plain
    ``curl`` (which bypasses the proxy for localhost) succeeds. We
    append the local host to ``NO_PROXY``/``no_proxy`` — process-local and
    non-destructive — so local vLLM/sglang endpoints work out of the box.
    """
    if not api_base:
        return
    host = urlparse(api_base).hostname or ""
    if host not in _LOCAL_HOSTS:
        return
    for var in ("NO_PROXY", "no_proxy"):
        entries = {e.strip() for e in os.environ.get(var, "").split(",") if e.strip()}
        if host not in entries:
            entries.add(host)
            os.environ[var] = ",".join(sorted(entries))


__all__ = [
    "LiteLLMBackend",
    "env_without_proxy_for_local_model",
    "is_local_api_base",
    "without_proxy_for_local_model",
]

_MAX_MODEL_LEN: dict[str, int] = {}


def _served_max_model_len(api_base: str) -> int | None:
    base = (api_base or "").rstrip("/")
    if base in _MAX_MODEL_LEN:
        return _MAX_MODEL_LEN[base] or None
    val = 0
    try:
        with without_proxy_for_local_model(base):
            with urllib.request.urlopen(base + "/models", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        for m in data.get("data", []):
            ml = m.get("max_model_len")
            if isinstance(ml, int) and ml > 0:
                val = ml if val == 0 else min(val, ml)
    except Exception:
        val = 0
    _MAX_MODEL_LEN[base] = val
    return val or None


try:
    from litellm.exceptions import RateLimitError as LiteLLMRateLimitError
except ImportError:  # pragma: no cover

    class LiteLLMRateLimitError(Exception):  # type: ignore[no-redef]
        pass


_TRANSIENT_TOKENS = (
    "timeout",
    "timed out",
    "connection reset",
    "remote end closed",
    "503",
    "502",
    "504",
    # Transport-level failures that openai/httpx/urllib3 raise as separate
    # exception classes but stringify with substrings litellm forwards to us.
    # Added 2026-05-12: a gpt-oss-120b server bounce produced
    # `openai.APIConnectionError('Connection error.')` and the previous list
    # didn't match, so 48 eval calls hard-failed on the first attempt.
    "connection error",
    "server disconnected",
    "apiconnectionerror",
    "connection aborted",
)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, LiteLLMRateLimitError):
        return True
    msg = str(exc).lower()
    return any(tok in msg for tok in _TRANSIENT_TOKENS)


# Locally-served reasoning models default to "thinking ON" under vLLM/sglang,
# which routes the answer to the reasoning channel and can leave ``content``
# empty (observed with Qwen3 and gpt-oss-120b). Each entry maps a
# case-insensitive model-name substring to the ``extra_body`` control that
# keeps ``content`` populated. Extend this table as new local models land.
#   - Qwen3: disable the thinking chat-template branch outright.
#   - gpt-oss (harmony): can't hard-disable; ``reasoning_effort="low"`` caps
#     analysis tokens so the final channel still emits content in budget.
_REASONING_CONTROLS: tuple[tuple[str, dict[str, Any]], ...] = (
    ("qwen3", {"chat_template_kwargs": {"enable_thinking": False}}),
    ("gpt-oss", {"reasoning_effort": "low"}),
)


def _default_reasoning_controls(model: str) -> dict[str, Any] | None:
    """Default ``extra_body`` for a locally-served reasoning model, else None."""
    m = (model or "").lower()
    for needle, controls in _REASONING_CONTROLS:
        if needle in m:
            # Deep-ish copy so the shared table can't be mutated by callers.
            return {k: (dict(v) if isinstance(v, dict) else v) for k, v in controls.items()}
    return None


class LiteLLMBackend:
    """Backend using LiteLLM — supports Claude, OpenAI, and 100+ other providers.

    Requires ``pip install evo-skills[llm]`` (LiteLLM dependency).

    Local reasoning models (Qwen3, gpt-oss, …) are served by vLLM/sglang
    with thinking ON, which routes the answer to the reasoning channel and
    can leave ``content`` empty. For known families we auto-apply an
    ``extra_body`` control (see ``_REASONING_CONTROLS``) so ``content`` is
    populated. Opt out with ``EVO_LLM_THINKING_ON=1`` (or the legacy
    ``QWEN3_THINKING_ON=1`` for Qwen3). An explicit ``extra_body`` kwarg or
    ``EVO_LLM_REASONING_EFFORT`` env overrides the default. ``complete``
    also falls back to ``reasoning_content`` when ``content`` is empty.
    """

    seed_mode: SeedMode = "forwarded"

    def __init__(self, model: str = "anthropic/claude-sonnet-4-5-20241022", **kwargs: Any) -> None:
        try:
            import litellm  # noqa: F401
        except ImportError:
            raise ImportError(
                "LiteLLM is required for this backend. Install with: pip install evo-skills[llm]"
            )
        self._model = model
        self._kwargs = kwargs
        explicit_reasoning_effort = self._kwargs.pop("reasoning_effort", None)
        if self._kwargs.get("api_key") is None and is_local_api_base(
            str(self._kwargs.get("api_base") or "")
        ):
            self._kwargs["api_key"] = "not-needed"
        # Local endpoints must bypass any corporate HTTP(S)_PROXY (see helper).
        _bypass_proxy_for_local(self._kwargs.get("api_base"))
        # Auto-apply reasoning controls for locally-served reasoning models
        # (Qwen3, gpt-oss, …) unless the caller passed an explicit ``extra_body``
        # or opted out. ``EVO_LLM_THINKING_ON`` is the general opt-out;
        # ``QWEN3_THINKING_ON`` is kept as a back-compat opt-out for Qwen3.
        opted_out = bool(os.environ.get("EVO_LLM_THINKING_ON"))
        if "qwen3" in model.lower() and os.environ.get("QWEN3_THINKING_ON"):
            opted_out = True
        if "extra_body" not in self._kwargs and not opted_out:
            controls = _default_reasoning_controls(model)
            if controls is not None:
                self._kwargs["extra_body"] = controls
        # Env-var fallback for CLI callers that do not construct LiteLLMBackend
        # with explicit manifest sampling knobs.
        env_temp = os.environ.get("EVO_LLM_TEMPERATURE")
        if env_temp and "temperature" not in self._kwargs:
            try:
                self._kwargs["temperature"] = float(env_temp)
            except ValueError:
                pass
        # A caller value wins over the legacy environment fallback and the
        # model-family auto-default above.
        reasoning_effort = (
            explicit_reasoning_effort
            if explicit_reasoning_effort is not None
            else config.llm_reasoning_effort()
        )
        if reasoning_effort:
            normalized_effort = str(reasoning_effort).lower()
            model_family = model.lower()
            if normalized_effort == "off":
                eb = self._kwargs.get("extra_body")
                if not isinstance(eb, dict):
                    eb = {}
                    self._kwargs["extra_body"] = eb
                if "qwen3" in model_family:
                    chat_template = eb.setdefault("chat_template_kwargs", {})
                    if isinstance(chat_template, dict):
                        chat_template["enable_thinking"] = False
                    eb.pop("reasoning_effort", None)
                elif "gpt-oss" in model_family:
                    eb["reasoning_effort"] = "low"
                else:
                    eb.pop("reasoning_effort", None)
                    if not eb:
                        self._kwargs.pop("extra_body", None)
            elif "qwen3" in model_family:
                eb = self._kwargs.setdefault("extra_body", {})
                if isinstance(eb, dict):
                    chat_template = eb.setdefault("chat_template_kwargs", {})
                    if isinstance(chat_template, dict):
                        chat_template["enable_thinking"] = True
                    eb.pop("reasoning_effort", None)
            elif "gpt-oss" in model_family:
                eb = self._kwargs.setdefault("extra_body", {})
                if isinstance(eb, dict):
                    eb["reasoning_effort"] = reasoning_effort
            else:
                self._kwargs["reasoning_effort"] = reasoning_effort
        env_max = os.environ.get("EVO_LLM_MAX_TOKENS")
        if env_max and "max_tokens" not in self._kwargs:
            try:
                self._kwargs["max_tokens"] = int(env_max)
            except ValueError:
                pass

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        import litellm

        call_messages = list(messages)
        if system:
            call_messages.insert(0, {"role": "system", "content": system})
        call_kwargs = dict(self._kwargs)
        if seed is not None:
            call_kwargs["seed"] = seed
        # Clamp output budget for local vLLM: max_tokens must leave room for the
        # prompt within max_model_len, else the server 400s the whole request.
        mt = call_kwargs.get("max_tokens")
        ab = str(call_kwargs.get("api_base") or "")
        if mt and is_local_api_base(ab):
            sml = _served_max_model_len(ab)
            if sml:
                reserve = int(os.environ.get("EVO_PROMPT_RESERVE_TOKENS", "32768") or "32768")
                cap = max(256, sml - reserve)
                if int(mt) > cap:
                    call_kwargs["max_tokens"] = cap

        _call_timeout = float(os.environ.get("EVO_LLM_CALL_TIMEOUT_S", "900") or "900")
        call_kwargs.setdefault("timeout", _call_timeout)

        async def _attempt() -> LLMResponse:
            start = time.monotonic()
            with without_proxy_for_local_model(ab):
                response = await asyncio.wait_for(
                    litellm.acompletion(
                        model=self._model,
                        messages=call_messages,
                        **call_kwargs,
                    ),
                    timeout=_call_timeout,
                )
            elapsed_ms = ms_since(start)

            choice = response.choices[0]
            content = (choice.message.content or "").strip()
            if not content:
                content = (getattr(choice.message, "reasoning_content", None) or "").strip()
            usage = response.usage

            return LLMResponse(
                content=content,
                tokens_in=usage.prompt_tokens if usage else 0,
                tokens_out=usage.completion_tokens if usage else 0,
                time_ms=elapsed_ms,
                finish_reason=(getattr(choice, "finish_reason", "") or ""),
            )

        return await retry_async(
            _attempt,
            classify=_is_retryable,
            max_attempts=6,
            base_delay_s=4.0,
            cap_delay_s=30.0,
        )

    async def complete_with_skill(
        self,
        messages: list[dict[str, str]],
        skill: Skill,
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Inject skill instructions into context, then complete."""
        return await self.complete_with_skills(messages, [skill], system, seed=seed)

    async def complete_with_skills(
        self,
        messages: list[dict[str, str]],
        skills: list[Skill],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Inject multiple skills into context, then complete."""
        skill_blocks = "\n\n".join(
            f'<skill_content name="{s.name}">\n{s.body}\n</skill_content>' for s in skills
        )

        if system:
            combined_system = f"{system}\n\n{skill_blocks}"
        else:
            combined_system = skill_blocks

        return await self.complete(messages, system=combined_system, seed=seed)
