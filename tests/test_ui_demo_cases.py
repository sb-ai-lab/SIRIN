import copy
import hashlib
import json
from pathlib import Path

import pytest

from sirin.ui.demo_cases import (
    generation_messages,
    load_demo_cases,
    load_psiloqa_span_demo_case,
)


def test_psiloqa_span_demo_case_is_exact_held_out_fixture():
    case = load_psiloqa_span_demo_case()

    assert case['sample_id'] == (
        'psiloqa_ServiceNow-AI/Apriel-5B-Instruct_4775'
    )
    assert (case['split'], case['dataset_index']) == ('test', 133)
    assert case['question'] == (
        'What inspired D. H. Lawrence to reflect upon death and myths of '
        "resurrection when writing the first part of 'The Escaped Cock'?"
    )
    assert case['context'].startswith(
        'Answer the question based on the passage.\n'
        'Passage: The Escaped Cock is a short novel'
    )
    assert case['context'].endswith(f"Question: {case['question']}\n")
    assert case['messages'][0]['content'] == case['context']
    assert len(case['answer']) == 457
    assert case['messages'] == [
        {'role': 'user', 'content': case['messages'][0]['content']},
        {'role': 'assistant', 'content': case['answer']},
    ]
    assert case['content_sha256'] == {
        'user': 'c20e5dae79c0f0b251245cc5c9aa8667a6426c13af93518863e3f0a09e9d8e9b',
        'assistant': (
            '3514a976ef4c2e80ad925c30873165d8ca2cf89d62831424237fe36caac50570'
        ),
    }
    assert case['messages_sha256'] == (
        'b0c178f932ea3e63ef2ff030e49e05a0021758fbcedccab31cb61a355735c87c'
    )
    assert case['gold_spans'] == [[121, 456]]
    assert case['answer'][121:456] == (
        'likely influenced by his interest in mythology and the symbolism of birds, '
        'particularly the cock, which is often associated with resurrection and '
        'renewal in various cultures. Additionally, his personal experiences and '
        'observations of the natural world, as well as his interest in psychoanalysis, '
        'may have also contributed to this theme'
    )
    assert case['gold_visibility'] == 'hidden'
    assert case['source_answer_model'] == (
        'ServiceNow-AI/Apriel-5B-Instruct'
    )
    assert case['representation_model'] == 'Qwen/Qwen3-4B'
    assert 'proxy' in case['representation_disclosure'].lower()
    assert 'curated' in case['selection_disclosure'].lower()


def test_psiloqa_span_demo_loader_rejects_changed_message_content(tmp_path):
    case = copy.deepcopy(load_psiloqa_span_demo_case())
    case['messages'][1]['content'] += ' changed'
    path = tmp_path / 'psiloqa_span_demo.json'
    path.write_text(
        json.dumps({'schema_version': 1, 'case': case}), encoding='utf-8'
    )

    with pytest.raises(ValueError, match='assistant content SHA-256 mismatch'):
        load_psiloqa_span_demo_case(path)


def test_recorded_demo_cases_are_exact_and_portable():
    cases = load_demo_cases()

    assert list(cases) == ['681a1674', 'ef66a6e5', '07741c44']
    marvel = cases['681a1674']
    assert marvel['question'] == 'How many Marvel movies did I re-watch?'
    assert marvel['prediction'] == 'One'
    assert marvel['gold'] == '2'
    assert marvel['score'] == 0.9983455751552265
    assert marvel['prompt_sha256'] == (
        'a904e2548ace27e5f7c39f3517edeeb955bce764278b2937789e5bf3b44f0976'
    )
    assert marvel['messages_sha256'] == (
        '3f07c9b1f81e48bfb936cd655195d13193787313a4c45680ee290270626d0ee4'
    )
    assert generation_messages(marvel)[0] == {
        'role': 'system',
        'content': (
            'You are a professional Q&A assistant. Extract concise answers from context. '
            'You must output valid JSON format.'
        ),
    }
    assert [item['label'] for item in marvel['evidence_excerpts']] == [
        'Context 1',
        'Context 2',
        'Context 5',
    ]

    sports = cases['ef66a6e5']
    assert sports['prediction'] == '1 sport (tennis)'
    assert sports['gold'] == 'two'
    assert sports['score'] is None
    assert sports['prompt_sha256'] == (
        'e40f335ee8a0db16a8d3b1089a10b14da8ba70b10ede2b063bcfa700c072742b'
    )
    assert sports['messages_sha256'] == (
        '006aaf6b6a218e1fe36e2ce020c4400f059c00fe8363305931d2300871600c00'
    )
    trace = sports['token_trace']
    assert trace['token_pieces'] == ['1', ' sport', ' (', 'ten', 'nis', ')']
    assert trace['normalized_scores'][:2] == pytest.approx([0.8806687427, 1.0])
    source = Path(__file__).parents[1] / trace['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == trace['source_sha256']

    sneakers = cases['07741c44']
    assert sneakers['question'] == 'Where do I initially keep my old sneakers?'
    assert sneakers['prediction'] == 'In a shoe rack'
    assert sneakers['gold'] == 'under my bed'
    assert sneakers['score'] == pytest.approx(0.7290154702)
    assert sneakers['provenance']['category'] == 'knowledge-update'
    assert sneakers['evaluation_scope'] == (
        'training example approved for mechanics demonstration'
    )

    assert {case['detector'] for case in cases.values()} == {
        'Nested grouped-OOF hidden-state logistic probe',
        'Token uncertainty (chosen-token NLL + top-20 entropy)',
    }
    assert all(case['threshold'] is None for case in cases.values())
    assert all(
        case['provenance']['score_method']
        == 'StandardScaler -> PCA(256) -> balanced LogisticRegression'
        for case in (marvel,)
    )
    assert [
        (case['provenance']['fold'], case['provenance']['probe_layer'])
        for case in cases.values()
    ] == [
        (4, 30),
        (None, None),
        (3, 30),
    ]
    assert all(
        not Path(case['provenance'][field]).is_absolute()
        for case in cases.values()
        for field in ('trace', 'score_source')
    )
    assert '/home/' not in json.dumps(cases)


def test_loader_rejects_changed_prompt(tmp_path):
    cases = copy.deepcopy(list(load_demo_cases().values()))
    cases[0]['answer_prompt'] += 'changed'
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps({'schema_version': 2, 'cases': cases}), encoding='utf-8')

    with pytest.raises(ValueError, match='prompt SHA-256 mismatch'):
        load_demo_cases(path)


def test_loader_rejects_missing_required_field(tmp_path):
    cases = copy.deepcopy(list(load_demo_cases().values()))
    del cases[0]['prediction']
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps({'schema_version': 2, 'cases': cases}), encoding='utf-8')

    with pytest.raises(ValueError, match='missing: prediction'):
        load_demo_cases(path)


def test_loader_rejects_changed_message_sequence(tmp_path):
    cases = copy.deepcopy(list(load_demo_cases().values()))
    cases[0]['system_prompt'] += ' changed'
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps({'schema_version': 2, 'cases': cases}), encoding='utf-8')

    with pytest.raises(ValueError, match='messages SHA-256 mismatch'):
        load_demo_cases(path)


def test_loader_validates_optional_token_trace(tmp_path):
    case = copy.deepcopy(next(iter(load_demo_cases().values())))
    case['prediction'] = '1 sport (tennis)'
    case['score'] = None
    case['token_trace'] = {
        'answer_sha256': (
            '1e3620d40641252c717b85c570955b06fa98583cdbe9d8d657f98c5d226207f8'
        ),
        'metric': 'chosen-token negative log-probability',
        'normalization': 'per-answer min-max',
        'token_pieces': ['1', ' sport', ' (', 'ten', 'nis', ')'],
        'token_offsets': [[0, 1], [1, 7], [7, 9], [9, 12], [12, 15], [15, 16]],
        'raw_scores': [0.8, 0.6, 0.2, 0.3, 0.0, 0.1],
        'normalized_scores': [1.0, 0.75, 0.25, 0.375, 0.0, 0.125],
        'top20_entropy': [0.9, 0.7, 0.3, 0.4, 0.0, 0.1],
        'source': 'artifacts/token_trace.json',
        'source_sha256': '0' * 64,
    }
    path = tmp_path / 'cases.json'
    path.write_text(
        json.dumps({'schema_version': 2, 'cases': [case]}), encoding='utf-8'
    )

    assert load_demo_cases(path)[case['sample_id']]['token_trace']['token_pieces'][
        1
    ] == (' sport')

    case['token_trace']['token_offsets'][1] = [4, 9]
    path.write_text(
        json.dumps({'schema_version': 2, 'cases': [case]}), encoding='utf-8'
    )
    with pytest.raises(ValueError, match='token offsets are not contiguous'):
        load_demo_cases(path)
