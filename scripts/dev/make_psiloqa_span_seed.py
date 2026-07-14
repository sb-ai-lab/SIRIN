"""Build ``sirin/ui/assets/psiloqa_span_seed.json`` from recorded probe outputs.

The seed asset carries one PsiloQA held-out case together with REAL span-probe
outputs. It is the source of the first-run "Recorded result" landing card. All probe
scores, the decision threshold, the selected layer, and the checkpoint hashes are
copied verbatim from recorded artifacts; nothing is invented.

Sources (``--source``):

- ``live-export`` (default): the census case, recorded on 2026-07-14. Two artifacts
  under ``output/sirin_a_star_demo/psiloqa_span/live_replay_2026-07-14/``:

  * ``census_char_scores.json`` — the full per-character probe trace, captured by
    calling the product's own detect path (``build_preset_detector`` +
    ``detection_view_model``, the same functions the app's detect() closure calls).
    This is the trace the asset stores; the portable export format does not carry
    per-character scores.
  * ``census_live_export.json`` — the portable export of the recorded-replay run
    driven through the app UI (Census number chip -> Replay recorded answer ->
    Export run). It corroborates the capture: same case, same τ, same span shape,
    scores within bf16 run-to-run variance (documented in the disclosure).

- ``experiment``: the Llanbadoc case from the A* demo experiment artifacts
  (``top5_demo_cases.json``); kept for reference, predates the recorded_run field.

Regenerate with::

    /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_psiloqa_span_seed.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
EXPERIMENT = REPO / 'output/sirin_a_star_demo/psiloqa_span/experiment'
LIVE_DIR = REPO / 'output/sirin_a_star_demo/psiloqa_span/live_replay_2026-07-14'
CHECKPOINT_DIR = REPO / 'demo/checkpoints/qwen3_4b_psiloqa_span_linear'
DEMO_CASES = REPO / 'sirin/ui/assets/psiloqa_demo_cases.json'
OUT = REPO / 'sirin/ui/assets/psiloqa_span_seed.json'

PRESET_NAME = 'Probing — Token Linear · PsiloQA/Qwen3-4B'
CENSUS_CASE_ID = 'psiloqa_NousResearch/Nous-Hermes-2-Mistral-7B-DPO_22242'
LLANBADOC_CASE_ID = 'psiloqa_NousResearch/Nous-Hermes-2-Mistral-7B-DPO_22244'
CORROBORATION_SCORE_TOLERANCE = 0.1


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


def _chip_case(case_id: str) -> dict[str, Any]:
    return next(
        case
        for case in json.loads(DEMO_CASES.read_text())['cases']
        if case['case_id'] == case_id
    )


def _merge_runs(
    offsets: list[list[int]], scores: list[float], threshold: float
) -> list[dict[str, Any]]:
    """Demo merge rule: contiguous >= τ runs; span score = run max, plus run mean."""
    spans: list[dict[str, Any]] = []
    run: list[float] = []
    run_start = run_end = 0
    for (start, end), score in zip(offsets, scores):
        if score >= threshold:
            if not run:
                run_start = start
            run_end = end
            run.append(score)
        elif run:
            spans.append({
                'span': [run_start, run_end],
                'max_score': max(run),
                'mean_score': sum(run) / len(run),
            })
            run = []
    if run:
        spans.append({
            'span': [run_start, run_end],
            'max_score': max(run),
            'mean_score': sum(run) / len(run),
        })
    return spans


def _gold_metrics(
    spans: list[dict[str, Any]], gold: list[list[int]], answer_length: int
) -> dict[str, Any]:
    predicted = {
        index
        for entry in spans
        for index in range(entry['span'][0], entry['span'][1])
    }
    gold_chars = {index for start, end in gold for index in range(start, end)}
    union = predicted | gold_chars
    return {
        'iou': len(predicted & gold_chars) / len(union) if union else 0.0,
        'predicted_coverage': len(predicted) / answer_length,
        'predicted_runs': len(spans),
        'false_positive_runs': sum(
            1
            for entry in spans
            if not gold_chars & set(range(entry['span'][0], entry['span'][1]))
        ),
    }


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
        'representation_model': chip['representation_model'],
        'representation_disclosure': chip['representation_disclosure'],
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


def _check_export_corroborates(
    spans: list[dict[str, Any]], run: dict[str, Any]
) -> None:
    """The UI-exported run must corroborate the captured trace within bf16 variance.

    Span-probe scores drift slightly between independent live runs (non-deterministic
    bf16 GPU kernels), so exact equality across the two recordings is not required —
    but every suspect segment the app showed must overlap a derived span with a close
    score, or the two artifacts do not describe the same detection behavior.
    """
    exported = [
        segment
        for segment in run['analysis']['segments']
        if segment.get('verdict') is True
    ]
    if not exported:
        raise SystemExit('Exported run has no suspect segments to corroborate')
    for segment in exported:
        start, end = segment['startCodePoint'], segment['endCodePoint']
        match = next(
            (
                entry
                for entry in spans
                if entry['span'][0] < end and start < entry['span'][1]
            ),
            None,
        )
        if match is None:
            raise SystemExit(
                f'Exported segment [{start},{end}] has no overlapping derived span'
            )
        if abs(match['max_score'] - float(segment['score'])) > CORROBORATION_SCORE_TOLERANCE:
            raise SystemExit(
                f'Exported segment [{start},{end}] score {segment["score"]:.3f} '
                f'diverges from the captured trace beyond tolerance'
            )


def build_from_live_export() -> dict[str, Any]:
    document = json.loads((LIVE_DIR / 'census_live_export.json').read_text())
    capture = json.loads((LIVE_DIR / 'census_char_scores.json').read_text())
    run = document['run']
    chip = _chip_case(CENSUS_CASE_ID)
    answer = chip['answer']

    if capture['case_id'] != CENSUS_CASE_ID or run['inputs'].get('exampleId') != CENSUS_CASE_ID:
        raise SystemExit('Artifacts do not belong to the census case')
    if run['answer'] != answer or capture['answer'] != answer:
        raise SystemExit('Export/capture answer does not match the verified case')
    if run['origin'] != 'recordedAnswerLiveDetection' or run['status'] != 'succeeded':
        raise SystemExit('Export is not a successful live recorded replay')
    if not capture['preds_equal_score_ge_threshold']:
        raise SystemExit('Capture predictions are not the >= threshold rule')

    threshold = float(run['analysis']['threshold'])
    if abs(float(capture['threshold']) - threshold) > 1e-12:
        raise SystemExit('Capture threshold does not match the exported run')
    scores = [float(score) for score in capture['scores']]
    if len(scores) != len(answer):
        raise SystemExit('Capture scores are not character-aligned to the answer')
    offsets = [[index, index + 1] for index in range(len(answer))]

    spans = _merge_runs(offsets, scores, threshold)
    _check_export_corroborates(spans, run)
    for entry in spans:
        entry['text'] = answer[entry['span'][0]:entry['span'][1]]

    case = _base_case(chip)
    case['model_revision'] = json.loads(
        (CHECKPOINT_DIR / 'manifest.json').read_text()
    )['model_revision']
    case['detector'] = _detector_block(threshold)
    case['source_disclosure'] = (
        'Probe scores were recorded once on 2026-07-14 by running the live span '
        'probe over this verified held-out answer through the product detect path; '
        'a recorded-replay run driven through the app UI the same day (exported '
        f"run {run['id']}) corroborates them within bf16 run-to-run variance. "
        'On this landing card they are recorded results — detection is not '
        'running now.'
    )
    case['recorded_run'] = {
        'run_id': run['id'],
        'exported_sha256': document['integrity']['sha256'],
        'exported_at': run['completedAt'],
        'origin': run['origin'],
    }
    case['probe'] = {
        'metric': 'character_span_probe_score',
        'normalization': 'per_character_sigmoid_in_unit_interval',
        'token_offsets': offsets,
        'token_scores': scores,
        'predicted_spans': [entry['span'] for entry in spans],
        'predicted_span_scores': [
            {
                'span': entry['span'],
                'max_score': entry['max_score'],
                'mean_score': entry['mean_score'],
                'text': entry['text'],
            }
            for entry in spans
        ],
        **_gold_metrics(spans, case['gold_spans'], len(answer)),
    }
    case['experiment_source'] = (
        'output/sirin_a_star_demo/psiloqa_span/live_replay_2026-07-14/'
        'census_char_scores.json'
    )
    return case


def build_from_experiment() -> dict[str, Any]:
    top5 = json.loads((EXPERIMENT / 'top5_demo_cases.json').read_text())
    provenance = json.loads((EXPERIMENT / 'provenance.json').read_text())
    chip = _chip_case(LLANBADOC_CASE_ID)
    record = next(item for item in top5['top5'] if item['id'] == LLANBADOC_CASE_ID)
    if record['answer'] != chip['answer'] or record['question'] != chip['question']:
        raise SystemExit('Experiment record does not match the verified case')

    case = _base_case(chip)
    case['dataset_index'] = int(record['dataset_index'])
    case['model_revision'] = provenance['model_revision']
    case['detector'] = _detector_block(float(top5['threshold']))
    case['source_disclosure'] = (
        'Probe scores are the recorded held-out span-probe outputs from the '
        'SIRIN A* PsiloQA span demo experiment run; detection did not run live.'
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
        'output/sirin_a_star_demo/psiloqa_span/experiment/top5_demo_cases.json'
    )
    return case


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--source', choices=('live-export', 'experiment'), default='live-export'
    )
    args = parser.parse_args()
    case = (
        build_from_live_export()
        if args.source == 'live-export'
        else build_from_experiment()
    )
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
        f"spans = {len(probe['predicted_span_scores'])}"
    )
    for entry in probe['predicted_span_scores']:
        print(f"  {entry['span']} max={entry['max_score']:.4f} {entry['text']!r}")


if __name__ == '__main__':
    main()
