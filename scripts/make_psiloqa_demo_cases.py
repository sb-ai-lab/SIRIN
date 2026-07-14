"""Build the curated PsiloQA span demo-case asset from the ranked top-5 export."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    REPO_ROOT
    / 'output/sirin_a_star_demo/psiloqa_span/experiment/top5_demo_cases.json'
)
FIXTURE_PATH = REPO_ROOT / 'sirin/ui/assets/psiloqa_span_demo.json'
ASSET_PATH = REPO_ROOT / 'sirin/ui/assets/psiloqa_demo_cases.json'
CHECKPOINT = 'demo/checkpoints/qwen3_4b_psiloqa_span_linear'
PROMPT_PREFIX = 'Answer the question based on the passage.\nPassage: '

SELECTED_CASES = (
    (
        133,
        'D. H. Lawrence',
        'Invented rationale (bird symbolism, psychoanalysis); the passage '
        'credits the 1927 Etruscan tombs visit.',
    ),
    (
        870,
        'Llanbadoc',
        'Whole answer fabricated: claims Oliver Cromwell was born in the '
        'Welsh village of Llanbadoc.',
    ),
    (
        499,
        'Videna electra',
        'A Palau land snail described as a beetle genus from Indonesia.',
    ),
    (
        473,
        'Apollo roles',
        'Invented Apollo mission-scientist and backup-pilot roles for '
        'Joseph Shea.',
    ),
    (
        869,
        'Census number',
        'Single fabricated figure: the answer reports a 2011 census '
        'population of 345 for Llanbadoc; the passage says 806. One small '
        'confident span, the rest of the answer stays clean.',
    ),
    (
        763,
        'Harvard roles',
        'Localized spans: invented "professor of law / Dean of Harvard Law '
        'School" roles; the passage says E. Kinney Zalesne is a writer and '
        'Senior Advisor to a Harvard initiative. Most of the answer stays '
        'clean.',
    ),
)

DATASET_PATH = '/home/jovyan/ybelikova/sirin-final/data/datasets/psiloqa_en_span'

# Cut a stored answer right after this marker (inclusive); the case is then
# flagged answer_truncated and the UI discloses the excerpt.
TRUNCATE_AFTER = {869: '345 people.'}

DISCLOSURE_FIELDS = (
    'representation_model',
    'representation_disclosure',
    'selection_disclosure',
    'annotation_disclosure',
    'license',
)


def build_prompt(passage: str, question: str) -> str:
    return (
        'Answer the question based on the passage.'
        f'\nPassage: {passage}\nQuestion: {question}\n'
    )


def split_passage(user_content: str, question: str) -> str:
    suffix = f'\nQuestion: {question}\n'
    if not user_content.startswith(PROMPT_PREFIX) or not user_content.endswith(suffix):
        raise ValueError('User prompt does not follow the PsiloQA template')
    return user_content[len(PROMPT_PREFIX):len(user_content) - len(suffix)]


def source_answer_model(case_id: str) -> str:
    if not case_id.startswith('psiloqa_'):
        raise ValueError(f'Unexpected PsiloQA case id: {case_id}')
    model, _, tail = case_id.removeprefix('psiloqa_').rpartition('_')
    if not model or not tail.isdigit():
        raise ValueError(f'Unexpected PsiloQA case id: {case_id}')
    return model


def canonical_messages_sha256(messages: list[dict[str, str]]) -> str:
    encoded = json.dumps(
        messages,
        ensure_ascii=False,
        separators=(',', ':'),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_case(
    raw: dict[str, Any],
    label: str,
    why_notable: str,
    disclosures: dict[str, str],
) -> dict[str, Any]:
    case_id = raw['id']
    messages = [
        {'role': message['role'], 'content': message['content']}
        for message in raw['input']
    ]
    if [message['role'] for message in messages] != ['user', 'assistant']:
        raise ValueError(f'Case {case_id} input must be a user/assistant pair')
    if raw['answer'] != messages[1]['content']:
        raise ValueError(f'Case {case_id} answer must match the assistant message')

    answer = raw['answer']
    truncate_marker = TRUNCATE_AFTER.get(raw['dataset_index'])
    truncated = False
    if truncate_marker:
        marker_at = answer.find(truncate_marker)
        if marker_at < 0:
            raise ValueError(f'Case {case_id} truncate marker not found')
        answer = answer[: marker_at + len(truncate_marker)]
        messages[1]['content'] = answer
        truncated = True
        for span in raw['gold_spans']:
            if span[1] > len(answer):
                raise ValueError(f'Case {case_id} truncation cuts a gold span')

    passage = split_passage(messages[0]['content'], raw['question'])
    if build_prompt(passage, raw['question']) != messages[0]['content']:
        raise ValueError(f'Case {case_id} prompt roundtrip failed')

    return {
        'case_id': case_id,
        'label': label,
        'why_notable': why_notable,
        'dataset': 'psiloqa_en_span',
        'split': 'test',
        'dataset_index': raw['dataset_index'],
        'passage': passage,
        'question': raw['question'],
        'answer': answer,
        'answer_truncated': truncated,
        'messages': messages,
        'content_sha256': {
            'user': hashlib.sha256(messages[0]['content'].encode()).hexdigest(),
            'assistant': hashlib.sha256(messages[1]['content'].encode()).hexdigest(),
        },
        'messages_sha256': canonical_messages_sha256(messages),
        'gold_spans': raw['gold_spans'],
        'gold_visibility': 'hidden',
        'source_answer_model': source_answer_model(case_id),
        **disclosures,
    }


def main() -> None:
    source = json.loads(SOURCE_PATH.read_text(encoding='utf-8'))
    fixture_case = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))['case']
    disclosures = {field: fixture_case[field] for field in DISCLOSURE_FIELDS}

    by_index = {case['dataset_index']: case for case in source['top5']}
    missing = [index for index, _, _ in SELECTED_CASES if index not in by_index]
    if missing:
        from datasets import load_from_disk

        test_split = load_from_disk(DATASET_PATH)['test']
        for index in missing:
            row = test_split[index]
            by_index[index] = {
                'id': row['id'],
                'dataset_index': index,
                'question': row['question'],
                'answer': row['input'][1]['content'],
                'input': row['input'],
                'gold_spans': row['target'],
            }
    cases = [
        build_case(by_index[dataset_index], label, why_notable, disclosures)
        for dataset_index, label, why_notable in SELECTED_CASES
    ]

    payload = {
        'schema_version': 1,
        'source': str(SOURCE_PATH.relative_to(REPO_ROOT)),
        'checkpoint': CHECKPOINT,
        'cases': cases,
    }
    ASSET_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(f'Wrote {len(cases)} cases to {ASSET_PATH.relative_to(REPO_ROOT)}')


if __name__ == '__main__':
    main()
