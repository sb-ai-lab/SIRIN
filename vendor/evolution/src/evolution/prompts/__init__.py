"""Canonical home for every prompt the framework sends to an LLM.

One import surface so a newcomer (or coding agent) can discover and read all
task-solving, reflection, and rewrite prompts in one place::

    from evolution import prompts
    print(prompts.BASE_SOLVER_SYSTEM_PROMPT)
    print(prompts.REFLECT_SYSTEM_ORACLE)

Each constant is defined in the module that *uses* it (so the prompt sits next
to the code that renders and sends it) and re-exported here. The authoritative
definitions live in:

* task solving      — :mod:`evolution.eval.solver`
* reflection/diagnose — :mod:`evolution.evolve.reflection`,
  :mod:`evolution.evolve.reflection_evidence`
* rewrite / edit    — :mod:`evolution.evolve.reflect`

Prompt text is covered by golden tests (``tests/test_prompts_golden.py``): any
edit to a prompt must update its golden hash, which keeps changes deliberate and
reviewable (prompt wording is load-bearing for measured fitness).
"""

from __future__ import annotations

import re
from pathlib import Path

from evolution.eval.solver import (
    BASE_SOLVER_SYSTEM_PROMPT,
    CODE_RETRY_SYSTEM_REMINDER,
    OUTPUT_CWD_CONTRACT,
    ROOT_CWD_CONTRACT,
)
from evolution.evolve.reflect import (
    CODEX_FILE_EDIT_PROMPT,
    CODEX_FILE_EDIT_SYSTEM,
    REWRITE_PROMPT,
    REWRITE_SYSTEM,
    SESSION_PROMPT,
    SESSION_SYSTEM_BLIND,
    SESSION_SYSTEM_ORACLE,
)
from evolution.evolve.reflection import (
    REFLECT_PROMPT,
    REFLECT_SUCCESS_PROMPT,
    REFLECT_SYSTEM_BLIND,
    REFLECT_SYSTEM_ORACLE,
)
from evolution.evolve.reflection_evidence import ORACLE_LEAD_IN

__all__ = [
    # task solving
    "BASE_SOLVER_SYSTEM_PROMPT",
    "ROOT_CWD_CONTRACT",
    "OUTPUT_CWD_CONTRACT",
    "CODE_RETRY_SYSTEM_REMINDER",
    # reflection / diagnose
    "REFLECT_SYSTEM_BLIND",
    "REFLECT_SYSTEM_ORACLE",
    "REFLECT_PROMPT",
    "REFLECT_SUCCESS_PROMPT",
    "ORACLE_LEAD_IN",
    # rewrite / edit
    "REWRITE_SYSTEM",
    "REWRITE_PROMPT",
    "CODEX_FILE_EDIT_SYSTEM",
    "CODEX_FILE_EDIT_PROMPT",
    "SESSION_SYSTEM_BLIND",
    "SESSION_SYSTEM_ORACLE",
    "SESSION_PROMPT",
]

_PROMPTS_DIR = Path(__file__).resolve().parent
_INCLUDE_RE = re.compile(r"\{\{include:([\w./-]+)\}\}")
_INCLUDE_NAME_RE = re.compile(r"^_blocks/[A-Za-z0-9_-]+$")
_TOKEN_RE = re.compile(r"\{([a-z_]+)\}")
_prompt_cache: dict[str, str] = {}


def _read_prompt_file(name: str) -> str:
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def _validate_include_name(name: str) -> None:
    if not _INCLUDE_NAME_RE.fullmatch(name):
        raise ValueError(f"prompt includes must reference _blocks/<name>, got {name!r}")
    root = (_PROMPTS_DIR / "_blocks").resolve()
    path = (_PROMPTS_DIR / f"{name}.md").resolve()
    if root not in path.parents:
        raise ValueError(f"prompt include escapes _blocks/: {name!r}")


def load_prompt(name: str) -> str:
    if name in _prompt_cache:
        return _prompt_cache[name]
    text = _read_prompt_file(name)

    def _inline(match: re.Match[str]) -> str:
        block_name = match.group(1)
        _validate_include_name(block_name)
        block_text = _read_prompt_file(block_name)
        if _INCLUDE_RE.search(block_text):
            raise ValueError(f"nested include not allowed: {block_name}")
        return block_text

    _prompt_cache[name] = _INCLUDE_RE.sub(_inline, text)
    return _prompt_cache[name]


def render(name: str, /, **kwargs: str) -> str:
    text = load_prompt(name)
    tokens = set(_TOKEN_RE.findall(text))
    given = set(kwargs)
    if tokens != given:
        missing = sorted(tokens - given)
        extra = sorted(given - tokens)
        raise ValueError(f"placeholder mismatch: missing={missing} extra={extra}")
    return _TOKEN_RE.sub(lambda m: kwargs[m.group(1)], text)


def clear_cache() -> None:
    _prompt_cache.clear()
