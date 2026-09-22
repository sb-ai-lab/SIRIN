"""Single per-cell append-only log of every evolution improvement attempt.

One file per evolution run (cell), ``<run_dir>/attempts.jsonl``, accumulates one
JSON line per event so the whole improve→gate loop is auditable without a scatter
of per-round/per-attempt files:

- ``kind="generation"`` — one editor attempt, for ANY editor (hermes, the gpt-oss
  ``evolution`` rewriter, or the codex/claude session editor): the produced ``new_body``
  plus, when the adapter supplies them, the prompt and raw native trace. Written by the
  centralized logger in ``skill_editors.edit_skill`` even for attempts the δ-gate later
  rejects (the round-keyed native trace file is overwritten on retries; this log is not).
- ``kind="gate"`` — one δ-gate decision: parent/candidate ``M_gate``, ``delta_m``,
  ``tau``, ``zone``, ``gate_status`` — including the intermediate retry attempts that
  ``run_gated_edit_attempts`` would otherwise discard.

Entries share ``round`` + ``attempt`` keys so a generation and its gate decision
correlate. Logging is strictly additive and best-effort: every call is guarded so a
logging failure can never perturb an evolution run.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

FILENAME = "attempts.jsonl"

# Telemetry side-channel key: an editor adapter may stash generation-log extras (prompt +
# native trace) under this key in its returned telemetry; edit_skill pops it and folds it into
# the kind="generation" record. Shared constant so the writer and reader can never drift.
GENERATION_LOG_EXTRA_KEY = "_generation_log_extra"


def attempts_log_path(run_dir: Any) -> Path:
    return Path(run_dir) / FILENAME


def append_attempt(run_dir: Any, entry: dict[str, Any]) -> None:
    """Append one event as a JSON line to ``<run_dir>/attempts.jsonl``.

    Best-effort: swallows all errors so instrumentation never breaks a run.
    """
    try:
        path = attempts_log_path(run_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"ts": time.time(), **entry}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
