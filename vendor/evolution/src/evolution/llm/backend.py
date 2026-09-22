"""Abstract LLM backend protocol and factory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

from evolution.core.models import Skill

SeedMode = Literal["forwarded", "unsupported"]


@dataclass
class LLMResponse:
    """Response from an LLM completion."""

    content: str
    tokens_in: int = 0
    tokens_out: int = 0
    time_ms: int = 0
    finish_reason: str = ""

    @property
    def total_tokens(self) -> int:
        return self.tokens_in + self.tokens_out


@runtime_checkable
class LLMBackend(Protocol):
    """Protocol that all LLM backends must implement."""

    seed_mode: SeedMode

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Send messages to the LLM and get a text response."""
        ...

    async def complete_with_skill(
        self,
        messages: list[dict[str, str]],
        skill: Skill,
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Complete with a skill's instructions injected into context."""
        ...

    async def complete_with_skills(
        self,
        messages: list[dict[str, str]],
        skills: list[Skill],
        system: str | None = None,
        seed: int | None = None,
    ) -> LLMResponse:
        """Complete with multiple skills injected into context."""
        ...


def model_seed_mode(name: str) -> SeedMode:
    """Return seed handling for a model routed by :func:`get_backend`."""
    if name in {"codex", "claude-code", "hermes"} or name.startswith(
        ("codex/", "claude-code/", "hermes/", "gigachat")
    ):
        return "unsupported"
    return "forwarded"


def require_seed_support(
    backend: object,
    seed: int | None,
    *,
    label: str | None = None,
) -> None:
    """Reject seeded calls unless a backend explicitly forwards the seed."""
    if seed is not None and getattr(backend, "seed_mode", "unsupported") != "forwarded":
        raise ValueError(f"{label or type(backend).__name__} does not support seeded completions")


def get_backend(name: str, **kwargs) -> LLMBackend:
    """Factory: resolve a backend name to an instance.

    Supported:
      - 'mock' -> MockBackend (for testing)
      - 'claude' -> LiteLLMBackend with Claude model
      - 'openai' -> LiteLLMBackend with GPT model
      - 'gigachat' / 'gigachat-pro' / 'gigachat-max' / 'gigachat-3-ultra' ->
            GigaChatBackend (short aliases mapped to SDK model names)
      - 'gigachat/<MODEL>' -> GigaChatBackend with <MODEL> verbatim
            (litellm-style prefix; e.g. 'gigachat/GigaChat-3-Ultra')
      - 'codex' / 'codex/<MODEL>' -> AgentBackend using `codex exec`
      - 'claude-code' / 'claude-code/<MODEL>' -> AgentBackend using `claude -p`
      - 'hermes' / 'hermes/<MODEL>' -> AgentBackend using `hermes -z`
      - any other string -> LiteLLMBackend with that model name
    """
    agent_permission = kwargs.pop("agent_permission", "safe")
    if agent_permission not in ("safe", "unsafe"):
        raise ValueError("agent_permission must be 'safe' or 'unsafe'")

    if name == "mock":
        from evolution.llm.mock_backend import MockBackend

        return MockBackend(**kwargs)

    if (
        name in ("codex", "claude-code", "hermes")
        or name.startswith("codex/")
        or name.startswith("claude-code/")
        or name.startswith("hermes/")
    ):
        from evolution.llm.agent_backend import AgentBackend

        return AgentBackend(model=name, agent_permission=agent_permission, **kwargs)

    # Litellm-style routing: `gigachat/<MODEL>` -> GigaChatBackend with <MODEL>.
    # The SDK is case-sensitive on model names, so we pass the suffix verbatim.
    if name.startswith("gigachat/"):
        from evolution.llm.gigachat_backend import GigaChatBackend

        return GigaChatBackend(model=name.split("/", 1)[1], **kwargs)

    # GigaChat short aliases — lowercase keys, SDK-canonical values.
    _gigachat_models = {
        "gigachat": "GigaChat-2-Pro",  # default: best general-purpose
        "gigachat-lite": "GigaChat-2-Pro-Lite",  # lighter/faster
        "gigachat-pro": "GigaChat-2-Pro",  # alias
        "gigachat-max": "GigaChat-2-Max",  # most capable
        "gigachat-2-pro": "GigaChat-2-Pro",
        "gigachat-2-max": "GigaChat-2-Max",
        "gigachat-3-ultra": "GigaChat-3-Ultra",  # newest tier
    }
    if name.startswith("gigachat"):
        from evolution.llm.gigachat_backend import GigaChatBackend

        model = _gigachat_models.get(name.lower(), name)
        return GigaChatBackend(model=model, **kwargs)

    from evolution.llm.litellm_backend import LiteLLMBackend

    model_map = {
        "claude": "anthropic/claude-sonnet-4-5-20241022",
        "openai": "gpt-4o",
    }
    model = model_map.get(name, name)
    return LiteLLMBackend(model=model, **kwargs)
