"""LLM backend using GigaChat SDK (Sber)."""

from __future__ import annotations

import os
import time
from typing import Any

from evolution.core._util import ms_since
from evolution.core.models import Skill
from evolution.llm.backend import LLMResponse, SeedMode, require_seed_support
from evolution.llm.proxy_env import without_proxy_env
from evolution.llm.retry import retry_async

_NON_RETRYABLE_TOKENS = (
    "401 unauthorized",
    "403 forbidden",
    "404 not found",
    "invalid api key",
    "invalid credentials",
)


def _is_retryable(exc: BaseException) -> bool:
    msg = str(exc).lower()
    cls_name = type(exc).__name__.lower()
    cls_module = type(exc).__module__.lower()

    # GigaChat-specific scope flap surfaces as auth-shaped but is transient.
    if "scope from db" in msg:
        return True
    # httpx exceptions often have empty str(); classify by class name so
    # transient timeouts/connect errors retry even with no message.
    if cls_module.startswith("httpx") and any(
        n in cls_name for n in ("timeout", "connect", "remote", "network")
    ):
        return True
    if any(tok in msg for tok in _NON_RETRYABLE_TOKENS):
        return False
    return True


class GigaChatBackend:
    """Backend for Sber GigaChat API.

    Requires: pip install gigachat

    Authentication (any one):
      - credentials="<auth_key>" (recommended)
      - GIGACHAT_CREDENTIALS env var
      - access_token="<token>"

    Models: GigaChat, GigaChat-Plus, GigaChat-Pro, GigaChat-Max
    """

    seed_mode: SeedMode = "unsupported"

    def __init__(
        self,
        model: str = "GigaChat",
        credentials: str | None = None,
        api_key: str | None = None,
        scope: str | None = None,
        max_tokens: int | None = 16384,
        temperature: float | None = None,
        top_p: float | None = None,
        reasoning_effort: str | None = None,
        verify_ssl_certs: bool = False,
        **kwargs: Any,
    ) -> None:
        if reasoning_effort is not None:
            raise ValueError("GigaChat does not support reasoning_effort")
        self._model = model
        # max_tokens=None ⇒ omit from the request ⇒ uncapped output (model runs
        # to a natural stop). temperature/top_p default None ⇒ server defaults.
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p

        # Accept api_key as an alias for credentials for generic backend callers.
        creds = credentials or api_key
        resolved_scope = scope or os.environ.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
        # Drop kwargs the SDK doesn't recognize (the orchestrator forwards
        # api_base="" and similar generic keys; api_base is irrelevant here).
        sanitized_kwargs = {k: v for k, v in kwargs.items() if k != "api_base" and v != ""}
        # GigaChat-Max can take 60-120s on reasoning-heavy tasks; httpx
        # default ~5s read timeout trips repeatedly. Override via env.
        sanitized_kwargs.setdefault(
            "timeout",
            float(os.environ.get("GIGACHAT_TIMEOUT_SEC", "180")),
        )
        self._client_kwargs: dict[str, Any] = {
            "scope": resolved_scope,
            "verify_ssl_certs": verify_ssl_certs,
            **sanitized_kwargs,
        }
        if creds:
            self._client_kwargs["credentials"] = creds

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        require_seed_support(self, seed)
        from gigachat import GigaChat
        from gigachat.models import Chat, Messages, MessagesRole

        call_messages: list[Messages] = []
        if system:
            call_messages.append(Messages(role=MessagesRole.SYSTEM, content=system))
        for msg in messages:
            role = {
                "user": MessagesRole.USER,
                "assistant": MessagesRole.ASSISTANT,
                "system": MessagesRole.SYSTEM,
            }.get(msg["role"], MessagesRole.USER)
            call_messages.append(Messages(role=role, content=msg["content"]))

        chat_kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": call_messages,
        }
        # Include each tunable only when set so a None means "omit / server
        # default" — notably max_tokens=None ⇒ uncapped output.
        if self._max_tokens is not None:
            chat_kwargs["max_tokens"] = self._max_tokens
        if self._temperature is not None:
            chat_kwargs["temperature"] = self._temperature
        if self._top_p is not None:
            chat_kwargs["top_p"] = self._top_p
        chat_request = Chat(**chat_kwargs)

        async def _attempt() -> LLMResponse:
            # Unset proxy env vars to avoid TLS-in-TLS issues (Python 3.10).
            with without_proxy_env():
                start = time.monotonic()
                async with GigaChat(**self._client_kwargs) as client:
                    response = await client.achat(chat_request)
                elapsed_ms = ms_since(start)

            content = response.choices[0].message.content or ""
            usage = response.usage
            return LLMResponse(
                content=content,
                tokens_in=usage.prompt_tokens if usage else 0,
                tokens_out=usage.completion_tokens if usage else 0,
                time_ms=elapsed_ms,
                finish_reason=(getattr(response.choices[0], "finish_reason", "") or ""),
            )

        return await retry_async(
            _attempt,
            classify=_is_retryable,
            max_attempts=8,
            base_delay_s=4.0,
            cap_delay_s=60.0,
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
