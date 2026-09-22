"""The evaluation suite, and the seam mismatch it makes measurable.

``EvalRequest`` is frozen at six fields, deliberately: its docstring says
widening it is how a seam turns into a second config object. That is a sound
rule for the family it was designed for, where a case is a dialogue scenario and
the runtime holds everything else.

This family cannot meet it. ``evolution.workflow.solve`` takes twenty-one
parameters, and eight of them are per-evaluation facts with no field to live in:

===========================  =====================================================
Needed by ``solve``          Why no ``EvalRequest`` field fits
===========================  =====================================================
``skill_name``               The artefact is an immutable *version*, selected per
``snapshot``                 call. ``skills_dir`` names a directory, not a version.
``manifest``                 Train/validation/test membership is a first-class
                             input here; the agent family splits inside its own
                             loop.
``manifest_scope``           Which slice of that manifest this call may see.
``pass_env``                 The child-environment allowlist. A security boundary,
                             not a model knob.
``timeout``                  Per-solve wall clock, enforced per child process.
``attempt_seed``             Seed forwarding, which some backends reject outright.
``project_dir``              Where the skill store and traces live.
===========================  =====================================================

Eight, not nine: ``solve`` also needs ``tasks_dir``, and an earlier version of
this table counted it here. It does not belong. ``FlatTaskCorpus`` writes it into
every case dict and ``cases`` is a real ``EvalRequest`` field, so it crosses the
seam typed rather than smuggled — ``_run_case`` reads it back off the case when
no override carries one. ``model`` is excluded for the same reason: ``agent_llm``
is a field. The eight above are the ones with nowhere to go, and
``IMPEDANCE_FIELDS`` is the list a test asserts against.

The only route is to smuggle them on ``cfg``, which is typed ``Any``. That works
and is what ``SolveOverrides`` does — but it means the seam does not in fact
carry this family's evaluator; it carries an opaque payload the other side
cannot inspect, validate or migrate. Recording that is the point of this module.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from evolution.agent_shim.corpus import FlatTaskCorpus
from evolution.agent_shim.scoring import CaseOutcome, score_cases

#: The eight facts that must ride on ``cfg`` because ``EvalRequest`` has no field
#: for them. Asserted by a test so the number in the M1 report stays true.
IMPEDANCE_FIELDS = (
    "skill_name",
    "snapshot",
    "manifest",
    "manifest_scope",
    "pass_env",
    "timeout",
    "attempt_seed",
    "project_dir",
)


@dataclass
class SolveOverrides:
    """Per-evaluation facts carried as opaque payload on ``EvalRequest.cfg``.

    Every field here is a fact the agent seam cannot see. A suite on the other
    side receives it as ``Any`` and cannot validate a single one.
    """

    model: str = "mock"
    skill_name: str | None = None
    snapshot: str | None = None
    manifest: Any = None
    manifest_scope: str | None = None
    pass_env: Collection[str] = ()
    timeout: float | None = None
    attempt_seed: int | None = None
    project_dir: Path | None = None
    tasks_dir: Path | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_cfg(cls, cfg: Any) -> SolveOverrides:
        """Recover overrides from an opaque ``cfg``, tolerating anything.

        ``cfg`` is typed ``Any`` on the other side of the seam, so this accepts
        an instance of this class, a mapping, or an object with matching
        attributes, and falls back to defaults. The tolerance is itself evidence:
        there is no contract to check against.
        """
        if isinstance(cfg, cls):
            return cfg
        names = {f.name for f in fields(cls)}
        if isinstance(cfg, dict):
            return cls(**{k: v for k, v in cfg.items() if k in names})
        found = {name: getattr(cfg, name) for name in names if hasattr(cfg, name)}
        return cls(**found)


class PytestEvaluationSuite:
    """Runs this family's cases through ``solve`` and scores the batch."""

    name = "flat_pytest_v1"

    def __init__(self, tasks_dir: Path | None = None) -> None:
        self._corpus = FlatTaskCorpus(tasks_dir)

    def load_cases(self, cfg: Any) -> list[dict[str, Any]]:
        overrides = SolveOverrides.from_cfg(cfg)
        return self._corpus.load_cases(project_dir=overrides.project_dir)

    def evaluate(self, request: Any) -> dict[str, Any]:
        """Solve every case in *request* and return the aggregate score.

        ``request`` is duck-typed rather than imported: the real ``EvalRequest``
        lives in the agent package, and importing it here would break the
        one-way dependency rule this shim exists to respect.
        """
        overrides = SolveOverrides.from_cfg(getattr(request, "cfg", None))
        cases = list(getattr(request, "cases", ()) or ())
        outcomes = [self._run_case(case, overrides) for case in cases]
        return score_cases(outcomes)

    def _run_case(self, case: dict[str, Any], overrides: SolveOverrides) -> CaseOutcome:
        from evolution.workflow import solve

        case_id = str(case.get("case_id") or case.get("task_name") or "<unnamed>")
        kwargs: dict[str, Any] = {
            "model": overrides.model,
            "project_dir": overrides.project_dir,
            "tasks_dir": overrides.tasks_dir or case.get("tasks_dir"),
            "skill_name": overrides.skill_name,
            "snapshot": overrides.snapshot,
            "manifest": overrides.manifest,
            "manifest_scope": overrides.manifest_scope,
            "pass_env": overrides.pass_env,
            "attempt_seed": overrides.attempt_seed,
        }
        if overrides.timeout is not None:
            kwargs["timeout"] = overrides.timeout
        try:
            result = solve(str(case.get("task_name") or case_id), **kwargs)
        except Exception as exc:
            return CaseOutcome(case_id=case_id, passed=False, error=f"{type(exc).__name__}: {exc}")
        return CaseOutcome(case_id=case_id, passed=bool(getattr(result, "passed", False)))
