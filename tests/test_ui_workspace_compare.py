"""Compare mode (PR-8/9): the runCompare controller flow, the localization-agreement + Δscore
helpers, and the ComparePayload contract round-trip."""

from uuid import uuid4

import pytest

from sirin.ui.workspace.compare import (
    build_compare_payload,
    compute_agreement,
    score_delta,
)
from sirin.ui.workspace.contracts import (
    ActionEnvelope,
    ComparePayload,
    ReceiptStatus,
    RunStatus,
    ScoreSemantics,
    SetupSnapshot,
    TaskType,
)
from sirin.ui.workspace.controller import WorkspaceController
from sirin.ui.workspace.run_engine import RunEngine
from sirin.ui.workspace.session import WorkspaceSession


_CLIENT_ID = '22222222-2222-2222-2222-222222222222'


def _setup(preset='A-probe', family='probing', level='token', semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE, threshold=0.5):
    return SetupSnapshot(
        detector_preset=preset,
        detector_family=family,
        detector_level=level,
        threshold=threshold,
        score_semantics=semantics,
    )


def _span_run(answer, spans, setup):
    """A terminal, SCORE_SUPPLIED_ANSWER run whose analysis carries the given graded spans."""
    from sirin.ui.workspace.contracts import RunMode, RunRequest

    engine = RunEngine(generate=None, detect=lambda _a, _r, _s: {'spans': spans})
    request = RunRequest(
        question='q', context='c', supplied_answer=answer, mode=RunMode.SCORE_SUPPLIED_ANSWER
    )
    return engine.execute(engine.reserve(request, setup, 0), request)


def _envelope(session, action_type, payload):
    return ActionEnvelope(
        client_instance_id=_CLIENT_ID,
        sequence=session.state.high_water.get(_CLIENT_ID, 0) + 1,
        action_id=str(uuid4()),
        type=action_type,
        expected_setup_revision=session.state.setup_revision,
        expected_runs_revision=session.state.runs_revision,
        payload=payload,
    )


def _compare_setup(preset_b, setup_a):
    if preset_b == 'A-probe':
        raise ValueError('Choose a different detector for side B.')
    if preset_b == 'missing':
        raise ValueError('The selected comparison detector is not available.')
    return _setup(preset='B-judge', family='judge', level='token', semantics=ScoreSemantics.SPAN_AGREEMENT, threshold=None)


# --- helpers: localization agreement -------------------------------------------------------------

def test_agreement_counts_overlapping_and_disjoint_characters():
    setup = _setup()
    run_a = _span_run('abcd', [{'start': 0, 'end': 2, 'score': 0.9, 'verdict': True}], setup)
    run_b = _span_run('abcd', [{'start': 1, 'end': 3, 'score': 0.8, 'verdict': True}], setup)

    agreement, note = compute_agreement(run_a, run_b)

    assert note is None
    assert (agreement.both, agreement.a_only, agreement.b_only, agreement.neither) == (1, 1, 1, 1)


def test_agreement_is_none_when_answers_differ():
    setup = _setup()
    run_a = _span_run('abcd', [{'start': 0, 'end': 1, 'verdict': True}], setup)
    run_b = _span_run('WXYZ', [{'start': 0, 'end': 1, 'verdict': True}], setup)

    agreement, note = compute_agreement(run_a, run_b)

    assert agreement is None
    assert 'differ' in note


def test_agreement_is_none_when_one_side_has_no_localization():
    setup = _setup()
    span_run = _span_run('abcd', [{'start': 0, 'end': 2, 'verdict': True}], setup)
    # A sequence-level result over the same answer: a whole-answer score, no per-character segments.
    sequence_run = _span_run('abcd', [], _setup(level='sequence'))
    sequence_run = sequence_run.model_copy(update={
        'analysis': sequence_run.analysis.model_copy(update={'segments': [], 'verdict': True, 'score': 0.7})
    })

    agreement, note = compute_agreement(span_run, sequence_run)

    assert agreement is None
    assert 'whole answer' in note


# --- helpers: Δscore comparability rule (the one server-side gate) --------------------------------

CAL = ScoreSemantics.CALIBRATED_PROBABILITY
RAW = ScoreSemantics.THRESHOLDED_RAW_SCORE
REL = ScoreSemantics.RELATIVE_WITHIN_ANSWER
AGR = ScoreSemantics.SPAN_AGREEMENT


@pytest.mark.parametrize('a_sem,b_sem,expect_number', [
    (CAL, CAL, True),    # both calibrated probabilities: the one comparable absolute scale
    (CAL, RAW, False),   # mixed scales
    (RAW, RAW, False),   # two raw thresholded scores from different probes are NOT comparable
    (REL, REL, False),   # relative-within-answer never compares across runs
    (AGR, AGR, False),   # judge agreement is not a probability
    (CAL, REL, False),
])
def test_score_delta_only_for_matching_calibrated_probabilities(a_sem, b_sem, expect_number):
    delta, note = score_delta(a_sem, 0.8, b_sem, 0.5)

    if expect_number:
        assert delta == pytest.approx(-0.3)
        assert 'Different score scales' not in note
    else:
        assert delta is None
        assert note == 'Different score scales — localization overlap only.'


def test_score_delta_requires_both_scores_present():
    assert score_delta(CAL, 0.8, CAL, None)[0] is None


# --- ComparePayload contract round-trip -----------------------------------------------------------

def test_compare_payload_round_trips_camel_case():
    setup = _setup()
    run_a = _span_run('abcd', [{'start': 0, 'end': 2, 'verdict': True}], setup)
    run_b = _span_run('abcd', [{'start': 1, 'end': 3, 'verdict': True}], setup)

    payload = build_compare_payload(run_a, run_b, 'A-probe', 'B-judge')
    dumped = payload.model_dump(mode='json', by_alias=True)

    assert dumped['presetA'] == 'A-probe'
    assert dumped['agreement'] == {'both': 1, 'aOnly': 1, 'bOnly': 1, 'neither': 1}
    assert dumped['deltaNote'] == 'Different score scales — localization overlap only.'
    # Round-trips back through the strict (extra='forbid') DTO.
    assert ComparePayload.model_validate(dumped).agreement.a_only == 1


# --- controller runCompare ------------------------------------------------------------------------

def _controller():
    session = WorkspaceSession({})
    engine = RunEngine(
        generate=lambda _r, _s: 'abcd',
        detect=lambda _a, _r, s: {'spans': [{'start': 0, 'end': 2, 'score': 0.9, 'verdict': True}]}
        if s.detector_preset == 'A-probe'
        else {'spans': [{'start': 1, 'end': 3, 'score': 0.8, 'verdict': True}]},
    )
    return session, WorkspaceController(session, engine, compare_setup=_compare_setup)


def _drain(controller):
    for _ in range(12):
        if not controller.advance():
            break


def test_run_compare_supplied_answer_scores_both_sides_and_reports_agreement():
    session, controller = _controller()

    receipt = controller.handle(
        _envelope(session, 'runCompare', {
            'inputs': {'question': 'q?', 'context': 'ctx', 'suppliedAnswer': 'abcd'},
            'presetB': 'B-judge',
        }),
        setup=_setup(),
    )
    _drain(controller)

    assert receipt.status is ReceiptStatus.ACCEPTED
    assert {run.setup_snapshot.detector_preset: run.status for run in session.state.runs} == {
        'A-probe': RunStatus.SUCCEEDED,
        'B-judge': RunStatus.SUCCEEDED,
    }
    compare = controller._compare_payload()
    assert compare.agreement.both == 1
    assert compare.run_a.answer == compare.run_b.answer == 'abcd'


def test_run_compare_generate_reuses_side_a_answer_for_side_b():
    session, controller = _controller()

    controller.handle(
        _envelope(session, 'runCompare', {
            'inputs': {'question': 'q?', 'context': 'ctx'},
            'presetB': 'B-judge',
        }),
        setup=_setup(),
    )
    _drain(controller)

    runs = {run.setup_snapshot.detector_preset: run for run in session.state.runs}
    # B never generated a second answer — it scored exactly the answer A produced.
    assert runs['A-probe'].answer == 'abcd'
    assert runs['B-judge'].answer == 'abcd'
    assert runs['B-judge'].status is RunStatus.SUCCEEDED


def test_run_compare_rejects_unknown_preset_without_queuing_runs():
    session, controller = _controller()

    receipt = controller.handle(
        _envelope(session, 'runCompare', {
            'inputs': {'question': 'q?', 'context': 'ctx'},
            'presetB': 'missing',
        }),
        setup=_setup(),
    )

    assert receipt.status is ReceiptStatus.REJECTED
    assert 'not available' in receipt.message
    assert session.state.runs == []
    assert session.state.compare is None


def test_run_compare_accepts_a_lagging_runs_revision():
    # The runs revision is informational: compare appends new runs, so a payload that
    # trails the server (slow hosts) must not block it.
    session, controller = _controller()
    action = _envelope(session, 'runCompare', {
        'inputs': {'question': 'q?', 'context': 'ctx'},
        'presetB': 'B-judge',
    })
    action = action.model_copy(update={'expected_runs_revision': 999})

    receipt = controller.handle(action, setup=_setup())

    assert receipt.status is ReceiptStatus.ACCEPTED
    assert len(session.state.runs) == 2  # side A + side B queued


def test_run_compare_rejects_a_side_b_setup_error_before_running():
    session, controller = _controller()

    receipt = controller.handle(
        _envelope(session, 'runCompare', {
            'inputs': {'question': 'q?', 'context': 'ctx'},
            'presetB': 'B-judge',
        }),
        setup=_setup(),
        submission_error='The comparison detector needs an API key for OpenRouter.',
    )

    assert receipt.status is ReceiptStatus.REJECTED
    assert 'API key' in receipt.message
    assert session.state.runs == []
