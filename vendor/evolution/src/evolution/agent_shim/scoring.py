"""Reduce per-case solve outcomes to the scalar the gate consumes.

Scoring is the other half of the seam that fits. Both families end at a pass
rate over cases, so nothing here is impedance — it is included to make the
contrast with ``evaluation.py`` legible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseOutcome:
    """One case's result, in the shape a gate can aggregate."""

    case_id: str
    passed: bool
    error: str | None = None

    @property
    def is_error(self) -> bool:
        """True when the case failed to run at all, rather than failing its tests.

        The distinction matters to the gate: a workspace that never built is not
        evidence that a skill is worse, and counting it as a failure lets
        infrastructure noise look like a regression.
        """
        return self.error is not None


def score_cases(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    """Aggregate outcomes into pass rate, counts, and an error tally."""
    total = len(outcomes)
    errors = [outcome for outcome in outcomes if outcome.is_error]
    scored = [outcome for outcome in outcomes if not outcome.is_error]
    passed = [outcome for outcome in scored if outcome.passed]
    return {
        "total": total,
        "scored": len(scored),
        "passed": len(passed),
        "errors": len(errors),
        # Denominator is the scored cases, not the total: an errored case has no
        # signal, and folding it in as a failure biases the rate downward by an
        # amount that depends on infrastructure health rather than skill quality.
        "pass_rate": (len(passed) / len(scored)) if scored else None,
        "error_case_ids": [outcome.case_id for outcome in errors],
    }
