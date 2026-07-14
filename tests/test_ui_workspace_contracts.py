import pytest
from pydantic import ValidationError

from sirin.ui.workspace.contracts import (
    AnalysisKind,
    ExampleSummary,
    Provenance,
    RunMode,
    RunRequest,
    ScoreSemantics,
    SetupSnapshot,
    TaskType,
    TextSegment,
)
from sirin.ui.workspace.presenter import present_analysis


def test_contracts_serialize_camel_case_and_reject_unknown_fields():
    payload = {
        'detectorPreset': 'probe',
        'detectorFamily': 'probing',
        'detectorLevel': 'sequence',
        'scoreSemantics': 'thresholdedRawScore',
    }

    setup = SetupSnapshot.model_validate(payload)

    assert setup.model_dump(by_alias=True)['scoreSemantics'] == 'thresholdedRawScore'
    with pytest.raises(ValidationError, match='Extra inputs are not permitted'):
        SetupSnapshot.model_validate({**payload, 'futureField': True})


def test_span_presentation_preserves_unicode_code_points_and_score_semantics():
    answer = 'A😀Bé'
    setup = SetupSnapshot(
        detector_preset='probe',
        detector_family='probing',
        detector_level='span',
        threshold=0.38,
        score_semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE,
    )

    result = present_analysis(
        answer,
        setup,
        {'spans': [{'start': 1, 'end': 3, 'score': 0.9}]},
    )

    assert result.kind is AnalysisKind.SPAN
    assert result.score_semantics is ScoreSemantics.THRESHOLDED_RAW_SCORE
    assert ''.join(segment.text for segment in result.segments) == answer
    assert [
        (segment.start_code_point, segment.end_code_point)
        for segment in result.segments
    ] == [(0, 1), (1, 3), (3, 4)]
    assert [segment.verdict for segment in result.segments] == [None, True, None]
    assert result.model_dump(by_alias=True)['segments'][1]['startCodePoint'] == 1
    with pytest.raises(ValidationError, match='Unicode code points'):
        TextSegment(text='😀', startCodePoint=0, endCodePoint=2)


def test_presenter_normalizes_legacy_sequence_token_and_claim_outputs():
    setup = SetupSnapshot(
        detector_preset='legacy',
        detector_family='probing',
        detector_level='sequence',
        threshold=0.5,
    )

    sequence = present_analysis('answer', setup, {'probability': 0.8, 'prediction': 1})
    token = present_analysis(
        'answer',
        setup.model_copy(update={'detector_level': 'token'}),
        {'spans': None},
    )
    claims = present_analysis(
        'answer',
        setup.model_copy(update={'detector_level': 'claim'}),
        {'claims': [{'fact': 'A grounded fact', 'prob': 0.7, 'pred': 1}]},
    )
    answerability = present_analysis(
        '',
        setup.model_copy(update={'task': TaskType.ANSWERABILITY}),
        {},
    )

    assert (sequence.score, sequence.verdict) == (0.8, True)
    assert token.kind is AnalysisKind.TOKEN
    assert token.segments == []
    assert claims.kind is AnalysisKind.CLAIM
    assert claims.claims[0].model_dump() == {
        'text': 'A grounded fact',
        'verdict': True,
        'score': 0.7,
    }
    assert answerability.label == 'Answerability detector result'


def test_example_prompt_round_trips_into_a_quick_prompt_request():
    example = ExampleSummary(
        id='quick-example',
        label='Quick prompt',
        dataset='curated',
        prompt='Summarize the evidence.',
        recorded_answer='A concise summary.',
        provenance=Provenance(),
    )

    request = RunRequest(mode=RunMode.QUICK_PROMPT, prompt=example.prompt)

    assert request.prompt == 'Summarize the evidence.'
    assert example.model_dump(by_alias=True)['recordedAnswer'] == 'A concise summary.'
