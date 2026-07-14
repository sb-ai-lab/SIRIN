"""Bundled recorded detector runs for the hosted demo (assets/recorded_runs/*.json).

Each asset is a strict portable ``sirin.run`` document (SHA-256 integrity verified by
``import_portable_json``) exported by ``scripts/dev/record_replay_runs.py`` from a REAL
local run of that preset. The hosted Space ships no GPU and no model weights, so these
presets serve their recorded results: loaded records get a fresh id/timestamps and the
honest ``RECORDED_RESULT`` origin, exactly like the landing span seeds. A broken asset
raises (misattributed evidence must never render); an absent directory is an empty list.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .contracts import RunOrigin, RunRecord, utc_now
from .session import import_portable_json

_RECORDED_RUNS_DIR = (
    Path(__file__).resolve().parents[1] / 'assets' / 'recorded_runs'
)


def load_recorded_runs(setup_revision: int = 0) -> list[RunRecord]:
    """All bundled recorded runs, one fresh ``RECORDED_RESULT`` record per asset."""
    if not _RECORDED_RUNS_DIR.is_dir():
        return []
    runs: list[RunRecord] = []
    now = utc_now()
    for path in sorted(_RECORDED_RUNS_DIR.glob('*.json')):
        (record,) = import_portable_json(path.read_text(encoding='utf-8'))
        runs.append(record.model_copy(update={
            'id': str(uuid4()),
            'created_at': now,
            'completed_at': now,
            'origin': RunOrigin.RECORDED_RESULT,
            'setup_revision': setup_revision,
        }))
    return runs
