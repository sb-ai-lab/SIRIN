"""Resolve the Python interpreter used to run a task's solution + tests.

sb-bench tasks declare a role (de / ds / genai / infra / pm / swe). Each role
has its own conda env holding the dependency surface that role's tasks need
(duckdb, pandera, openpyxl, pdf/docx/pptx, …). Running a role's solution under
the evo CLI's own interpreter (``sys.executable``) instead makes lib-heavy roles
fail with ``ModuleNotFoundError`` regardless of skill quality — a silent
confounder in evolution results. This module maps a role to its env python.

Resolution order for a role:

1. ``EVO_DISABLE_ROLE_PYTHON=1`` — explicit opt-out; use ``sys.executable``.
2. ``EVO_ROLE_PYTHON_<ROLE>`` — explicit per-role interpreter override.
3. ``<mlspace>/envs/<role>-env/bin/python`` where ``<mlspace>`` is
   ``EVO_MLSPACE_ROOT`` or ``account_home()/.mlspace``. The mlspace root comes
   from the real account home (passwd), never ``$HOME`` — which is redirected to
   an agent config sandbox here, so ``Path.home()`` would miss and silently fall
   back, reintroducing the confounder this module exists to remove.

A role with no resolvable interpreter raises :class:`RolePythonUnavailable`
rather than silently falling back, so a misconfigured env fails loudly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from evolution.paths import account_home

ROLES: tuple[str, ...] = ("de", "ds", "genai", "infra", "pm", "swe")


class RolePythonUnavailable(RuntimeError):
    """Raised when a role has no resolvable interpreter and no opt-out is set."""


def _mlspace_root() -> Path:
    root = os.environ.get("EVO_MLSPACE_ROOT")
    return Path(root) if root else account_home() / ".mlspace"


def expected_role_python(role: str | None) -> str | None:
    """Return the mapped interpreter path for ``role`` (no existence check, no raise).

    The ``EVO_ROLE_PYTHON_<ROLE>`` override if set, else the mlspace env python
    for a known role, else ``None``. For diagnostics that want the expected path.
    """
    if not role:
        return None
    role_key = role.strip().lower()
    override = os.environ.get(f"EVO_ROLE_PYTHON_{role_key.upper()}")
    if override:
        return override
    if role_key in ROLES:
        return str(_mlspace_root() / "envs" / f"{role_key}-env" / "bin" / "python")
    return None


def resolve_python_for_role(role: str | None) -> str:
    """Return the interpreter path for ``role``.

    ``None``/empty role or ``EVO_DISABLE_ROLE_PYTHON=1`` → ``sys.executable``.
    Otherwise the resolved role interpreter; raises
    :class:`RolePythonUnavailable` if none resolves.
    """
    if not role:
        return sys.executable
    if os.environ.get("EVO_DISABLE_ROLE_PYTHON") == "1":
        return sys.executable

    candidate = expected_role_python(role)
    if candidate and os.path.exists(candidate):
        return candidate

    role_key = role.strip().lower()
    detail = (
        f"mapped python {candidate!r} does not exist"
        if candidate
        else f"unknown role (known: {', '.join(ROLES)}) and no EVO_ROLE_PYTHON_{role_key.upper()} set"
    )
    raise RolePythonUnavailable(
        f"No interpreter for role {role_key!r}: {detail}. Fix the role env, set "
        f"EVO_ROLE_PYTHON_{role_key.upper()}=<python> or EVO_MLSPACE_ROOT=<dir>, or set "
        f"EVO_DISABLE_ROLE_PYTHON=1 to run under {sys.executable}."
    )
