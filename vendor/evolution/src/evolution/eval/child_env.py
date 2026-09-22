"""Environment construction for untrusted solution and verifier children."""

from __future__ import annotations

import os
from collections.abc import Collection, Mapping

_RUNTIME_ENV_KEYS = frozenset(
    {
        "PATH",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TZ",
        "TERM",
        "TMPDIR",
        "PYTHONPATH",
        "PYTHONIOENCODING",
        "PYTHONUTF8",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "LD_LIBRARY_PATH",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
    }
)

PROVIDER_SECRET_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "DASHSCOPE_API_KEY",
        "GIGACHAT_API_KEY",
        "GIGACHAT_CREDENTIALS",
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "MISTRAL_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "TOGETHERAI_API_KEY",
    }
)


def minimal_child_env(
    base_env: Mapping[str, str] | None = None,
    *,
    allow: Collection[str] = (),
) -> dict[str, str]:
    """Return only runtime essentials plus explicitly allowed variables.

    Provider credentials and unrelated host/session state are absent by
    default. Callers that truly need another variable must name it in
    ``allow``; that explicit seam can also opt a provider credential back in
    for a child whose job is to contact that provider.
    """

    source = os.environ if base_env is None else base_env
    names = (_RUNTIME_ENV_KEYS - PROVIDER_SECRET_NAMES) | frozenset(allow)
    return {name: source[name] for name in names if name in source}
