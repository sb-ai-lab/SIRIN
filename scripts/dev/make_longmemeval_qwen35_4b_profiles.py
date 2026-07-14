"""Build the three LongMemEval Qwen3.5-4B UI profiles (SimpleMem / LightMem / Mem0).

Mirrors the shape of ``sirin/ui/assets/longmemeval_qwen35.json`` (the 35B profile) but points at
each variant's ``sirin_datasets/qwen35_4b`` outputs with the 4B probe geometry (32 layers, hidden
size 2560 -> layers [16,27,28,29,30,31], feature shape [6,1,2560]). Every checkpoint threshold is
read verbatim from that detector's ``config.joblib`` (the same source the 35B profile used), and
every checkpoint path is verified to exist before the profile is written. Nothing is invented.

Run from the repo root::

    /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/make_longmemeval_qwen35_4b_profiles.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / 'sirin/ui/assets'
MODEL_PATH = 'Qwen/Qwen3.5-4B'
MODEL_REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
LAYERS = [16, 27, 28, 29, 30, 31]
FEATURE_SHAPE = [6, 1, 2560]
TASK_FEATURE = {'hallucination_strict': 'Hiddens_R', 'answerability_strict': 'Hiddens_L'}
DETECTORS = {'linear': 'Linear', 'catboost': 'CatBoost', 'tabpfn': 'TabPFN'}

# (variant key, sidebar label, absolute run subdir, strict sample counts, whether a UQ run exists)
VARIANTS = [
    (
        'simplemem',
        'SimpleMem',
        '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
        'pure_simplemem_qwen35_35b_a3b/20260703_120500_qwen35_35b_a3b_s_full_combined_500',
        {'hallucination_strict': 409, 'answerability_strict': 469},
        False,
    ),
    (
        'lightmem',
        'LightMem',
        '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
        'pure_lightmem_qwen35b_a3b_qwen3emb_llmlingua_tp4_30110_full/'
        'lightmem_qwen35b_a3b_qwen3emb_llmlingua_tp4_30110_full_combined_500',
        {'hallucination_strict': 384, 'answerability_strict': 444},
        True,
    ),
    (
        'mem0',
        'Mem0',
        '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
        'pure_mem0_qwen35b_a3b_gpuembed4-5_qwen6-7_batch150_flash_bm25_combined/'
        'mem0_qwen35b_a3b_gpuembed4-5_qwen6-7_batch150_flash_bm25_combined_500',
        {'hallucination_strict': 295, 'answerability_strict': 342},
        True,
    ),
]


def _threshold(detector_dir: Path) -> float:
    config = detector_dir / 'config.joblib'
    if not config.is_file():
        raise SystemExit(f'Missing config.joblib: {config}')
    value = joblib.load(config).get('threshold')
    if value is None:
        raise SystemExit(f'No threshold in {config}')
    return float(value)


def _checkpoints(base: Path) -> dict[str, Any]:
    checkpoints: dict[str, Any] = {}
    for task, prefix in TASK_FEATURE.items():
        entries: dict[str, Any] = {}
        for key, suffix in DETECTORS.items():
            detector_dir = base / 'saved_detectors' / task / f'{prefix}_{suffix}'
            if not detector_dir.is_dir():
                raise SystemExit(f'Missing detector dir: {detector_dir}')
            entries[key] = {
                'path': str(detector_dir),
                'threshold': _threshold(detector_dir),
            }
        best_dir = base / 'saved_detectors' / task / 'best'
        if not best_dir.is_dir():
            raise SystemExit(f'Missing best dir: {best_dir}')
        best_threshold = _threshold(best_dir)
        # `best` is a copied detector dir; its threshold matches TabPFN in every variant/task.
        target = next(
            (key for key, entry in entries.items() if entry['threshold'] == best_threshold),
            'tabpfn',
        )
        entries['best'] = {
            'path': str(best_dir),
            'target': target,
            'threshold': best_threshold,
        }
        checkpoints[task] = entries
    return checkpoints


def _uncertainty(base: Path, samples: dict[str, int], has_uq: bool) -> dict[str, Any]:
    reason = (
        'Sequence uncertainty ran but no full-set optimal threshold was calibrated for this '
        'Qwen3.5-4B variant; scores are recorded in sirin_metrics.json but not thresholded here.'
        if has_uq
        else 'This variant is a probing-only run; no uncertainty baselines were computed.'
    )
    return {
        'sequence': {
            'methods': ['MeanTokenEntropy', 'Perplexity'],
            'aggregation_method': 'mean',
            'max_new_tokens': 64,
            'thresholds': {
                task: {'value': None, 'fit': 'not calibrated', 'samples': count}
                for task, count in samples.items()
            },
            'metrics': str(base / 'sirin_metrics.json'),
            'reason': reason,
        },
        'token': {
            'methods': ['MaximumTokenProbability', 'TokenEntropy'],
            'threshold': None,
            'reason': 'No token-labelled LongMemEval Qwen3.5-4B calibration was run.',
        },
    }


def build_profile(variant: str, label: str, run_root: str, samples, has_uq) -> dict[str, Any]:
    base = Path(run_root) / 'sirin_datasets' / 'qwen35_4b'
    if not base.is_dir():
        raise SystemExit(f'Missing qwen35_4b dir: {base}')
    return {
        'schema_version': 1,
        'name': f'LongMemEval / Qwen3.5-4B · {label}',
        'variant': variant,
        'label': f'Qwen3.5-4B · {label}',
        'dataset': 'LongMemEval',
        'model': {
            'path': MODEL_PATH,
            'revision': MODEL_REVISION,
            'device': 'cuda',
            'dtype': 'bf16',
            'max_length': 2048,
        },
        'generation_api': {
            'backend': 'Custom OpenAI-compatible',
            'base_url': 'http://127.0.0.1:8000/v1',
            'api_key_env': 'SIRIN_CUSTOM_OPENAI_API_KEY',
            'note': (
                'Local Qwen3.5-4B probe server. The LongMemEval answers were generated by the '
                'Qwen3.5-35B-A3B memory pipeline; the 4B model is the hidden-state extractor only.'
            ),
        },
        'ui': {
            'default_preset': 'Probing — Sequence TabPFN (checkpoint)',
            'max_tokens': 192,
            'temperature': 0.0,
            'default_checkpoint': {
                'preset': 'Probing — Sequence TabPFN (checkpoint)',
                'task': 'hallucination_strict',
                'detector': 'tabpfn',
            },
        },
        'run': {
            'root': str(base),
            'hiddens_config': str(base / 'config_resolved.yaml'),
        },
        'probing': {
            'hallucination_strict': {
                'feature': 'Hiddens_R',
                'layers': LAYERS,
                'side': 'RIGHT',
                'pooling_type': 'mean',
                'locate_answer_start': True,
                'checkpoint_feature_shape': FEATURE_SHAPE,
            }
        },
        'checkpoints': _checkpoints(base),
        'uncertainty': _uncertainty(base, samples, has_uq),
    }


def main() -> None:
    for variant, label, run_root, samples, has_uq in VARIANTS:
        profile = build_profile(variant, label, run_root, samples, has_uq)
        out = ASSETS / f'longmemeval_qwen35_4b_{variant}.json'
        out.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
        )
        print(f'wrote {out.name} ({out.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
