from datetime import datetime, timezone
from uuid import uuid4

from sirin.ui.workspace.contracts import (
    AnalysisKind,
    AnalysisResult,
    RunInputs,
    RunMode,
    RunOrigin,
    RunRecord,
    RunStatus,
    ScoreSemantics,
    SetupSnapshot,
    TaskType,
)
import copy

import pytest

from sirin.ui.demo_cases import load_psiloqa_span_seed
from sirin.ui.workspace.controller import WorkspaceController
from sirin.ui.workspace.run_engine import RunEngine
from sirin.ui.workspace.seed import (
    _seed_spans,
    build_seed_run,
    derive_probe_spans,
    seed_draft,
)
from sirin.ui.workspace.session import (
    WorkspaceSession,
    export_run,
    import_portable_json,
)

CENSUS_EXAMPLE_ID = 'psiloqa_NousResearch/Nous-Hermes-2-Mistral-7B-DPO_22242'


def _controller(store=None):
    session = WorkspaceSession(store if store is not None else {})
    return WorkspaceController(
        session, RunEngine(generate=None, detect=lambda *args: {})
    )


def _faithfulness_setup():
    return SetupSnapshot(
        detector_preset='Probing — Token Linear · PsiloQA/Qwen3-4B',
        detector_family='probing',
        detector_level='token',
        task=TaskType.FAITHFULNESS,
    )


def _terminal_run():
    now = datetime(2026, 7, 14, tzinfo=timezone.utc)
    return RunRecord(
        id=str(uuid4()),
        created_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        origin=RunOrigin.SUPPLIED_ANSWER,
        setup_revision=0,
        setup_snapshot=_faithfulness_setup(),
        inputs=RunInputs(question='Q?', supplied_answer='answer'),
        answer='answer',
        analysis=AnalysisResult(
            kind=AnalysisKind.SEQUENCE,
            score_semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE,
            label='Supported',
            verdict=False,
            score=0.1,
        ),
        request_digest='a' * 64,
    )


def test_seed_run_is_a_terminal_recorded_result_span_record():
    run = build_seed_run(3)

    assert run.status is RunStatus.SUCCEEDED
    assert run.origin is RunOrigin.RECORDED_RESULT
    assert run.setup_revision == 3
    assert run.analysis.kind is AnalysisKind.SPAN
    assert run.analysis.verdict is True
    assert run.analysis.threshold is not None
    assert run.inputs.example_id == CENSUS_EXAMPLE_ID
    assert run.provenance.integrity_sha256 == (
        'dc132cc8512dcde25b721d78dc7f1a33c9da26ce2519e4d755a75ec0341551a9'
    )
    assert any(segment.score is not None for segment in run.analysis.segments)


def test_demo_merge_rule_builds_one_graded_span_per_contiguous_run():
    # Demo rule (demo_renderer.probe_spans): contiguous >= τ tokens merge; badge = run max.
    offsets = [[0, 4], [4, 8], [8, 12], [12, 16], [16, 20]]
    scores = [0.40, 0.95, 0.10, 0.60, 0.61]

    spans = derive_probe_spans(offsets, scores, threshold=0.382)

    assert spans == [
        {'start': 0, 'end': 8, 'score': 0.95, 'verdict': True},
        {'start': 12, 'end': 20, 'score': 0.61, 'verdict': True},
    ]


def test_census_derivation_reproduces_the_recorded_probe_spans():
    # The five graded spans are derived from the recorded per-character trace and must
    # reproduce the artifact's own merged spans exactly — the demo-parity gradation
    # ('2', ' United', ' parish of Llan', ' in Monmouthshire,', '345 people').
    case = load_psiloqa_span_seed()

    spans = _seed_spans(case)

    assert [[span['start'], span['end']] for span in spans] == [
        [68, 69], [72, 79], [99, 114], [119, 137], [168, 178],
    ]
    assert spans[-1]['score'] == pytest.approx(0.9529435634613037)
    assert case['answer'][168:178] == '345 people'


def test_seed_fails_loudly_when_derivation_and_artifact_disagree():
    case = copy.deepcopy(load_psiloqa_span_seed())
    case['probe']['predicted_spans'] = [[2, 100], [110, 160]]

    with pytest.raises(ValueError, match='do not match the recorded probe spans'):
        _seed_spans(case)


def test_new_recorded_result_enums_round_trip_through_portable_json():
    assert RunMode.RECORDED_RESULT.value == 'recordedResult'
    assert RunOrigin.RECORDED_RESULT.value == 'recordedResultVerified'

    restored = import_portable_json(export_run(build_seed_run()))

    assert len(restored) == 1
    assert restored[0].origin is RunOrigin.RECORDED_RESULT
    assert restored[0].analysis.kind is AnalysisKind.SPAN


def test_fresh_faithfulness_session_seeds_exactly_once():
    controller = _controller()

    assert controller.seed_landing(_faithfulness_setup()) is True
    assert len(controller.session.state.runs) == 1
    assert controller.session.selected().origin is RunOrigin.RECORDED_RESULT
    # A second call on the same session is a no-op.
    assert controller.seed_landing(_faithfulness_setup()) is False
    assert len(controller.session.state.runs) == 1


def test_seed_prefills_the_census_draft_only_while_pristine():
    controller = _controller()
    controller.seed_landing(_faithfulness_setup())

    payload = controller.build_payload(setup=_faithfulness_setup())
    assert payload.draft is not None
    assert payload.draft['analyze']['exampleId'] == CENSUS_EXAMPLE_ID
    assert payload.draft['analyze']['question'] == seed_draft()['analyze']['question']

    controller.session.add_run(_terminal_run())
    later = controller.build_payload(setup=_faithfulness_setup())
    assert later.draft is None


def test_seed_never_returns_after_the_seed_is_deleted():
    controller = _controller()
    controller.seed_landing(_faithfulness_setup())
    seed_id = controller.session.state.runs[0].id

    controller.session.delete(seed_id)

    assert controller.seed_landing(_faithfulness_setup()) is False
    assert controller.session.state.runs == []


def test_imported_sessions_are_not_seeded():
    controller = _controller()
    controller.session.import_runs([_terminal_run()])

    assert controller.seed_landing(_faithfulness_setup()) is False
    assert all(
        run.origin is not RunOrigin.RECORDED_RESULT
        for run in controller.session.state.runs
    )


def test_answerability_landing_is_not_seeded():
    controller = _controller()
    setup = SetupSnapshot(
        detector_preset='Probing — Answerability TabPFN (checkpoint)',
        detector_family='probing',
        detector_level='sequence',
        task=TaskType.ANSWERABILITY,
    )

    assert controller.seed_landing(setup) is False
    assert controller.session.state.runs == []
