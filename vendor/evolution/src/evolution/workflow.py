"""Public lifecycle APIs for trace-driven skill evolution.

This module is the framework-facing surface for users who want to compose
Evolution from Python instead of shelling out to ``evo``.  The APIs use generic
task, skill, trace, and version vocabulary.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from evolution.config import llm_max_tokens
from evolution.core.bindings import SkillBinding, resolve_skill_bindings
from evolution.core.models import LineageEntry, LineageOrigin, Skill, SkillFrontmatter
from evolution.core.parser import parse_skill_md, write_skill_md
from evolution.core.store import SkillStore
from evolution.core.validator import ValidationResult, validate_skill
from evolution.eval.paths import resolve_tasks_root
from evolution.eval.runner import run_task
from evolution.eval.solver import DEFAULT_SOLVE_TIMEOUT_S, SolveResult, solve_task
from evolution.eval.task import Task, TaskResult, discover_tasks
from evolution.eval.workspace import setup_workspace
from evolution.evolve.reflect import (
    collect_reflections,
    reflect_failing_traces,
    rewrite_skill_with_audit,
)
from evolution.evolve.rewrite_outcome import PROMOTED_ELIGIBLE, RewriteOutcome
from evolution.lineage.state_io import skill_mutation_lock
from evolution.lineage.traces import TraceStore
from evolution.lineage.tracker import LineageTracker
from evolution.lineage.version import VersionStore, hash_managed_tree
from evolution.llm.backend import LLMBackend, get_backend
from evolution.splits import SplitManifest


@dataclass(frozen=True)
class TraceView:
    """A resolved trace directory plus its metadata and loaded sections."""

    trace_id: str
    trace_dir: Path
    metadata: dict[str, Any]
    sections: dict[str, str]


def skill_store(
    *,
    project_dir: Path | str | None = None,
    user_dir: Path | str | None = None,
) -> SkillStore:
    """Return a skill store for a project."""

    project = Path(project_dir or Path.cwd())
    return SkillStore(project_dir=project, user_dir=_user_dir(user_dir))


def list_tasks(
    tasks_dir: Path | str | None = None,
    *,
    project_dir: Path | str | None = None,
) -> list[Task]:
    """Discover framework tasks under a task root."""

    root = resolve_tasks_root(tasks_dir, project_dir=project_dir)
    return discover_tasks(root)


def get_task(
    task_name: str,
    *,
    tasks_dir: Path | str | None = None,
    project_dir: Path | str | None = None,
) -> Task:
    """Load one task by name from a task root."""

    by_name = {task.name: task for task in list_tasks(tasks_dir, project_dir=project_dir)}
    try:
        return by_name[task_name]
    except KeyError as exc:
        available = ", ".join(sorted(by_name)) or "<none>"
        raise KeyError(f"Task {task_name!r} not found. Available tasks: {available}") from exc


def resolve_skills(
    name: str,
    *,
    store: SkillStore | None = None,
    project_dir: Path | str | None = None,
    user_dir: Path | str | None = None,
    snapshot: str | None = None,
) -> list[Skill]:
    """Resolve a skill or skill container name to concrete skill objects."""

    project = Path(project_dir or Path.cwd())
    store = store or skill_store(project_dir=project, user_dir=user_dir)

    from evolution.core.containers import ContainerStore

    containers = ContainerStore(project_dir=project, user_dir=_user_dir(user_dir))
    if containers.has(name):
        return containers.resolve(name, store, snapshot_label=snapshot)
    if store.has(name):
        return [store.get(name)]
    return []


def resolve_task_bindings(
    task: Task,
    *,
    store: SkillStore,
    project_dir: Path | str,
    skill_name: str | None = None,
    snapshot: str | None = None,
    skill_version: str | None = None,
    working: bool = False,
) -> list[SkillBinding]:
    """Resolve a task's primary selector without dropping supporting skills."""

    requirements = list(task.skills_required)
    if skill_name:
        requirements = [skill_name, *requirements[1:]] if requirements else [skill_name]
    if not requirements:
        return []
    if working and (snapshot or skill_version):
        raise ValueError("version, snapshot, and working selectors cannot be combined")
    if snapshot or skill_version:
        selected = resolve_skill_bindings(
            requirements[:1],
            store=store,
            project_dir=project_dir,
            user_dir=Path.home(),
            snapshot=snapshot,
            skill_version=skill_version,
        )
        supporting = resolve_skill_bindings(
            requirements[1:],
            store=store,
            project_dir=project_dir,
            user_dir=Path.home(),
            working=working,
        )
        return _deduplicate_bindings([*selected, *supporting])
    return resolve_skill_bindings(
        requirements,
        store=store,
        project_dir=project_dir,
        user_dir=Path.home(),
        skill_version=skill_version,
        working=working,
    )


def _deduplicate_bindings(bindings: list[SkillBinding]) -> list[SkillBinding]:
    unique: dict[Path, SkillBinding] = {}
    for binding in bindings:
        key = binding.owner.path.resolve()
        previous = unique.get(key)
        if previous and (previous.version, previous.sha256) != (binding.version, binding.sha256):
            raise ValueError(f"Conflicting pins for skill {binding.name!r}")
        unique.setdefault(key, binding)
    return list(unique.values())


def evaluate_task(
    task_name: str,
    workspace: Path | str,
    *,
    tasks_dir: Path | str | None = None,
    project_dir: Path | str | None = None,
    timeout: float | None = None,
    pass_env: Collection[str] = (),
) -> TaskResult:
    """Run one task evaluator against an existing workspace."""

    task = get_task(task_name, tasks_dir=tasks_dir, project_dir=project_dir)
    return run_task(task, Path(workspace), timeout=timeout, pass_env=pass_env)


def solve(
    task_name: str,
    *,
    model: str,
    project_dir: Path | str | None = None,
    tasks_dir: Path | str | None = None,
    workspace: Path | str | None = None,
    backend: LLMBackend | None = None,
    skill_name: str | None = None,
    no_skill: bool = False,
    snapshot: str | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
    agent_permission: str = "safe",
    max_tokens: int | None = None,
    timeout: float = DEFAULT_SOLVE_TIMEOUT_S,
    manifest: SplitManifest | Path | str | None = None,
    manifest_scope: str | None = None,
    attempt_seed: int | None = None,
    trace_spec_idx: int | None = None,
    round_id: str | None = None,
    phase: str = "collect",
    pass_env: Collection[str] = (),
) -> SolveResult:
    """Set up a workspace, solve a task, evaluate it, and record traces."""

    project = Path(project_dir or Path.cwd())
    task = get_task(task_name, tasks_dir=tasks_dir, project_dir=project)
    ws = setup_workspace(
        task,
        Path(workspace) if workspace is not None else None,
        project_dir=project,
    )

    if backend is None:
        backend_kwargs: dict[str, Any] = {"max_tokens": llm_max_tokens(max_tokens)}
        if api_base:
            backend_kwargs["api_base"] = api_base
        if api_key:
            backend_kwargs["api_key"] = api_key
        backend = get_backend(model, agent_permission=agent_permission, **backend_kwargs)

    bindings: list[SkillBinding] = []
    if not no_skill:
        store = skill_store(project_dir=project)
        bindings = resolve_task_bindings(
            task,
            store=store,
            project_dir=project,
            skill_name=skill_name,
            snapshot=snapshot,
        )

    split_manifest = _coerce_manifest(manifest)

    return solve_task(
        task,
        backend,
        ws,
        bindings=bindings,
        timeout=timeout,
        model_name=model,
        manifest=split_manifest,
        manifest_scope=manifest_scope,
        attempt_seed=attempt_seed,
        trace_spec_idx=trace_spec_idx,
        round_id=round_id,
        phase=phase,
        pass_env=pass_env,
    )


def list_traces(
    skill_name: str,
    *,
    project_dir: Path | str | None = None,
    version: str | None = None,
    model: str | None = None,
    task: str | None = None,
) -> list[dict]:
    """List saved traces for a skill."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    return TraceStore(skill).list(skill_version=version, model=model, task=task)


def load_trace(
    skill_name: str,
    trace_id: str | int | None = None,
    *,
    project_dir: Path | str | None = None,
    last: bool = False,
    sections: tuple[str, ...] = ("prompt", "response", "code", "result"),
) -> TraceView:
    """Resolve and load a trace by id, one-based index, negative index, or latest."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    store = TraceStore(skill)
    index = store.list()
    if not index:
        raise KeyError(f"No traces found for skill {skill_name!r}")

    if last or trace_id is None:
        resolved = index[-1]["id"]
    elif isinstance(trace_id, int) or str(trace_id).lstrip("-").isdigit():
        idx = int(trace_id)
        if idx > 0:
            idx -= 1
        try:
            resolved = index[idx]["id"]
        except IndexError as exc:
            raise IndexError(f"Trace index {trace_id!r} is out of range") from exc
    else:
        resolved = str(trace_id)

    trace_dir = store.resolve_trace_dir(resolved)
    if not trace_dir.is_dir():
        raise KeyError(f"Trace {resolved!r} not found for skill {skill_name!r}")

    metadata_path = store.resolve_trace_file(resolved, "result.json")
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    filenames = {
        "prompt": "prompt.md",
        "response": "response.md",
        "code": "solve.py",
        "result": "result.json",
        "evidence": "evidence.json",
        "reflection": "reflection.json",
    }
    loaded: dict[str, str] = {}
    for section in sections:
        path = store.resolve_trace_file(resolved, filenames[section])
        if path.exists():
            loaded[section] = path.read_text(encoding="utf-8")

    return TraceView(trace_id=resolved, trace_dir=trace_dir, metadata=metadata, sections=loaded)


def reflect(
    skill_name: str,
    *,
    model: str = "openrouter/anthropic/claude-sonnet-4",
    backend: LLMBackend | None = None,
    project_dir: Path | str | None = None,
    task: str | None = None,
    tasks_dir: Path | str | None = None,
    trace_model: str | None = None,
    limit: int | None = None,
    api_base: str | None = None,
    max_tokens: int | None = None,
    agent_permission: str = "safe",
    manifest: SplitManifest | Path | str | None = None,
    scope: str = "skill_evolution",
    strict: bool = True,
    require_v3_evidence: bool = False,
) -> list[dict]:
    """Analyze eligible failing traces and save ``reflection.json`` files."""

    project = Path(project_dir or Path.cwd())
    skill = skill_store(project_dir=project).get(skill_name)
    task_instruction = ""
    if task:
        task_instruction = get_task(task, tasks_dir=tasks_dir, project_dir=project).instruction

    if backend is None:
        backend_kwargs: dict[str, Any] = {"max_tokens": llm_max_tokens(max_tokens)}
        if api_base:
            backend_kwargs["api_base"] = api_base
        backend = get_backend(model, agent_permission=agent_permission, **backend_kwargs)

    split_manifest = _coerce_manifest(manifest)

    return reflect_failing_traces(
        backend,
        skill,
        task_instruction,
        task_filter=task,
        trace_model=trace_model,
        limit=limit,
        manifest=split_manifest,
        scope=scope,
        strict=strict,
        require_v3_evidence=require_v3_evidence,
    )


def rewrite(
    skill_name: str,
    *,
    model: str = "openrouter/anthropic/claude-sonnet-4",
    backend: LLMBackend | None = None,
    project_dir: Path | str | None = None,
    task: str | None = None,
    tasks_dir: Path | str | None = None,
    trace_model: str | None = None,
    skill_version: str | None = None,
    api_base: str | None = None,
    max_tokens: int | None = None,
    agent_permission: str = "safe",
    manifest: SplitManifest | Path | str | None = None,
    scope: str = "skill_evolution",
    include_best_trace_code: bool = False,
    rewrite_mode: str = "text-return",
    version_decay: bool = True,
    max_rewrite_attempts: int = 1,
    apply: bool = False,
) -> RewriteOutcome:
    """Rewrite a skill from saved reflections and optionally update SKILL.md."""

    project = Path(project_dir or Path.cwd())
    skill = skill_store(project_dir=project).get(skill_name)
    parent_sha256 = hash_managed_tree(skill.path)
    split_manifest = _coerce_manifest(manifest)
    reflections = collect_reflections(
        skill,
        task_filter=task,
        trace_model=trace_model,
        skill_version=skill_version,
        manifest=split_manifest,
        scope=scope,
    )
    if not reflections:
        raise ValueError(f"No reflections found for skill {skill_name!r}")

    task_instruction = ""
    if task:
        task_instruction = get_task(task, tasks_dir=tasks_dir, project_dir=project).instruction

    if backend is None:
        backend_kwargs: dict[str, Any] = {"max_tokens": llm_max_tokens(max_tokens)}
        if api_base:
            backend_kwargs["api_base"] = api_base
        backend = get_backend(model, agent_permission=agent_permission, **backend_kwargs)

    outcome = asyncio.run(
        rewrite_skill_with_audit(
            backend,
            skill,
            reflections,
            task_instruction=task_instruction,
            task_filter=task,
            manifest=split_manifest,
            include_best_trace_code=include_best_trace_code,
            rewrite_mode=rewrite_mode,
            version_decay=version_decay,
            max_rewrite_attempts=max_rewrite_attempts,
        )
    )

    if apply and outcome.candidate_status == PROMOTED_ELIGIBLE:
        with skill_mutation_lock(skill.path):
            if hash_managed_tree(skill.path) != parent_sha256:
                raise RuntimeError("Skill changed while rewrite was running")
            raw_fm, _ = parse_skill_md(skill.skill_md_path)
            write_skill_md(
                skill.skill_md_path,
                SkillFrontmatter.model_validate(raw_fm),
                outcome.body,
            )

    return outcome


def validate_candidate(
    skill_name: str, *, project_dir: Path | str | None = None
) -> ValidationResult:
    """Validate the current working-copy SKILL.md for a skill."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    return validate_skill(skill.path)


def commit_skill(
    skill_name: str,
    *,
    project_dir: Path | str | None = None,
    origin: str = "manual",
    mutation_type: str = "manual-edit",
    promote: bool = True,
    fitness: float | None = None,
) -> str:
    """Snapshot the current working-copy skill and optionally promote it."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    with skill_mutation_lock(skill.path):
        validation = validate_skill(skill.path)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))

        tracker = LineageTracker(skill)
        version = tracker.next_version_label()
        VersionStore(skill).save(version)
        tracker.record(
            LineageEntry(
                version=version,
                parent=tracker.current_version or None,
                timestamp=datetime.now(),
                origin=cast(LineageOrigin, origin),
                mutation_type=mutation_type,
                fitness=fitness,
                status="candidate",
            )
        )
        if promote:
            tracker.promote(version, fitness=fitness)
    return version


def promote_skill(
    skill_name: str,
    version: str,
    *,
    project_dir: Path | str | None = None,
    fitness: float | None = None,
) -> None:
    """Promote an existing skill version."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    LineageTracker(skill).promote(version, fitness=fitness)


def reject_skill(
    skill_name: str,
    version: str,
    *,
    project_dir: Path | str | None = None,
    fitness: float | None = None,
) -> None:
    """Mark an existing candidate version as rejected."""

    skill = skill_store(project_dir=project_dir).get(skill_name)
    LineageTracker(skill).reject(version, fitness=fitness)


def _user_dir(user_dir: Path | str | None) -> Path:
    return Path(user_dir).expanduser() if user_dir else Path.home()


def _coerce_manifest(manifest: SplitManifest | Path | str | None) -> SplitManifest | None:
    if manifest is None or isinstance(manifest, SplitManifest):
        return manifest
    return SplitManifest.load(Path(manifest))
