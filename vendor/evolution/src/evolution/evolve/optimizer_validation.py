"""Confidential paired measurements for production optimizer promotion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Arm = Literal["parent", "candidate"]


@dataclass(frozen=True, slots=True)
class ValidationMeasurement:
    seed: int
    passed: int
    total: int
    pass_rate: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "seed": self.seed,
            "passed": self.passed,
            "total": self.total,
            "pass_rate": self.pass_rate,
        }


@dataclass(frozen=True, slots=True)
class ValidationPair:
    task_id: str
    trial: int
    seed: int
    arms: tuple[Arm, Arm]


def paired_schedule(
    task_ids: list[str], *, trials: int, base_seed: int, round_index: int
) -> list[ValidationPair]:
    """Return shared-seed pairs with deterministic counterbalanced arm order."""

    pairs: list[ValidationPair] = []
    for task_id in task_ids:
        for trial in range(trials):
            payload = json.dumps(
                [base_seed, "validation", round_index, task_id, trial],
                separators=(",", ":"),
            )
            seed = int.from_bytes(hashlib.sha256(payload.encode()).digest()[:4], "big")
            arms: tuple[Arm, Arm] = (
                ("parent", "candidate") if len(pairs) % 2 == 0 else ("candidate", "parent")
            )
            pairs.append(ValidationPair(task_id, trial, seed & 0x7FFFFFFF, arms))
    return pairs
