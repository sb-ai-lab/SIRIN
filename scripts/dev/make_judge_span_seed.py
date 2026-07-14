"""Build ``sirin/ui/assets/judge_span_seed.json`` from a recorded token-judge run.

The seed asset carries ONE PsiloQA held-out case together with the REAL per-character
span-agreement scores from a token API judge run. It is the source of the token-judge
"Recorded result" landing card (beside the probe seed). Every char score, span, and the
generations hash come from an actual judge run; nothing is invented and the judge never
saw the gold spans.

Chosen case: the Hartmuth Pfeil date case (``psiloqa_togethercomputer/…_13194``). The
answer invents two dates; the judge tagged exactly those two fragments and its two spans
coincide exactly with the (hidden) gold annotation — a clean, disclosed narrative.

Two sources, same asset schema:

* default (no ``--api-provider``): replay the recorded campaign jsonl
  ``output/psiloqa_span_qwen35_4b/judge/token_judge_test.jsonl`` (campaign P4) — the original
  invocation, unchanged::

      /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_judge_span_seed.py

* ``--api-provider OpenRouter``: run the judge LIVE, built exactly the UI way
  (``sirin.ui.presets._build_openai_token_judge``; the key comes from env
  ``OPENROUTER_API_KEY`` via ``resolve_api_provider``), and record the real run::

      /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_judge_span_seed.py \
          --api-provider OpenRouter --provider-label OpenRouter \
          --judge-model nvidia/nemotron-3-super-120b-a12b:free --num-beams 3

Either way the PsiloQA test split supplies the verified answer/gold, every char score comes from
a real judge run (never invented), and any failure aborts before the asset is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--judge-model', default=JUDGE_MODEL)
    parser.add_argument(
        '--provider-label',
        default=PROVIDER_LABEL,
        help='Disclosure label for the seed card (a provider name, NEVER a base URL)',
    )
    parser.add_argument(
        '--api-provider',
        default='',
        help="Run the judge live via this UI provider (e.g. 'OpenRouter'); "
        'empty (default) replays the recorded campaign jsonl',
    )
    parser.add_argument('--temperature', type=float, default=TEMPERATURE)
    parser.add_argument('--num-beams', type=int, default=3)
    return parser.parse_args()


def _replayed_record() -> dict[str, Any]:
    """The recorded campaign-P4 consensus for CASE_ID, verbatim from the jsonl."""
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
    return {
        'char_scores': [float(score) for score in record['char_scores']],
        'requested': int(record['requested']),
        'valid': int(record['valid']),
        'generations_sha256': record['generations_sha256'],
        'experiment_source': 'output/psiloqa_span_qwen35_4b/judge/token_judge_test.jsonl',
    }


def _live_record(messages: list[dict[str, str]], args: argparse.Namespace) -> dict[str, Any]:
    """One real judge run over ``messages``, built exactly the UI way. Fails loudly.

    A zero-valid-votes run (JudgeAnnotationError) is retried ONCE; any other failure — or a
    second zero-valid run — propagates and the asset is never written.
    """
    from sirin.detection.judging.judges.base import JudgeAnnotationError
    from sirin.ui.presets import _build_openai_token_judge

    judge = _build_openai_token_judge(
        judge_model=args.judge_model, api_provider=args.api_provider
    )
    judge.config.temperature = args.temperature
    judge.config.num_beams = args.num_beams
    for attempt in (1, 2):
        try:
            char_probs, _, _ = judge.detect([messages])
            break
        except JudgeAnnotationError:
            if attempt == 2:
                raise
            print('Live run had zero valid votes; retrying once…', file=sys.stderr)
    consensus = judge.last_consensus[0]
    return {
        'char_scores': [float(score) for score in char_probs[0]],
        'requested': int(consensus['requested']),
        'valid': int(consensus['valid']),
        'generations_sha256': _canonical_sha256(judge.last_generations),
        'experiment_source': (
            f'live {args.api_provider} token-judge run '
            f'(scripts/dev/make_judge_span_seed.py, {date.today().isoformat()})'
        ),
    }


def main() -> None:
    args = _parse_args()
    split = load_from_disk(DATASET_PATH)[SPLIT]
    row = next(row for row in split if row['id'] == CASE_ID)
    user = row['input'][0]['content']
    answer = row['input'][1]['content']
    question = row['question']
    passage = _split_passage(user, question)
    if build_psiloqa_prompt(passage, question) != user:
        raise SystemExit('Passage/question do not rebuild the user prompt')

    messages = [
        {'role': 'user', 'content': user},
        {'role': 'assistant', 'content': answer},
    ]
    record = _live_record(messages, args) if args.api_provider else _replayed_record()

    char_scores = record['char_scores']
    if len(char_scores) != len(answer):
        raise SystemExit('Recorded char scores are not aligned to the answer')
    predicted_spans = judge_seed_predicted_spans(char_scores)
    gold_spans = [[int(a), int(b)] for a, b in row['target']]
    if not gold_spans:
        raise SystemExit('Case has no gold spans')
    iou = _char_iou(predicted_spans, gold_spans)

    judge_sentence = (
        f'The token API judge tagged both invented dates ({record["valid"]}/'
        f'{record["requested"]} samples agreed on each), and its two spans coincide '
        f'exactly with the hidden gold annotation (character IoU {iou:.2f}).'
        if predicted_spans == gold_spans
        else f'The token API judge ({record["valid"]}/{record["requested"]} valid '
        f'samples) tagged spans {predicted_spans}; character IoU {iou:.2f} against '
        'the hidden gold annotation.'
    )
    why_notable = (
        'Two fabricated dates: the answer gives "March 1, 1883" and "March 1, 1963", '
        'but the passage states 13 February 1893 - 4 June 1962. ' + judge_sentence
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
            'judge_model': args.judge_model,
            'provider_label': args.provider_label,
            'temperature': args.temperature,
            'requested': record['requested'],
            'valid': record['valid'],
        },
        'judge': {
            'char_scores': char_scores,
            'predicted_spans': predicted_spans,
            'generations_sha256': record['generations_sha256'],
        },
        'experiment_source': record['experiment_source'],
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
    print(f"valid/requested = {record['valid']}/{record['requested']}")
    print(f'spans = {predicted_spans}  gold = {gold_spans}  iou = {iou:.3f}')


if __name__ == '__main__':
    main()
