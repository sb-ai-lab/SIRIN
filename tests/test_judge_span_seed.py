"""Contract for the token-judge landing seed asset (assets/judge_span_seed.json, schema 1).

This synthetic fixture IS the contract the GPU campaign will emit: a valid asset loads, seeds a
terminal recorded-result judge run through the product path, and any misaligned score fails loudly.
"""

import hashlib
import json

import pytest

from sirin.ui.demo_cases import (
    _canonical_sha256,
    build_psiloqa_prompt,
    judge_seed_predicted_spans,
    load_judge_span_seed,
)
from sirin.ui.workspace.contracts import (
    AnalysisKind,
    RunOrigin,
    RunStatus,
    ScoreSemantics,
)
from sirin.ui.workspace.seed import build_judge_seed_run, build_seed_runs
from sirin.ui.workspace.session import (
    WorkspaceSession,
    export_run,
    import_portable_json,
)


def _fixture_payload():
    question = 'What is the population?'
    passage = 'The population was 806.'
    context = build_psiloqa_prompt(passage, question)
    answer = 'It was 345 people.'  # "345" is the fabricated figure at chars 7:10
    assert answer[7:10] == '345'
    scores = [0.0] * len(answer)
    for index in range(7, 10):
        scores[index] = 2 / 3
    messages = [
        {'role': 'user', 'content': context},
        {'role': 'assistant', 'content': answer},
    ]
    case = {
        'sample_id': 'judge_demo_1',
        'example_id': 'judge_demo_1',
        'dataset': 'psiloqa_en_span',
        'split': 'test',
        'question': question,
        'passage': passage,
        'context': context,
        'answer': answer,
        'messages': messages,
        'content_sha256': {
            'user': hashlib.sha256(context.encode()).hexdigest(),
            'assistant': hashlib.sha256(answer.encode()).hexdigest(),
        },
        'messages_sha256': _canonical_sha256(
            [{'role': m['role'], 'content': m['content']} for m in messages]
        ),
        'answer_sha256': hashlib.sha256(answer.encode()).hexdigest(),
        'gold_spans': [[7, 10]],
        'gold_visibility': 'hidden',
        'source_answer_model': 'demo/answer-model',
        'why_notable': 'One fabricated census figure.',
        'license': 'CC-BY-4.0',
        'detector': {
            'preset': 'Judge — API Span (zero-shot)',
            'family': 'judge',
            'level': 'token',
            'score_semantics': 'spanAgreement',
            'judge_model': 'demo/judge',
            'provider_label': 'OpenRouter',
            'temperature': 0.7,
            'requested': 3,
            'valid': 2,
        },
        'judge': {
            'char_scores': scores,
            'predicted_spans': judge_seed_predicted_spans(scores),
            'generations_sha256': hashlib.sha256(b'recorded-generations').hexdigest(),
        },
        'experiment_source': 'output/demo/judge_span/census.json',
    }
    return {
        'schema_version': 1,
        'case': case,
        'integrity': {'algorithm': 'sha256', 'sha256': _canonical_sha256(case)},
    }


def _write(tmp_path, payload):
    path = tmp_path / 'judge_span_seed.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return str(path)


def test_absent_asset_is_silent():
    # A missing judge asset returns None (never raises), so the landing can fall back to the probe seed.
    assert load_judge_span_seed('/nonexistent/judge_span_seed.json') is None


def test_shipped_judge_asset_seeds_a_recorded_judge_card():
    # The campaign ships assets/judge_span_seed.json, so the landing now carries the judge card too,
    # beside the probe hero seed. (Count is not pinned — a second probe seed may also be shipped.)
    runs = build_seed_runs()
    judge_runs = [run for run in runs if run.setup_snapshot.detector_family == 'judge']
    assert len(judge_runs) == 1
    assert judge_runs[0].origin is RunOrigin.RECORDED_RESULT
    assert any(run.setup_snapshot.detector_family == 'probing' for run in runs)


def test_valid_fixture_loads_and_seeds_a_recorded_judge_run(tmp_path):
    path = _write(tmp_path, _fixture_payload())

    case = load_judge_span_seed(path)
    assert case['detector']['score_semantics'] == 'spanAgreement'

    run = build_judge_seed_run(path=path)
    assert run.origin is RunOrigin.RECORDED_RESULT
    assert run.status is RunStatus.SUCCEEDED
    assert run.analysis.kind is AnalysisKind.SPAN
    assert run.analysis.score_semantics is ScoreSemantics.SPAN_AGREEMENT
    assert run.setup_snapshot.detector_family == 'judge'
    assert not run.setup_snapshot.calibrated
    assert 'not a calibrated probability' in (run.analysis.note or '')
    assert any(
        segment.verdict and segment.text == '345' for segment in run.analysis.segments
    )
    # Recorded judge run seeds into a session and round-trips through portable export.
    session = WorkspaceSession({})
    session.add_run(run)
    assert session.selected().id == run.id
    restored = import_portable_json(export_run(run))
    assert restored[0].analysis.score_semantics is ScoreSemantics.SPAN_AGREEMENT
    assert all('http' not in d for d in run.provenance.disclosures)


def test_tampered_char_score_breaks_alignment_and_raises(tmp_path):
    payload = _fixture_payload()
    # Tag character 0 without updating predicted_spans, then re-seal integrity so the check that
    # fires is the char-offset alignment, not the payload hash.
    payload['case']['judge']['char_scores'][0] = 0.5
    payload['integrity']['sha256'] = _canonical_sha256(payload['case'])
    path = _write(tmp_path, payload)

    with pytest.raises(ValueError, match='char-offset-exact'):
        load_judge_span_seed(path)


def test_payload_hash_mismatch_raises(tmp_path):
    payload = _fixture_payload()
    payload['case']['answer'] = payload['case']['answer'] + ' tampered'  # integrity now stale
    path = _write(tmp_path, payload)

    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        load_judge_span_seed(path)
