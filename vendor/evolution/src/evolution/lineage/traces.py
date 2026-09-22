"""Manage .traces/ directory for a skill — save, list, and query traces."""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evolution.core.models import Skill, SkillTrace
from evolution.lineage.state_io import atomic_write_json, atomic_write_text, transaction_lock

log = logging.getLogger(__name__)

TraceIndex = list[dict[str, Any]]


class TraceIndexError(RuntimeError):
    """Raised when a persisted trace index cannot be trusted."""


@dataclass(frozen=True)
class TraceRepairReport:
    """Observable result of rebuilding an index from trace directories."""

    indexed: int
    skipped: tuple[str, ...]


def new_trace_id() -> str:
    """Return a collision-safe identifier suitable for a trace directory."""

    return str(uuid.uuid4())


def validate_trace_id(trace_id: str) -> str:
    """Return *trace_id* if it is one safe path component."""

    if (
        not trace_id
        or trace_id in {".", ".."}
        or "/" in trace_id
        or "\\" in trace_id
        or trace_id != trace_id.strip()
        or not trace_id.isprintable()
    ):
        raise ValueError(f"Invalid trace id: {trace_id!r}")
    return trace_id


def resolve_trace_artifact(trace_dir: Path, filename: str) -> Path:
    """Resolve one direct artifact without following directory or file links."""

    directory = Path(trace_dir)
    if directory.is_symlink():
        raise ValueError(f"Trace directory cannot be a symlink: {directory}")
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError(f"Invalid trace filename: {filename!r}")
    resolved_dir = directory.resolve()
    candidate = directory / filename
    if candidate.is_symlink():
        raise ValueError(f"Trace file cannot be a symlink: {filename!r}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_dir):
        raise ValueError(f"Trace file escapes its directory: {filename!r}")
    return resolved


def _retention_cap() -> int:
    """Max traces kept per skill (EVO_TRACE_RETENTION); 0 disables pruning."""
    raw = os.environ.get("EVO_TRACE_RETENTION", "0").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def load_trace_evidence(trace_dir: Path) -> dict | None:
    """Read a trace evidence packet, returning None if it is absent or invalid."""
    path = resolve_trace_artifact(trace_dir, "evidence.json")
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


class TraceStore:
    """Manages .traces/ directory for a skill."""

    def __init__(self, skill: Skill) -> None:
        self._skill = skill
        self._traces_dir = skill.path / ".traces"
        self._index_path = self._traces_dir / "index.json"
        self._lock_path = self._traces_dir / ".index.lock"

    @property
    def traces_dir(self) -> Path:
        return self._traces_dir

    def resolve_trace_dir(self, trace_id: str) -> Path:
        """Resolve one trace directory without permitting escape or symlinks."""

        trace_id = validate_trace_id(trace_id)
        root = self._resolved_traces_root()
        candidate = self._traces_dir / trace_id
        if candidate.is_symlink():
            raise ValueError(f"Trace directory cannot be a symlink: {trace_id!r}")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Trace id escapes .traces: {trace_id!r}")
        return resolved

    def resolve_trace_file(self, trace_id: str, filename: str) -> Path:
        """Resolve a direct trace file without following an escaping symlink."""

        trace_dir = self.resolve_trace_dir(trace_id)
        return resolve_trace_artifact(trace_dir, filename)

    def save(
        self,
        trace: SkillTrace,
        prompt: str,
        response: str,
        code: str,
        evidence: dict | None = None,
    ) -> Path:
        """Save a trace: writes files + appends to index.

        Creates:
            .traces/<trace_id>/prompt.md
            .traces/<trace_id>/response.md
            .traces/<trace_id>/solve.py
            .traces/<trace_id>/result.json
            .traces/<trace_id>/evidence.json   (only if ``evidence`` given)

        ``result.json`` is unchanged/backward-compatible; the observable
        evidence packet is written to a separate ``evidence.json`` so older
        readers keep working.

        Returns the trace directory path.
        """
        trace_dir = self.resolve_trace_dir(trace.id)
        self._traces_dir.mkdir(parents=True, exist_ok=True)
        try:
            trace_dir.mkdir(exist_ok=False)
        except FileExistsError as exc:
            raise FileExistsError(f"Trace id {trace.id!r} already exists") from exc

        # Write trace files
        atomic_write_text(trace_dir / "prompt.md", prompt)
        atomic_write_text(trace_dir / "response.md", response)
        atomic_write_text(trace_dir / "solve.py", code)
        atomic_write_text(trace_dir / "result.json", trace.model_dump_json(indent=2) + "\n")
        if evidence is not None:
            atomic_write_json(trace_dir / "evidence.json", evidence)

        # Lock the index read-modify-write: parallel K-attempt produce shares it.
        with transaction_lock(self._lock_path):
            index = self._load_index()
            index.append(trace.model_dump(mode="json"))
            index = self._prune_locked(index)
            self._save_index(index)

        return trace_dir

    def list(
        self,
        skill_version: str | None = None,
        model: str | None = None,
        task: str | None = None,
    ) -> TraceIndex:
        """Query traces with optional filters."""
        index = self._load_index()
        if skill_version:
            index = [t for t in index if t["skill_version"] == skill_version]
        if model:
            index = [t for t in index if t["model"] == model]
        if task:
            index = [t for t in index if t["task"] == task]
        return index

    def fitness(self, skill_version: str) -> float | None:
        """Average pass_rate across all traces for a version."""
        traces = self.list(skill_version=skill_version)
        if not traces:
            return None
        return sum(t["pass_rate"] for t in traces) / len(traces)

    def count(self, skill_version: str | None = None) -> int:
        """Number of traces, optionally filtered by version."""
        return len(self.list(skill_version=skill_version))

    def repair_index(self) -> TraceRepairReport:
        """Rebuild ``index.json`` from valid on-disk trace result packets.

        Invalid or partial trace directories remain untouched and are reported
        by name so callers can inspect them before deciding whether to delete
        anything.
        """

        entries: list[dict[str, Any]] = []
        skipped: list[str] = []
        self._resolved_traces_root()
        with transaction_lock(self._lock_path):
            self._traces_dir.mkdir(parents=True, exist_ok=True)
            for trace_dir in sorted(self._traces_dir.iterdir(), key=lambda path: path.name):
                if not trace_dir.is_dir():
                    continue
                try:
                    trace_dir = self.resolve_trace_dir(trace_dir.name)
                    trace = SkillTrace.model_validate_json(
                        self.resolve_trace_file(trace_dir.name, "result.json").read_text(
                            encoding="utf-8"
                        )
                    )
                except Exception:
                    skipped.append(trace_dir.name)
                    continue
                if trace.id != trace_dir.name:
                    skipped.append(trace_dir.name)
                    continue
                entries.append(trace.model_dump(mode="json"))
            entries.sort(key=lambda entry: (str(entry.get("timestamp", "")), str(entry["id"])))
            self._save_index(entries)
        return TraceRepairReport(indexed=len(entries), skipped=tuple(skipped))

    # -- Private helpers --

    def _prune_locked(self, index: TraceIndex) -> TraceIndex:
        """Drop the oldest traces beyond the retention cap (index is append-ordered)."""
        cap = _retention_cap()
        if not cap or len(index) <= cap:
            return index
        drop, keep = index[:-cap], index[-cap:]
        for entry in drop:
            trace_id = str(entry.get("id", ""))
            if trace_id:
                try:
                    trace_dir = self.resolve_trace_dir(trace_id)
                except ValueError as exc:
                    raise TraceIndexError(
                        f"{self._skill.name}: trace index contains unsafe id {trace_id!r}"
                    ) from exc
                shutil.rmtree(trace_dir, ignore_errors=True)
        log.info(
            "trace retention: pruned %d oldest of %d traces under %s (cap=%d)",
            len(drop),
            len(index),
            self._traces_dir,
            cap,
        )
        return keep

    def _load_index(self) -> TraceIndex:
        try:
            self._resolved_traces_root()
        except ValueError as exc:
            raise TraceIndexError(f"{self._skill.name}: unsafe .traces directory") from exc
        if not self._index_path.exists():
            return []
        if self._index_path.is_symlink():
            raise TraceIndexError(f"{self._skill.name}: trace index cannot be a symlink")
        try:
            data = json.loads(self._index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise TraceIndexError(
                f"{self._skill.name}: {self._index_path} is unreadable or corrupt; "
                "repair the trace index before continuing"
            ) from exc
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise TraceIndexError(
                f"{self._skill.name}: {self._index_path} is not a trace-entry list; "
                "repair the trace index before continuing"
            )
        try:
            ids = [SkillTrace.model_validate(item).id for item in data]
            for trace_id in ids:
                self.resolve_trace_dir(trace_id)
        except (ValidationError, ValueError) as exc:
            raise TraceIndexError(
                f"{self._skill.name}: {self._index_path} contains an invalid trace entry; "
                "repair the trace index before continuing"
            ) from exc
        if len(ids) != len(set(ids)):
            raise TraceIndexError(
                f"{self._skill.name}: {self._index_path} contains duplicate trace ids; "
                "repair the trace index before continuing"
            )
        return data

    def _save_index(self, index: TraceIndex) -> None:
        self._traces_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self._index_path, index)

    def _resolved_traces_root(self) -> Path:
        if self._traces_dir.is_symlink():
            raise ValueError(f"Trace root cannot be a symlink: {self._traces_dir}")
        return self._traces_dir.resolve()
