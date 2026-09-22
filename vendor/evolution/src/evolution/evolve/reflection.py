"""Trace reflection and reflection-store helpers for skill evolution."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
from collections.abc import Collection
from pathlib import Path
from typing import Any

from evolution import config
from evolution.core.models import Skill
from evolution.evolve._legacy_prompts import load_legacy_prompt
from evolution.evolve.reflection_evidence import (
    render_artifacts,
    render_failure_evidence,
    render_oracle_sections,
    render_solve_diag,
    render_train_evidence,
    validate_trace_provenance,
)
from evolution.lineage.state_io import atomic_write_text
from evolution.lineage.traces import TraceStore, load_trace_evidence, resolve_trace_artifact
from evolution.llm.backend import LLMBackend
from evolution.splits import SplitManifest, assert_no_leakage

REFLECTION_SCHEMA = "evolution-reflection-v2"
REFLECTION_INPUT_SCHEMA = "evolution-reflection-input-v1"

SIBLING_DIGEST_MAX_LINES = int(os.environ.get("EVO_REFLECT_SIBLING_MAX", "20") or "20")

logger = logging.getLogger(__name__)

_SECRET_SETTING_NAMES = frozenset(
    {
        "access_token",
        "api_key",
        "auth_token",
        "authorization",
        "cookie",
        "credential",
        "credentials",
        "password",
        "secret",
    }
)
_BACKEND_SETTING_FIELDS = (
    "_client_kwargs",
    "_kwargs",
    "_max_tokens",
    "_reasoning_effort",
    "_sandbox",
    "_temperature",
    "_timeout_s",
    "_top_p",
    "agent_permission",
    "max_tokens",
    "reasoning_effort",
    "temperature",
    "timeout_s",
    "top_p",
)


def _backend_label(backend: LLMBackend) -> str:
    for attr in ("model_label", "_model", "model"):
        value = getattr(backend, attr, None)
        if value:
            return str(value)
    return backend.__class__.__name__


def _backend_settings(backend: LLMBackend) -> dict[str, object]:
    """Return stable backend configuration without credentials or call state."""

    def is_secret(name: object) -> bool:
        normalized = str(name).lstrip("_").lower().replace("-", "_")
        return normalized in _SECRET_SETTING_NAMES or normalized.endswith(
            tuple(f"_{secret}" for secret in _SECRET_SETTING_NAMES)
        )

    def normalize(value: Any) -> object:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
                if not is_secret(key)
            }
        if isinstance(value, (list, tuple)):
            return [normalize(item) for item in value]
        if isinstance(value, (set, frozenset)):
            return sorted((normalize(item) for item in value), key=str)
        if callable(value):
            module = getattr(value, "__module__", type(value).__module__)
            name = getattr(value, "__qualname__", type(value).__qualname__)
            return f"{module}.{name}"
        return f"{type(value).__module__}.{type(value).__qualname__}"

    state: dict[str, object] = {
        "class": f"{type(backend).__module__}.{type(backend).__qualname__}",
        "model": _backend_label(backend),
        "seed_mode": getattr(backend, "seed_mode", "unsupported"),
    }
    for name in _BACKEND_SETTING_FIELDS:
        if hasattr(backend, name):
            state[name.lstrip("_")] = normalize(getattr(backend, name))
    return state


def reflection_input_identity(
    *,
    parent_body: str,
    task_instruction: str,
    train_evidence: dict | None,
    prompt_revision: str,
    policy_revision: str,
    user_prompt: str,
    system_prompt: str,
    kind: str,
    reflector_settings: dict[str, object],
) -> dict[str, object]:
    """Return the complete identity used to reuse a train reflection."""
    payload = {
        "schema": REFLECTION_INPUT_SCHEMA,
        "parent_body_sha256": _sha256(parent_body),
        "task_instruction_sha256": _sha256(task_instruction),
        "train_evidence_sha256": _sha256(
            json.dumps(train_evidence or {}, sort_keys=True, separators=(",", ":"), default=str)
        ),
        "prompt_revision": prompt_revision,
        "policy_revision": policy_revision,
        "user_prompt_sha256": _sha256(user_prompt),
        "system_prompt_sha256": _sha256(system_prompt),
        "kind": kind,
        "reflector_settings": reflector_settings,
    }
    return {**payload, "identity_sha256": _json_hash(payload)}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_hash(value: object) -> str:
    return _sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str))


def _enforce_scope(
    traces: list[dict],
    manifest: SplitManifest | None,
    scope: str,
    caller: str,
) -> list[dict]:
    """Filter traces to the requested manifest scope and fail on leakage."""
    if manifest is None:
        return traces
    allowed = manifest.ids(scope)
    task_ids = {t.get("task", "") for t in traces if t.get("task")}
    known = manifest.all_ids()
    to_check = [tid for tid in task_ids if tid in known]
    assert_no_leakage(
        manifest,
        [tid for tid in to_check if tid not in allowed],
        scope=scope,
        context=caller,
    )
    filtered = [t for t in traces if t.get("task", "") in allowed]
    if len(filtered) != len(traces):
        logger.info(
            "%s: filtered %d/%d traces by manifest %s scope=%s",
            caller,
            len(traces) - len(filtered),
            len(traces),
            manifest.name,
            scope,
        )
    return filtered


REFLECT_SYSTEM_BLIND = load_legacy_prompt("reflect_system_blind")

REFLECT_SYSTEM_ORACLE = load_legacy_prompt("reflect_system_oracle")

# Back-compat alias: legacy import surface defaults to the blind wording.
REFLECT_SYSTEM = REFLECT_SYSTEM_BLIND


def _reflect_system() -> str:
    """Render the live reflector system prompt for the active evidence mode."""
    from evolution import prompts

    return prompts.render("system_reflect", evidence_policy=_reflect_evidence_policy())


def _reflect_evidence_policy() -> str:
    from evolution import prompts

    return prompts.load_prompt(
        "_blocks/blind_evidence" if config.reflect_blind() else "_blocks/oracle_evidence"
    )


def _reflect_runtime_contract() -> str:
    from evolution import prompts

    return prompts.load_prompt("_blocks/runtime_path_contract_neutral")


REFLECT_PROMPT = load_legacy_prompt("reflect_prompt")


REFLECT_SUCCESS_PROMPT = load_legacy_prompt("reflect_success_prompt")


def _render_section(title: str, blob: str) -> str:
    if not blob:
        return ""
    return f"\n## {title}\n{blob}\n"


def _render_oracle_block(blob: str) -> str:
    """Slot the already-headed oracle sections as their own block, or empty."""
    if not blob:
        return ""
    return f"\n{blob}\n"


def _digest_for_trace(trace: dict, evidence: dict | None) -> str:
    fe = (evidence or {}).get("failure_evidence") or {}
    vr = fe.get("verifier_result") or {}
    cat = str(vr.get("verification_category") or "?")
    fcats = fe.get("failure_categories") or []
    top_fc = str(fcats[0]) if fcats else "-"
    arts = (evidence or {}).get("produced_artifacts")
    n_arts = (
        sum(1 for a in arts if isinstance(a, dict) and a.get("path"))
        if isinstance(arts, list)
        else 0
    )
    passed = trace.get("passed", 0)
    total = trace.get("total", 0)
    return f"pass={passed}/{total} verifier={cat} top_failure={top_fc} artifacts={n_arts}"


def build_sibling_digests(
    traces: list[dict],
    evidences: dict[str, dict | None],
) -> dict[str, str]:
    """Map trace_id -> one-line digest for every supplied trace."""
    out: dict[str, str] = {}
    for t in traces:
        tid = t.get("id") or ""
        if not tid:
            continue
        out[tid] = _digest_for_trace(t, evidences.get(tid))
    return out


def _render_siblings_blob(self_id: str, digests: dict[str, str]) -> str:
    items = [d for tid, d in digests.items() if tid != self_id]
    if not items:
        return ""
    if len(items) > SIBLING_DIGEST_MAX_LINES:
        items = items[:SIBLING_DIGEST_MAX_LINES]
        items.append(f"(capped at {SIBLING_DIGEST_MAX_LINES} sibling lines)")
    return "\n".join(f"- {line}" for line in items)


def extract_workspace_view(trace_dir: Path, task_instruction: str) -> str:
    """Return the agent-visible workspace block from ``prompt.md``.

    Solver prompts are saved as ``{task.instruction}\\n\\n{workspace_context}``;
    strip the leading instruction prefix and return the remainder. Empty string
    on missing files or instruction-only prompts (legacy traces).
    """
    p = resolve_trace_artifact(trace_dir, "prompt.md")
    if not p.is_file():
        return ""
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return ""
    stripped = text
    if task_instruction and stripped.startswith(task_instruction):
        stripped = stripped[len(task_instruction) :]
    return stripped.strip()


async def reflect_trace(
    backend: LLMBackend,
    trace_dir: Path,
    skill: Skill,
    task_instruction: str,
    require_v3_evidence: bool = False,
    *,
    kind: str = "failure",
    siblings: dict[str, str] | None = None,
    meta_skill_blob: str = "",
    rejected_edits_blob: str = "",
    workspace_view: str | None = None,
) -> dict:
    """Analyze a single trace and return structured reflection.

    ``kind="failure"`` uses the top-level ``reflect_failure`` prompt; ``"success"``
    uses ``reflect_success``. Legacy prompt constants remain importable but are
    no longer the live rendering path. Legacy control blobs remain accepted but
    are intentionally not rendered.
    """
    result, prompt, system, reflection_input = _prepare_reflection_request(
        backend,
        trace_dir,
        skill,
        task_instruction,
        kind=kind,
        siblings=siblings,
        workspace_view=workspace_view,
    )

    resp = await backend.complete(
        [{"role": "user", "content": prompt}],
        system=system,
    )

    reflection = _extract_json(resp.content)
    reflection["trace_id"] = result.get("id", trace_dir.name)
    reflection["model"] = result.get("model", "")
    reflection["reflector_model"] = _backend_label(backend)
    reflection["pass_rate"] = result.get("pass_rate", 0.0)
    reflection["tokens_used"] = resp.total_tokens
    reflection["kind"] = kind
    reflection["reflection_input"] = reflection_input
    reflection.setdefault("schema", REFLECTION_SCHEMA)

    if kind == "success":
        if require_v3_evidence:
            if reflection.get("evidence_sufficiency") not in ("sufficient", "insufficient"):
                reflection["evidence_sufficiency"] = "insufficient"
            if not isinstance(reflection.get("preserve_recommended"), bool):
                reflection["preserve_recommended"] = False
        else:
            reflection.setdefault("evidence_sufficiency", "sufficient")
            reflection.setdefault("preserve_recommended", True)
    else:
        if require_v3_evidence:
            if reflection.get("evidence_sufficiency") not in ("sufficient", "insufficient"):
                reflection["evidence_sufficiency"] = "insufficient"
            if not isinstance(reflection.get("rewrite_recommended"), bool):
                reflection["rewrite_recommended"] = False
        else:
            reflection.setdefault("evidence_sufficiency", "sufficient")
            reflection.setdefault("rewrite_recommended", True)

    return reflection


def _prepare_reflection_request(
    backend: LLMBackend,
    trace_dir: Path,
    skill: Skill,
    task_instruction: str,
    *,
    kind: str,
    siblings: dict[str, str] | None,
    workspace_view: str | None,
) -> tuple[dict, str, str, dict[str, object]]:
    """Render the exact reflection request and its semantic identity."""
    code = resolve_trace_artifact(trace_dir, "solve.py").read_text(encoding="utf-8")
    result = json.loads(
        resolve_trace_artifact(trace_dir, "result.json").read_text(encoding="utf-8")
    )
    evidence = load_trace_evidence(trace_dir)
    strict_train_evidence = bool(
        isinstance(evidence, dict)
        and isinstance((evidence.get("failure_evidence") or {}).get("train_evidence"), dict)
    )
    solve_exit, solve_timeout, solve_diag = render_solve_diag(evidence)
    self_id = result.get("id", trace_dir.name)
    if workspace_view is None:
        workspace_view = extract_workspace_view(trace_dir, task_instruction)

    evidence_parts = [
        _render_section("Agent Workspace View", workspace_view or ""),
        _render_section("Generated Solver Code", f"```python\n{code}\n```"),
    ]
    if not strict_train_evidence:
        evidence_parts.insert(
            1,
            _render_section(
                "Other Train Traces This Round",
                _render_siblings_blob(self_id, siblings or {}),
            ),
        )
    if strict_train_evidence:
        evidence_parts.append(_render_section("Train Evidence", render_train_evidence(evidence)))
    else:
        evidence_parts.extend(
            [
                _render_section(
                    "Execution Evidence",
                    f"Passed: {result.get('passed', 0)}/{result.get('total', 0)}",
                ),
                _render_section(
                    "Agent Solve Diagnostics",
                    "\n".join(
                        [
                            f"- solve_exit_code: {solve_exit}",
                            f"- solve_timeout: {solve_timeout}",
                            f"- solve_diagnostic: {solve_diag}",
                        ]
                    ),
                ),
                _render_section("Failure Evidence", render_failure_evidence(evidence)),
                _render_section("Produced Artifact Metadata", render_artifacts(evidence)),
                _render_oracle_block(render_oracle_sections(evidence)),
            ]
        )
    from evolution import prompts

    prompt = prompts.render(
        "reflect_success" if kind == "success" else "reflect_failure",
        task_context=f"### Task Instruction\n{task_instruction}",
        runtime_contract=_reflect_runtime_contract(),
        skill_body=skill.body,
        evidence_policy=_reflect_evidence_policy(),
        evidence="\n".join(part for part in evidence_parts if part.strip()),
        n_traces="1",
        round_memory="",
        rejected_attempts="",
    )
    system = _reflect_system()
    reflection_input = reflection_input_identity(
        parent_body=skill.body,
        task_instruction=task_instruction,
        train_evidence=((evidence or {}).get("failure_evidence") or {}).get("train_evidence"),
        prompt_revision="reflect-v2",
        policy_revision="train-evidence-v1",
        user_prompt=prompt,
        system_prompt=system,
        kind=kind,
        reflector_settings=_backend_settings(backend),
    )
    return result, prompt, system, reflection_input


def save_reflection(trace_dir: Path, reflection: dict) -> Path:
    """Save reflection.json into the trace folder."""
    path = resolve_trace_artifact(trace_dir, "reflection.json")
    atomic_write_text(path, json.dumps(reflection, indent=2))
    return path


def load_reflection(trace_dir: Path) -> dict | None:
    """Load reflection.json from a trace folder, or None."""
    path = resolve_trace_artifact(trace_dir, "reflection.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_success_traces(
    success_traces: list[tuple[dict, Path]], k: int
) -> list[tuple[dict, Path]]:
    """Pick up to ``k`` passing traces with task diversity preference."""
    if k <= 0 or not success_traces:
        return []
    seen_tasks: set[str] = set()
    primary: list[tuple[dict, Path]] = []
    spillover: list[tuple[dict, Path]] = []
    for t, d in success_traces:
        task = str(t.get("task") or "")
        if task and task not in seen_tasks:
            primary.append((t, d))
            seen_tasks.add(task)
        else:
            spillover.append((t, d))
    picked = primary[:k]
    if len(picked) < k:
        picked.extend(spillover[: k - len(picked)])
    return picked


def reflect_failing_traces(
    backend: LLMBackend,
    skill: Skill,
    task_instruction: str,
    task_filter: str | None = None,
    trace_model: str | None = None,
    limit: int | None = None,
    manifest: SplitManifest | None = None,
    scope: str = "skill_evolution",
    strict: bool = False,
    require_v3_evidence: bool = False,
    trace_ids: Collection[str] | None = None,
) -> list[dict]:
    """Analyze train traces (failure + sampled success) and save reflections."""
    ts = TraceStore(skill)
    traces = ts.list(task=task_filter)
    if trace_ids is not None:
        selected = set(trace_ids)
        traces = [trace for trace in traces if str(trace.get("id")) in selected]
    if trace_model:
        traces = [t for t in traces if trace_model.lower() in t.get("model", "").lower()]
    traces = _enforce_scope(traces, manifest, scope=scope, caller="reflect_failing_traces")

    failing: list[tuple[dict, Path]] = []
    passing: list[tuple[dict, Path]] = []
    for t in traces:
        trace_dir = ts.resolve_trace_dir(t["id"])
        if not trace_dir.exists():
            continue
        evidence = load_trace_evidence(trace_dir)
        trace_phase = (evidence or {}).get("trace_context", {}).get("phase")
        existing = load_reflection(trace_dir)
        strict_train = bool(
            isinstance(evidence, dict)
            and isinstance((evidence.get("failure_evidence") or {}).get("train_evidence"), dict)
        )
        if existing and not strict_train:
            continue
        if trace_ids is not None and trace_phase != "collect":
            continue
        if trace_ids is None and trace_phase in {
            "promotion_validation",
            "validation",
            "held_out",
            "cross_role",
            "genm",
        }:
            continue
        if t.get("success"):
            passing.append((t, trace_dir))
        else:
            failing.append((t, trace_dir))

    if config.reflect_drop_mixed() and failing and passing:
        passing_keys = {(t.get("task"), t.get("skill_version")) for t, _d in passing}
        kept = [
            (t, d)
            for t, d in failing
            if (t.get("task"), t.get("skill_version")) not in passing_keys
        ]
        dropped = len(failing) - len(kept)
        if dropped:
            logger.info(
                "reflect_failing_traces: EVO_REFLECT_DROP_MIXED dropped %d mixed-signal "
                "failing trace(s) for %s",
                dropped,
                skill.name,
            )
        failing = kept

    if not failing and not passing:
        return []
    if limit is not None:
        failing = failing[:limit]

    successes = _sample_success_traces(passing, config.reflect_success_k())
    targets: list[tuple[dict, Path, str]] = [
        *((t, d, "failure") for t, d in failing),
        *((t, d, "success") for t, d in successes),
    ]

    require_v3 = require_v3_evidence or manifest is not None
    evidences: dict[str, dict | None] = {}
    for trace, trace_dir, _kind in targets:
        ev = load_trace_evidence(trace_dir)
        evidences[trace.get("id", "")] = ev
        validate_trace_provenance(
            trace=trace,
            trace_dir=trace_dir,
            evidence=ev,
            manifest=manifest,
            scope=scope,
            require_v3_evidence=require_v3,
        )

    sibling_digests = build_sibling_digests([t for t, _d, _k in targets], evidences)
    reflections: list[dict] = []
    for t, trace_dir, kind in targets:
        try:
            expected = _prepare_reflection_request(
                backend,
                trace_dir,
                skill,
                task_instruction,
                kind=kind,
                siblings=sibling_digests,
                workspace_view=None,
            )
            existing = load_reflection(trace_dir)
            if existing and existing.get("reflection_input") == expected[-1]:
                continue
            reflection = asyncio.run(
                reflect_trace(
                    backend,
                    trace_dir,
                    skill,
                    task_instruction,
                    require_v3_evidence=require_v3,
                    kind=kind,
                    siblings=sibling_digests,
                )
            )
            if "parse_error" in reflection:
                raise ValueError(
                    f"reflection JSON parse failed for trace {t['id']}: "
                    f"{reflection.get('parse_error')}"
                )
            save_reflection(trace_dir, reflection)
            reflections.append(reflection)
        except Exception as exc:
            if strict:
                raise
            reflections.append({"trace_id": t["id"], "error": str(exc), "kind": kind})

    return reflections


def collect_reflections(
    skill: Skill,
    task_filter: str | None = None,
    trace_model: str | None = None,
    skill_version: str | None = None,
    manifest: SplitManifest | None = None,
    scope: str = "skill_evolution",
) -> list[dict]:
    """Collect all existing reflections from trace folders."""
    ts = TraceStore(skill)
    traces = ts.list(task=task_filter)

    if trace_model:
        traces = [t for t in traces if trace_model.lower() in t.get("model", "").lower()]
    if skill_version:
        traces = [t for t in traces if t.get("skill_version") == skill_version]

    traces = _enforce_scope(traces, manifest, scope=scope, caller="collect_reflections")

    reflections = []
    for t in traces:
        r = load_reflection(ts.resolve_trace_dir(t["id"]))
        if r:
            reflections.append(r)
    return reflections


def scoped_trace_dirs(
    skill: Skill,
    task_filter: str | None = None,
    trace_model: str | None = None,
    skill_version: str | None = None,
    manifest: SplitManifest | None = None,
    scope: str = "skill_evolution",
) -> list[tuple[dict, Path]]:
    """Return ``(trace_dict, trace_dir)`` pairs in the same train scope as
    :func:`collect_reflections`.

    Used by the agentic-session rewrite mode to seed raw traces (``solve.py`` +
    evidence) the agent explores. Applies the identical model/version/manifest
    filtering and drops ``promotion_validation``-phase traces (held-back δ-gate
    pool) so the session never sees validation data. Missing trace dirs are
    skipped.
    """
    ts = TraceStore(skill)
    traces = ts.list(task=task_filter)
    if trace_model:
        traces = [t for t in traces if trace_model.lower() in t.get("model", "").lower()]
    if skill_version:
        traces = [t for t in traces if t.get("skill_version") == skill_version]
    traces = _enforce_scope(traces, manifest, scope=scope, caller="scoped_trace_dirs")

    pairs: list[tuple[dict, Path]] = []
    for t in traces:
        trace_dir = ts.resolve_trace_dir(t["id"])
        if not trace_dir.is_dir():
            continue
        ev = load_trace_evidence(trace_dir)
        if (ev or {}).get("trace_context", {}).get("phase") == "promotion_validation":
            continue
        pairs.append((t, trace_dir))
    return pairs


def _first_balanced_object(text: str) -> str | None:
    """Return the first brace-balanced ``{...}`` span (string-aware)."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        start = text.find("{", start + 1)
    return None


def _repair_jsonish(span: str) -> str:
    """Best-effort repair of near-JSON weak models emit: drop trailing commas,
    and convert single-quoted objects (no double-quotes present) to double."""
    repaired = re.sub(r",(\s*[}\]])", r"\1", span)
    if '"' not in repaired and "'" in repaired:
        repaired = repaired.replace("'", '"')
    return repaired


def _extract_json(text: str) -> dict:
    """Extract JSON object from an LLM response."""
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    span = _first_balanced_object(text)
    if span:
        try:
            return json.loads(span)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(_repair_jsonish(span))
        except json.JSONDecodeError:
            pass

    logger.warning("could not extract JSON from reflector response (%d chars)", len(text))
    return {"raw_response": text, "parse_error": "Could not extract JSON"}
