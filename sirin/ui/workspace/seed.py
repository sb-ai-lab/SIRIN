"""First-run landing seed: a terminal recorded-result run from the census case.

A fresh shared-safe session lands on an empty editor with no evidence to show. This
module turns the verified ``psiloqa_span_seed.json`` asset into a first-class terminal
``RunRecord`` so the very first view already shows the full graded census result. The
run carries the recorded probe outputs (scores, threshold, layer) and honest provenance
(``RunOrigin.RECORDED_RESULT``); detection did not run live, so it is never labelled as
though it did. The run is a normal record: exportable, immutable, and rerunnable live.
"""

from __future__ import annotations

import hashlib
from typing import Any
from uuid import uuid4

from sirin.ui.demo_cases import (
    load_judge_span_seed,
    load_psiloqa_span_seed,
    load_psiloqa_span_seed_qwen35,
)
from sirin.ui.path_policy import is_hosted

from .contracts import (
    Provenance,
    RunInputs,
    RunOrigin,
    RunRecord,
    RunStatus,
    ScoreSemantics,
    SetupSnapshot,
    TaskType,
    utc_now,
)
from .presenter import present_analysis


def _seed_setup(case: dict[str, Any]) -> SetupSnapshot:
    detector = case['detector']
    return SetupSnapshot(
        detector_preset=detector['preset'],
        detector_family=detector['family'],
        detector_level=detector['level'],
        task=TaskType.FAITHFULNESS,
        model_id=case['representation_model'],
        calibrated=False,
        threshold=float(detector['threshold']),
        threshold_source=detector['threshold_method'],
        score_semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE,
        layer=int(detector['selected_layer']),
    )


def _seed_provenance(case: dict[str, Any]) -> Provenance:
    detector = case['detector']
    return Provenance(
        dataset=case['dataset'],
        split=case['split'],
        source_model=case['source_answer_model'],
        representation_model=case['representation_model'],
        revision=case['model_revision'],
        integrity_sha256=case['checkpoint_sha256']['model.pt'],
        disclosures=[
            case['source_disclosure'],
            case['representation_disclosure'],
            case['selection_disclosure'],
            case['annotation_disclosure'],
            (
                f"Recorded probe: layer {detector['selected_layer']}, "
                f"seed {detector['selected_seed']}, "
                f"τ = {float(detector['threshold']):.5f}."
            ),
            f"License: {case['license']}",
        ],
    )


def _seed_request_digest(case: dict[str, Any]) -> str:
    material = f"sirin.seed.recorded-result:{case['sample_id']}:{case['answer_sha256']}"
    return hashlib.sha256(material.encode()).hexdigest()


def derive_probe_spans(
    token_offsets: list[list[int]],
    token_scores: list[float],
    threshold: float,
) -> list[dict[str, Any]]:
    """Merge contiguous above-threshold tokens into graded spans (badge = run max).

    This is the north-star demo's presentation rule (``demo_renderer.probe_spans``):
    every maximal run of adjacent tokens scoring at or above τ becomes one span whose
    score is the run's maximum. Tokens below τ break the run and stay plain text.
    """
    spans: list[dict[str, Any]] = []
    run_start: int | None = None
    run_end = 0
    run_max = 0.0
    for (start, end), score in zip(token_offsets, token_scores):
        if score >= threshold:
            if run_start is None:
                run_start, run_max = start, score
            run_end = end
            run_max = max(run_max, score)
        elif run_start is not None:
            spans.append(
                {'start': run_start, 'end': run_end, 'score': run_max, 'verdict': True}
            )
            run_start = None
    if run_start is not None:
        spans.append(
            {'start': run_start, 'end': run_end, 'score': run_max, 'verdict': True}
        )
    return spans


def _seed_spans(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive the seed presentation spans and cross-check them against the artifact.

    The spans are derived from the recorded per-token scores, never hardcoded. The
    experiment used the same merge rule, so the derivation must reproduce the recorded
    ``predicted_spans`` and max scores exactly — any drift means the derivation and the
    artifact disagree, and misattributed evidence must fail loudly rather than render.
    """
    threshold = float(case['detector']['threshold'])
    spans = derive_probe_spans(
        case['probe']['token_offsets'], case['probe']['token_scores'], threshold
    )
    if [[span['start'], span['end']] for span in spans] != case['probe']['predicted_spans']:
        raise ValueError('Seed derived spans do not match the recorded probe spans')
    recorded_max = [entry['max_score'] for entry in case['probe']['predicted_span_scores']]
    if len(spans) != len(recorded_max) or any(
        abs(span['score'] - expected) > 1e-9
        for span, expected in zip(spans, recorded_max)
    ):
        raise ValueError('Seed derived span scores do not match the recorded probe scores')
    return spans


def build_seed_run(
    setup_revision: int = 0, case: dict[str, Any] | None = None
) -> RunRecord:
    """Build the terminal recorded-result run for a probe span seed (census hero by default)."""
    if case is None:
        case = load_psiloqa_span_seed()
    setup = _seed_setup(case)
    analysis = present_analysis(case['answer'], setup, {'spans': _seed_spans(case)})
    now = utc_now()
    return RunRecord(
        id=str(uuid4()),
        created_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        origin=RunOrigin.RECORDED_RESULT,
        setup_revision=setup_revision,
        setup_snapshot=setup,
        inputs=RunInputs(
            context=case['passage'],
            question=case['question'],
            supplied_answer=case['answer'],
            example_id=case['example_id'],
        ),
        answer=case['answer'],
        analysis=analysis,
        provenance=_seed_provenance(case),
        request_digest=_seed_request_digest(case),
    )


def _judge_seed_spans(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Graded spans from the recorded per-character judge scores (badge = run max agreement).

    Every maximal run of tagged (score > 0) characters is one span; the loader already verified
    these offsets equal the recorded ``predicted_spans``, and we cross-check again so misattributed
    evidence fails loudly rather than rendering.
    """
    scores = case['judge']['char_scores']
    spans: list[dict[str, Any]] = []
    run_start: int | None = None
    run_max = 0.0
    for index, score in enumerate(scores):
        if score > 0:
            if run_start is None:
                run_start, run_max = index, score
            run_max = max(run_max, score)
        elif run_start is not None:
            spans.append({'start': run_start, 'end': index, 'score': run_max, 'verdict': True})
            run_start = None
    if run_start is not None:
        spans.append({'start': run_start, 'end': len(scores), 'score': run_max, 'verdict': True})
    if [[span['start'], span['end']] for span in spans] != case['judge']['predicted_spans']:
        raise ValueError('Judge seed derived spans do not match the recorded predicted spans')
    return spans


def build_judge_seed_run(
    setup_revision: int = 0,
    path: str | None = None,
) -> RunRecord | None:
    """Build the terminal recorded-result run for the token API judge, or None if no asset.

    Renders through the same product path as the probe seed (``present_analysis``) with origin
    ``RECORDED_RESULT`` and the honest span-agreement label — k/n judge consensus, never a
    calibrated probability or ground truth.
    """
    case = load_judge_span_seed(path)
    if case is None:
        return None
    detector = case['detector']
    requested, valid = detector['requested'], detector['valid']
    setup = SetupSnapshot(
        detector_preset=detector['preset'],
        detector_family='judge',
        detector_level='token',
        task=TaskType.FAITHFULNESS,
        model_id=detector['judge_model'],
        provider_label=detector['provider_label'],
        calibrated=False,
        threshold=None,
        score_semantics=ScoreSemantics.SPAN_AGREEMENT,
    )
    signal_note = (
        f"Each character's score is the fraction of {valid}/{requested} judge samples that "
        'tagged it. Agreement is judge consensus, not a calibrated probability and not ground truth.'
    )
    analysis = present_analysis(
        case['answer'], setup, {'spans': _judge_seed_spans(case), 'signal_note': signal_note}
    )
    provenance = Provenance(
        dataset=case['dataset'],
        split=case['split'],
        source_model=case['source_answer_model'],
        disclosures=[
            f"Judge model: {detector['judge_model']}",
            f"Judge provider: {detector['provider_label']}",
            f'Judge samples: {valid}/{requested} verbatim-aligned',
            f"Judge temperature: {detector['temperature']}",
            'Recorded judge annotation — detection is not running now.',
            f"License: {case['license']}",
        ],
    )
    now = utc_now()
    return RunRecord(
        id=str(uuid4()),
        created_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        origin=RunOrigin.RECORDED_RESULT,
        setup_revision=setup_revision,
        setup_snapshot=setup,
        inputs=RunInputs(
            context=case['passage'],
            question=case['question'],
            supplied_answer=case['answer'],
            example_id=case['example_id'],
        ),
        answer=case['answer'],
        analysis=analysis,
        provenance=provenance,
        request_digest=hashlib.sha256(
            f"sirin.seed.judge-result:{case['sample_id']}:{case['answer_sha256']}".encode()
        ).hexdigest(),
    )


def build_second_probe_seed_run(setup_revision: int = 0) -> RunRecord | None:
    """Recorded-result run for the Qwen3.5-4B probe seed, or None when its asset is absent.

    Renders through the same product path as the hero probe seed; an absent asset is silent by
    design (the landing keeps the Qwen3-4B hero alone).
    """
    case = load_psiloqa_span_seed_qwen35()
    if case is None:
        return None
    return build_seed_run(setup_revision, case=case)


def build_seed_runs(setup_revision: int = 0) -> list[RunRecord]:
    """All landing seeds: the census hero probe seed plus, when present, the judge and Qwen3.5-4B
    probe seeds.

    The hero probe seed is added last so it stays the selected card; the judge seed and the second
    (Qwen3.5-4B) probe seed sit beside it when their assets are present. Absent assets are silent —
    the unchanged landing is the hero probe seed alone. Hosted profile: the census (Qwen3-4B) seed
    is dropped and the Qwen3.5-4B probe seed, added last, becomes the selected hero.
    """
    runs: list[RunRecord] = []
    judge = build_judge_seed_run(setup_revision)
    if judge is not None:
        runs.append(judge)
    second_probe = build_second_probe_seed_run(setup_revision)
    if second_probe is not None:
        runs.append(second_probe)
    if not is_hosted():
        runs.append(build_seed_run(setup_revision))
    return runs


def build_recorded_replay(example_id: str, setup_revision: int = 0) -> RunRecord | None:
    """Fresh RECORDED_RESULT run for the seed whose example matches, or None.

    Serves "replay" for presets that cannot score live on the hosted CPU demo: the run is
    rebuilt from the verified bundled asset through the same derivation path as the landing
    seed (fresh id and timestamps, recorded provenance intact) — never from mutable session
    history, so a cleared run list cannot poison it.
    """
    for build in (build_judge_seed_run, build_second_probe_seed_run,
                  lambda revision: build_seed_run(revision)):
        try:
            record = build(setup_revision)
        except FileNotFoundError:
            continue
        if record is not None and record.inputs.example_id == example_id:
            return record
    return None


def seed_draft() -> dict[str, Any]:
    """Client draft that prefills the landing example (hosted: the Qwen3.5-4B seed; else census)."""
    case = load_psiloqa_span_seed_qwen35() if is_hosted() else None
    if case is None:
        case = load_psiloqa_span_seed()
    return {
        'analyze': {
            'task': 'faithfulness',
            'mode': 'generate',
            'exampleId': case['example_id'],
            'context': case['passage'],
            'question': case['question'],
            'answer': case['answer'],
            'prompt': '',
            'sourceRunId': None,
        },
        'quickPrompt': '',
    }
