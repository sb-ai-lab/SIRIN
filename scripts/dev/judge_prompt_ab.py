"""A/B demo judge prompts on labeled pools via local vLLM Qwen3.5-4B.

Tunes on PsiloQA VALIDATION (test reserved for one-shot confirm) and LongMemEval
SimpleMem answerability_strict. Gold labels never enter any prompt.

Results 2026-07-14 (Qwen3.5-4B, thinking off, verdict_max_tokens=16):
  hallucination  tune(val n=87, 75 pos): H-current .931 | H-no-tail .937 | H-minimal .949 | H-no-system .912
                 CONFIRM(test n=116, 75 pos): H-current .847 | H-minimal .806  -> tuning "win" did not replicate
  answerability  tune(n=120 bal): A-current .624 | A-task-system .641 | A-minimal .727
                 CONFIRM(held-out n=84, 24 pos): A-current .760 | A-minimal .743 -> did not replicate
Verdict: KEEP the current prompts — simplified variants tie or regress on held-out
slices; dropping the system prompt clearly hurts (.912). Rerun `confirm` against
nemotron:free (swap VLLM config for OpenRouter) before ever changing the Space prompts.

Usage: python scripts/dev/judge_prompt_ab.py {halluc|ans|both|confirm}
"""

import json
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, '/home/jovyan/parchiev/magistr/repos/SIRIN')

from sirin.detection.judging import SequenceOpenAIJudge
from sirin.detection.judging.judges.base import JudgeAnnotationError
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig
from sirin.models.inference import OpenAIConfig

VLLM = dict(
    model_path='Qwen/Qwen3.5-4B',
    base_url='http://localhost:8000/v1',
    api_key='EMPTY',
    extra_body={'chat_template_kwargs': {'enable_thinking': False}},
)
DEFAULT_SYSTEM = None  # sentinel: keep JudgeBaseConfig default

CURRENT_JUDGE_PROMPT = (
    "You verify whether the assistant response is faithful to the provided context. "
    "Reply with 1 if it contains hallucinated, unsupported, or contradicted claims, "
    "otherwise reply with 0.\n"
    'Dialogue: "{sample}"\n'
    "Answer with a SINGLE character that is the digit 1 or the digit 0. Do not output JSON, "
    "quotes, spaces, reasoning, or any other character. Your entire reply must be exactly one "
    "digit: "
)
CURRENT_ANSWERABILITY_PROMPT = (
    "You are given a context passage and a question, with no answer. Decide whether the "
    "context contains enough information to answer the question.\n"
    'Dialogue: "{sample}"\n'
    "Reply with 1 if the context is NOT sufficient to answer the question, or 0 if it IS "
    "sufficient. Answer with a SINGLE character that is the digit 1 or the digit 0. Do not "
    "output JSON, quotes, spaces, reasoning, or any other character. Your entire reply must "
    "be exactly one digit: "
)

HALLUC_VARIANTS = {
    'H-current': dict(system=DEFAULT_SYSTEM, user=CURRENT_JUDGE_PROMPT),
    'H-no-tail': dict(
        system=DEFAULT_SYSTEM,
        user=(
            "You verify whether the assistant response is faithful to the provided context. "
            "Reply with 1 if it contains hallucinated, unsupported, or contradicted claims, "
            "otherwise reply with 0.\n"
            'Dialogue: "{sample}"\n'
            "Digit: "
        ),
    ),
    'H-minimal': dict(
        system='You are a strict hallucination detector. Answer with a single digit.',
        user=(
            'Dialogue: "{sample}"\n'
            'Reply 1 if the answer contains claims unsupported by or contradicting the '
            'context, else 0. One digit only: '
        ),
    ),
    'H-no-system': dict(system='', user=CURRENT_JUDGE_PROMPT),
}

ANSWERABILITY_VARIANTS = {
    'A-current': dict(system=DEFAULT_SYSTEM, user=CURRENT_ANSWERABILITY_PROMPT),
    'A-task-system': dict(
        system=(
            'You judge whether a context contains enough information to answer a '
            'question. Answer with a single digit.'
        ),
        user=CURRENT_ANSWERABILITY_PROMPT,
    ),
    'A-minimal': dict(
        system=(
            'You judge whether a context contains enough information to answer a '
            'question. Answer with a single digit.'
        ),
        user=(
            'Context and question:\n"{sample}"\n'
            'Reply 1 if the context is NOT sufficient to answer the question, 0 if it is. '
            'One digit only: '
        ),
    ),
}


def load_psiloqa_validation(n=150, seed=42, split='validation'):
    from datasets import load_from_disk
    sys.path.insert(0, '/home/jovyan/parchiev/magistr/repos/SIRIN')
    from demo.train_psiloqa_span_linear import prompt_disjoint_indices

    ds = load_from_disk('/home/jovyan/ybelikova/sirin-final/data/datasets/psiloqa_en_span')
    _, val_idx, test_idx = prompt_disjoint_indices(ds)
    base, indices = (ds['train'], val_idx) if split == 'validation' else (ds['test'], test_idx)
    rows = []
    for i in indices:
        row = base[int(i)]
        rows.append({'input': row['input'], 'label': int(bool(len(row['target'])))})
    rng = np.random.RandomState(seed)
    pos = [r for r in rows if r['label'] == 1]
    neg = [r for r in rows if r['label'] == 0]
    take = n // 2
    picked = (
        [pos[i] for i in rng.choice(len(pos), min(take, len(pos)), replace=False)]
        + [neg[i] for i in rng.choice(len(neg), min(take, len(neg)), replace=False)]
    )
    rng.shuffle(picked)
    return picked


def _tuning_answerability_ids(df, n=120, seed=42):
    """Reproduce the exact tuning draw (sequential rng across pos then neg)."""
    rng = np.random.RandomState(seed)
    pos = df[df.ans_strict == 1]
    neg = df[df.ans_strict == 0]
    take = n // 2
    old_pos = pos.sample(min(take, len(pos)), random_state=rng)
    old_neg = neg.sample(min(take, len(neg)), random_state=rng)
    return set(old_pos.sample_id) | set(old_neg.sample_id)


def load_answerability(n=120, seed=42, exclude_first=0):
    D = ('/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
         'pure_simplemem_qwen35_35b_a3b/20260703_120500_qwen35_35b_a3b_s_full_combined_500/'
         'sirin_datasets/qwen35_4b')
    df = pd.read_parquet(D + '/dataset/trustmem_dataset.parquet')
    df['ans_strict'] = df['labels'].map(lambda s: json.loads(s).get('answerability_strict'))
    df = df.dropna(subset=['ans_strict'])
    if exclude_first:
        used = _tuning_answerability_ids(df)
        df = df[~df.sample_id.isin(used)]
        seed = 7  # fresh draw over the untouched remainder
    rng = np.random.RandomState(seed)
    pos = df[df.ans_strict == 1]
    neg = df[df.ans_strict == 0]
    take = n // 2
    picked = pd.concat([
        pos.sample(min(take, len(pos)), random_state=rng),
        neg.sample(min(take, len(neg)), random_state=rng),
    ]).sample(frac=1, random_state=rng)
    rows = []
    for _, r in picked.iterrows():
        user = f"{r.context_text}\n\nQuestion: {r.question}"
        rows.append({
            'input': [{'role': 'user', 'content': user},
                      {'role': 'assistant', 'content': ''}],
            'label': int(r.ans_strict),
        })
    return rows


def make_judge(system, user, dialogue_format=None):
    cfg_kwargs = dict(user_prompt=user, temperature=0.0, verdict_max_tokens=16)
    if system is not DEFAULT_SYSTEM:
        cfg_kwargs['system_prompt'] = system
    if dialogue_format is not None:
        cfg_kwargs['dialogue_format'] = dialogue_format
    adapter = OpenAIModelAdapter(OpenAIConfig(**VLLM))
    adapter.load()
    return SequenceOpenAIJudge(OpenAIJudgeConfig(**cfg_kwargs), adapter)


def run_variant(name, spec, rows, dialogue_format=None):
    judge = make_judge(spec['system'], spec['user'], dialogue_format)
    inputs = [r['input'] for r in rows]
    labels = np.array([r['label'] for r in rows])
    t0 = time.time()
    probs, preds, failed = [], [], 0
    # batches keep one bad sample from killing the whole run
    B = 25
    for i in range(0, len(inputs), B):
        chunk = inputs[i:i + B]
        try:
            p, d, _ = judge.detect(chunk)
            probs.extend(list(p)); preds.extend(list(d))
        except JudgeAnnotationError:
            for sample in chunk:  # isolate the failures
                try:
                    p, d, _ = judge.detect([sample])
                    probs.extend(list(p)); preds.extend(list(d))
                except JudgeAnnotationError:
                    probs.append(np.nan); preds.append(-1); failed += 1
    dt = time.time() - t0
    probs = np.array(probs, dtype=float); preds = np.array(preds)
    ok = np.isfinite(probs) & (preds >= 0)
    auc = roc_auc_score(labels[ok], probs[ok]) if ok.sum() > 2 and len(set(labels[ok])) > 1 else float('nan')
    acc = float((preds[ok] == labels[ok]).mean()) if ok.any() else float('nan')
    # prompt size: system + formatted user for a mid-size sample (chars, cost proxy)
    sys_p = judge.config.system_prompt
    mid = sorted(inputs, key=lambda s: len(str(s)))[len(inputs) // 2]
    from sirin.detection.judging.judges.utils import build_prompt_messages
    msgs = build_prompt_messages(judge.config, [mid])[0]
    overhead = len(sys_p) + len(msgs[1]['content']) - len(str(mid[0]['content'])) - len(str(mid[1]['content']))
    print(f"{name:16s} auc={auc:.3f} acc@0.5={acc:.3f} failed={failed:3d} "
          f"prompt_overhead={overhead:5d}ch wall={dt:6.1f}s n={len(rows)}")
    return dict(name=name, auc=float(auc), acc=float(acc), failed=failed,
                overhead=overhead, wall=dt)


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'both'
    results = []
    if which in ('halluc', 'both'):
        rows = load_psiloqa_validation()
        print(f"\n=== hallucination (PsiloQA validation, n={len(rows)}, "
              f"pos={sum(r['label'] for r in rows)}) ===")
        for name, spec in HALLUC_VARIANTS.items():
            results.append(run_variant(name, spec, rows))
    if which in ('ans', 'both'):
        rows = load_answerability()
        print(f"\n=== answerability (LongMemEval strict, n={len(rows)}, "
              f"pos={sum(r['label'] for r in rows)}) ===")
        for name, spec in ANSWERABILITY_VARIANTS.items():
            results.append(run_variant(name, spec, rows, dialogue_format='{question}'))
    if which == 'confirm':
        rows = load_psiloqa_validation(split='test')
        print(f"\n=== CONFIRM hallucination (PsiloQA TEST, n={len(rows)}, "
              f"pos={sum(r['label'] for r in rows)}) ===")
        for name in ('H-current', 'H-minimal'):
            results.append(run_variant(name, HALLUC_VARIANTS[name], rows))
        rows = load_answerability(exclude_first=60)
        print(f"\n=== CONFIRM answerability (LongMemEval held-out, n={len(rows)}, "
              f"pos={sum(r['label'] for r in rows)}) ===")
        for name in ('A-current', 'A-minimal'):
            results.append(
                run_variant(name, ANSWERABILITY_VARIANTS[name], rows,
                            dialogue_format='{question}')
            )
    out = '/tmp/claude-1000/-home-jovyan-parchiev-magistr-repos-SIRIN/fccf2893-2af0-43bb-be28-e7fcba15f2f6/scratchpad/prompt_tune_results.json'
    with open(out, 'a') as f:
        f.write(json.dumps({'run': which, 'ts': time.time(), 'results': results}) + '\n')
