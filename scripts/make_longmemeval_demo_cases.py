"""Rebuild the LongMemEval recorded demo cases (schema v2) from the SimpleMem run.

Two cases are (re)built from the pure-SimpleMem Qwen3.5-35B-A3B run records, each a
real hallucination the span-tag judge (Qwen3.5-4B, num_beams=3) flags:

  * e3038f8c — count: memories list 57 records + 12 figurines + 25 coins + 5 books
    (99 total); the answer says "74 items", silently dropping the 25 coins.
  * 0bc8ad92 — temporal: the last museum visit *with a friend* was 22 Oct 2022 (gold
    5 months elapsed); the answer says "Approximately 4 months".

Answers, prompts, gold and judge probabilities are copied verbatim from the run; SIRIN
did not generate them (they were produced by Qwen/Qwen3.5-35B-A3B inside SimpleMem). The
token-uncertainty showcase case ``ef66a6e5`` is copied verbatim from the existing asset so
its recorded token_trace survives regeneration untouched.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_PATH = REPO_ROOT / 'sirin/ui/assets/demo_cases.json'
RUN_GLOB = (
    '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
    'pure_simplemem_qwen35_35b_a3b/*_500'
)
SYSTEM_PROMPT = (
    'You are a professional Q&A assistant. Extract concise answers from context. '
    'You must output valid JSON format.'
)
# The answer-generation endpoint recorded in the run's builder provenance.
ANSWER_BASE_URL = 'http://127.0.0.1:30035/v1'
DETECTOR = 'Span-tag judge sequence probability (Qwen3.5-4B, 3-beam)'
PRESERVED_CASE_ID = 'ef66a6e5'

# (sample_id, title, category, evidence context numbers) — order is the final chip order,
# with the preserved token-trace case slotted in the middle.
NEW_CASES = (
    ('e3038f8c', 'Rare-items count', [3, 4, 9, 17]),
    ('0bc8ad92', 'Months since museum visit', [2, 3]),
)
CASE_ORDER = ('e3038f8c', PRESERVED_CASE_ID, '0bc8ad92')

_BLOCK_RE = re.compile(
    r'\[Context (\d+)\]\nContent: (.*?)'
    r'(?=\nTime:|\nPersons:|\nLocation:|\nRelated Entities:|\nTopic:)',
    re.S,
)


def resolve_run_dir() -> Path:
    matches = sorted(Path('/').glob(RUN_GLOB.lstrip('/')))
    if not matches:
        raise FileNotFoundError(f'No SimpleMem run dir matches {RUN_GLOB}')
    return matches[-1]


def context_blocks(prompt: str) -> dict[int, str]:
    return {int(n): body.strip() for n, body in _BLOCK_RE.findall(prompt)}


def messages_sha256(system_prompt: str, user_prompt: str) -> str:
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_prompt},
    ]
    encoded = json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_case(
    row: pd.Series,
    sample_id: str,
    title: str,
    evidence_contexts: list[int],
    p_hallucination: float,
) -> dict[str, Any]:
    answer_prompt = row['prompt_user']
    prediction = row['prompt_assistant']
    if prediction != row['prediction']:
        raise ValueError(f'{sample_id}: prompt_assistant must equal prediction')

    blocks = context_blocks(answer_prompt)
    missing = [n for n in evidence_contexts if n not in blocks]
    if missing:
        raise ValueError(f'{sample_id}: evidence contexts {missing} not in prompt')
    evidence_excerpts = [
        {'label': f'Context {n}', 'rank': n, 'content': blocks[n]}
        for n in evidence_contexts
    ]

    return {
        'sample_id': sample_id,
        'title': title,
        'question': row['question'],
        'answer_prompt': answer_prompt,
        'prompt_sha256': hashlib.sha256(answer_prompt.encode()).hexdigest(),
        'system_prompt': SYSTEM_PROMPT,
        'messages_sha256': messages_sha256(SYSTEM_PROMPT, answer_prompt),
        'prediction': prediction,
        'gold': row['gold'],
        'score': p_hallucination,
        'threshold': None,
        'detector': DETECTOR,
        # Unlike the earlier training-example cases, these come from the recorded evaluation
        # run: the judge scored them once and nothing was ever fitted on them.
        'evaluation_scope': (
            'recorded evaluation example — the judge score comes from the '
            'archived run and was never fitted on this sample'
        ),
        'evidence_excerpts': evidence_excerpts,
        'provenance': {
            'dataset': 'longmemeval',
            'dataset_variant': 's',
            'source': 'pure_simplemem',
            'model': 'Qwen/Qwen3.5-35B-A3B',
            'base_url': ANSWER_BASE_URL,
            'run': '20260703_120500_qwen35_35b_a3b_s_full_combined_500',
            'trace': 'simplemem_trace.jsonl',
            'score_source': (
                'sirin_datasets/qwen35_4b/judge_span/sequence_judge.jsonl'
            ),
            'score_method': (
                'span-tag judge (Qwen/Qwen3.5-4B, num_beams=3, temperature=0.7)'
            ),
            'score_protocol': 'sequence p(hallucination) from span-tag judge votes',
            'fold': None,
            'probe_layer': None,
            'generation_temperature': 0.1,
            'response_format': 'JSON answer field',
            'category': row['category'],
        },
    }


def load_p_hallucination(seq_judge_path: Path) -> dict[str, float]:
    scores: dict[str, float] = {}
    for line in seq_judge_path.read_text(encoding='utf-8').splitlines():
        record = json.loads(line)
        scores[record['id']] = float(record['p_hallucination'])
    return scores


def preserved_case() -> dict[str, Any]:
    existing = json.loads(ASSET_PATH.read_text(encoding='utf-8'))['cases']
    for case in existing:
        if case['sample_id'] == PRESERVED_CASE_ID:
            return case
    raise ValueError(f'Existing asset is missing {PRESERVED_CASE_ID}')


def main() -> None:
    run_dir = resolve_run_dir()
    qwen = run_dir / 'sirin_datasets/qwen35_4b'
    frame = pd.read_parquet(qwen / 'dataset/trustmem_dataset.parquet').set_index(
        'sample_id'
    )
    p_hall = load_p_hallucination(qwen / 'judge_span/sequence_judge.jsonl')

    built = {PRESERVED_CASE_ID: preserved_case()}
    for sample_id, title, evidence in NEW_CASES:
        built[sample_id] = build_case(
            frame.loc[sample_id], sample_id, title, evidence, p_hall[sample_id]
        )

    cases = [built[sample_id] for sample_id in CASE_ORDER]
    payload = {'schema_version': 2, 'cases': cases}
    ASSET_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(f'Wrote {len(cases)} cases to {ASSET_PATH.relative_to(REPO_ROOT)}')


if __name__ == '__main__':
    main()
