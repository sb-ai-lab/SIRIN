"""Promotion gate — decide whether a rewritten skill CANDIDATE replaces its PARENT.

Pure, dependency-free decision logic shared by every caller (the public evolve
workflow and the research harnesses). Given per-task validation pass-rates for the
parent and candidate bodies, ``gate_candidate`` returns ``(promote, telemetry)``
under one of several metrics selected by ``EVO_GATE_METRIC``:

  - ``pass_rate``      : promote iff candidate mean > parent mean + delta - tolerance.
  - ``solve_count``    : the same comparison on a full-solve-weighted score.
  - ``perm_lex``       : exact task-stratified lexicographic permutation test on
                         ``(full-solve gain, pass-rate gain)``; false-promotion rate
                         bounded by ``EVO_PROMOTE_ALPHA`` under the no-gain null.
  - ``perm_lex_paired``: the seed-paired sign-flip variant — higher power when the
                         parent and candidate trials share solver seeds.

The trial — not the test — is the unit of evidence; per-test outcomes only define
full-solve (all tests pass) and pass-rate (fraction passed).
"""

from __future__ import annotations

import itertools
import math
import os
import random
from collections.abc import Callable
from fractions import Fraction
from typing import Any, TypeVar

_EditResultT = TypeVar("_EditResultT")


def run_gated_edit_attempts(
    *,
    max_attempts: int,
    edit_fn: Callable[[list[dict[str, Any]]], _EditResultT],
    gate_fn: Callable[[_EditResultT], tuple[bool, dict[str, Any]]],
    on_reject: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Retry the editor until its edit passes the gate, or keep the latest after N.

    Turns the delta gate into a *barrier the editor must pass*: each rejected
    attempt is fed back into the next ``edit_fn`` call so the editor can see its
    prior failures and try a different fix.

    - ``edit_fn(rejected)`` -> edit_res. Receives the accumulating list of prior
      rejection records (``{attempt, edit_res, telemetry}``) so the caller can
      render them into the editor prompt.
    - ``gate_fn(edit_res)`` -> ``(passed, telemetry)``. Returns ``True`` whenever
      the edit is acceptable — including when the gate does not apply (no change /
      gate disabled), which the caller encodes in its closure.
    - ``on_reject(record)`` -> side effect per rejection (e.g. write a copy of the
      failed skill to disk).

    Returns ``{edit_res, passed, attempts, rejected, exhausted}``. On exhaustion,
    ``edit_res`` is the latest failed attempt.
    """
    n = max(1, int(max_attempts))
    rejected: list[dict[str, Any]] = []
    edit_res: _EditResultT | None = None
    for att in range(n):
        edit_res = edit_fn(rejected)
        passed, tel = gate_fn(edit_res)
        if passed:
            return {
                "edit_res": edit_res,
                "passed": True,
                "attempts": att + 1,
                "rejected": rejected,
                "exhausted": False,
            }
        record = {"attempt": att, "edit_res": edit_res, "telemetry": tel}
        rejected.append(record)
        if on_reject is not None:
            on_reject(record)
        if tel.get("gate_status") == "error":
            break
    return {
        "edit_res": edit_res,
        "passed": False,
        "attempts": len(rejected),
        "rejected": rejected,
        "exhausted": True,
    }


def solve_count_score(per_task_rates: list[list[float]]) -> float | None:
    """Solve-count metric over the POOL of all runs across all tasks.

    ``(solved_runs + mean_run_pass_rate) / (K + 1)`` where K = total runs, solved_runs =
    # pooled runs fully solved (pass_rate >= 1-1e-9), mean_run_pass_rate = mean of every
    run's pass_rate. Each run is weighted equally (run pass_rate is already passed/total,
    so totals don't bias it). Rewards reliability (more solved runs) and keeps complete
    solves dominant over high partials. Range [0,1], =1.0 iff every run fully solves.
    None when there are no runs.
    """
    rates = [r for runs in per_task_rates for r in runs]
    if not rates:
        return None
    K = len(rates)
    solved = sum(1 for r in rates if r >= 1.0 - 1e-9)
    return (solved + sum(rates) / K) / (K + 1)


def solve_count_trainval(
    train_rates: list[list[float]], val_rates: list[list[float]]
) -> float | None:
    """Equal-weighted mean of the train and validation solve-count blocks."""
    parts = [
        score
        for score in (solve_count_score(train_rates), solve_count_score(val_rates))
        if score is not None
    ]
    return (sum(parts) / len(parts)) if parts else None


def _concat_per_task(
    previous: list[list[float]] | None, current: list[list[float]]
) -> list[list[float]]:
    """Append current samples to the matching per-task parent sample pools."""
    if not previous:
        return [list(rates) for rates in current]
    return [
        list(previous[i] if i < len(previous) else []) + list(rates)
        for i, rates in enumerate(current)
    ]


def tau_band(n_train: int, n_val: int, scale: float = 0.5) -> float:
    """Noise band scaled to half the gain from one fully solved task."""
    value = float(scale)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"EVO_GATE_TAU_SCALE must be finite and non-negative, got {value}")
    return value / (2 * max(int(n_train), int(n_val), 1))


def gate_zone(delta_m: float, tau: float) -> str:
    """Classify a candidate as an improvement, regression, or noise."""
    if delta_m > tau:
        return "improve"
    if delta_m < -tau:
        return "regress"
    return "noise"


GATE_METRICS = ("pass_rate", "solve_count", "perm_lex", "perm_lex_paired")


def validate_gate_environment(*, allow_trainval: bool = False) -> None:
    delta = float(os.environ.get("EVO_PROMOTE_DELTA", "0.0") or "0.0")
    tolerance = float(os.environ.get("EVO_PROMOTE_TOLERANCE", "0.0") or "0.0")
    if not math.isfinite(delta) or not math.isfinite(tolerance):
        raise ValueError("EVO_PROMOTE_DELTA and EVO_PROMOTE_TOLERANCE must be finite")
    metric = (os.environ.get("EVO_GATE_METRIC", "pass_rate") or "pass_rate").strip().lower()
    if metric == "solve_count_trainval" and allow_trainval:
        tau_band(0, 0, float(os.environ.get("EVO_GATE_TAU_SCALE", "0.5") or "0.5"))
        return
    if metric not in GATE_METRICS:
        raise ValueError(f"unknown EVO_GATE_METRIC {metric!r}; expected one of {GATE_METRICS}")
    if metric in ("perm_lex", "perm_lex_paired"):
        alpha = float(os.environ.get("EVO_PROMOTE_ALPHA", "0.10") or "0.10")
        if not 0 < alpha < 1:
            raise ValueError(f"EVO_PROMOTE_ALPHA {alpha} out of range (0, 1)")


def _is_full_solve(rate: float) -> int:
    return 1 if rate >= 1.0 - 1e-9 else 0


def _lex_ge(a: tuple[Fraction, float], b: tuple[Fraction, float]) -> bool:
    if a[0] != b[0]:
        return a[0] > b[0]
    return a[1] >= b[1] - 1e-9


def _lex_gt_zero(stat: tuple[Fraction, float]) -> bool:
    return stat[0] > 0 or (stat[0] == 0 and stat[1] > 1e-9)


def _joint_p_floor(joint: dict[tuple[Fraction, float], int], total: int) -> float:
    """Minimal achievable p: probability mass at the lexicographic max of the
    realized joint support. Under tied pairs the support collapses and this
    floor rises far above the naive ``1/2^n``."""
    lex_max = max(joint)
    return sum(c for st, c in joint.items() if _lex_ge(st, lex_max)) / total


def _lex_gate_telemetry(
    joint: dict[tuple[Fraction, float], int], obs: tuple[Fraction, float], alpha: float
) -> tuple[bool, dict]:
    total = sum(joint.values())
    p_value = sum(c for st, c in joint.items() if _lex_ge(st, obs)) / total
    p_floor = _joint_p_floor(joint, total)
    telemetry: dict[str, Any] = {
        "p_value": p_value,
        "d_full": float(obs[0]),
        "d_rate": obs[1],
        "alpha": alpha,
        "perm_space": total,
        "p_floor": p_floor,
    }
    if p_floor > alpha:
        telemetry["status"] = "UNDERPOWERED"
    return p_value <= alpha, telemetry


def _task_perm_dist(parent_rates: list[float], cand_rates: list[float]) -> dict | None:
    """Exact within-task relabeling distribution of (D_full, D_rate) for one task.

    Pools the candidate and parent trial pass_rates, enumerates every way to relabel
    ``len(cand_rates)`` of them as the candidate arm, and tallies the full-solve
    contrast (exact ``Fraction``) and pass-rate contrast (rounded float).
    """
    nc, npar = len(cand_rates), len(parent_rates)
    if nc == 0 or npar == 0:
        return None
    pooled = list(cand_rates) + list(parent_rates)
    full = [_is_full_solve(r) for r in pooled]
    n = len(pooled)
    dist: dict[tuple[Fraction, float], int] = {}
    for sel in itertools.combinations(range(n), nc):
        sel_set = set(sel)
        cf = sum(full[i] for i in sel)
        pf = sum(full[i] for i in range(n) if i not in sel_set)
        cr = sum(pooled[i] for i in sel)
        pr = sum(pooled[i] for i in range(n) if i not in sel_set)
        key = (Fraction(cf, nc) - Fraction(pf, npar), round(cr / nc - pr / npar, 9))
        dist[key] = dist.get(key, 0) + 1
    return dist


def perm_lex_decision(
    parent_rates: list[list[float]], cand_rates: list[list[float]], alpha: float
) -> tuple[bool, dict]:
    """Exact task-stratified lexicographic permutation gate (unpaired).

    Promote iff the observed ``(full-solve gain, pass-rate gain)`` is lexicographically
    positive AND the exact stratified permutation p-value is ``<= alpha``. The
    permutation relabels candidate/parent trials within each task with trial counts
    fixed, so the false-promotion rate is bounded by ``alpha`` under the no-gain null
    regardless of verifier noise. Full-solve is primary; pass-rate breaks ties only.
    """
    obs_f = Fraction(0)
    obs_r = 0.0
    dists: list[dict] = []
    for p_t, c_t in zip(parent_rates, cand_rates, strict=True):
        d = _task_perm_dist(p_t, c_t)
        if d is None:
            return False, {"p_value": None, "reason": "inconclusive_missing_arm"}
        dists.append(d)
        nc, npar = len(c_t), len(p_t)
        cf = sum(_is_full_solve(r) for r in c_t)
        pf = sum(_is_full_solve(r) for r in p_t)
        obs_f += Fraction(cf, nc) - Fraction(pf, npar)
        obs_r = round(obs_r + (sum(c_t) / nc - sum(p_t) / npar), 9)
    obs = (obs_f, obs_r)
    if not _lex_gt_zero(obs):
        return False, {
            "p_value": None,
            "d_full": float(obs_f),
            "d_rate": obs_r,
            "reason": "no_observed_gain",
        }
    joint: dict[tuple[Fraction, float], int] = {(Fraction(0), 0.0): 1}
    for d in dists:
        nxt: dict[tuple[Fraction, float], int] = {}
        for (af, ar), ac in joint.items():
            for (bf, br), bc in d.items():
                key = (af + bf, round(ar + br, 9))
                nxt[key] = nxt.get(key, 0) + ac * bc
        if len(nxt) > 2_000_000:
            raise RuntimeError(
                "perm_lex joint distribution too large; reduce validation tasks or gate trials"
            )
        joint = nxt
    return _lex_gate_telemetry(joint, obs, alpha)


def _paired_pair_contributions(
    parent_rates: list[list[float]], cand_rates: list[list[float]]
) -> list[tuple[Fraction, float]] | None:
    """Per (task, seed) paired contribution to ``(D_full, D_rate)``.

    Requires the parent and candidate to have the SAME trial count per task (paired
    seeds). Each pair contributes ``(f_cand - f_parent)/K_t`` to the full-solve gain
    and ``(r_cand - r_parent)/K_t`` to the pass-rate gain.
    """
    contribs: list[tuple[Fraction, float]] = []
    for p_t, c_t in zip(parent_rates, cand_rates, strict=True):
        kt = len(c_t)
        if kt == 0 or kt != len(p_t):
            return None
        for k in range(kt):
            df = Fraction(_is_full_solve(c_t[k]) - _is_full_solve(p_t[k]), kt)
            dr = round((c_t[k] - p_t[k]) / kt, 9)
            contribs.append((df, dr))
    return contribs


def perm_lex_paired_decision(
    parent_rates: list[list[float]], cand_rates: list[list[float]], alpha: float
) -> tuple[bool, dict]:
    """Exact seed-paired sign-flip lexicographic permutation gate.

    Valid only when parent and candidate trials share solver seeds (paired). The null
    flips, independently per (task, seed) pair, which arm is labeled the candidate; the
    observed all-positive labeling is compared lexicographically against the full
    ``2^(#pairs)`` sign assignments. Removes between-seed variance, so it has much more
    power than the unpaired test at the same trial budget.
    """
    contribs = _paired_pair_contributions(parent_rates, cand_rates)
    if contribs is None:
        return False, {"p_value": None, "reason": "unpaired_or_empty"}
    obs_f = sum((c[0] for c in contribs), Fraction(0))
    obs_r = round(sum(c[1] for c in contribs), 9)
    obs = (obs_f, obs_r)
    if not _lex_gt_zero(obs):
        return False, {
            "p_value": None,
            "d_full": float(obs_f),
            "d_rate": obs_r,
            "reason": "no_observed_gain",
        }
    joint: dict[tuple[Fraction, float], int] = {(Fraction(0), 0.0): 1}
    for df, dr in contribs:
        nxt: dict[tuple[Fraction, float], int] = {}
        for (af, ar), ac in joint.items():
            for sign in (1, -1):
                key = (af + sign * df, round(ar + sign * dr, 9))
                nxt[key] = nxt.get(key, 0) + ac
        if len(nxt) > 2_000_000:
            raise RuntimeError(
                "perm_lex_paired joint distribution too large; reduce validation tasks or gate trials"
            )
        joint = nxt
    promote, telemetry = _lex_gate_telemetry(joint, obs, alpha)
    telemetry["paired"] = True
    return promote, telemetry


def conservative_paired_gate(
    parent_by_task: dict[str, list[float]],
    candidate_by_task: dict[str, list[float]],
    *,
    alpha: float = 0.10,
    min_pairs: int = 4,
) -> tuple[bool, dict[str, Any]]:
    """Apply the production promotion policy to paired validation measurements."""
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be finite and in (0, 1)")
    if min_pairs < 1:
        raise ValueError("min_pairs must be positive")
    if parent_by_task.keys() != candidate_by_task.keys():
        raise ValueError("parent and candidate must contain the same tasks")

    task_ids = sorted(parent_by_task)
    parent: list[list[float]] = []
    candidate: list[list[float]] = []
    task_means: dict[str, dict[str, float]] = {}
    for task_id in task_ids:
        p_rates = [float(value) for value in parent_by_task[task_id]]
        c_rates = [float(value) for value in candidate_by_task[task_id]]
        if not p_rates or len(p_rates) != len(c_rates):
            raise ValueError(f"task {task_id!r} must have the same paired trial count")
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in p_rates + c_rates):
            raise ValueError(f"task {task_id!r} pass rates must be finite and in [0, 1]")
        parent.append(p_rates)
        candidate.append(c_rates)
        task_means[task_id] = {
            "parent": sum(p_rates) / len(p_rates),
            "candidate": sum(c_rates) / len(c_rates),
        }

    n_pairs = sum(map(len, parent))
    telemetry: dict[str, Any] = {
        "gate": "conservative_paired",
        "alpha": alpha,
        "n_pairs": n_pairs,
        "task_ids": task_ids,
        "task_means": task_means,
    }
    if n_pairs < min_pairs:
        return False, {**telemetry, "reason": "insufficient_pairs"}

    regressions = [
        task_id for task_id, means in task_means.items() if means["candidate"] < means["parent"]
    ]
    if regressions:
        return False, {**telemetry, "reason": "task_regression", "regressions": regressions}

    promote, decision = perm_lex_paired_decision(parent, candidate, alpha)
    telemetry.update(decision)
    if promote:
        telemetry["reason"] = "paired_improvement"
        return True, telemetry
    telemetry["reason"] = (
        "underpowered"
        if decision.get("status") == "UNDERPOWERED"
        else decision.get("reason", "no_significant_gain")
    )
    return False, telemetry


def _aggregate_gate_metric(per_task_rates: list[list[float]], metric: str) -> float:
    """Aggregate per-task per-trial pass_rates into the gate's comparison scalar.

    ``pass_rate``: mean of all trial pass_rates. ``solve_count``: the pooled-runs
    solve-count score (see ``solve_count_score``). Any other metric raises.
    """
    if metric == "solve_count":
        return solve_count_score(per_task_rates) or 0.0
    if metric != "pass_rate":
        raise ValueError(f"unknown gate metric {metric!r}; expected one of {GATE_METRICS}")
    flat = [r for rates in per_task_rates for r in rates]
    return (sum(flat) / len(flat)) if flat else 0.0


def editor_facing_gate_reason(telemetry: dict, *, blind: bool) -> str:
    """Why the gate rejected an edit, phrased for the editor's next attempt.

    Blind mode (paper) must NOT leak the held-out signal: no validation scores,
    no held-out task ids — only a coarse, generalizing-steer message. Non-blind
    (exploratory) may include the numeric delta to help debugging.
    """
    coarse = (
        "Rejected: this edit did not improve the skill on held-out tasks (it did not "
        "generalize). Make a more general fix to the procedure for the failure category, "
        "and do NOT remove working content that other tasks rely on."
    )
    if blind:
        return coarse
    try:
        pm = float(telemetry.get("parent_mean", 0.0))
        cm = float(telemetry.get("candidate_mean", 0.0))
        nv = int(telemetry.get("n_val", 0))
        tol = float(telemetry.get("tolerance", 0.0) or 0.0)
        label = str(telemetry.get("metric") or "pass_rate").replace("_", " ")
        if tol > 0:
            tail = (
                f"rejected because it fell more than the allowed {tol:.0%} tolerance below "
                f"the current skill (needed >= {pm - tol:.2f})"
            )
        else:
            tail = "needed to be strictly higher"
        return f"{coarse} (held-out {label} {cm:.2f} vs current {pm:.2f} on {nv} task(s); {tail})."
    except (TypeError, ValueError):
        return coarse


def split_train_ids(train_ids: list[str]) -> tuple[list[str], list[str]]:
    """diagnose (train_a) / validate (train_b) split. N<2 -> no validation split."""
    n = len(train_ids)
    if n < 2:
        return list(train_ids), []
    if n == 3:
        return train_ids[:2], train_ids[2:]
    k = math.ceil(0.6 * n)
    return train_ids[:k], train_ids[k:]


def delta_gate_enabled(train_ids: list[str]) -> bool:
    if os.environ.get("EVO_DISABLE_DELTA_GATE") == "1":
        return False
    return len(split_train_ids(train_ids)[1]) > 0


def gate_candidate(
    *,
    parent_body: str,
    candidate_body: str,
    validate_ids: list[str],
    score_fn: Callable[[str, str], Any],
    delta: float | None = None,
    tolerance: float | None = None,
    metric: str | None = None,
) -> tuple[bool, dict]:
    """Promote iff the candidate beats the parent under the selected gate metric.

    ``score_fn(body, task_id)`` -> the per-task validation result: either a single
    pass_rate float, or a list of per-trial pass_rates (needed by ``solve_count`` /
    ``perm_lex`` / ``perm_lex_paired``). ``metric`` (``EVO_GATE_METRIC``) selects the
    decision rule:
      - ``"pass_rate"`` (default): cand_mean > parent_mean + delta - tolerance.
      - ``"solve_count"``: same comparison on the full-solve-weighted score.
      - ``"perm_lex"``: exact unpaired lexicographic permutation, FP <= EVO_PROMOTE_ALPHA.
      - ``"perm_lex_paired"``: the seed-paired sign-flip variant (requires shared seeds).
    ``delta`` (EVO_PROMOTE_DELTA) and ``tolerance`` (EVO_PROMOTE_TOLERANCE) only apply
    to the mean-comparison metrics.
    """
    if delta is None:
        delta = float(os.environ.get("EVO_PROMOTE_DELTA", "0.0") or "0.0")
    if tolerance is None:
        tolerance = float(os.environ.get("EVO_PROMOTE_TOLERANCE", "0.0") or "0.0")
    if metric is None:
        metric = (os.environ.get("EVO_GATE_METRIC", "pass_rate") or "pass_rate").strip().lower()
    if metric not in GATE_METRICS:
        raise ValueError(f"unknown EVO_GATE_METRIC {metric!r}; expected one of {GATE_METRICS}")
    if not math.isfinite(delta) or not math.isfinite(tolerance):
        raise ValueError("delta and tolerance must be finite")
    if not validate_ids:
        return False, {
            "gate": "delta_gate",
            "gate_status": "rolled_back",
            "reason": "no_validation_tasks",
            "n_val": 0,
            "val_task_ids": [],
        }
    alpha: float | None = None
    if metric in ("perm_lex", "perm_lex_paired"):
        alpha = float(os.environ.get("EVO_PROMOTE_ALPHA", "0.10") or "0.10")
        if not 0 < alpha < 1:
            raise ValueError(f"EVO_PROMOTE_ALPHA {alpha} out of range (0, 1)")

    def _per_task_rates(body: str) -> list[list[float]]:
        out: list[list[float]] = []
        for t in validate_ids:
            r = score_fn(body, t)
            out.append([float(r)] if isinstance(r, (int, float)) else [float(x) for x in r])
        return out

    parent_rates = _per_task_rates(parent_body)
    cand_rates = _per_task_rates(candidate_body)
    if metric in ("perm_lex", "perm_lex_paired"):
        assert alpha is not None
        decide = perm_lex_paired_decision if metric == "perm_lex_paired" else perm_lex_decision
        promote, extra = decide(parent_rates, cand_rates, alpha)
        telemetry = {
            "gate": metric,
            "gate_status": "promoted" if promote else "rolled_back",
            "metric": metric,
            "n_val": len(validate_ids),
            "val_task_ids": list(validate_ids),
            **extra,
        }
        return promote, telemetry
    parent_mean = _aggregate_gate_metric(parent_rates, metric)
    cand_mean = _aggregate_gate_metric(cand_rates, metric)
    promote = cand_mean > parent_mean + delta - tolerance
    telemetry = {
        "gate": "delta_gate",
        "gate_status": "promoted" if promote else "rolled_back",
        "metric": metric,
        "parent_mean": parent_mean,
        "candidate_mean": cand_mean,
        "delta": delta,
        "tolerance": tolerance,
        "observed_delta": cand_mean - parent_mean,
        "n_val": len(validate_ids),
        "val_task_ids": list(validate_ids),
    }
    return promote, telemetry


def gate_candidate_trainval(
    *,
    parent_body: str,
    candidate_body: str,
    train_ids: list[str],
    val_ids: list[str],
    score_fn: Callable[[str, str], Any],
    tau_scale: float | None = None,
    parent_prev: dict | None = None,
) -> tuple[bool, dict]:
    """Apply the noise-aware ratchet gate to equal-weighted train/validation blocks."""
    if tau_scale is None:
        tau_scale = float(os.environ.get("EVO_GATE_TAU_SCALE", "0.5") or "0.5")

    def _rates(body: str, ids: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for task_id in ids:
            result = score_fn(body, task_id)
            out.append(
                [float(result)]
                if isinstance(result, (int, float))
                else [float(value) for value in result]
            )
        return out

    candidate_train = _rates(candidate_body, train_ids)
    candidate_val = _rates(candidate_body, val_ids)
    parent_train = _rates(parent_body, train_ids)
    parent_val = _rates(parent_body, val_ids)
    if os.environ.get("EVO_GATE_POOL_PARENT") == "1" and parent_prev:
        parent_train = _concat_per_task(parent_prev.get("train"), parent_train)
        parent_val = _concat_per_task(parent_prev.get("val"), parent_val)

    parent_mean = solve_count_trainval(parent_train, parent_val)
    candidate_mean = solve_count_trainval(candidate_train, candidate_val)
    tau = tau_band(len(train_ids), len(val_ids), tau_scale)
    delta_m = (candidate_mean or 0.0) - (parent_mean or 0.0)
    zone = gate_zone(delta_m, tau)
    telemetry = {
        "gate": "delta_gate_trainval",
        "metric": "solve_count_trainval",
        "zone": zone,
        "gate_status": "rolled_back" if zone == "regress" else "promoted",
        "parent_mean": parent_mean,
        "candidate_mean": candidate_mean,
        "delta_m": delta_m,
        "tau": tau,
        "n_train": len(train_ids),
        "n_val": len(val_ids),
        "train_task_ids": list(train_ids),
        "val_task_ids": list(val_ids),
        "parent_pool": {"train": parent_train, "val": parent_val},
        "cand_samples": {"train": candidate_train, "val": candidate_val},
        "n_parent_runs": sum(len(rates) for rates in parent_train + parent_val),
    }
    return zone != "regress", telemetry


def _race_version_index(version: str) -> int:
    if version.startswith("v") and version[1:].isdigit():
        return int(version[1:])
    raise ValueError(f"race version must look like vN, got {version!r}")


def _race_flat_rates(
    version_rates: dict[str, list[list[float]]], versions: list[str]
) -> dict[str, list[float]]:
    shapes = {tuple(len(task) for task in version_rates[v]) for v in versions}
    if len(shapes) != 1:
        raise ValueError(f"race arms must share the (task, trial) shape, got {sorted(shapes)}")
    flat = {v: [r for task in version_rates[v] for r in task] for v in versions}
    if not flat[versions[0]]:
        raise ValueError("race has no (task, trial) units")
    return flat


_N_MC_FLIPS = 20000


def _max_stat_null(contrast_vectors: list[list[float]]) -> tuple[list[float], bool]:
    """Null max-stat distribution over shared sign flips, plus whether it is exact.

    Flipping a unit whose diff is zero in EVERY version is a no-op, so the null
    depends only on the union of nonzero-diff units across versions: enumeration
    over those units is exact whenever there are <= 16 of them, regardless of the
    total unit count. Otherwise falls back to fixed-seed Monte-Carlo flips.
    """
    n_units = len(contrast_vectors[0])
    nonzero = [i for i in range(n_units) if any(vec[i] for vec in contrast_vectors)]

    def stat(signs: tuple[int, ...] | list[int]) -> float:
        return max(
            sum(s * vec[i] for s, i in zip(signs, nonzero, strict=True)) / n_units
            for vec in contrast_vectors
        )

    if len(nonzero) <= 16:
        return [stat(signs) for signs in itertools.product((1, -1), repeat=len(nonzero))], True
    rng = random.Random(0)
    return [stat([rng.choice((1, -1)) for _ in nonzero]) for _ in range(_N_MC_FLIPS)], False


RACE_SHIP_RULES = ("argmax", "confirm")


def _race_confidence(p_value: float, p_floor: float) -> str:
    if p_floor > 0.20:
        return "underpowered"
    for level in (0.05, 0.10, 0.20):
        if p_value <= level:
            return f"confirmed@{level:.2f}"
    return "unconfirmed"


def _race_labels_argmax(v_star: str, base: str, confidence: str) -> tuple[str, str]:
    if v_star == base:
        return base, "reeval_ship_v0"
    tag = "confirmed" if confidence.startswith("confirmed") else confidence
    return v_star, f"reeval_argmax_{tag}"


def race_ship_decision(
    version_rates: dict[str, list[list[float]]],
    *,
    alpha: float,
    ship_rule: str = "argmax",
) -> dict[str, Any]:
    """End-of-run version-race ship rule (EVO_SELECT_METRIC=reeval).

    ``version_rates[version]`` holds per-task lists of per-trial pass_rates from a
    contemporaneous re-solve of every version on ALL train tasks. The pairing unit is
    ``(task, trial-index)``; version i's trial k on task t pairs with the baseline's
    trial k on task t. Let ``v* = argmax mean pass_rate`` (ties keep the earliest
    version). ``v*`` is tested against the baseline (lowest version, v0) with an
    exact max-T sign-flip test: the same sign flips are applied to every version's
    paired contrasts and ``p = P(max_i D_i* >= D_{v*})``. Flips are fully enumerated
    when at most 16 units have a nonzero diff vs the baseline in any version
    (zero-diff units cannot change any version's statistic), else 20,000
    Monte-Carlo flips with a fixed seed. The data-conditional floor is the
    minimal achievable p given the realized contrasts.

    ``ship_rule="argmax"`` (default) ships ``v*`` and records the sign-flip test as a
    typed confidence label (``confirmed@0.05/0.10/0.20`` / ``unconfirmed`` /
    ``underpowered`` when floor > 0.20). ``ship_rule="confirm"`` ships ``v*`` only
    when ``p <= alpha`` (floor > alpha => UNDERPOWERED => baseline), else the baseline.
    """
    if ship_rule not in RACE_SHIP_RULES:
        raise ValueError(
            f"unknown EVO_RACE_SHIP_RULE {ship_rule!r}; expected one of {RACE_SHIP_RULES}"
        )
    if not version_rates:
        raise ValueError("race_ship_decision: no versions")
    versions = sorted(version_rates, key=_race_version_index)
    flat = _race_flat_rates(version_rates, versions)
    base = versions[0]
    means = {v: sum(flat[v]) / len(flat[v]) for v in versions}
    result = {
        "versions": versions,
        "baseline": base,
        "means": means,
        "alpha": alpha,
        "ship_rule": ship_rule,
        "n_units": len(flat[base]),
    }
    if len(versions) == 1:
        return {
            **result,
            "best_version": base,
            "shipped_version": base,
            "label": "reeval_single_version",
            "confidence": None,
            "d_vs_baseline": {base: 0.0},
            "p_value": None,
            "p_floor": None,
        }
    contrasts = {v: [c - b for c, b in zip(flat[v], flat[base], strict=True)] for v in versions[1:]}
    d = {base: 0.0, **{v: sum(cs) / len(cs) for v, cs in contrasts.items()}}
    v_star = max(versions, key=lambda v: (means[v], -_race_version_index(v)))
    stats, exact = _max_stat_null(list(contrasts.values()))
    tol = 1e-9
    p_floor = sum(1 for s in stats if s >= max(stats) - tol) / len(stats)
    hits = sum(1 for s in stats if s >= d[v_star] - tol)
    p_value = hits / len(stats) if exact else (1 + hits) / (1 + len(stats))
    confidence = _race_confidence(p_value, p_floor)
    if ship_rule == "argmax":
        shipped, label = _race_labels_argmax(v_star, base, confidence)
    elif p_floor > alpha:
        shipped, label = base, "reeval_ship_v0_underpowered"
    elif v_star == base or p_value > alpha:
        shipped, label = base, "reeval_ship_v0_nonseparation"
    else:
        shipped, label = v_star, "reeval_confirmed_winner"
    return {
        **result,
        "best_version": v_star,
        "shipped_version": shipped,
        "label": label,
        "confidence": confidence,
        "d_vs_baseline": d,
        "p_value": p_value,
        "p_floor": p_floor,
        "exact": exact,
    }
