"""End-to-end behaviour of the API token judge through the v2 run path.

Covers PR-2 (a pasted key never leaks into any exported/derived artifact) and PR-3 (honest
span-agreement semantics + note, graded k/n disclosures, the K-of-N verbatim warning, and the
``JudgeAnnotationError`` -> actionable partial mapping). The judge's network ``sample`` is faked,
so no request leaves the process.
"""

import json

import pytest

from sirin.ui.presets import _build_openai_token_judge
from sirin.ui.providers import resolve_api_provider
from sirin.ui.streamlit_app import build_sample, detection_view_model
from sirin.ui.workspace.contracts import (
    RunMode,
    RunRequest,
    RunStatus,
    ScoreSemantics,
    SetupSnapshot,
    derive_score_semantics,
)
from sirin.ui.workspace.run_engine import RunEngine
from sirin.ui.workspace.session import export_run

SENTINEL = 'sk-SENTINEL-DO-NOT-LEAK-abcdef123456'
ANSWER = 'abcd'


def _run_judge(monkeypatch, gens, *, key=SENTINEL):
    judge = _build_openai_token_judge(
        judge_api_key=key, api_provider='OpenRouter', judge_model='demo/judge'
    )
    judge.config.num_beams = len(gens)
    monkeypatch.setattr(
        judge.model_adapter,
        'sample',
        lambda inputs, max_tokens=None, temperature=None, top_p=None, n=1: [gens],
    )
    result = judge.detect([build_sample('the prompt', ANSWER)])
    view = detection_view_model(result, ANSWER, judge)
    setup = SetupSnapshot(
        detector_preset='Judge — API Span (zero-shot)',
        detector_family='judge',
        detector_level='token',
    )
    engine = RunEngine(generate=None, detect=lambda *_a: view)
    request = RunRequest(
        mode=RunMode.SCORE_SUPPLIED_ANSWER, question='q', supplied_answer=ANSWER
    )
    run = engine.execute(engine.reserve(request, setup, 0), request)
    return judge, view, run


def test_derive_routes_token_judge_to_span_agreement():
    assert (
        derive_score_semantics(calibrated=True, family='judge', level='token')
        is ScoreSemantics.SPAN_AGREEMENT
    )
    # A sequence judge stays a verdict; the calibrated display flag must not become a probability.
    assert (
        derive_score_semantics(calibrated=False, family='judge', level='sequence')
        is ScoreSemantics.VERDICT
    )


def test_token_judge_run_is_span_agreement_with_honest_note(monkeypatch):
    gens = ['ab[SPAN]cd[/SPAN]', 'ab[SPAN]cd[/SPAN]', 'ab[SPAN]cd[/SPAN]', 'abcd', 'abcd']  # cd 3/5
    _judge, _view, run = _run_judge(monkeypatch, gens)

    assert run.status is RunStatus.SUCCEEDED
    assert run.setup_snapshot.score_semantics is ScoreSemantics.SPAN_AGREEMENT
    assert run.analysis.score_semantics is ScoreSemantics.SPAN_AGREEMENT
    assert 'not a calibrated probability' in (run.analysis.note or '')
    assert '5/5' in run.analysis.note  # valid/requested denominator
    # cd is graded above the judge threshold (3/5), ab clean -> one suspect span
    span = next(s for s in run.analysis.segments if s.verdict and s.text == 'cd')
    assert span.score == pytest.approx(0.6)


def test_judge_disclosures_carry_counts_never_key_or_base_url(monkeypatch):
    gens = ['ab[SPAN]cd[/SPAN]', 'abcd', 'abcd']
    _judge, _view, run = _run_judge(monkeypatch, gens)

    disclosures = run.provenance.disclosures
    assert 'Judge model: demo/judge' in disclosures
    assert 'Judge provider: OpenRouter' in disclosures
    assert 'Judge samples: 3/3 verbatim-aligned' in disclosures
    assert any(d.startswith('Judge temperature:') for d in disclosures)
    assert all(SENTINEL not in d and 'http' not in d for d in disclosures)


def test_kn_verbatim_warning_when_some_samples_dropped(monkeypatch):
    gens = ['ab[SPAN]cd[/SPAN]', 'abcd', 'not an echo', 'xy', 'ab']  # only 2 of 5 echo
    _judge, _view, run = _run_judge(monkeypatch, gens)

    assert run.warnings == ['3 of 5 judge samples were not verbatim and were excluded.']


def test_pasted_key_never_enters_export_or_snapshot(monkeypatch):
    gens = ['ab[SPAN]cd[/SPAN]', 'abcd', 'abcd']
    judge, view, run = _run_judge(monkeypatch, gens)

    # The key really reached the live adapter, so absence downstream is a guarantee, not a gap.
    assert judge.model_adapter.config.api_key == SENTINEL
    assert SENTINEL not in json.dumps(view)
    payload = run.model_dump(mode='json', by_alias=True)
    assert SENTINEL not in json.dumps(payload)
    assert SENTINEL not in export_run(run)
    assert SENTINEL not in json.dumps(run.setup_snapshot.model_dump(mode='json'))
    assert SENTINEL not in json.dumps(run.provenance.model_dump(mode='json'))


def test_judge_annotation_error_maps_to_actionable_partial():
    # Named to match the engine's decoupled matcher; no heavy detection import needed.
    class JudgeAnnotationError(Exception):
        pass

    def detect(_answer, _request, _setup):
        raise JudgeAnnotationError('no verbatim annotation')

    engine = RunEngine(generate=None, detect=detect)
    setup = SetupSnapshot(
        detector_preset='Judge — API Span (zero-shot)',
        detector_family='judge',
        detector_level='token',
    )
    request = RunRequest(
        mode=RunMode.SCORE_SUPPLIED_ANSWER, question='q', supplied_answer=ANSWER
    )
    run = engine.execute(engine.reserve(request, setup, 0), request)

    assert run.status is RunStatus.PARTIAL
    assert run.answer == ANSWER
    assert run.error.code == 'judge_no_aligned_annotation'
    assert 'verbatim' in run.error.message


def _run_sequence_judge(
    monkeypatch, generation, logprob_result, *, verdict_max_tokens=None, captured=None
):
    from sirin.ui.presets import _build_openai_judge

    judge = _build_openai_judge(
        judge_api_key=SENTINEL, api_provider='OpenRouter', judge_model='demo/judge'
    )
    if verdict_max_tokens is not None:
        judge.config.verdict_max_tokens = verdict_max_tokens

    def fake_sample(inputs, **kwargs):
        if captured is not None:
            captured.update(kwargs)
        return [generation], [logprob_result]

    monkeypatch.setattr(judge.model_adapter, 'sample', fake_sample)
    return judge, judge.detect([build_sample('the prompt', ANSWER)])


def test_sequence_judge_never_fabricates_a_verdict(monkeypatch):
    # A reasoning model spends the one-token budget on thinking ('We'), returns no
    # logprobs (OpenRouter :free routes): raise, never a silent pred=0 all-clear.
    from sirin.detection.judging.judges.base import JudgeAnnotationError

    with pytest.raises(JudgeAnnotationError, match='bare class digit'):
        _run_sequence_judge(monkeypatch, 'We', None)


def test_sequence_judge_digit_without_logprobs_keeps_verdict_no_score(monkeypatch):
    _judge, (probs, preds, _) = _run_sequence_judge(monkeypatch, '1', None)

    assert preds[0] == 1
    assert probs[0] != probs[0]  # nan score: verdict holds, probability honestly absent


def test_presenter_scalar_drops_non_finite_scores():
    from sirin.ui.workspace.presenter import _scalar

    assert _scalar(float('nan')) is None
    assert _scalar(float('inf')) is None
    assert _scalar(0.5) == 0.5


def test_provider_rate_limit_maps_to_actionable_partial():
    # Named to match the engine's decoupled matcher; free-tier daily quotas make
    # this the most common failure a public demo visitor hits.
    class RateLimitError(Exception):
        pass

    def detect(_answer, _request, _setup):
        raise RateLimitError('429 free-models-per-day')

    engine = RunEngine(generate=None, detect=detect)
    setup = SetupSnapshot(
        detector_preset='Judge — API Span (zero-shot)',
        detector_family='judge',
        detector_level='token',
    )
    request = RunRequest(
        mode=RunMode.SCORE_SUPPLIED_ANSWER, question='q', supplied_answer=ANSWER
    )
    run = engine.execute(engine.reserve(request, setup, 0), request)

    assert run.status is RunStatus.PARTIAL
    assert run.answer == ANSWER
    assert run.error.code == 'provider_rate_limited'
    assert 'rate-limited' in run.error.message
    assert '429' not in run.error.message  # our copy, never raw provider output


def test_provider_auth_failure_maps_to_actionable_partial():
    class AuthenticationError(Exception):
        pass

    def detect(_answer, _request, _setup):
        raise AuthenticationError('401 bad key sk-secret')

    engine = RunEngine(generate=None, detect=detect)
    setup = SetupSnapshot(
        detector_preset='Judge — API Span (zero-shot)',
        detector_family='judge',
        detector_level='token',
    )
    request = RunRequest(
        mode=RunMode.SCORE_SUPPLIED_ANSWER, question='q', supplied_answer=ANSWER
    )
    run = engine.execute(engine.reserve(request, setup, 0), request)

    assert run.error.code == 'provider_auth_failed'
    assert 'sk-secret' not in run.error.message


def test_pasted_key_wins_over_env_and_absence_is_actionable(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'env-key')
    assert resolve_api_provider('OpenAI', api_key='pasted-key').api_key == 'pasted-key'
    assert resolve_api_provider('OpenAI').api_key == 'env-key'
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with pytest.raises(ValueError, match='OPENAI_API_KEY'):
        resolve_api_provider('OpenAI')


def test_sequence_judge_extracts_digit_from_reasoning_answer(monkeypatch):
    # OpenRouter reasoning models put prose in content; the verdict digit is scanned out.
    _judge, (probs, preds, _) = _run_sequence_judge(monkeypatch, 'The answer is 1', None)

    assert preds[0] == 1
    assert probs[0] != probs[0]  # nan: no logprobs -> no score, verdict holds


def test_sequence_judge_multi_token_answer_never_borrows_first_token_logprob(monkeypatch):
    # The adapter's logprobs carry no token text: for a multi-token answer the first
    # logprob belongs to a thinking token, not the digit -> honest nan, not a fake score.
    _judge, (probs, preds, _) = _run_sequence_judge(
        monkeypatch, 'The answer is 1', [[-0.1, -2.0]]
    )

    assert preds[0] == 1
    assert probs[0] != probs[0]


def test_sequence_judge_single_digit_answer_keeps_logprob_score(monkeypatch):
    _judge, (probs, preds, _) = _run_sequence_judge(monkeypatch, '1', [[-0.1, -2.0]])

    assert preds[0] == 1
    assert probs[0] == pytest.approx(0.1)


def test_sequence_judge_one_token_protocol_is_unchanged(monkeypatch):
    captured = {}
    _judge, (probs, preds, _) = _run_sequence_judge(
        monkeypatch, '0', None, verdict_max_tokens=1, captured=captured
    )

    assert preds[0] == 0
    assert captured['max_tokens'] == 1


def test_sequence_judge_raises_when_no_digit_anywhere(monkeypatch):
    from sirin.detection.judging.judges.base import JudgeAnnotationError

    with pytest.raises(JudgeAnnotationError, match='class digit'):
        _run_sequence_judge(monkeypatch, 'I refuse to answer.', None)


def test_ui_builder_gives_reasoning_judges_room_to_think():
    from sirin.ui.presets import _build_openai_judge

    judge = _build_openai_judge(
        judge_api_key=SENTINEL, api_provider='OpenRouter', judge_model='demo/judge'
    )
    assert judge.config.verdict_max_tokens == 512
