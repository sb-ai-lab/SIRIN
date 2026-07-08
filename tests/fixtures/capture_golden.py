"""Capture golden vectors from the pristine tree before Phase 1+ edits."""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / 'golden'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIXED_SAMPLES = [
    [
        {'role': 'user', 'content': 'What is the capital of France?'},
        {'role': 'assistant', 'content': 'Paris is the capital of France.'},
    ],
    [
        {'role': 'user', 'content': 'Who wrote Hamlet?'},
        {'role': 'assistant', 'content': 'William Shakespeare wrote Hamlet.'},
    ],
]


def capture_answerability_probs():
    from sirin.ui.presets import _build_probing_answerability

    detector = _build_probing_answerability(checkpoint_dir=None)
    probs = []
    for sample in FIXED_SAMPLES:
        sample_probs, _, _ = detector.detect([sample])
        probs.append(float(sample_probs[0]))
    return probs


def capture_uncertainty_scores():
    """Requires a loaded HF model on GPU — skip if unavailable."""
    import torch
    from sirin.detection.processors.uncertainty import SequenceUncertaintyFeatureProcessor
    from sirin.inference.adapters import HfModelAdapter
    from sirin.models.detection import UncertaintyFeatureProcessorConfig
    from sirin.models.inference import HFConfig

    if not torch.cuda.is_available():
        print("CUDA unavailable - skipping uncertainty golden capture")
        return None

    adapter = HfModelAdapter(config=HFConfig(model_path='sshleifer/tiny-gpt2', device='cuda'))
    config = UncertaintyFeatureProcessorConfig(uncertainty_methods=['MeanTokenEntropy'])
    processor = SequenceUncertaintyFeatureProcessor(config=config, extractor=adapter)
    processor.setup_extractor()
    processor.generate_features(FIXED_SAMPLES)
    return processor.last_method_scores


def main():
    golden = {'samples': FIXED_SAMPLES}

    try:
        golden['answerability_probs'] = capture_answerability_probs()
        print(f"Answerability probs: {golden['answerability_probs']}")
    except Exception as exc:
        print(f"Answerability capture failed: {exc}")
        golden['answerability_probs'] = None

    try:
        golden['uncertainty_scores'] = capture_uncertainty_scores()
        print(f"Uncertainty scores: {golden['uncertainty_scores']}")
    except Exception as exc:
        print(f"Uncertainty capture failed: {exc}")
        golden['uncertainty_scores'] = None

    out_path = OUTPUT_DIR / 'baseline.json'
    out_path.write_text(json.dumps(golden, indent=2))
    print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
