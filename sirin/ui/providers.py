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


def require_shared_key_model(provider: str, model: str, pasted_key: str | None) -> None:
    """On the hosted profile, the server's shared env key serves ONLY the configured
    default model (``SIRIN_OPENROUTER_MODEL``).

    The model field is visitor-editable, so without this gate a public Space carrying a
    funded OPENROUTER_API_KEY secret would let any visitor bill arbitrary models to it.
    A pasted key is the visitor's own — no restriction. Non-hosted deployments (local
    dev, campaign scripts) keep full env-key freedom.
    """
    if pasted_key or not is_hosted():
        return
    if provider == OPENROUTER_PROVIDER and model != provider_models(provider)[0]:
        raise ValueError(
            f'The shared demo key serves only the default model '
            f'({provider_models(provider)[0]}) — paste your own API key in the '
            f'sidebar to use {model}.'
        )
