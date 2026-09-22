"""The shared, bounded edit brake for finalized skill bodies."""

from __future__ import annotations

import difflib
import hashlib
import math
import os
import warnings
from collections.abc import Mapping
from dataclasses import asdict, dataclass

DEFAULT_BASE_BUDGET = 0.40
DECAY_FLOOR = 0.10
METRIC_REVISION = "normalized-line-churn-v1"
SCHEDULE = "inverse-sqrt-promotion-count-v1"
SUPERSEDED_ENV_VARS = (
    "EVO_C1_EDIT_BUDGET_FRAC",
    "EVO_REWRITE_MAX_DELTA_MIN_CHARS",
    "EVO_REWRITE_MAX_GROWTH",
    "EVO_REWRITE_MIN_CHARS",
    "EVO_REWRITE_MIN_LINES",
)
_warned_superseded: set[str] = set()


def resolve_base_budget(environ: Mapping[str, str] | None = None) -> float:
    """Read the only relative churn setting and reject invalid values."""
    env = os.environ if environ is None else environ
    ignored = [
        name
        for name in SUPERSEDED_ENV_VARS
        if str(env.get(name) or "").strip() and name not in _warned_superseded
    ]
    if ignored:
        warnings.warn(
            "Ignoring superseded relative rewrite controls: " + ", ".join(ignored),
            UserWarning,
            stacklevel=2,
        )
        _warned_superseded.update(ignored)
    raw = str(env.get("EVO_REWRITE_MAX_DELTA_FRAC", DEFAULT_BASE_BUDGET))
    try:
        budget = float(raw)
    except ValueError as exc:
        raise ValueError("EVO_REWRITE_MAX_DELTA_FRAC must be a finite number in [0, 1]") from exc
    if not math.isfinite(budget) or not 0 <= budget <= 1:
        raise ValueError("EVO_REWRITE_MAX_DELTA_FRAC must be a finite number in [0, 1]")
    return budget


def effective_budget(
    base_budget: float, promotion_count: int, *, version_decay: bool = True
) -> float:
    """Return the admission budget for a retained-parent maturity."""
    if not math.isfinite(base_budget) or not 0 <= base_budget <= 1:
        raise ValueError("base_budget must be a finite number in [0, 1]")
    if promotion_count < 0:
        raise ValueError("promotion_count must be non-negative")
    if not version_decay:
        return base_budget
    return max(base_budget / math.sqrt(promotion_count + 1), min(base_budget, DECAY_FLOOR))


def format_effective_budget(budget: float) -> str:
    """Render the resolved floating-point budget without coarse rounding."""
    return f"{budget:.12g} ({budget:.2%})"


def _metric_lines(body: str) -> list[str]:
    normalized = str(body).replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in normalized.split("\n") if line.strip()]


def _changed_mass(parent: list[str], candidate: list[str]) -> tuple[int, int]:
    changed = 0
    max_length = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, parent, candidate).get_opcodes():
        if tag == "equal":
            continue
        changed_lines = [*parent[i1:i2], *candidate[j1:j2]]
        changed += len(changed_lines)
        max_length = max(max_length, *(map(len, changed_lines) or [0]))
    return changed, max_length


def _changed_char_count(parent: str, candidate: str) -> int:
    return sum(
        (i2 - i1) + (j2 - j1)
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, parent, candidate).get_opcodes()
        if tag != "equal"
    )


@dataclass(frozen=True, slots=True)
class EditBrakeEvidence:
    """Auditable admission evidence for one finalized candidate body."""

    version_decay_enabled: bool
    schedule: str
    floor_frac: float
    metric_revision: str
    parent_version: str | None
    promotion_count: int
    base_budget_frac: float
    effective_budget_frac: float
    normalized_churn: float
    allowed: bool
    decision: str
    parent_sha256: str
    candidate_sha256: str
    parent_char_count: int
    candidate_char_count: int
    character_delta: int
    changed_character_count: int
    parent_non_empty_line_count: int
    candidate_non_empty_line_count: int
    changed_line_mass: int
    max_changed_line_length: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def analyze_edit(
    parent_body: str,
    candidate_body: str,
    *,
    base_budget: float | None = None,
    promotion_count: int = 0,
    version_decay: bool = True,
    parent_version: str | None = None,
) -> EditBrakeEvidence:
    """Measure finalized bodies and make the single shared admission decision."""
    base = resolve_base_budget() if base_budget is None else float(base_budget)
    budget = effective_budget(base, promotion_count, version_decay=version_decay)
    parent_lines, candidate_lines = _metric_lines(parent_body), _metric_lines(candidate_body)
    changed_mass, max_length = _changed_mass(parent_lines, candidate_lines)
    total = len(parent_lines) + len(candidate_lines)
    churn = changed_mass / total if total else 0.0
    return EditBrakeEvidence(
        version_decay_enabled=version_decay,
        schedule=SCHEDULE if version_decay else "constant-v1",
        floor_frac=min(base, DECAY_FLOOR),
        metric_revision=METRIC_REVISION,
        parent_version=parent_version,
        promotion_count=promotion_count,
        base_budget_frac=base,
        effective_budget_frac=budget,
        normalized_churn=churn,
        allowed=churn <= budget,
        decision="allowed" if churn <= budget else "candidate_edit_budget_exceeded",
        parent_sha256=hashlib.sha256(parent_body.encode()).hexdigest(),
        candidate_sha256=hashlib.sha256(candidate_body.encode()).hexdigest(),
        parent_char_count=len(parent_body),
        candidate_char_count=len(candidate_body),
        character_delta=len(candidate_body) - len(parent_body),
        changed_character_count=_changed_char_count(parent_body, candidate_body),
        parent_non_empty_line_count=len(parent_lines),
        candidate_non_empty_line_count=len(candidate_lines),
        changed_line_mass=changed_mass,
        max_changed_line_length=max_length,
    )


def retry_feedback(evidence: EditBrakeEvidence, attempt: int) -> str:
    """Give an editor bounded feedback without repeating candidate content."""
    excess = evidence.normalized_churn - evidence.effective_budget_frac
    return (
        f"Attempt {attempt} exceeded the edit brake: observed churn "
        f"{evidence.normalized_churn:.12g} ({evidence.normalized_churn:.2%}); permitted churn "
        f"{format_effective_budget(evidence.effective_budget_frac)}; "
        f"excess {excess:.1%}. Make the smallest sufficient edit from the unchanged parent. "
        f"Character delta was {evidence.character_delta}; changed characters were "
        f"{evidence.changed_character_count}."
    )


__all__ = [
    "DECAY_FLOOR",
    "DEFAULT_BASE_BUDGET",
    "EditBrakeEvidence",
    "METRIC_REVISION",
    "SCHEDULE",
    "SUPERSEDED_ENV_VARS",
    "analyze_edit",
    "effective_budget",
    "format_effective_budget",
    "resolve_base_budget",
    "retry_feedback",
]
