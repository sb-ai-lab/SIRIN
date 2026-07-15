from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

from sirin.ui.path_policy import is_hosted, is_trusted_local


OPENAI_PROVIDER = 'OpenAI'
OPENROUTER_PROVIDER = 'OpenRouter'
ANTHROPIC_PROVIDER = 'Anthropic'
CUSTOM_PROVIDER = 'Custom OpenAI-compatible'

API_PROVIDER_BASE_URLS = {
    OPENAI_PROVIDER: 'https://api.openai.com/v1',
    OPENROUTER_PROVIDER: 'https://openrouter.ai/api/v1',
    ANTHROPIC_PROVIDER: 'https://api.anthropic.com/v1/',
}
API_PROVIDER_KEY_ENVS = {
    OPENAI_PROVIDER: 'OPENAI_API_KEY',
    OPENROUTER_PROVIDER: 'OPENROUTER_API_KEY',
    ANTHROPIC_PROVIDER: 'ANTHROPIC_API_KEY',
}
API_PROVIDER_DEFAULT_MODEL_ENVS = {
    OPENAI_PROVIDER: 'SIRIN_OPENAI_MODEL',
    OPENROUTER_PROVIDER: 'SIRIN_OPENROUTER_MODEL',
    ANTHROPIC_PROVIDER: 'SIRIN_ANTHROPIC_MODEL',
    CUSTOM_PROVIDER: 'SIRIN_CUSTOM_OPENAI_MODEL',
}
API_PROVIDER_DEFAULT_MODELS = {
    OPENAI_PROVIDER: 'gpt-4.1-mini',
    OPENROUTER_PROVIDER: 'openai/gpt-4.1-mini',
    ANTHROPIC_PROVIDER: 'claude-sonnet-4-6',
}
LOCAL_OPENAI_DEFAULT_BASE_URL = 'http://localhost:8000/v1'


def custom_openai_base_url() -> str:
    """Custom-provider base URL: the env override, else the local vLLM default."""
    return os.getenv('SIRIN_CUSTOM_OPENAI_BASE_URL', '') or LOCAL_OPENAI_DEFAULT_BASE_URL


def local_openai_models(base_url: str, timeout: float = 1.5) -> list[str]:
    """Model ids served by an OpenAI-compatible ``/models`` endpoint; [] when unreachable."""
    try:
        with urllib.request.urlopen(
            f"{base_url.rstrip('/')}/models", timeout=timeout
        ) as response:
            payload = json.load(response)
    except (OSError, ValueError):
        return []
    data = payload.get('data') if isinstance(payload, dict) else None
    return [str(item['id']) for item in data or [] if isinstance(item, dict) and item.get('id')]


@dataclass(frozen=True)
class ApiProvider:
    name: str
    base_url: str
    api_key: str


def available_api_providers() -> list[str]:
    providers = [OPENAI_PROVIDER, OPENROUTER_PROVIDER, ANTHROPIC_PROVIDER]
    if is_trusted_local():
        providers.append(CUSTOM_PROVIDER)
    return providers


def provider_models(provider: str) -> list[str]:
    default_model = API_PROVIDER_DEFAULT_MODELS.get(provider, '')
    env_var = API_PROVIDER_DEFAULT_MODEL_ENVS.get(provider)
    return [os.getenv(env_var, default_model) if env_var else default_model]


def resolve_api_provider(
    provider: str,
    custom_base_url: str = '',
    api_key: str | None = None,
) -> ApiProvider:
    if provider == CUSTOM_PROVIDER:
        if not is_trusted_local():
            raise ValueError('Custom OpenAI-compatible endpoints require trusted local mode.')
        if not custom_base_url:
            raise ValueError('Custom OpenAI-compatible endpoint requires a base URL.')
        return ApiProvider(
            name=provider,
            base_url=custom_base_url,
            api_key=api_key or os.getenv('SIRIN_CUSTOM_OPENAI_API_KEY') or 'EMPTY',
        )

    if provider not in API_PROVIDER_BASE_URLS:
        raise ValueError(f'Unknown API provider: {provider}')

    env_var = API_PROVIDER_KEY_ENVS[provider]
    resolved_key = api_key or os.getenv(env_var)
    if not resolved_key:
        raise ValueError(f'Set {env_var} to use {provider}.')
    return ApiProvider(
        name=provider,
        base_url=API_PROVIDER_BASE_URLS[provider],
        api_key=resolved_key,
    )


def openrouter_reasoning_extra_body(model: str) -> dict:
    """OpenRouter ``reasoning`` request extension for one model (generation and judges).

    The configured default demo model is verified live to support disabling reasoning
    outright — no chain-of-thought to overrun the completion budget (OpenRouter mirrors
    a truncated chain-of-thought into ``content``, which reads as a garbage answer and
    fails the judges' verbatim echo), and no free-tier quota burned on thinking. Other
    models are not verified to accept ``enabled: false``, so they keep the official cap
    that stops an unbounded chain-of-thought from overrunning the budget.
    """
    if model == provider_models(OPENROUTER_PROVIDER)[0]:
        return {'reasoning': {'enabled': False}}
    return {'reasoning': {'max_tokens': 1024}}


def require_shared_key_model(provider: str, model: str, pasted_key: str | None) -> None:
    """On the hosted profile, the server's shared env key funds ONLY the configured
    **free** OpenRouter demo model (``SIRIN_OPENROUTER_MODEL``, which must be a ``:free``
    route). Any paid model — a non-default or non-free OpenRouter model, or any
    OpenAI/Anthropic model — requires the visitor's own pasted key.

    The model field is visitor-editable, so without this gate a public Space carrying a
    funded key secret would let any visitor bill arbitrary models to it. This fails closed:
    if the deploy env leaves ``SIRIN_OPENROUTER_MODEL`` unset or set to a paid route, the
    shared key serves nothing rather than silently billing a paid model. A pasted key is
    the visitor's own — no restriction. Non-hosted deployments keep full env-key freedom.
    """
    if pasted_key or not is_hosted():
        return
    free_default = provider_models(OPENROUTER_PROVIDER)[0]
    serves_shared_model = (
        provider == OPENROUTER_PROVIDER
        and model == free_default
        and free_default.endswith(':free')
    )
    if not serves_shared_model:
        raise ValueError(
            f'The shared demo key serves only the free OpenRouter demo model '
            f'({free_default}) — paste your own API key in the sidebar to use {model}.'
        )
