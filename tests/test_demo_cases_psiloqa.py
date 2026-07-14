import copy
import json

import pytest

from sirin.ui.demo_cases import load_psiloqa_demo_cases


def _write_tampered_asset(tmp_path, mutate):
    cases = copy.deepcopy(load_psiloqa_demo_cases())
    mutate(cases)
    path = tmp_path / 'psiloqa_demo_cases.json'
    path.write_text(
        json.dumps({'schema_version': 1, 'cases': cases}), encoding='utf-8'
    )
    return path


def test_curated_cases_load_in_demo_order():
    cases = load_psiloqa_demo_cases()

    assert [(case['dataset_index'], case['label']) for case in cases] == [
        (133, 'D. H. Lawrence'),
        (460, 'Douglas Wright'),
        (822, 'LECT2 disorder'),
        (984, 'Picard influences'),
        (473, 'Apollo roles'),
    ]


def test_hero_case_is_verified_escaped_cock_fixture():
    hero = load_psiloqa_demo_cases()[0]

    assert (
        hero['case_id'],
        hero['split'],
        hero['gold_spans'],
        hero['gold_visibility'],
        hero['source_answer_model'],
        len(hero['answer']),
    ) == (
        'psiloqa_ServiceNow-AI/Apriel-5B-Instruct_4775',
        'test',
        [[121, 456]],
        'hidden',
        'ServiceNow-AI/Apriel-5B-Instruct',
        457,
    )


def test_loader_rejects_changed_assistant_content(tmp_path):
    def mutate(cases):
        cases[0]['messages'][1]['content'] += ' changed'

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='assistant content SHA-256 mismatch'):
        load_psiloqa_demo_cases(path)


def test_loader_rejects_changed_messages_digest(tmp_path):
    def mutate(cases):
        cases[0]['messages_sha256'] = '0' * 64

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='messages SHA-256 mismatch'):
        load_psiloqa_demo_cases(path)


def test_loader_rejects_passage_that_cannot_rebuild_prompt(tmp_path):
    def mutate(cases):
        cases[0]['passage'] = 'A different passage entirely.'

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='do not rebuild the user prompt'):
        load_psiloqa_demo_cases(path)


def test_loader_rejects_gold_span_beyond_answer(tmp_path):
    def mutate(cases):
        cases[0]['gold_spans'] = [[0, len(cases[0]['answer']) + 1]]

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='gold spans are invalid'):
        load_psiloqa_demo_cases(path)


def test_loader_rejects_duplicate_labels(tmp_path):
    def mutate(cases):
        cases[1]['label'] = cases[0]['label']

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='Duplicate PsiloQA demo case label'):
        load_psiloqa_demo_cases(path)
