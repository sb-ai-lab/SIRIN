"""Mock LLM backend for testing — returns canned responses."""

from __future__ import annotations

from typing import Any

from evolution.core.models import Skill
from evolution.llm.backend import LLMResponse, SeedMode


class MockBackend:
    """A mock backend that returns preconfigured responses.

    Usage:
        backend = MockBackend(responses=["response 1", "response 2"])
        # First call returns "response 1", second returns "response 2", etc.
        # If responses exhausted, returns default_response.
    """

    seed_mode: SeedMode = "forwarded"

    def __init__(
        self,
        responses: list[str] | None = None,
        default_response: str = "mock response",
        **_ignored_kwargs: Any,
    ) -> None:
        # Accept and ignore backend kwargs (max_tokens, api_base, api_key, ...)
        # that get_backend forwards, mirroring CodexBackend — so `-m mock`
        # works on every code path (e.g. `evo run solve`) without a TypeError.
        self._responses = list(responses or [])
        self._default = default_response
        self.calls: list[dict] = []  # record of all calls for assertion

    def _next_response(self) -> str:
        if self._responses:
            return self._responses.pop(0)
        return self._default

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        self.calls.append({"messages": messages, "system": system, "skill": None, "seed": seed})
        return LLMResponse(
            content=self._next_response(),
            tokens_in=100,
            tokens_out=50,
            time_ms=500,
        )

    async def complete_with_skill(
        self,
        messages: list[dict[str, str]],
        skill: Skill,
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        return await self.complete_with_skills(messages, [skill], system, seed=seed)

    async def complete_with_skills(
        self,
        messages: list[dict[str, str]],
        skills: list[Skill],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {
                "messages": messages,
                "system": system,
                "skills": [s.name for s in skills],
                "seed": seed,
            }
        )
        return LLMResponse(
            content=self._next_response(),
            tokens_in=200,
            tokens_out=100,
            time_ms=800,
        )
