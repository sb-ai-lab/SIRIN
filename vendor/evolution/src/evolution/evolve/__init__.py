"""Core skill-evolution lifecycle package.

This package contains framework features used to improve reusable skills from
execution traces: reflection, evidence rendering, rewrite sanitization, rewrite
guards, structured rewrite outcomes, and preservation scoring. Research-only
adapter-specialization helpers live under ``experiments/research`` (outside the
core package).
"""

from __future__ import annotations

from evolution.evolve.optimizer import (
    OptimizationRunError,
    load_optimization_status,
    optimize_skill,
)
from evolution.evolve.optimizer_state import OptimizationResult
from evolution.evolve.promotion_gate import (
    delta_gate_enabled,
    editor_facing_gate_reason,
    gate_candidate,
    gate_candidate_trainval,
    gate_zone,
    perm_lex_decision,
    perm_lex_paired_decision,
    run_gated_edit_attempts,
    solve_count_score,
    solve_count_trainval,
    split_train_ids,
    tau_band,
)

__all__ = [
    "OptimizationResult",
    "OptimizationRunError",
    "delta_gate_enabled",
    "editor_facing_gate_reason",
    "gate_candidate",
    "gate_candidate_trainval",
    "gate_zone",
    "perm_lex_decision",
    "perm_lex_paired_decision",
    "run_gated_edit_attempts",
    "solve_count_score",
    "solve_count_trainval",
    "split_train_ids",
    "tau_band",
    "optimize_skill",
    "load_optimization_status",
]
