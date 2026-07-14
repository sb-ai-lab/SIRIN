import copy
import json

import pytest

from sirin.ui.demo_cases import (
    _canonical_sha256,
    load_psiloqa_span_seed,
)


def _write_seed(tmp_path, mutate, *, reseal=False):
    case = copy.deepcopy(load_psiloqa_span_seed())
    mutate(case)
    integrity_sha = _canonical_sha256(case) if reseal else 'a' * 64
    payload = {
        'schema_version': 1,
        'case': case,
        'integrity': {'algorithm': 'sha256', 'sha256': integrity_sha},
    }
    path = tmp_path / 'psiloqa_span_seed.json'
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return path


def test_seed_loads_with_recorded_probe_outputs():
    case = load_psiloqa_span_seed()

    assert (
        case['title'],
        case['dataset_index'],
        case['gold_spans'],
        case['gold_visibility'],
        case['detector']['selected_layer'],
        len(case['probe']['token_scores']),
        case['example_id'],
    ) == (
        'Census number',
        869,
        [[168, 171]],
        'hidden',
        24,
        179,
        'psiloqa_NousResearch/Nous-Hermes-2-Mistral-7B-DPO_22242',
    )
    assert case['detector']['threshold'] == pytest.approx(0.38198363780975336)
    assert case['checkpoint_sha256']['model.pt'] == (
        'dc132cc8512dcde25b721d78dc7f1a33c9da26ce2519e4d755a75ec0341551a9'
    )
    assert all(0.0 <= score <= 1.0 for score in case['probe']['token_scores'])


def test_seed_records_the_app_export_attribution():
    case = load_psiloqa_span_seed()

    recorded = case['recorded_run']
    assert recorded['origin'] == 'recordedAnswerLiveDetection'
    assert len(recorded['exported_sha256']) == 64
    assert recorded['run_id']
    assert case['experiment_source'].endswith('census_char_scores.json')


def test_seed_rejects_invalid_recorded_run_attribution(tmp_path):
    def mutate(case):
        case['recorded_run']['exported_sha256'] = 'nope'

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match='recorded-run attribution is invalid'):
        load_psiloqa_span_seed(path)


def test_seed_rejects_payload_tampering(tmp_path):
    def mutate(case):
        case['answer'] += ' changed'

    path = _write_seed(tmp_path, mutate)

    with pytest.raises(ValueError, match='payload SHA-256 mismatch'):
        load_psiloqa_span_seed(path)


def test_seed_fails_loudly_on_token_misalignment(tmp_path):
    def mutate(case):
        first, second = case['probe']['token_offsets'][0]
        case['probe']['token_offsets'][0] = [first, second + 1]

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match='token offsets are not contiguous'):
        load_psiloqa_span_seed(path)


def test_seed_rejects_out_of_range_token_score(tmp_path):
    def mutate(case):
        case['probe']['token_scores'][0] = 1.5

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match=r'token scores must be finite in \[0, 1\]'):
        load_psiloqa_span_seed(path)


def test_seed_rejects_predicted_span_text_drift(tmp_path):
    def mutate(case):
        case['probe']['predicted_span_scores'][0]['text'] += '!'

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match='predicted span is misaligned'):
        load_psiloqa_span_seed(path)


def test_seed_rejects_invalid_checkpoint_hash(tmp_path):
    def mutate(case):
        case['checkpoint_sha256']['model.pt'] = 'not-a-hash'

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match='checkpoint SHA-256 values are invalid'):
        load_psiloqa_span_seed(path)


def test_seed_rejects_threshold_outside_unit_interval(tmp_path):
    def mutate(case):
        case['detector']['threshold'] = 1.0

    path = _write_seed(tmp_path, mutate, reseal=True)

    with pytest.raises(ValueError, match=r'threshold must be within \(0, 1\)'):
        load_psiloqa_span_seed(path)
