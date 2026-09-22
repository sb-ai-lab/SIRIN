"""Synchronous collect, reflect, rewrite, and conservative promotion workflow."""

from __future__ import annotations

import asyncio
import hashlib
import math
import os
import shutil
import tempfile
from collections.abc import Collection, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from evolution.config import llm_max_tokens, llm_reasoning_effort
from evolution.core.bindings import SkillBinding, resolve_skill_bindings
from evolution.core.models import LineageEntry, Skill
from evolution.core.parser import load_skill
from evolution.core.store import SkillStore
from evolution.eval.paths import resolve_tasks_root
from evolution.eval.solver import DEFAULT_SOLVE_TIMEOUT_S, SolveResult, solve_task
from evolution.eval.task import Task, load_task
from evolution.eval.workspace import setup_workspace
from evolution.evolve.edit_brake import DECAY_FLOOR, METRIC_REVISION, SCHEDULE, resolve_base_budget
from evolution.evolve.optimizer_state import (
    RUN_SCHEMA,
    OptimizationResult,
    checkpoint,
    fail_state,
    json_digest,
    new_run_id,
    now,
    optimizer_lease,
    read_state,
    result_from_state,
    tree_digest,
    validate_run_id,
    write_state,
)
from evolution.evolve.optimizer_validation import ValidationMeasurement, paired_schedule
from evolution.evolve.promotion_gate import conservative_paired_gate
from evolution.evolve.reflect import (
    collect_reflections,
    load_reflection,
    normalize_rewrite_mode,
    reflect_failing_traces,
    rewrite_skill_with_audit,
)
from evolution.evolve.rewrite_outcome import PROMOTED_ELIGIBLE, RewriteOutcome
from evolution.lineage.state_io import atomic_write_text, fsync_directory
from evolution.lineage.traces import TraceStore
from evolution.lineage.tracker import LineageTracker
from evolution.lineage.version import VersionStore, hash_managed_tree, hash_tree
from evolution.llm.backend import (
    LLMBackend,
    SeedMode,
    get_backend,
    model_seed_mode,
    require_seed_support,
)
from evolution.splits import SplitManifest

MIN_VALIDATION_PAIRS = 4
SATURATION_RECOMMENDATION = "Choose a validation task with headroom or expand the validation pool."
UNDERPOWERED_RECOMMENDATION = "Increase --trials and rerun with the same train/validation split."


class OptimizationRunError(RuntimeError):
    """Public, secret-free wrapper for a failed optimizer execution."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(f"Optimizer failed ({reason_code})")


def load_optimization_status(
    skill_name: str,
    run_id: str | None = None,
    *,
    project_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Load one durable optimizer checkpoint without changing it."""

    project = Path(project_dir or Path.cwd()).resolve()
    store = SkillStore(project_dir=project, user_dir=Path.home())
    if not store.has(skill_name):
        raise KeyError(f"Skill {skill_name!r} not found")
    runs = store.get(skill_name).path / ".evolution" / "runs"
    if run_id:
        path = runs / validate_run_id(run_id) / "run.json"
    else:
        candidates = [candidate for candidate in runs.glob("*/run.json") if candidate.is_file()]
        if not candidates:
            raise FileNotFoundError(f"No optimizer runs found for {skill_name!r}")
        path = max(candidates, key=lambda candidate: candidate.stat().st_mtime_ns)
    state = read_state(path)
    if state.get("schema") != RUN_SCHEMA or state.get("skill_name") != skill_name:
        raise ValueError("Invalid optimizer run state")
    return state


def optimize_skill(
    skill_name: str,
    *,
    train_tasks: Sequence[str],
    validate_tasks: Sequence[str],
    solver_model: str,
    editor_model: str | None = None,
    project_dir: Path | str | None = None,
    tasks_dir: Path | str | None = None,
    rounds: int = 1,
    trials: int = 4,
    seed: int = 0,
    rewrite_mode: str = "edit-ops",
    version_decay: bool = True,
    max_rewrite_attempts: int = 1,
    manifest: SplitManifest | Path | str | None = None,
    api_base: str | None = None,
    solver_api_base: str | None = None,
    editor_api_base: str | None = None,
    solver_temperature: float | None = None,
    editor_temperature: float | None = None,
    solver_reasoning_effort: str | None = None,
    editor_reasoning_effort: str | None = None,
    agent_permission: str = "safe",
    max_tokens: int | None = None,
    timeout: float = DEFAULT_SOLVE_TIMEOUT_S,
    resume: str | None = None,
    dry_run: bool = False,
    solver_backend: LLMBackend | None = None,
    editor_backend: LLMBackend | None = None,
    pass_env: Collection[str] = (),
) -> OptimizationResult:
    """Improve one folder-addressed skill from explicit train and validation pools."""

    project = Path(project_dir or Path.cwd()).resolve()
    task_root = resolve_tasks_root(tasks_dir, project_dir=project)
    train_ids = _unique(train_tasks, "train")
    validation_ids = _unique(validate_tasks, "validate")
    overlap = sorted(set(train_ids) & set(validation_ids))
    if overlap:
        raise ValueError(f"train and validation tasks overlap: {overlap}")
    if rounds < 1 or trials < 1 or max_rewrite_attempts < 1:
        raise ValueError("rounds, trials, and max_rewrite_attempts must all be positive")
    base_budget = resolve_base_budget()
    if len(validation_ids) * trials < MIN_VALIDATION_PAIRS:
        raise ValueError(
            f"validation plan requires at least {MIN_VALIDATION_PAIRS} paired trials; "
            "increase --trials or add validation tasks"
        )
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if not solver_model.strip():
        raise ValueError("solver_model must not be empty")
    solver_seed_mode = model_seed_mode(solver_model)
    if solver_seed_mode != "forwarded":
        raise ValueError(f"Solver model {solver_model!r} does not support seeded completions")
    if solver_backend is not None:
        require_seed_support(solver_backend, seed, label="Solver backend")
    legacy_temperature = os.environ.get("EVO_LLM_TEMPERATURE")
    legacy_reasoning_effort = llm_reasoning_effort()
    solver_temperature = _temperature(
        solver_temperature if solver_temperature is not None else legacy_temperature,
        "solver_temperature",
    )
    editor_temperature = _temperature(
        editor_temperature if editor_temperature is not None else legacy_temperature,
        "editor_temperature",
    )
    solver_reasoning_effort = _reasoning_effort(
        solver_reasoning_effort if solver_reasoning_effort is not None else legacy_reasoning_effort,
        "solver_reasoning_effort",
    )
    editor_reasoning_effort = _reasoning_effort(
        editor_reasoning_effort if editor_reasoning_effort is not None else legacy_reasoning_effort,
        "editor_reasoning_effort",
    )
    if agent_permission not in ("safe", "unsafe"):
        raise ValueError("agent_permission must be 'safe' or 'unsafe'")
    if resume and dry_run:
        raise ValueError("dry_run and resume cannot be combined")
    mode = normalize_rewrite_mode(rewrite_mode)
    if mode == "agentic-session":
        raise ValueError("agentic-session is not supported by the multi-task optimizer")

    split_manifest = _coerce_manifest(manifest)
    if split_manifest:
        split_manifest.assert_no_leakage(
            train_ids, scope="skill_evolution", context="optimizer training"
        )
        invalid_validation = sorted(set(validation_ids) - split_manifest.val_ids())
        if invalid_validation:
            raise ValueError(
                f"validation tasks must belong to manifest split 'val': {invalid_validation}"
            )

    tasks = _load_tasks(task_root, [*train_ids, *validation_ids])
    store = SkillStore(project_dir=project, user_dir=Path.home())
    if not store.has(skill_name):
        raise KeyError(f"Skill {skill_name!r} not found")
    target = store.get(skill_name)
    resume_id = validate_run_id(resume) if resume else None
    resume_path = (
        target.path / ".evolution" / "runs" / resume_id / "run.json" if resume_id else None
    )
    saved_state = read_state(resume_path) if resume_path else None
    if saved_state and (
        saved_state.get("schema") != RUN_SCHEMA or saved_state.get("run_id") != resume_id
    ):
        raise ValueError("Invalid optimizer run state")
    if (
        saved_state
        and saved_state.get("status") not in {"completed", "inconclusive"}
        and "edit_brake" not in (saved_state.get("identity") or {})
    ):
        raise ValueError("Legacy partial optimizer run cannot resume; start a fresh run")
    if (
        saved_state
        and saved_state.get("status") not in {"completed", "inconclusive"}
        and any(
            "candidate_version" in round_state for round_state in (saved_state.get("rounds") or [])
        )
    ):
        raise ValueError("Legacy partial optimizer run cannot resume; start a fresh run")
    initial_version = (
        str(saved_state["initial_version"])
        if saved_state
        else LineageTracker(target).current_version
    )
    if not VersionStore(target).exists(initial_version):
        raise ValueError(f"Active version {initial_version!r} has no snapshot")
    bindings = _resolve_bindings(
        store=store,
        project=project,
        target=target,
        task_ids=[*train_ids, *validation_ids],
        tasks=tasks,
    )
    bindings = {
        task_id: _bindings_for_version(selected, target=target, version=initial_version)
        for task_id, selected in bindings.items()
    }

    resolved_tokens = llm_max_tokens(max_tokens)
    solver_runtime = {
        "api_base": solver_api_base if solver_api_base is not None else api_base,
        "temperature": solver_temperature,
        "reasoning_effort": solver_reasoning_effort,
    }
    editor_runtime = {
        "api_base": editor_api_base if editor_api_base is not None else api_base,
        "temperature": editor_temperature,
        "reasoning_effort": editor_reasoning_effort,
    }
    # ``None`` means the backend's model-family auto policy; model IDs already
    # live in the identity, so duplicating that policy here would let it drift.
    runtime = {
        "solver": {**solver_runtime, "api_base": _sanitized_api_base(solver_runtime["api_base"])},
        "editor": {**editor_runtime, "api_base": _sanitized_api_base(editor_runtime["api_base"])},
    }
    identity = _resume_identity(
        skill_name=skill_name,
        initial_version=initial_version,
        target=target,
        task_ids=[*train_ids, *validation_ids],
        train_ids=train_ids,
        validation_ids=validation_ids,
        tasks=tasks,
        bindings=bindings,
        solver_model=solver_model,
        solver_seed_mode=solver_seed_mode,
        editor_model=editor_model or solver_model,
        rounds=rounds,
        trials=trials,
        seed=seed,
        rewrite_mode=mode,
        max_tokens=resolved_tokens,
        agent_permission=agent_permission,
        runtime=runtime,
        pass_env=pass_env,
        manifest=split_manifest,
        base_budget=base_budget,
        version_decay=version_decay,
        max_rewrite_attempts=max_rewrite_attempts,
    )
    identity_sha = json_digest(identity)
    if saved_state and not _resume_identity_matches(saved_state, identity, identity_sha):
        raise ValueError("Resume identity does not match the saved run")

    plan = _call_plan(
        train_ids=train_ids,
        validation_ids=validation_ids,
        rounds=rounds,
        trials=trials,
        seed=seed,
        solver_model=solver_model,
        solver_seed_mode=solver_seed_mode,
        editor_model=editor_model or solver_model,
        rewrite_mode=mode,
        runtime=runtime,
    )
    if dry_run:
        return OptimizationResult(
            run_id="dry-run",
            status="dry_run",
            skill_name=skill_name,
            initial_version=initial_version,
            final_version=initial_version,
            rounds=[],
            run_path=None,
            plan=plan,
        )

    run_id = resume_id or new_run_id()
    run_path = target.path / ".evolution" / "runs" / run_id / "run.json"
    with optimizer_lease(target.path):
        tracker = LineageTracker(target)
        versions = VersionStore(target)
        if versions.digest(initial_version) != identity["initial_sha256"]:
            raise RuntimeError("optimizer_parent_changed")
        if not saved_state and tracker.current_version != initial_version:
            raise RuntimeError("optimizer_parent_changed")
        if resume_path is not None:
            saved_state = read_state(resume_path)
            if (
                saved_state.get("schema") != RUN_SCHEMA
                or saved_state.get("run_id") != resume_id
                or not _resume_identity_matches(saved_state, identity, identity_sha)
            ):
                raise ValueError("Resume identity does not match the saved run")
        if saved_state:
            state = saved_state
            migrated_identity = state.get("identity_sha256") != identity_sha
            if migrated_identity:
                state["identity"] = identity
                state["identity_sha256"] = identity_sha
            if state.get("status") in {"completed", "inconclusive"}:
                if migrated_identity:
                    write_state(run_path, state)
                return result_from_state(state, run_path)
            _repair_interrupted_promotion(target, tracker, versions, state, run_path)
            state["status"] = "running"
            state["error"] = None
        else:
            if run_path.exists():
                raise FileExistsError(f"Optimizer run already exists: {run_id}")
            _require_clean_active(target, initial_version)
            state = {
                "schema": RUN_SCHEMA,
                "run_id": run_id,
                "skill_name": skill_name,
                "created_at": now(),
                "updated_at": now(),
                "identity": identity,
                "identity_sha256": identity_sha,
                "status": "running",
                "phase": "preflight",
                "initial_version": initial_version,
                "final_version": initial_version,
                "rounds": [],
                "error": None,
                "reason": None,
                "recommendation": None,
            }
        _require_clean_active(target, tracker.current_version)
        write_state(run_path, state)
        solver_backend_kwargs: dict[str, Any] = {"max_tokens": resolved_tokens}
        editor_backend_kwargs: dict[str, Any] = {"max_tokens": resolved_tokens}
        for key, value in solver_runtime.items():
            if value is not None and value != "":
                solver_backend_kwargs[key] = value
        for key, value in editor_runtime.items():
            if value is not None and value != "":
                editor_backend_kwargs[key] = value
        try:
            solve_backend = solver_backend or get_backend(
                solver_model, agent_permission=agent_permission, **solver_backend_kwargs
            )
            edit_backend = editor_backend or get_backend(
                editor_model or solver_model,
                agent_permission=agent_permission,
                **editor_backend_kwargs,
            )
            _run_rounds(
                state=state,
                state_path=run_path,
                target=target,
                tracker=tracker,
                versions=versions,
                tasks=tasks,
                train_ids=train_ids,
                validation_ids=validation_ids,
                bindings=bindings,
                rounds=rounds,
                trials=trials,
                seed=seed,
                solver_model=solver_model,
                solver_backend=solve_backend,
                editor_backend=edit_backend,
                rewrite_mode=mode,
                project=project,
                timeout=timeout,
                manifest=split_manifest,
                pass_env=pass_env,
                base_budget=base_budget,
                version_decay=version_decay,
                max_rewrite_attempts=max_rewrite_attempts,
            )
        except BaseException as exc:
            reason_code = _failure_code(exc)
            fail_state(run_path, state, reason_code)
            if isinstance(exc, Exception):
                raise OptimizationRunError(reason_code) from exc
            raise
    return result_from_state(state, run_path)


def _unique(values: Sequence[str], label: str) -> list[str]:
    result = [str(value).strip() for value in values if str(value).strip()]
    if not result:
        raise ValueError(f"at least one {label} task is required")
    if len(result) != len(set(result)):
        raise ValueError(f"duplicate {label} task ids are not allowed")
    invalid = [value for value in result if Path(value).name != value or value in {".", ".."}]
    if invalid:
        raise ValueError(f"invalid {label} task id: {invalid[0]!r}")
    return result


def _temperature(value: float | str | None, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number between 0 and 2") from exc
    if not math.isfinite(normalized) or not 0 <= normalized <= 2:
        raise ValueError(f"{label} must be a finite number between 0 and 2")
    return normalized


def _reasoning_effort(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized not in {"off", "low", "medium", "high", "xhigh"}:
        raise ValueError(f"{label} must be one of: off, low, medium, high, xhigh")
    return normalized


def _sanitized_api_base(value: object) -> str | None:
    if not value:
        return None
    parsed = urlsplit(str(value).strip())
    try:
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError("api_base must be an absolute HTTP(S) URL") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not host:
        raise ValueError("api_base must be an absolute HTTP(S) URL")
    if ":" in host:
        host = f"[{host}]"
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("api_base has an invalid port") from exc
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _resume_identity_matches(
    saved_state: dict[str, Any], identity: dict[str, Any], identity_sha: str
) -> bool:
    saved_identity = saved_state.get("identity")
    if not isinstance(saved_identity, dict) or saved_identity.get(
        "solver_seed_mode"
    ) != identity.get("solver_seed_mode"):
        return False
    if saved_state.get("identity_sha256") == identity_sha:
        return True
    legacy = dict(identity)
    legacy.pop("runtime", None)
    return saved_identity == legacy and saved_state.get("identity_sha256") == json_digest(legacy)


def _load_tasks(root: Path, task_ids: list[str]) -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for task_id in task_ids:
        path = (root / task_id).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Task {task_id!r} resolves outside the task root")
        try:
            task = load_task(path)
        except (FileNotFoundError, ValueError) as exc:
            raise KeyError(f"Task {task_id!r} not found under the task root") from exc
        if task.name != task_id:
            raise ValueError(f"Task directory {task_id!r} declares name {task.name!r}")
        tasks[task_id] = task
    return tasks


def _resolve_bindings(
    *,
    store: SkillStore,
    project: Path,
    target: Skill,
    task_ids: list[str],
    tasks: dict[str, Task],
) -> dict[str, list[SkillBinding]]:
    result: dict[str, list[SkillBinding]] = {}
    target_path = target.path.resolve()
    for task_id in task_ids:
        selected = resolve_skill_bindings(
            tasks[task_id].skills_required,
            store=store,
            project_dir=project,
        )
        if sum(binding.owner.path.resolve() == target_path for binding in selected) != 1:
            raise ValueError(f"Task {task_id!r} must require target skill exactly once")
        result[task_id] = selected
    return result


def _resume_identity(
    *,
    skill_name: str,
    initial_version: str,
    target: Skill,
    task_ids: list[str],
    train_ids: list[str],
    validation_ids: list[str],
    tasks: dict[str, Task],
    bindings: dict[str, list[SkillBinding]],
    solver_model: str,
    solver_seed_mode: SeedMode,
    editor_model: str,
    rounds: int,
    trials: int,
    seed: int,
    rewrite_mode: str,
    max_tokens: int,
    agent_permission: str,
    runtime: dict[str, dict[str, Any]],
    pass_env: Collection[str],
    manifest: SplitManifest | None,
    base_budget: float,
    version_decay: bool,
    max_rewrite_attempts: int,
) -> dict[str, Any]:
    """Build a location-free resume identity from logical IDs and content hashes."""

    return {
        "skill_id": skill_name,
        "initial_version": initial_version,
        "initial_sha256": VersionStore(target).digest(initial_version),
        "train_tasks": list(train_ids),
        "validation_tasks": list(validation_ids),
        "tasks": {task_id: tree_digest(tasks[task_id].path) for task_id in task_ids},
        "bindings": {
            task_id: [
                {
                    "skill_id": binding.owner.path.name,
                    "version": binding.version,
                    "sha256": binding.sha256,
                }
                for binding in bindings[task_id]
            ]
            for task_id in task_ids
        },
        "solver_model": solver_model,
        "solver_seed_mode": solver_seed_mode,
        "editor_model": editor_model,
        "rounds": rounds,
        "trials": trials,
        "seed": seed,
        "rewrite_mode": rewrite_mode,
        "max_tokens": max_tokens,
        "agent_permission": agent_permission,
        "runtime": runtime,
        "pass_env": sorted(set(pass_env)),
        "manifest": ({"id": manifest.name, "sha256": manifest.sha256} if manifest else None),
        "edit_brake": {
            "metric_revision": METRIC_REVISION,
            "base_budget_frac": base_budget,
            "version_decay_enabled": version_decay,
            "schedule": SCHEDULE if version_decay else "constant-v1",
            "floor_frac": min(base_budget, DECAY_FLOOR),
            "promotion_count_source": "retained-parent-ancestry",
            "max_rewrite_attempts": max_rewrite_attempts,
        },
    }


def _run_rounds(
    *,
    state: dict[str, Any],
    state_path: Path,
    target: Skill,
    tracker: LineageTracker,
    versions: VersionStore,
    tasks: dict[str, Task],
    train_ids: list[str],
    validation_ids: list[str],
    bindings: dict[str, list[SkillBinding]],
    rounds: int,
    trials: int,
    seed: int,
    solver_model: str,
    solver_backend: LLMBackend,
    editor_backend: LLMBackend,
    rewrite_mode: str,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    pass_env: Collection[str],
    base_budget: float,
    version_decay: bool,
    max_rewrite_attempts: int,
) -> None:
    for round_index in range(rounds):
        if round_index < len(state["rounds"]):
            round_state = state["rounds"][round_index]
        else:
            parent_version = tracker.current_version
            _require_clean_active(target, parent_version)
            round_state = {
                "round": round_index,
                "round_id": f"{state['run_id']}.r{round_index:03d}",
                "parent_version": parent_version,
                "parent_sha256": versions.digest(parent_version),
                "promotion_count": tracker.promotion_count(parent_version),
                "reserved_version": tracker.next_version_label(),
                "saturation": {"measurements": {}, "saturated": None},
                "collect": {},
                "reflection": None,
                "rewrite": None,
                "candidate_artifact": None,
                "candidate_sha256": None,
                "candidate_train_diagnostic": {"measurements": {}},
                "validation": {
                    "measurements": {"parent": {}, "candidate": {}},
                    "decision": None,
                    "telemetry": None,
                },
                "outcome": None,
            }
            state["rounds"].append(round_state)
            checkpoint(state_path, state, "round_setup")

        if round_state.get("outcome"):
            continue
        parent_version = str(round_state["parent_version"])
        if versions.digest(parent_version) != round_state["parent_sha256"]:
            raise RuntimeError("parent_content_tampered")
        parent_skill = versions.load(parent_version)

        if round_state.get("rewrite") is None:
            if _parent_saturation_preflight(
                state=state,
                state_path=state_path,
                round_state=round_state,
                target=target,
                tasks=tasks,
                validation_ids=validation_ids,
                trials=trials,
                seed=seed,
                round_index=round_index,
                parent_version=parent_version,
                backend=solver_backend,
                project=project,
                timeout=timeout,
                manifest=manifest,
                bindings=bindings,
                pass_env=pass_env,
            ):
                round_state["outcome"] = "inconclusive"
                round_state["reason"] = "validation_saturated"
                round_state["recommendation"] = SATURATION_RECOMMENDATION
                state["status"] = "inconclusive"
                state["reason"] = "validation_saturated"
                state["recommendation"] = SATURATION_RECOMMENDATION
                state["final_version"] = tracker.current_version
                checkpoint(state_path, state, "inconclusive")
                return
            _collect_round(
                state=state,
                state_path=state_path,
                round_state=round_state,
                target=target,
                parent_version=parent_version,
                tasks=tasks,
                train_ids=train_ids,
                trials=trials,
                seed=seed,
                solver_model=solver_model,
                backend=solver_backend,
                project=project,
                timeout=timeout,
                manifest=manifest,
                bindings=bindings,
                pass_env=pass_env,
            )
            reflection_ids = round_state.get("reflection")
            if reflection_ids is None:
                reflections = _reflect_round(
                    skill=_owner_view(target, parent_skill),
                    backend=editor_backend,
                    tasks=tasks,
                    train_ids=train_ids,
                    trace_ids=[str(entry["trace_id"]) for entry in round_state["collect"].values()],
                    manifest=manifest,
                )
                round_state["reflection"] = [
                    str(item.get("trace_id")) for item in reflections if item.get("trace_id")
                ]
                checkpoint(state_path, state, "reflection")
            else:
                reflections = _load_round_reflections(target, list(reflection_ids))
            if not reflections:
                round_state["rewrite"] = {"status": "no_reflections"}
            else:
                outcome = _rewrite_round(
                    skill=_owner_view(target, parent_skill),
                    backend=editor_backend,
                    reflections=reflections,
                    rewrite_mode=rewrite_mode,
                    promotion_count=int(round_state["promotion_count"]),
                    parent_version=parent_version,
                    base_budget=base_budget,
                    version_decay=version_decay,
                    max_rewrite_attempts=max_rewrite_attempts,
                    audit_root=state_path.parent / "rewrite_attempts",
                )
                rewrite: dict[str, Any] = {"status": outcome.candidate_status}
                rewrite["edit_brake"] = outcome.edit_brake
                rewrite["rewrite_attempts"] = outcome.rewrite_attempts
                if outcome.candidate_status == PROMOTED_ELIGIBLE:
                    rewrite["candidate_body"] = outcome.body
                    rewrite["candidate_body_sha256"] = _text_digest(outcome.body)
                round_state["rewrite"] = rewrite
            checkpoint(state_path, state, "rewrite")

        rewrite = round_state["rewrite"] or {}
        if rewrite.get("status") != PROMOTED_ELIGIBLE:
            round_state["outcome"] = "rewrite_rejected"
            checkpoint(state_path, state, "round_complete")
            continue

        candidate_body = str(rewrite["candidate_body"])
        if _text_digest(candidate_body) != rewrite.get("candidate_body_sha256"):
            raise RuntimeError("candidate_content_tampered")
        candidate_hash = _save_candidate_tree(
            versions,
            parent_version=parent_version,
            candidates_dir=state_path.parent / "candidates",
            body=candidate_body,
        )
        expected_hash = round_state.get("candidate_sha256")
        if expected_hash and expected_hash != candidate_hash:
            raise RuntimeError("candidate_content_tampered")
        round_state["candidate_artifact"] = candidate_hash
        round_state["candidate_sha256"] = candidate_hash
        checkpoint(state_path, state, "candidate_artifact")
        candidate_path = _candidate_path(state_path, candidate_hash)

        _candidate_train_diagnostic(
            state=state,
            state_path=state_path,
            round_state=round_state,
            target=target,
            tasks=tasks,
            train_ids=train_ids,
            trials=trials,
            candidate_path=candidate_path,
            backend=solver_backend,
            project=project,
            timeout=timeout,
            manifest=manifest,
            bindings=bindings,
            pass_env=pass_env,
        )

        _validate_round(
            state=state,
            state_path=state_path,
            round_state=round_state,
            target=target,
            tasks=tasks,
            validation_ids=validation_ids,
            trials=trials,
            seed=seed,
            round_index=round_index,
            parent_version=parent_version,
            candidate_path=candidate_path,
            backend=solver_backend,
            project=project,
            timeout=timeout,
            manifest=manifest,
            bindings=bindings,
            pass_env=pass_env,
        )

        validation = round_state["validation"]
        if validation.get("decision") is None:
            measurements = validation["measurements"]
            parent_rates = {
                task_id: [float(item["pass_rate"]) for item in measurements["parent"][task_id]]
                for task_id in validation_ids
            }
            candidate_rates = {
                task_id: [float(item["pass_rate"]) for item in measurements["candidate"][task_id]]
                for task_id in validation_ids
            }
            promote, telemetry = conservative_paired_gate(parent_rates, candidate_rates, alpha=0.10)
            validation["decision"] = (
                "promote"
                if promote
                else ("inconclusive" if telemetry.get("reason") == "underpowered" else "reject")
            )
            validation["telemetry"] = telemetry
            checkpoint(state_path, state, "promotion_decision")

        if validation["decision"] == "promote":
            _verify_candidate(candidate_path, round_state)
            _require_unchanged_parent(target, tracker, versions, parent_version)
            candidate_version = str(round_state["reserved_version"])
            _promote_candidate_tree(versions, candidate_path, candidate_version)
            _ensure_candidate(tracker, candidate_version, parent_version, rewrite_mode)
            tracker.promote(candidate_version)
            round_state["outcome"] = "promoted"
        elif validation["decision"] == "inconclusive":
            round_state["outcome"] = "inconclusive"
            round_state["reason"] = "underpowered"
            round_state["recommendation"] = UNDERPOWERED_RECOMMENDATION
            state["status"] = "inconclusive"
            state["reason"] = "underpowered"
            state["recommendation"] = UNDERPOWERED_RECOMMENDATION
            state["final_version"] = tracker.current_version
            checkpoint(state_path, state, "inconclusive")
            return
        else:
            round_state["outcome"] = "rejected"
        state["final_version"] = tracker.current_version
        checkpoint(state_path, state, "round_complete")

    state["status"] = "completed"
    state["phase"] = "complete"
    state["final_version"] = tracker.current_version
    write_state(state_path, state)


def _parent_saturation_preflight(
    *,
    state: dict[str, Any],
    state_path: Path,
    round_state: dict[str, Any],
    target: Skill,
    tasks: dict[str, Task],
    validation_ids: list[str],
    trials: int,
    seed: int,
    round_index: int,
    parent_version: str,
    backend: LLMBackend,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    bindings: dict[str, list[SkillBinding]],
    pass_env: Collection[str],
) -> bool:
    saturation = round_state.setdefault("saturation", {"measurements": {}, "saturated": None})
    if saturation.get("saturated") is not None:
        return bool(saturation["saturated"])
    measurements = saturation.setdefault("measurements", {})
    for task_id in validation_ids:
        records = measurements.setdefault(task_id, [])
        selected = _bindings_for_version(bindings[task_id], target=target, version=parent_version)
        for trial in range(trials):
            attempt_seed = _stable_seed(seed, "validation_saturation", round_index, task_id, trial)
            if len(records) > trial:
                if int(records[trial]["seed"]) != attempt_seed:
                    raise RuntimeError("validation_seed_mismatch")
                continue
            measurement = _validate_one(
                arm="parent",
                seed=attempt_seed,
                phase="validation_saturation",
                task=tasks[task_id],
                backend=backend,
                project=project,
                timeout=timeout,
                manifest=manifest,
                bindings=selected,
                pass_env=pass_env,
            )
            records.append(measurement.to_dict())
            checkpoint(state_path, state, "validation_saturation")
    saturation["saturated"] = all(
        float(item["pass_rate"]) >= 1.0 - 1e-9
        for records in measurements.values()
        for item in records
    )
    checkpoint(state_path, state, "validation_saturation")
    return bool(saturation["saturated"])


def _candidate_train_diagnostic(
    *,
    state: dict[str, Any],
    state_path: Path,
    round_state: dict[str, Any],
    target: Skill,
    tasks: dict[str, Task],
    train_ids: list[str],
    trials: int,
    candidate_path: Path,
    backend: LLMBackend,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    bindings: dict[str, list[SkillBinding]],
    pass_env: Collection[str],
) -> None:
    diagnostic = round_state.setdefault("candidate_train_diagnostic", {"measurements": {}})
    measurements = diagnostic.setdefault("measurements", {})
    for task_id in train_ids:
        records = measurements.setdefault(task_id, [])
        selected = _bindings_for_candidate(bindings[task_id], target=target, path=candidate_path)
        for trial in range(trials):
            attempt_seed = int(round_state["collect"][f"{task_id}#{trial}"]["seed"])
            if len(records) > trial:
                if int(records[trial]["seed"]) != attempt_seed:
                    raise RuntimeError("validation_seed_mismatch")
                continue
            measurement = _validate_one(
                arm="candidate",
                seed=attempt_seed,
                phase="candidate_train_diagnostic",
                task=tasks[task_id],
                backend=backend,
                project=project,
                timeout=timeout,
                manifest=manifest,
                bindings=selected,
                pass_env=pass_env,
            )
            records.append(measurement.to_dict())
            checkpoint(state_path, state, "candidate_train_diagnostic")


def _collect_round(
    *,
    state: dict[str, Any],
    state_path: Path,
    round_state: dict[str, Any],
    target: Skill,
    parent_version: str,
    tasks: dict[str, Task],
    train_ids: list[str],
    trials: int,
    seed: int,
    solver_model: str,
    backend: LLMBackend,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    bindings: dict[str, list[SkillBinding]],
    pass_env: Collection[str],
) -> None:
    for task_index, task_id in enumerate(train_ids):
        selected = _bindings_for_version(bindings[task_id], target=target, version=parent_version)
        for trial in range(trials):
            key = f"{task_id}#{trial}"
            if key in round_state["collect"]:
                continue
            attempt_seed = _stable_seed(seed, "collect", int(round_state["round"]), task_id, trial)
            trace_id = _find_collect_trace(
                target,
                task_id=task_id,
                round_id=str(round_state["round_id"]),
                seed=attempt_seed,
                trace_spec_idx=task_index * trials + trial,
            )
            if trace_id is None:
                trace_id = _collect_one(
                    target=target,
                    task=tasks[task_id],
                    backend=backend,
                    model=solver_model,
                    project=project,
                    timeout=timeout,
                    manifest=manifest,
                    round_id=str(round_state["round_id"]),
                    attempt_seed=attempt_seed,
                    trace_spec_idx=task_index * trials + trial,
                    trial=trial,
                    bindings=selected,
                    pass_env=pass_env,
                )
            round_state["collect"][key] = {"seed": attempt_seed, "trace_id": trace_id}
            checkpoint(state_path, state, "collect")


def _collect_one(
    *,
    target: Skill,
    task: Task,
    backend: LLMBackend,
    model: str,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    round_id: str,
    attempt_seed: int,
    trace_spec_idx: int,
    trial: int,
    bindings: list[SkillBinding],
    pass_env: Collection[str],
) -> str:
    del trial
    with tempfile.TemporaryDirectory(prefix="evo-opt-collect-") as tmp:
        workspace = setup_workspace(task, Path(tmp) / "workspace", project_dir=project)
        result = solve_task(
            task,
            backend,
            workspace,
            bindings=bindings,
            timeout=timeout,
            model_name=model,
            manifest=manifest,
            manifest_scope="skill_evolution" if manifest else None,
            attempt_seed=attempt_seed,
            trace_spec_idx=trace_spec_idx,
            round_id=round_id,
            phase="collect",
            trace_required=True,
            pass_env=pass_env,
        )
    error = _measurement_error_code(result)
    if error:
        raise RuntimeError(error)
    target_indexes = [
        index
        for index, binding in enumerate(bindings)
        if binding.owner.path.resolve() == target.path.resolve()
    ]
    if len(target_indexes) != 1 or len(result.trace_ids) != len(bindings):
        raise RuntimeError("training_trace_missing")
    return str(result.trace_ids[target_indexes[0]])


def _reflect_round(
    *,
    skill: Skill,
    backend: LLMBackend,
    tasks: dict[str, Task],
    train_ids: list[str],
    trace_ids: list[str],
    manifest: SplitManifest | None,
) -> list[dict[str, Any]]:
    for task_id in train_ids:
        reflect_failing_traces(
            backend,
            skill,
            tasks[task_id].instruction,
            task_filter=task_id,
            manifest=manifest,
            scope="skill_evolution",
            strict=True,
            require_v3_evidence=manifest is not None,
            trace_ids=trace_ids,
        )
    wanted = set(trace_ids)
    return [
        item
        for item in collect_reflections(skill, manifest=manifest, scope="skill_evolution")
        if str(item.get("trace_id")) in wanted
    ]


def _load_round_reflections(skill: Skill, trace_ids: list[str]) -> list[dict[str, Any]]:
    store = TraceStore(skill)
    reflections: list[dict[str, Any]] = []
    for trace_id in trace_ids:
        trace_dir = store.resolve_trace_dir(trace_id)
        item = load_reflection(trace_dir)
        if item is None:
            raise RuntimeError("reflection_checkpoint_missing")
        reflections.append(item)
    return reflections


def _rewrite_round(
    *,
    skill: Skill,
    backend: LLMBackend,
    reflections: list[dict[str, Any]],
    rewrite_mode: str,
    promotion_count: int,
    parent_version: str,
    base_budget: float,
    version_decay: bool,
    max_rewrite_attempts: int,
    audit_root: Path | None = None,
) -> RewriteOutcome:
    return asyncio.run(
        rewrite_skill_with_audit(
            backend,
            skill,
            reflections,
            include_best_trace_code=False,
            rewrite_mode=rewrite_mode,
            promotion_count=promotion_count,
            parent_version=parent_version,
            base_budget=base_budget,
            version_decay=version_decay,
            max_rewrite_attempts=max_rewrite_attempts,
            audit_root=audit_root,
        )
    )


def _validate_round(
    *,
    state: dict[str, Any],
    state_path: Path,
    round_state: dict[str, Any],
    target: Skill,
    tasks: dict[str, Task],
    validation_ids: list[str],
    trials: int,
    seed: int,
    round_index: int,
    parent_version: str,
    candidate_path: Path,
    backend: LLMBackend,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    bindings: dict[str, list[SkillBinding]],
    pass_env: Collection[str],
) -> None:
    measurements = round_state["validation"]["measurements"]
    for arm in ("parent", "candidate"):
        for task_id in validation_ids:
            measurements[arm].setdefault(task_id, [])
    for pair in paired_schedule(
        validation_ids, trials=trials, base_seed=seed, round_index=round_index
    ):
        for arm in pair.arms:
            records = measurements[arm][pair.task_id]
            if len(records) > pair.trial:
                if int(records[pair.trial]["seed"]) != pair.seed:
                    raise RuntimeError("validation_seed_mismatch")
                continue
            selected = (
                _bindings_for_version(bindings[pair.task_id], target=target, version=parent_version)
                if arm == "parent"
                else _bindings_for_candidate(
                    bindings[pair.task_id], target=target, path=candidate_path
                )
            )
            measurement = _validate_one(
                arm=arm,
                seed=pair.seed,
                phase="promotion_validation",
                task=tasks[pair.task_id],
                backend=backend,
                project=project,
                timeout=timeout,
                manifest=manifest,
                bindings=selected,
                pass_env=pass_env,
            )
            records.append(measurement.to_dict())
            checkpoint(state_path, state, "validation")


def _validate_one(
    *,
    arm: str,
    seed: int,
    phase: str,
    task: Task,
    backend: LLMBackend,
    project: Path,
    timeout: float,
    manifest: SplitManifest | None,
    bindings: list[SkillBinding],
    pass_env: Collection[str],
) -> ValidationMeasurement:
    del arm
    reason_code = "validation_failed"
    for _attempt in range(2):
        try:
            with tempfile.TemporaryDirectory(prefix="evo-opt-validation-") as tmp:
                workspace = setup_workspace(task, Path(tmp) / "workspace", project_dir=project)
                result = solve_task(
                    task,
                    backend,
                    workspace,
                    bindings=bindings,
                    timeout=timeout,
                    model_name="",
                    manifest=manifest,
                    manifest_scope=(
                        "skill_evolution"
                        if manifest and phase == "candidate_train_diagnostic"
                        else ("dev" if manifest else None)
                    ),
                    attempt_seed=seed,
                    phase=phase,
                    pass_env=pass_env,
                )
            reason_code = _measurement_error_code(result) or ""
            if result.trace_ids:
                reason_code = "validation_trace_persisted"
            if not reason_code:
                evaluated = result.eval_result
                assert evaluated is not None
                return ValidationMeasurement(
                    seed=seed,
                    passed=evaluated.passed,
                    total=evaluated.total_tests,
                    pass_rate=evaluated.pass_rate,
                )
        except Exception as exc:
            reason_code = _failure_code(exc)
    raise RuntimeError(reason_code)


def _measurement_error_code(result: SolveResult) -> str | None:
    if result.llm_transport_failed:
        return "model_transport_failed"
    if result.solve_exception:
        return "solve_exception"
    if any(str(error).startswith("output collection failed:") for error in result.errors):
        return "output_collection_failed"
    evaluated = result.eval_result
    if evaluated is None:
        return "evaluator_missing"
    if evaluated.total_tests <= 0:
        return "evaluator_no_tests"
    if any(not str(error).startswith("FAILED ") for error in evaluated.errors):
        return "evaluator_failed"
    if evaluated.passed + evaluated.failed <= 0:
        return "evaluator_no_scored_tests"
    return None


def _bindings_for_version(
    bindings: list[SkillBinding], *, target: Skill, version: str
) -> list[SkillBinding]:
    target_path = target.path.resolve()
    result: list[SkillBinding] = []
    replaced = 0
    for binding in bindings:
        if binding.owner.path.resolve() != target_path:
            result.append(binding)
            continue
        result.append(
            SkillBinding.pinned(
                target,
                version,
                name=binding.name,
                source="optimizer-version",
                container=binding.container,
                snapshot=binding.snapshot,
            )
        )
        replaced += 1
    if replaced != 1:
        raise ValueError("target_binding_missing")
    return result


def _bindings_for_candidate(
    bindings: list[SkillBinding], *, target: Skill, path: Path
) -> list[SkillBinding]:
    target_path = target.path.resolve()
    candidate = load_skill(path, validate_dir_name=False)
    digest = hash_managed_tree(path)
    result: list[SkillBinding] = []
    replaced = 0
    for binding in bindings:
        if binding.owner.path.resolve() != target_path:
            result.append(binding)
            continue
        result.append(
            SkillBinding(
                name=binding.name,
                skill=candidate,
                owner=target,
                version=f"candidate@{digest[:12]}",
                sha256=digest,
                source="optimizer-candidate",
                container=binding.container,
                snapshot=binding.snapshot,
            )
        )
        replaced += 1
    if replaced != 1:
        raise ValueError("target_binding_missing")
    return result


def _owner_view(owner: Skill, content: Skill) -> Skill:
    return content.model_copy(update={"path": owner.path, "skill_md_path": owner.skill_md_path})


def _save_candidate_tree(
    versions: VersionStore,
    *,
    parent_version: str,
    candidates_dir: Path,
    body: str,
) -> str:
    parent = versions.load(parent_version)
    candidates_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".optimizer-candidate-", dir=candidates_dir) as tmp:
        staged = Path(tmp) / "candidate"
        shutil.copytree(parent.path, staged, symlinks=True)
        hash_tree(staged)
        atomic_write_text(
            staged / "SKILL.md",
            _skill_md_with_body(parent.skill_md_path.read_text(encoding="utf-8"), body),
        )
        expected = hash_managed_tree(staged)
        destination = candidates_dir / expected
        if destination.exists():
            actual = hash_managed_tree(destination)
            if actual != expected:
                raise RuntimeError("candidate_content_tampered")
            return actual
        staged.rename(destination)
        fsync_directory(candidates_dir)
        return expected


def _skill_md_with_body(parent_text: str, body: str) -> str:
    lines = parent_text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("parent_skill_frontmatter_invalid")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            prefix = "".join(lines[: index + 1]).rstrip("\r\n")
            return f"{prefix}\n\n{body.strip()}\n"
    raise ValueError("parent_skill_frontmatter_invalid")


def _ensure_candidate(
    tracker: LineageTracker,
    version: str,
    parent_version: str,
    rewrite_mode: str,
) -> None:
    try:
        entry = tracker.get_entry(version)
    except KeyError:
        tracker.record(
            LineageEntry(
                version=version,
                timestamp=datetime.now(UTC),
                origin="mutation",
                parent=parent_version,
                mutation_type=f"optimize-{rewrite_mode}",
                status="candidate",
            )
        )
        return
    if entry.parent != parent_version:
        raise RuntimeError("candidate_parent_mismatch")


def _candidate_path(state_path: Path, candidate_sha256: str) -> Path:
    return state_path.parent / "candidates" / candidate_sha256


def _verify_candidate(path: Path, round_state: dict[str, Any]) -> None:
    if hash_managed_tree(path) != round_state["candidate_sha256"]:
        raise RuntimeError("candidate_content_tampered")


def _promote_candidate_tree(versions: VersionStore, candidate_path: Path, version: str) -> None:
    destination = versions.versions_dir / version
    expected = hash_managed_tree(candidate_path)
    if destination.exists():
        if hash_managed_tree(destination) != expected:
            raise RuntimeError("candidate_content_tampered")
        return
    with tempfile.TemporaryDirectory(prefix=f".{version}-", dir=versions.versions_dir) as tmp:
        staged = Path(tmp) / "candidate"
        shutil.copytree(candidate_path, staged, symlinks=True)
        if hash_managed_tree(staged) != expected:
            raise RuntimeError("candidate_content_tampered")
        staged.rename(destination)
        fsync_directory(versions.versions_dir)


def _repair_interrupted_promotion(
    target: Skill,
    tracker: LineageTracker,
    versions: VersionStore,
    state: dict[str, Any],
    state_path: Path,
) -> None:
    for round_state in reversed(list(state.get("rounds") or [])):
        validation = round_state.get("validation") or {}
        if validation.get("decision") != "promote" or round_state.get("outcome"):
            continue
        candidate_sha256 = str(round_state.get("candidate_artifact") or "")
        if not candidate_sha256:
            raise ValueError("Legacy partial optimizer runs require a fresh run")
        candidate_path = _candidate_path(state_path, candidate_sha256)
        _verify_candidate(candidate_path, round_state)
        candidate = str(round_state["reserved_version"])
        current = tracker.current_version
        if current == candidate:
            _require_clean_active(target, candidate)
        elif current == str(round_state["parent_version"]):
            live = _managed_files_digest(target.path)
            parent = _managed_files_digest(versions.versions_dir / current)
            staged = _managed_files_digest(candidate_path)
            if live not in {parent, staged}:
                raise RuntimeError("promotion_parent_changed")
            _promote_candidate_tree(versions, candidate_path, candidate)
            _ensure_candidate(
                tracker,
                candidate,
                str(round_state["parent_version"]),
                str(state["identity"]["rewrite_mode"]),
            )
            tracker.promote(candidate)
        else:
            raise RuntimeError("promotion_parent_changed")
        round_state["outcome"] = "promoted"
        state["final_version"] = tracker.current_version
        checkpoint(state_path, state, "round_complete")
        return


def _require_unchanged_parent(
    target: Skill,
    tracker: LineageTracker,
    versions: VersionStore,
    parent_version: str,
) -> None:
    if tracker.current_version != parent_version:
        raise RuntimeError("promotion_parent_changed")
    if _managed_files_digest(target.path) != _managed_files_digest(
        versions.versions_dir / parent_version
    ):
        raise RuntimeError("promotion_parent_changed")


def _require_clean_active(skill: Skill, version: str) -> None:
    if _managed_files_digest(skill.path) != _managed_files_digest(
        VersionStore(skill).versions_dir / version
    ):
        raise ValueError(f"Working skill differs from active {version}")


def _managed_files_digest(root: Path) -> str:
    """Compare effective managed files while ignoring harmless empty scaffold dirs."""

    digest = hashlib.sha256(b"evolution-optimizer-clean-v1\0")
    paths = [root / "SKILL.md"]
    for name in ("scripts", "references", "assets"):
        directory = root / name
        if directory.exists():
            paths.extend(path for path in directory.rglob("*") if path.is_file())
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise ValueError(f"Managed skill files cannot be symlinks: {path}")
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(str(path.stat().st_mode & 0o111).encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def _find_collect_trace(
    target: Skill,
    *,
    task_id: str,
    round_id: str,
    seed: int,
    trace_spec_idx: int,
) -> str | None:
    matches: list[str] = []
    for entry in TraceStore(target).list(task=task_id):
        context = entry.get("trace_context") or {}
        if (
            context.get("phase") == "collect"
            and context.get("round_id") == round_id
            and context.get("attempt_seed") == seed
            and context.get("trace_spec_idx") == trace_spec_idx
            and context.get("scored_measurement_valid") is True
            and int(entry.get("total") or 0) > 0
        ):
            matches.append(str(entry["id"]))
    if len(matches) > 1:
        raise RuntimeError("duplicate_training_traces")
    return matches[0] if matches else None


def _stable_seed(base: int, phase: str, round_index: int, task_id: str, trial: int) -> int:
    return (
        int.from_bytes(
            hashlib.sha256(f"{base}\0{phase}\0{round_index}\0{task_id}\0{trial}".encode()).digest()[
                :4
            ],
            "big",
        )
        & 0x7FFFFFFF
    )


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _failure_code(exc: BaseException) -> str:
    text = str(exc)
    allowed = {
        "candidate_content_tampered",
        "candidate_parent_mismatch",
        "duplicate_training_traces",
        "editor_outage",
        "evaluator_failed",
        "evaluator_missing",
        "evaluator_no_scored_tests",
        "evaluator_no_tests",
        "model_transport_failed",
        "optimizer_parent_changed",
        "output_collection_failed",
        "parent_content_tampered",
        "promotion_interrupted",
        "promotion_parent_changed",
        "reflection_checkpoint_missing",
        "solve_exception",
        "target_binding_missing",
        "training_trace_missing",
        "validation_failed",
        "validation_unavailable",
        "validation_seed_mismatch",
        "validation_trace_persisted",
    }
    return text if text in allowed else type(exc).__name__.lower()


def _coerce_manifest(value: SplitManifest | Path | str | None) -> SplitManifest | None:
    if value is None or isinstance(value, SplitManifest):
        return value
    return SplitManifest.load(value)


def _call_plan(
    *,
    train_ids: list[str],
    validation_ids: list[str],
    rounds: int,
    trials: int,
    seed: int,
    solver_model: str,
    solver_seed_mode: SeedMode,
    editor_model: str,
    rewrite_mode: str,
    runtime: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    saturation = []
    collect = []
    diagnostic = []
    validation = []
    for round_index in range(rounds):
        for task_id in validation_ids:
            for trial in range(trials):
                saturation.append(
                    {
                        "round": round_index,
                        "task": task_id,
                        "trial": trial,
                        "seed": _stable_seed(
                            seed, "validation_saturation", round_index, task_id, trial
                        ),
                        "arm": "parent",
                        "model": solver_model,
                    }
                )
        for task_id in train_ids:
            for trial in range(trials):
                attempt_seed = _stable_seed(seed, "collect", round_index, task_id, trial)
                collect.append(
                    {
                        "round": round_index,
                        "task": task_id,
                        "trial": trial,
                        "seed": attempt_seed,
                        "model": solver_model,
                    }
                )
                diagnostic.append(
                    {
                        "round": round_index,
                        "task": task_id,
                        "trial": trial,
                        "seed": attempt_seed,
                        "arm": "candidate",
                        "model": solver_model,
                    }
                )
        for pair in paired_schedule(
            validation_ids, trials=trials, base_seed=seed, round_index=round_index
        ):
            for arm in pair.arms:
                validation.append(
                    {
                        "round": round_index,
                        "task": pair.task_id,
                        "trial": pair.trial,
                        "seed": pair.seed,
                        "arm": arm,
                        "model": solver_model,
                    }
                )
    return {
        "solver_seed_mode": solver_seed_mode,
        "runtime": runtime,
        "saturation": saturation,
        "collect": collect,
        "reflect": [{"round": r, "tasks": train_ids} for r in range(rounds)],
        "rewrite": [
            {"round": r, "model": editor_model, "mode": rewrite_mode} for r in range(rounds)
        ],
        "diagnose": diagnostic,
        "validate": validation,
    }
