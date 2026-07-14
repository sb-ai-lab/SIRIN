"""A/B the span-tag prompts on PsiloQA validation rows (n=3 consensus, local vLLM).

Results 2026-07-14 (n=25, 19 with spans): S-current iou .538, valid 59/75, 1 failed
| S-compact iou .478, valid 29/75, 6 failed. The current prompt's explicit rules list
is LOAD-BEARING for verbatim-echo discipline — the compact variant halves validity.
Verdict: keep S-current.
"""

import json
import sys
import time

import numpy as np

sys.path.insert(0, '/home/jovyan/parchiev/magistr/repos/SIRIN')

from sirin.detection.judging import TokenOpenAIJudge
from sirin.detection.judging.judges.base import JudgeAnnotationError
from sirin.detection.judging.judges.utils.prompts import (
    SPAN_TAG_SYSTEM_PROMPT,
    SPAN_TAG_USER_PROMPT,
)
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig
from sirin.models.inference import OpenAIConfig

VLLM = dict(
    model_path='Qwen/Qwen3.5-4B',
    base_url='http://localhost:8000/v1',
    api_key='EMPTY',
    extra_body={'chat_template_kwargs': {'enable_thinking': False}},
)

SPAN_VARIANTS = {
    'S-current': dict(system=SPAN_TAG_SYSTEM_PROMPT, user=SPAN_TAG_USER_PROMPT),
    'S-compact': dict(
        system=(
            'You annotate hallucinations. Reproduce the assistant\'s answer EXACTLY, '
            'character for character, inserting [SPAN] and [/SPAN] around every part not '
            'supported by, or contradicted by, the context. The markers are the only '
            'characters you may add; never correct or paraphrase. If nothing is '
            'hallucinated, return the answer unchanged. Output only the annotated answer.'
        ),
        user=(
            'Dialogue:\n{sample}\n\nAnnotated answer:'
        ),
    ),
}


def load_rows(n=25, seed=42):
    from datasets import load_from_disk
    from demo.train_psiloqa_span_linear import prompt_disjoint_indices

    ds = load_from_disk('/home/jovyan/ybelikova/sirin-final/data/datasets/psiloqa_en_span')
    _, val_idx, _ = prompt_disjoint_indices(ds)
    base = ds['train']
    rows = []
    for i in val_idx:
        row = base[int(i)]
        answer = row['input'][-1]['content']
        if len(answer) > 600:  # keep the run cheap; demo answers are short anyway
            continue
        rows.append({'input': row['input'], 'answer': answer,
                     'spans': [list(s) for s in row['target']]})
    rng = np.random.RandomState(seed)
    with_span = [r for r in rows if r['spans']]
    without = [r for r in rows if not r['spans']]
    take_pos = min(n - n // 4, len(with_span))
    take_neg = min(n // 4, len(without))
    picked = (
        [with_span[i] for i in rng.choice(len(with_span), take_pos, replace=False)]
        + [without[i] for i in rng.choice(len(without), take_neg, replace=False)]
    )
    rng.shuffle(picked)
    return picked


def char_iou(pred_binary, spans, length):
    gold = np.zeros(length, dtype=bool)
    for start, end in spans:
        gold[int(start):int(end)] = True
    pred = np.asarray(pred_binary, dtype=bool)[:length]
    union = (gold | pred).sum()
    if union == 0:
        return 1.0  # both empty: perfect agreement
    return float((gold & pred).sum() / union)


def run_variant(name, spec, rows, n_beams=3):
    adapter = OpenAIModelAdapter(OpenAIConfig(**VLLM))
    adapter.load()
    judge = TokenOpenAIJudge(
        OpenAIJudgeConfig(
            system_prompt=spec['system'],
            user_prompt=spec['user'],
            temperature=0.7,
            num_beams=n_beams,
        ),
        adapter,
    )
    t0 = time.time()
    ious, valid_total, requested_total, failed = [], 0, 0, 0
    for row in rows:
        try:
            probs, _, _ = judge.detect([row['input']])
            consensus = judge.last_consensus[0]
            valid_total += consensus['valid']
            requested_total += consensus['requested']
            scores = np.asarray(probs[0], dtype=float)
            ious.append(char_iou(scores >= 2 / 3, row['spans'], len(row['answer'])))
        except JudgeAnnotationError:
            failed += 1
            requested_total += n_beams
    dt = time.time() - t0
    overhead = len(spec['system']) + len(spec['user'])
    print(f"{name:12s} mean_iou={np.mean(ious):.3f} n_scored={len(ious)} failed={failed} "
          f"valid={valid_total}/{requested_total} prompt_overhead={overhead:4d}ch wall={dt:6.1f}s")
    return dict(name=name, mean_iou=float(np.mean(ious)), n_scored=len(ious),
                failed=failed, valid=valid_total, requested=requested_total,
                overhead=overhead, wall=dt)


if __name__ == '__main__':
    rows = load_rows()
    print(f"=== span (PsiloQA validation, n={len(rows)}, "
          f"with_spans={sum(bool(r['spans']) for r in rows)}) ===")
    results = [run_variant(name, spec, rows) for name, spec in SPAN_VARIANTS.items()]
    out = ('/tmp/claude-1000/-home-jovyan-parchiev-magistr-repos-SIRIN/'
           'fccf2893-2af0-43bb-be28-e7fcba15f2f6/scratchpad/prompt_tune_results.json')
    with open(out, 'a') as f:
        f.write(json.dumps({'run': 'span', 'ts': time.time(), 'results': results}) + '\n')
