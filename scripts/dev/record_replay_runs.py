"""Record real detector runs as hosted replay assets (sirin/ui/assets/recorded_runs/).

The hosted Space has no GPU and no local model weights, so non-judge presets cannot score
live there. This script runs each preset FOR REAL through the same product path the UI
uses (build_preset_detector -> detect -> detection_view_model -> RunEngine.execute ->
present_analysis) and exports the terminal RunRecord with ``export_run`` (the strict
portable format, SHA-256 integrity included). The hosted UI replays these verified
records; nothing is invented and nothing is post-edited.

Run from the repo root (GPU host)::

    /home/jovyan/.mlspace/envs/sirin/bin/python scripts/dev/record_replay_runs.py \
        [uncertainty_sequence uncertainty_sequence_msp uncertainty_token answerability_tabpfn]
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEVICE = 'cuda:0'
GEN_MODEL = 'Qwen/Qwen3-4B'
OUT_DIR = REPO / 'sirin/ui/assets/recorded_runs'

RECORDINGS: dict[str, dict] = {
    'uncertainty_sequence': {
        'preset': 'Uncertainty — Sequence (zero-shot)',
        'mode': 'generateAndScore',
        'task': 'faithfulness',
    },
    'uncertainty_sequence_msp': {
        'preset': 'Uncertainty — Sequence · Sequence Probability (zero-shot)',
        'mode': 'generateAndScore',
        'task': 'faithfulness',
    },
    'uncertainty_token': {
        'preset': 'Uncertainty — Token (zero-shot)',
        'mode': 'generateAndScore',
        'task': 'faithfulness',
    },
    'answerability_tabpfn': {
        'preset': 'Probing — Answerability TabPFN (checkpoint)',
        'mode': 'answerability',
        'task': 'answerability',
    },
    # The M1 north-star detector: bundled LongMemEval TabPFN checkpoint on Qwen3.5-35B-A3B
    # hiddens, scoring one of its own curated recorded-answer cases. Run under sirin_exps
    # (transformers with qwen3_5) with SIRIN_UI_AUTO_DEVICE_MAP_GPUS + CUDA_VISIBLE_DEVICES
    # spanning enough GPUs for the 35B (see docs/ui_example.md).
    'sequence_tabpfn': {
        'preset': 'Probing — Sequence TabPFN (checkpoint)',
        'mode': 'recordedReplay',
        'task': 'faithfulness',
        'demo_case': 'e3038f8c',
        'checkpoint': 'demo/checkpoints/qwen35_longmemeval_hallucination_tabpfn',
        'gen_model': 'Qwen/Qwen3.5-35B-A3B',
        'device': 'cuda',
    },
}


def main() -> None:
    from sirin.ui.demo_cases import load_demo_cases, load_psiloqa_span_seed_qwen35
    from sirin.ui.presets import PRESETS
    from sirin.ui.streamlit_app import (
        _split_thinking,
        _v2_prompt,
        build_preset_detector,
        build_sample,
        detection_view_model,
        generate_answer,
        load_generator,
    )
    from sirin.ui.workspace.contracts import (
        Provenance,
        RunRequest,
        SetupSnapshot,
        derive_score_semantics,
    )
    from sirin.ui.workspace.run_engine import RunEngine
    from sirin.ui.workspace.session import export_run

    seed = load_psiloqa_span_seed_qwen35()
    if seed is None:
        raise SystemExit('qwen35 span seed asset is required (shared demo example)')

    targets = sys.argv[1:] or list(RECORDINGS)
    OUT_DIR.mkdir(exist_ok=True)

    for slug in targets:
        spec = RECORDINGS[slug]
        preset = PRESETS[spec['preset']]
        device = spec.get('device', DEVICE)
        gen_model = spec.get('gen_model', GEN_MODEL)
        print(f'=== {slug}: {preset.name}')

        detector = build_preset_detector(
            preset_name=preset.name,
            device=device,
            checkpoint_dir=str(REPO / spec['checkpoint']) if spec.get('checkpoint') else '',
            gen_backend='HF',
            gen_model=gen_model,
            gen_base_url='',
            judge_model='',
            judge_provider='OpenRouter',
            judge_api_key='',
        )

        def generate(request, _setup):
            adapter = load_generator('HF', gen_model, device, '', '')
            raw = generate_answer(
                adapter, 'HF', _v2_prompt(request), max_tokens=192, temperature=0.0
            )
            answer, _ = _split_thinking(raw)
            return answer

        def detect(answer, request, _setup):
            prompt = _v2_prompt(request)
            result = detector.detect([build_sample(prompt, answer.strip())])
            return detection_view_model(result, answer.strip(), detector)

        answerability = spec['task'] == 'answerability'
        setup = SetupSnapshot(
            task=spec['task'],
            detector_preset=preset.name,
            detector_family=preset.family,
            detector_level='token' if 'Token' in preset.name else 'sequence',
            model_id=None if answerability else gen_model,
            provider_label='HF',
            calibrated=bool(preset.calibrated),
            score_semantics=derive_score_semantics(
                calibrated=bool(preset.calibrated),
                family=preset.family,
                level='token' if 'Token' in preset.name else 'sequence',
            ),
        )
        recorded_note = (
            f'Recorded {date.today().isoformat()} on a local GPU; the hosted demo '
            'replays this verified result and does not run this detector live.'
        )
        if spec.get('demo_case'):
            case = load_demo_cases()[spec['demo_case']]
            request = RunRequest.model_construct(
                task=spec['task'],
                mode=spec['mode'],
                question=case['title'],
                prompt=case['answer_prompt'],
                supplied_answer=case['prediction'],
                example_id=case['sample_id'],
                source_run_id=None,
            )
            case_provenance = case['provenance']
            provenance = Provenance(
                dataset=case_provenance.get('dataset'),
                source_model=case_provenance.get('model'),
                disclosures=[
                    'Recorded answer replayed from the verified bundled artifact.',
                    recorded_note,
                ],
            )
        else:
            request = RunRequest(
                task=spec['task'],
                mode=spec['mode'],
                context=seed['passage'],
                question=seed['question'],
                supplied_answer='',
                example_id=seed['example_id'],
            )
            provenance = Provenance(
                dataset=seed['dataset'],
                split=seed['split'],
                disclosures=[recorded_note, f"License: {seed['license']}"],
            )

        engine = RunEngine(generate=generate, detect=detect)
        queued = engine.reserve(request, setup, setup_revision=0, provenance=provenance)
        record = engine.execute(queued, request)
        if record.status.value != 'succeeded':
            raise SystemExit(
                f'{slug} did not succeed: {record.status} '
                f'{record.error.message if record.error else ""}'
            )

        out_path = OUT_DIR / f'{slug}.json'
        out_path.write_text(export_run(record), encoding='utf-8')
        analysis = record.analysis.model_dump() if record.analysis else {}
        brief = {k: analysis.get(k) for k in ('level', 'verdict', 'score') if k in analysis}
        print(f'    wrote {out_path.name}; answer chars={len(record.answer or "")}, '
              f'analysis={brief}')


if __name__ == '__main__':
    main()
