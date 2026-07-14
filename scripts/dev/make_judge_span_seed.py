"""Build ``sirin/ui/assets/judge_span_seed.json`` from a recorded token-judge run.

The seed asset carries ONE PsiloQA held-out case together with the REAL per-character
span-agreement scores the token API judge recorded during campaign stage P4. It is the
source of the token-judge "Recorded result" landing card (beside the probe seed). Every
char score, span, and the generations hash are copied verbatim from the recorded jsonl;
nothing is invented and the judge never saw the gold spans.

Chosen case: the Hartmuth Pfeil date case (``psiloqa_togethercomputer/…_13194``). The
answer invents two dates; the judge tagged exactly those two fragments and its two spans
coincide exactly with the (hidden) gold annotation — a clean, disclosed narrative.

Source: ``output/psiloqa_span_qwen35_4b/judge/token_judge_test.jsonl`` (campaign P4) and the
PsiloQA test split for the verified answer/gold. Run from the repo root with an env that has
``datasets`` and the local ``sirin`` (e.g. the ``sirin`` conda env)::

    /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_judge_span_seed.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from datasets import load_from_disk

# Run as a script puts scripts/dev/ on sys.path[0], shadowing the repo-root ``sirin``; prepend the
# repo root so the LOCAL sirin (with sirin.ui) wins over any editable install elsewhere.
_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sirin.ui.demo_cases import (
    _canonical_sha256,
    build_psiloqa_prompt,
    judge_seed_predicted_spans,
    load_judge_span_seed,
)

REPO = Path(__file__).resolve().parents[2]
JUDGE_JSONL = REPO / 'output/psiloqa_span_qwen35_4b/judge/token_judge_test.jsonl'
DATASET_PATH = '/home/jovyan/ybelikova/sirin-final/data/datasets/psiloqa_en_span'
OUT = REPO / 'sirin/ui/assets/judge_span_seed.json'

CASE_ID = 'psiloqa_togethercomputer/Pythia-Chat-Base-7B-v0.16_13194'
SPLIT = 'test'
PROMPT_PREFIX = 'Answer the question based on the passage.\nPassage: '

PRESET = 'Judge — API Span (zero-shot)'
JUDGE_MODEL = 'Qwen/Qwen3.5-4B'
PROVIDER_LABEL = 'Custom OpenAI-compatible (local vLLM)'
TEMPERATURE = 0.7
LICENSE = 'CC-BY-4.0'


def _source_answer_model(case_id: str) -> str:
    model, _, tail = case_id.removeprefix('psiloqa_').rpartition('_')
    if not model or not tail.isdigit():
        raise SystemExit(f'Unexpected PsiloQA case id: {case_id}')
    return model


def _split_passage(user_content: str, question: str) -> str:
    suffix = f'\nQuestion: {question}\n'
    if not user_content.startswith(PROMPT_PREFIX) or not user_content.endswith(suffix):
        raise SystemExit('User prompt does not follow the PsiloQA template')
    return user_content[len(PROMPT_PREFIX):len(user_content) - len(suffix)]


def _char_iou(spans: list[list[int]], gold: list[list[int]]) -> float:
    pred = {i for a, b in spans for i in range(a, b)}
    gold_chars = {i for a, b in gold for i in range(a, b)}
    union = pred | gold_chars
    return len(pred & gold_chars) / len(union) if union else 0.0


def main() -> None:
    record = next(
        (
            json.loads(line)
            for line in JUDGE_JSONL.read_text().splitlines()
            if line.strip() and json.loads(line)['id'] == CASE_ID
        ),
        None,
    )
    if record is None:
        raise SystemExit(f'{CASE_ID} not found in {JUDGE_JSONL}')
    if record['status'] != 'ok' or record['valid'] < 2:
        raise SystemExit('Recorded judge run is not a valid multi-sample consensus')

    split = load_from_disk(DATASET_PATH)[SPLIT]
    row = next(row for row in split if row['id'] == CASE_ID)
    user = row['input'][0]['content']
    answer = row['input'][1]['content']
    question = row['question']
    passage = _split_passage(user, question)
    if build_psiloqa_prompt(passage, question) != user:
        raise SystemExit('Passage/question do not rebuild the user prompt')

    char_scores = [float(score) for score in record['char_scores']]
    if len(char_scores) != len(answer):
        raise SystemExit('Recorded char scores are not aligned to the answer')
    predicted_spans = judge_seed_predicted_spans(char_scores)
    gold_spans = [[int(a), int(b)] for a, b in row['target']]
    if not gold_spans:
        raise SystemExit('Case has no gold spans')
    iou = _char_iou(predicted_spans, gold_spans)

    messages = [
        {'role': 'user', 'content': user},
        {'role': 'assistant', 'content': answer},
    ]
    why_notable = (
        'Two fabricated dates: the answer gives "March 1, 1883" and "March 1, 1963", '
        'but the passage states 13 February 1893 - 4 June 1962. The token API judge '
        f'tagged both invented dates ({record["valid"]}/{record["requested"]} samples '
        'agreed on each), and its two spans coincide exactly with the hidden gold '
        f'annotation (character IoU {iou:.2f}).'
    )
    case = {
        'sample_id': CASE_ID,
        'example_id': CASE_ID,
        'dataset': 'psiloqa_en_span',
        'split': SPLIT,
        'question': question,
        'passage': passage,
        'context': user,
        'answer': answer,
        'messages': messages,
        'content_sha256': {
            'user': hashlib.sha256(user.encode()).hexdigest(),
            'assistant': hashlib.sha256(answer.encode()).hexdigest(),
        },
        'messages_sha256': _canonical_sha256(messages),
        'answer_sha256': hashlib.sha256(answer.encode()).hexdigest(),
        'gold_spans': gold_spans,
        'gold_visibility': 'hidden',
        'source_answer_model': _source_answer_model(CASE_ID),
        'why_notable': why_notable,
        'license': LICENSE,
        'detector': {
            'preset': PRESET,
            'family': 'judge',
            'level': 'token',
            'score_semantics': 'spanAgreement',
            'judge_model': JUDGE_MODEL,
            'provider_label': PROVIDER_LABEL,
            'temperature': TEMPERATURE,
            'requested': int(record['requested']),
            'valid': int(record['valid']),
        },
        'judge': {
            'char_scores': char_scores,
            'predicted_spans': predicted_spans,
            'generations_sha256': record['generations_sha256'],
        },
        'experiment_source': (
            'output/psiloqa_span_qwen35_4b/judge/token_judge_test.jsonl'
        ),
    }
    payload = {
        'schema_version': 1,
        'case': case,
        'integrity': {'algorithm': 'sha256', 'sha256': _canonical_sha256(case)},
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    # Round-trip through the loader: any misalignment/hash error raises here.
    load_judge_span_seed(OUT)
    print(f'wrote {OUT} ({OUT.stat().st_size} bytes)')
    print(f"integrity sha256 = {payload['integrity']['sha256']}")
    print(f'spans = {predicted_spans}  gold = {gold_spans}  iou = {iou:.3f}')


if __name__ == '__main__':
    main()
