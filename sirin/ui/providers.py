from __future__ import annotations

import os
from dataclasses import dataclass

from sirin.ui.path_policy import is_trusted_local


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
