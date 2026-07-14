"""Static, copy-paste recipes for extending SIRIN with a new detector.

Content-only module: the "Add a detector" view renders whatever this returns, so copy edits never
touch the component. Every ``code`` string is real, importable SIRIN API and is syntax-checked in
tests/test_ui_recipes.py; keep it that way when editing.
"""

from __future__ import annotations

from .contracts import DetectorRecipe


_WRAP_OPENAI_JUDGE = '''\
from sirin.detection.judging import SequenceOpenAIJudge
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig
from sirin.models.inference import OpenAIConfig

model = OpenAIModelAdapter(
    OpenAIConfig(
        model_path="your-model-id",
        api_key="sk-...",
        base_url="https://your-endpoint/v1",
    )
)
judge = SequenceOpenAIJudge(
    config=OpenAIJudgeConfig(
        # {sample} is required — the dialogue is inserted there. The single-digit clause forces
        # token 0 to be a bare 0/1 (structured prompts otherwise open a JSON object).
        user_prompt=(
            "Is the assistant answer faithful to the context? "
            'Dialogue: "{sample}". Reply with a single digit, 1 or 0: '
        ),
        temperature=0.0,
    ),
    model_adapter=model,
)
probs, preds, _ = judge.detect([
    [
        {"role": "user", "content": "Question and its supporting context"},
        {"role": "assistant", "content": "The answer to verify"},
    ]
])
'''


_TRAIN_TOKEN_PROBE = '''\
# 1. Train a token linear probe on your own PsiloQA-style span dataset. The CLI extracts hidden
#    states, sweeps the layer, and writes a checkpoint + manifest.json:
#
#    python demo/train_psiloqa_span_linear.py \\
#        --dataset /path/to/your_span_dataset \\
#        --model-id Qwen/Qwen3-4B \\
#        --layers auto \\
#        --checkpoint-dir /path/to/checkpoints/my_probe
#
# 2. Score span metrics for your own predictions with sirin.metrics.span:
from sirin.metrics.span import (
    character_scores,
    f1_optimal_threshold,
    span_classification_metrics,
    span_labels,
)

# Per token: the model score and its (start, end) char offset in the answer.
char_scores = character_scores(answer, token_offsets, token_scores)
char_labels = span_labels(len(answer), gold_spans)
threshold = f1_optimal_threshold(char_labels, char_scores)
metrics = span_classification_metrics([char_labels], [char_scores], threshold)
'''


_REGISTER_PRESET = '''\
from sirin.ui.presets import PRESETS, Preset


def build_my_detector(*, device="cuda", generator_adapter=None, **kwargs):
    # Return any object exposing .detect([sample]) -> (probs, preds, labels).
    from sirin.detection.processors import SequenceUncertaintyFeatureProcessor
    from sirin.detection.uncertainty import SequenceUncertaintyDetector
    from sirin.models.detection import (
        UncertaintyDetectorConfig,
        UncertaintyFeatureProcessorConfig,
    )

    processor = SequenceUncertaintyFeatureProcessor(
        config=UncertaintyFeatureProcessorConfig(uncertainty_methods=["Perplexity"]),
        extractor=generator_adapter,
    )
    return SequenceUncertaintyDetector(
        config=UncertaintyDetectorConfig(aggregation_method="mean"),
        feature_processor=processor,
    )


# PRESETS lives in sirin/ui/presets.py; add an entry so the sidebar lists your detector.
PRESETS["My — Sequence Detector (zero-shot)"] = Preset(
    name="My — Sequence Detector (zero-shot)",
    family="uncertainty",
    level="sequence",
    calibrated=False,
    requires_checkpoint=False,
    description="One honest line: what the score means, and that it is not a calibrated probability.",
    build=build_my_detector,
    display_mode="raw",
    census_caption="Perplexity · relative within-answer, uncalibrated",
)
'''


def detector_recipes() -> list[DetectorRecipe]:
    """The three static extension recipes, newest-friendly order (wrap, train, register)."""
    return [
        DetectorRecipe(
            id='wrap_openai_judge',
            title='Wrap an OpenAI-compatible endpoint as a judge',
            description=(
                'Point SIRIN at any OpenAI-compatible chat endpoint and score faithfulness with an '
                'LLM-as-judge. No training, no checkpoint — just a model id, key, and base URL.'
            ),
            code=_WRAP_OPENAI_JUDGE,
        ),
        DetectorRecipe(
            id='train_token_probe',
            title='Train a token linear probe on your span dataset',
            description=(
                'Extract hidden states and fit a per-token linear probe on your own span-labelled '
                'data via the training CLI, then score span metrics with sirin.metrics.span.'
            ),
            code=_TRAIN_TOKEN_PROBE,
            reference='demo/train_psiloqa_span_linear.py',
        ),
        DetectorRecipe(
            id='register_preset',
            title='Register your detector as a UI preset',
            description=(
                'Add a Preset to PRESETS in sirin/ui/presets.py so your detector shows up in the '
                'sidebar. The build callable returns any object with a .detect([sample]) method.'
            ),
            code=_REGISTER_PRESET,
        ),
    ]
