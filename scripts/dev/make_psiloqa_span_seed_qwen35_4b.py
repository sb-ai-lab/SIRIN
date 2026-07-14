"""Build ``sirin/ui/assets/psiloqa_span_seed_qwen35_4b.json`` — the SECOND probe landing seed.

This is the recorded-result landing card for the ``Probing — Token Linear · PsiloQA/Qwen3.5-4B``
preset (the Qwen3.5-4B campaign checkpoint). It carries the D. H. Lawrence hero case (dataset
index 133, character IoU 0.953) together with the REAL recorded span-probe outputs from the
campaign experiment (``output/psiloqa_span_qwen35_4b/experiment/top5_demo_cases.json``). Every
per-token score, span, the threshold, layer, seed, and scaling are copied verbatim from the
recorded artifacts; nothing is invented. The representation model is Qwen3.5-4B (the extractor),
distinct from ``source_answer_model`` (the model that produced the stored answer).

Two honest sources (``--source``):

- ``experiment`` (default): the campaign experiment's recorded held-out span-probe outputs. This
  is a real recorded run through the real training/eval code — no GPU needed to package it, and it
  reproduces what a live replay would produce (modulo bf16 run-to-run variance). ``recorded_run`` is
  ``None`` (this is the experiment record, not a UI-driven recorded replay).

- ``live-export``: RESERVED for a UI-driven recorded replay (per-character scores through the app
  detect path, with a ``recorded_run`` block), mirroring the Qwen3-4B hero seed. It needs the
  Qwen3.5-4B probe model loaded on cuda:0 (~12GB) plus captured artifacts; deferred while cuda:0 is
  occupied by the shared vLLM server.

Regenerate (experiment source, no GPU) with::

    /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_psiloqa_span_seed_qwen35_4b.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / 'output/psiloqa_span_qwen35_4b/experiment'
CHECKPOINT_DIR = REPO / 'demo/checkpoints/qwen35_4b_psiloqa_span_linear'
DEMO_CASES = REPO / 'sirin/ui/assets/psiloqa_demo_cases.json'
OUT = REPO / 'sirin/ui/assets/psiloqa_span_seed_qwen35_4b.json'

PRESET_NAME = 'Probing — Token Linear · PsiloQA/Qwen3.5-4B'
# The Qwen3.5-4B campaign hero: D. H. Lawrence (dataset index 133, character IoU 0.953).
HERO_DATASET_INDEX = 133
REPRESENTATION_MODEL = 'Qwen/Qwen3.5-4B'
REPRESENTATION_DISCLOSURE = (
    'Qwen3.5-4B is used only as the live probe hidden-state extractor for the stored '
    'answer; it did not generate this answer.'
)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _load_checksums(path: Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in path.read_text().splitlines():
        digest, _, name = line.partition('  ')
        if digest and name:
            sums[name.strip()] = digest.strip()
    return sums


def _chip_by_index(dataset_index: int) -> dict[str, Any]:
    return next(
        case
        for case in json.loads(DEMO_CASES.read_text())['cases']
        if int(case['dataset_index']) == dataset_index
    )


def _detector_block(threshold: float) -> dict[str, Any]:
    manifest = json.loads((CHECKPOINT_DIR / 'manifest.json').read_text())
    provenance = json.loads((CHECKPOINT_DIR / 'provenance.json').read_text())
    if abs(float(manifest['threshold']) - threshold) > 1e-12:
        raise SystemExit('Recorded threshold does not match the checkpoint manifest')
    return {
        'preset': PRESET_NAME,
        'family': 'probing',
        'level': 'span',
        'score_semantics': 'thresholdedRawScore',
        'threshold': float(manifest['threshold']),
        'threshold_method': manifest['threshold_method'],
        'selected_layer': int(manifest['hidden_state_index']),
        'selected_seed': int(provenance['selected_seed']),
        'scaling': {
            'method': provenance['scaling']['method'],
            'mean': float(provenance['scaling']['mean']),
            'scale': float(provenance['scaling']['scale']),
        },
    }


def _base_case(chip: dict[str, Any]) -> dict[str, Any]:
    messages = [
        {'role': message['role'], 'content': message['content']}
        for message in chip['messages']
    ]
    answer = chip['answer']
    return {
        'sample_id': chip['case_id'],
        'example_id': chip['case_id'],
        'dataset': chip['dataset'],
        'split': chip['split'],
        'dataset_index': int(chip['dataset_index']),
        'title': chip['label'],
        'question': chip['question'],
        'passage': chip['passage'],
        'context': messages[0]['content'],
        'answer': answer,
        'messages': messages,
        'gold_spans': [[int(a), int(b)] for a, b in chip['gold_spans']],
        'gold_visibility': 'hidden',
        'source_answer_model': chip['source_answer_model'],
        # The probe extractor is Qwen3.5-4B for THIS card, overriding the demo chip's proxy model.
        'representation_model': REPRESENTATION_MODEL,
        'representation_disclosure': REPRESENTATION_DISCLOSURE,
        'selection_disclosure': chip['selection_disclosure'],
        'annotation_disclosure': chip['annotation_disclosure'],
        'why_notable': chip['why_notable'],
        'license': chip['license'],
        'checkpoint_sha256': _load_checksums(CHECKPOINT_DIR / 'SHA256SUMS'),
        'content_sha256': {
            'user': hashlib.sha256(messages[0]['content'].encode()).hexdigest(),
            'assistant': hashlib.sha256(answer.encode()).hexdigest(),
        },
        'messages_sha256': _sha(messages),
        'answer_sha256': hashlib.sha256(answer.encode()).hexdigest(),
    }


def build_from_experiment() -> dict[str, Any]:
    top5 = json.loads((EXPERIMENT / 'top5_demo_cases.json').read_text())
    provenance = json.loads((EXPERIMENT / 'provenance.json').read_text())
    record = next(
        item for item in top5['top5'] if item['dataset_index'] == HERO_DATASET_INDEX
    )
    chip = _chip_by_index(HERO_DATASET_INDEX)
    if record['answer'] != chip['answer'] or record['question'] != chip['question']:
        raise SystemExit('Experiment record does not match the verified case')

    case = _base_case(chip)
    case['model_revision'] = provenance['model_revision']
    case['detector'] = _detector_block(float(top5['threshold']))
    case['source_disclosure'] = (
        'Probe scores are the recorded held-out span-probe outputs from the SIRIN PsiloQA '
        'Qwen3.5-4B span campaign experiment run; detection did not run live.'
    )
    case['recorded_run'] = None
    case['probe'] = {
        'metric': 'character_span_probe_score',
        'normalization': 'per_character_sigmoid_in_unit_interval',
        'token_offsets': [[int(a), int(b)] for a, b in record['token_offsets']],
        'token_scores': [float(value) for value in record['token_scores']],
        'predicted_spans': [[int(a), int(b)] for a, b in record['predicted_spans']],
        'predicted_span_scores': [
            {
                'span': [int(entry['span'][0]), int(entry['span'][1])],
                'max_score': float(entry['max_score']),
                'mean_score': float(entry['mean_score']),
                'text': entry['text'],
            }
            for entry in record['predicted_span_scores']
        ],
        'iou': float(record['iou']),
        'predicted_coverage': float(record['predicted_coverage']),
        'predicted_runs': int(record['predicted_runs']),
        'false_positive_runs': int(record['false_positive_runs']),
    }
    case['experiment_source'] = (
        'output/psiloqa_span_qwen35_4b/experiment/top5_demo_cases.json'
    )
    return case


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=('experiment',), default='experiment')
    parser.parse_args()

    case = build_from_experiment()
    payload = {
        'schema_version': 1,
        'case': case,
        'integrity': {'algorithm': 'sha256', 'sha256': _sha(case)},
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(f'wrote {OUT} ({OUT.stat().st_size} bytes)')
    print(f"integrity sha256 = {payload['integrity']['sha256']}")
    probe = case['probe']
    print(
        f"tokens = {len(probe['token_scores'])}, "
        f"spans = {len(probe['predicted_span_scores'])}, iou = {probe['iou']:.3f}"
    )


if __name__ == '__main__':
    main()
