"""Durable, relocatable optimizer state and its per-skill lease."""

from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evolution.lineage.state_io import atomic_write_json, skill_mutation_lock

RUN_SCHEMA = "evolution-production-optimizer-v1"


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    run_id: str
    status: str
    skill_name: str
    initial_version: str
    final_version: str
    rounds: list[dict[str, Any]]
    run_path: Path | None
    plan: dict[str, Any] | None = None
    reason: str | None = None
    recommendation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["run_path"] = str(self.run_path) if self.run_path else None
        return payload


def now() -> str:
    return datetime.now(UTC).isoformat()


def new_run_id() -> str:
    return f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{secrets.token_hex(4)}"


def validate_run_id(run_id: str) -> str:
    value = str(run_id).strip()
    if (
        not value
        or len(value) > 80
        or Path(value).name != value
        or any(not (char.isalnum() or char in "._-") for char in value)
    ):
        raise ValueError(f"Invalid run id: {run_id!r}")
    return value


def json_digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def tree_digest(root: Path) -> str:
    """Hash a task tree by relative names, modes, and bytes, never its location."""

    digest = hashlib.sha256(b"evolution-optimizer-task-v1\0")
    for path in sorted(Path(root).rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode()
        if path.is_symlink():
            raise ValueError(f"Task trees cannot contain symlinks: {path}")
        if path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
            continue
        if not path.is_file():
            raise ValueError(f"Task trees cannot contain special files: {path}")
        digest.update(b"F\0" + relative + b"\0")
        digest.update(str(path.stat().st_mode & 0o111).encode() + b"\0")
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def read_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Optimizer run not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Optimizer state is unreadable or malformed: {path}") from exc
    required = {
        "schema",
        "run_id",
        "skill_name",
        "status",
        "phase",
        "initial_version",
        "final_version",
        "rounds",
    }
    if not isinstance(data, dict) or not required.issubset(data):
        raise ValueError(f"Optimizer state is missing required fields: {path}")
    return data


def write_state(path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = now()
    atomic_write_json(path, state)


def checkpoint(path: Path, state: dict[str, Any], phase: str) -> None:
    state["phase"] = phase
    write_state(path, state)


def fail_state(path: Path, state: dict[str, Any], reason_code: str) -> None:
    """Persist only a typed failure code; exception diagnostics may contain secrets."""

    state["status"] = "failed"
    state["error"] = {"phase": state.get("phase"), "reason_code": reason_code}
    write_state(path, state)


@contextmanager
def optimizer_lease(skill_path: Path, *, timeout: float = 0.0) -> Iterator[None]:
    """Hold the global POSIX optimizer lease for one canonical skill folder."""

    with skill_mutation_lock(skill_path, timeout=timeout):
        yield


def result_from_state(state: dict[str, Any], path: Path) -> OptimizationResult:
    return OptimizationResult(
        run_id=str(state["run_id"]),
        status=str(state["status"]),
        skill_name=str(state["skill_name"]),
        initial_version=str(state["initial_version"]),
        final_version=str(state["final_version"]),
        rounds=list(state.get("rounds") or []),
        run_path=path,
        reason=state.get("reason"),
        recommendation=state.get("recommendation"),
    )
