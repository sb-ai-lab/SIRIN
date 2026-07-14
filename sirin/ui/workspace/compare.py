"""Honest side-by-side verdicts for two runs scored over the SAME answer text.

Localization agreement (do both detectors flag the same characters?) is comparable across ANY
detector types, so it is always offered when both sides expose per-character verdicts. A numeric
Δscore is NOT: scores with different semantics live on different scales, and even a raw thresholded
score means nothing across two probes. So the Δscore rule (``score_delta``) renders a number only when
both sides share the one absolute, cross-run-comparable scale — a calibrated probability — and states
the honest fallback otherwise.
"""

from __future__ import annotations

from .contracts import (
    CompareAgreement,
    ComparePayload,
    RunRecord,
    ScoreSemantics,
)

# The only score meaning that is an absolute, cross-detector-comparable scale.
_COMPARABLE_SEMANTICS = {ScoreSemantics.CALIBRATED_PROBABILITY}
_DIFFERENT_SCALES = 'Different score scales — localization overlap only.'


def _char_flags(run: RunRecord | None) -> list[bool] | None:
    """Per-character hallucination flags from a run's localized segments, or None if it has none.

    A sequence-level detector (a whole-answer verdict, no segments) returns None — there is nothing
    to overlap. A span/token detector partitions the answer into segments carrying per-character
    verdicts; only ``verdict is True`` characters are flagged.
    """
    analysis = run.analysis if run else None
    if analysis is None or not analysis.segments:
        return None
    length = len(run.answer)
    flags = [False] * length
    localized = False
    for segment in analysis.segments:
        if segment.verdict is None:
            continue
        localized = True
        if segment.verdict:
            for index in range(segment.start_code_point, min(segment.end_code_point, length)):
                flags[index] = True
    return flags if localized else None


def compute_agreement(
    run_a: RunRecord | None, run_b: RunRecord | None
) -> tuple[CompareAgreement | None, str | None]:
    """Count both-flag / A-only / B-only / neither characters, or say why it is undefined."""
    a_answer = run_a.answer if run_a else ''
    b_answer = run_b.answer if run_b else ''
    if not a_answer or not b_answer:
        return None, 'Both sides need a scored answer before per-character overlap is defined.'
    if a_answer != b_answer:
        return None, 'The two answers differ, so per-character overlap is undefined.'
    a_flags = _char_flags(run_a)
    b_flags = _char_flags(run_b)
    if a_flags is None or b_flags is None:
        return None, (
            'At least one detector scores the whole answer, not characters — '
            'there is no localization to overlap.'
        )
    both = sum(1 for fa, fb in zip(a_flags, b_flags) if fa and fb)
    a_only = sum(1 for fa, fb in zip(a_flags, b_flags) if fa and not fb)
    b_only = sum(1 for fa, fb in zip(a_flags, b_flags) if fb and not fa)
    neither = len(a_flags) - both - a_only - b_only
    return CompareAgreement(both=both, a_only=a_only, b_only=b_only, neither=neither), None


def score_delta(
    a_semantics: ScoreSemantics | str | None,
    a_score: float | None,
    b_semantics: ScoreSemantics | str | None,
    b_score: float | None,
) -> tuple[float | None, str]:
    """The single comparability rule: a Δscore only when BOTH sides are calibrated probabilities.

    Same-semantics is necessary but not sufficient — two thresholded raw scores from different probes,
    or two within-answer relative scores, are still incomparable. Only a calibrated probability is an
    absolute [0,1] scale, so only ``CALIBRATED_PROBABILITY`` on both sides yields a number.
    """
    if (
        a_semantics == b_semantics
        and a_semantics in _COMPARABLE_SEMANTICS
        and a_score is not None
        and b_score is not None
    ):
        return b_score - a_score, 'Calibrated probability difference (B − A).'
    return None, _DIFFERENT_SCALES


def build_compare_payload(
    run_a: RunRecord | None,
    run_b: RunRecord | None,
    preset_a: str | None = None,
    preset_b: str | None = None,
) -> ComparePayload:
    agreement, agreement_note = compute_agreement(run_a, run_b)
    a_analysis = run_a.analysis if run_a else None
    b_analysis = run_b.analysis if run_b else None
    delta_score, delta_note = score_delta(
        a_analysis.score_semantics if a_analysis else None,
        a_analysis.score if a_analysis else None,
        b_analysis.score_semantics if b_analysis else None,
        b_analysis.score if b_analysis else None,
    )
    return ComparePayload(
        run_a=run_a,
        run_b=run_b,
        preset_a=preset_a or (run_a.setup_snapshot.detector_preset if run_a else None),
        preset_b=preset_b or (run_b.setup_snapshot.detector_preset if run_b else None),
        agreement=agreement,
        agreement_note=agreement_note,
        delta_score=delta_score,
        delta_note=delta_note,
    )
