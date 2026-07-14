import copy
import json

import pytest

from sirin.ui.demo_cases import load_ragtruth_demo_cases
from sirin.ui.workspace.contracts import RunMode, TaskType
from sirin.ui.workspace.examples import ExampleRegistry


def _write_tampered_asset(tmp_path, mutate):
    cases = copy.deepcopy(load_ragtruth_demo_cases())
    mutate(cases)
    path = tmp_path / 'ragtruth_demo_cases.json'
    path.write_text(
        json.dumps({'schema_version': 1, 'cases': cases}), encoding='utf-8'
    )
    return path


def test_curated_cases_load_in_demo_order():
    cases = load_ragtruth_demo_cases()

    assert [(case['dataset_index'], case['label']) for case in cases] == [
        (0, 'RAGTruth: Bowel movement & weight'),
        (4, 'RAGTruth: Carbon footprint'),
        (138, 'RAGTruth: FEHA vs ADA'),
        (721, 'RAGTruth: Patterned paint rollers'),
    ]


def test_supported_case_carries_no_spans_hallucinated_cases_do():
    cases = load_ragtruth_demo_cases()

    assert cases[0]['gold_spans'] == []
    assert cases[0]['source_answer_model'] == 'gpt-4-0613'
    assert all(case['gold_visibility'] == 'hidden' for case in cases)
    assert [len(case['gold_spans']) for case in cases] == [0, 1, 2, 1]


def test_absent_asset_is_silent(tmp_path):
    assert load_ragtruth_demo_cases(tmp_path / 'missing.json') == []


def test_loader_rejects_changed_assistant_content(tmp_path):
    def mutate(cases):
        cases[0]['messages'][1]['content'] += ' changed'

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='assistant content SHA-256 mismatch'):
        load_ragtruth_demo_cases(path)


def test_loader_rejects_changed_messages_digest(tmp_path):
    def mutate(cases):
        cases[0]['messages_sha256'] = '0' * 64

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='messages SHA-256 mismatch'):
        load_ragtruth_demo_cases(path)


def test_loader_rejects_context_absent_from_prompt(tmp_path):
    def mutate(cases):
        cases[0]['context'] = 'A passage that never appears in the prompt.'

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='context does not appear in the prompt'):
        load_ragtruth_demo_cases(path)


def test_loader_rejects_gold_span_beyond_answer(tmp_path):
    def mutate(cases):
        cases[1]['gold_spans'] = [[0, len(cases[1]['answer']) + 1]]

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='gold spans are invalid'):
        load_ragtruth_demo_cases(path)


def test_loader_rejects_duplicate_labels(tmp_path):
    def mutate(cases):
        cases[1]['label'] = cases[0]['label']

    path = _write_tampered_asset(tmp_path, mutate)

    with pytest.raises(ValueError, match='Duplicate RAGTruth demo case label'):
        load_ragtruth_demo_cases(path)


def test_registry_exposes_ragtruth_chips_as_faithfulness_replays():
    registry = ExampleRegistry()
    summaries = {summary.id: summary for summary in registry.summaries()}

    for case in load_ragtruth_demo_cases():
        summary = summaries[case['case_id']]
        assert summary.label == case['label']
        assert summary.task == TaskType.FAITHFULNESS
        assert summary.context == case['context']
        assert summary.recorded_answer == case['answer']

        request, provenance = registry.resolve(case['case_id'])
        assert request.task == TaskType.FAITHFULNESS
        assert request.mode == RunMode.RECORDED_REPLAY
        assert request.supplied_answer == case['answer']
        assert provenance.dataset == 'ragtruth_qa'
