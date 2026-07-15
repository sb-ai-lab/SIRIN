from __future__ import annotations

import os
from pathlib import Path


def is_trusted_local() -> bool:
    # Never honor trusted-local on a hosted deployment: a stray SIRIN_UI_TRUSTED_LOCAL=1
    # there would drop the path-traversal boundary and unlock Custom endpoints on a
    # public host. Hosted always wins.
    return os.getenv('SIRIN_UI_TRUSTED_LOCAL') == '1' and not is_hosted()


def is_hosted() -> bool:
    return os.getenv('SIRIN_UI_HOSTED') == '1'


def _roots(env_var: str) -> list[Path]:
    return [
        Path(p).expanduser().resolve(strict=False)
        for p in os.getenv(env_var, '').split(os.pathsep)
        if p
    ]


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _require_path(path: str, *, roots_env: str, label: str) -> str:
    if not path:
        return ''
    resolved = Path(path).expanduser().resolve(strict=False)
    if is_trusted_local():
        return str(resolved)

    roots = _roots(roots_env)
    if roots and any(_inside(resolved, root) for root in roots):
        return str(resolved)

    prefix = 'No allowed roots configured. ' if not roots else ''
    raise ValueError(
        f'{prefix}Path is outside allowed UI {label} roots. '
        f'Set {roots_env} or SIRIN_UI_TRUSTED_LOCAL=1 for local development.'
    )


def require_data_path(path: str) -> str:
    return _require_path(path, roots_env='SIRIN_UI_DATA_ROOTS', label='data')


def require_checkpoint_path(path: str) -> str:
    return _require_path(
        path, roots_env='SIRIN_UI_CHECKPOINT_ROOTS', label='checkpoint'
    )
