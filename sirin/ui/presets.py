"""Detector presets for the SIRIN UI.

Each preset builds a ready detector (adapter -> feature processor -> detector) directly in
Python, so the UI can offer zero-shot detectors without the Hydra ``train`` composition (which
only yields a checkpoint-only TabPFN probe). Heavy sirin imports live inside ``build`` callables
so importing this module stays cheap and never loads torch.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sirin.ui.providers import OPENROUTER_PROVIDER, provider_models, resolve_api_provider

# default zero-shot uncertainty methods that need no attention maps (sdpa-safe).
_SEQ_UNC_METHODS = ['MeanTokenEntropy', 'Perplexity']
_TOK_UNC_METHODS = ['MaximumTokenProbability', 'TokenEntropy']
_DEFAULT_HF_MODEL = 'Qwen/Qwen3.5-4B'
_SEQUENCE_TABPFN_LAYERS = [-6, -5, -4, -3, -2, -1]
_JUDGE_PROMPT = (
    "You verify whether the assistant response is faithful to the provided context. "
    "Reply with 1 if it contains hallucinated, unsupported, or contradicted claims, "
    "otherwise reply with 0."
)


@dataclass
class Preset:
    name: str
    family: str            # 'uncertainty' | 'judge' | 'probing'
    level: str             # 'sequence' | 'token' | 'claim'
    calibrated: bool       # True if detect() probs are in [0, 1]
    requires_checkpoint: bool
    description: str
    build: Callable[..., Any]
    display_mode: str = 'gauge'
    is_judge: bool = False


def _hf_adapter(device: str, generator_adapter: Any) -> Any:
    from sirin.inference.adapters import HfModelAdapter

    if isinstance(generator_adapter, HfModelAdapter):
        return generator_adapter  # reuse the loaded generator; one model in VRAM.
    from sirin.models.inference import HFConfig

    return HfModelAdapter(
        HFConfig(model_path=_DEFAULT_HF_MODEL, device=device, attn_implementation='sdpa')
    )


def _tag(
    detector: Any,
    family: str,
    level: str,
    calibrated: bool,
    display_mode: str | None = None,
) -> Any:
    detector._ui_family = family
    detector._ui_level = level
    detector._ui_calibrated = calibrated
    detector._ui_display_mode = display_mode
    return detector


def _resolve_judge(
    judge_model: str | None,
    judge_api_key: str | None,
    api_provider: str = OPENROUTER_PROVIDER,
) -> tuple[str, str, str]:
    provider = resolve_api_provider(api_provider, api_key=judge_api_key)
    model_path = judge_model or provider_models(api_provider)[0]
    return model_path, provider.api_key, provider.base_url


def _build_uncertainty(
    level: str,
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    **kwargs: Any,
) -> Any:
    from sirin.detection.processors import (
        SequenceUncertaintyFeatureProcessor,
        TokenUncertaintyFeatureProcessor,
    )
    from sirin.detection.uncertainty import (
        SequenceUncertaintyDetector,
        TokenUncertaintyDetector,
    )
    from sirin.models.detection import (
        UncertaintyDetectorConfig,
        UncertaintyFeatureProcessorConfig,
    )

    extractor = _hf_adapter(device, generator_adapter)
    feature_config = UncertaintyFeatureProcessorConfig(
        uncertainty_methods=_TOK_UNC_METHODS if level == 'token' else _SEQ_UNC_METHODS,
        model_kwargs={'instruct': True},  # apply the chat template inside lm-polygraph
    )
    detector_config = UncertaintyDetectorConfig(aggregation_method='mean')
    if level == 'token':
        processor = TokenUncertaintyFeatureProcessor(config=feature_config, extractor=extractor)
        detector = TokenUncertaintyDetector(config=detector_config, feature_processor=processor)
    else:
        processor = SequenceUncertaintyFeatureProcessor(config=feature_config, extractor=extractor)
        detector = SequenceUncertaintyDetector(config=detector_config, feature_processor=processor)
    return _tag(
        detector,
        'uncertainty',
        level,
        calibrated=False,
        display_mode='heatmap' if level == 'token' else 'raw',
    )


def _build_uncertainty_sequence(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    **kwargs: Any,
) -> Any:
    return _build_uncertainty(
        'sequence',
        device=device,
        checkpoint_dir=checkpoint_dir,
        generator_adapter=generator_adapter,
        judge_model=judge_model,
        judge_api_key=judge_api_key,
        **kwargs,
    )


def _build_uncertainty_token(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    **kwargs: Any,
) -> Any:
    return _build_uncertainty(
        'token',
        device=device,
        checkpoint_dir=checkpoint_dir,
        generator_adapter=generator_adapter,
        judge_model=judge_model,
        judge_api_key=judge_api_key,
        **kwargs,
    )


def _build_openai_judge(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    **kwargs: Any,
) -> Any:
    from sirin.detection.judging import SequenceOpenAIJudge
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.detection import OpenAIJudgeConfig
    from sirin.models.inference import OpenAIConfig

    model_path, api_key, base_url = _resolve_judge(judge_model, judge_api_key, api_provider)
    model = OpenAIModelAdapter(
        OpenAIConfig(model_path=model_path, api_key=api_key, base_url=base_url)
    )
    judge = SequenceOpenAIJudge(
        # temperature 0 keeps the single-token verdict deterministic.
        config=OpenAIJudgeConfig(user_prompt=_JUDGE_PROMPT, temperature=0.0),
        model_adapter=model,
    )
    return _tag(judge, 'judge', 'sequence', calibrated=False, display_mode='verdict')


def _build_openai_token_judge(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    **kwargs: Any,
) -> Any:
    from sirin.detection.judging import TokenOpenAIJudge
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.detection import OpenAIJudgeConfig
    from sirin.models.inference import OpenAIConfig

    model_path, api_key, base_url = _resolve_judge(judge_model, judge_api_key, api_provider)
    model = OpenAIModelAdapter(
        OpenAIConfig(model_path=model_path, api_key=api_key, base_url=base_url)
    )
    judge = TokenOpenAIJudge(
        # temperature > 0 so the num_beams generations DIFFER — a character's score is their span-tag
        # agreement (a [0,1] consensus). At temperature 0 all generations are identical and the
        # "consensus" collapses to a single deterministic 0/1 pass.
        config=OpenAIJudgeConfig(user_prompt=_JUDGE_PROMPT, temperature=0.7),
        model_adapter=model,
    )
    # calibrated=True: the char scores are already fraction-in-[0,1], so show them absolute (a clean
    # answer reads all-clear) instead of min-max-stretching a near-binary array to a misleading mid-grey.
    return _tag(judge, 'judge', 'token', calibrated=True, display_mode='heatmap')


def _build_probing_sequence_tabpfn(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    **kwargs: Any,
) -> Any:
    if not checkpoint_dir:
        raise ValueError("This preset needs a trained checkpoint directory.")

    from sirin.definitions import SideType
    from sirin.detection.probing import SequenceTabPFNProbingDetector
    from sirin.detection.processors import HiddensProcessor
    from sirin.models.detection import HiddensProcessorConfig, ProbingDetectorConfig
    from sirin.models.inference import TokenLocatorConfig

    extractor = _hf_adapter(device, generator_adapter)
    processor = HiddensProcessor(
        config=HiddensProcessorConfig(
            token_locator_config=TokenLocatorConfig(locate_answer_start=True),
            layers=_SEQUENCE_TABPFN_LAYERS,
            side=SideType.RIGHT,
            pooling_type='mean',
        ),
        extractor=extractor,
    )
    detector = SequenceTabPFNProbingDetector(
        config=ProbingDetectorConfig(device='cpu', max_length=1),
        feature_processor=processor,
    )
    detector.load(checkpoint_dir)
    return _tag(detector, 'probing', 'sequence', calibrated=True, display_mode='gauge')


def _hf_hidden_size(model_path: str) -> int | None:
    if not model_path:
        return None
    try:
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
    except Exception:
        return None
    hidden_size = getattr(config, 'hidden_size', None)
    if hidden_size is not None:
        return int(hidden_size)
    text_config = getattr(config, 'text_config', None)
    if text_config is None:
        text_config = config.to_dict().get('text_config')
    if isinstance(text_config, dict):
        hidden_size = text_config.get('hidden_size')
    else:
        hidden_size = getattr(text_config, 'hidden_size', None)
    return int(hidden_size) if hidden_size is not None else None


def sequence_tabpfn_checkpoint_shape_error(
    checkpoint_dir: str,
    model_path: str | None = None,
) -> str | None:
    """Fast compatibility check for the UI's sequence TabPFN probing preset."""
    config_path = Path(checkpoint_dir) / 'compressor_config.joblib'
    if not config_path.exists():
        return None
    import joblib

    config = joblib.load(config_path)
    shapes = list(config.get('feature_shapes') or [])
    if not shapes:
        return None
    expected = tuple(shapes[0][1:])
    configured = (len(_SEQUENCE_TABPFN_LAYERS), 1, expected[-1])
    if expected != configured:
        return (
            'Checkpoint/processor mismatch before generation: '
            f'checkpoint expects feature shape {expected}, but the UI sequence TabPFN preset '
            f'is configured for {configured}. Use a matching checkpoint or update the preset.'
        )
    hidden_size = _hf_hidden_size(model_path or '')
    if hidden_size is not None and hidden_size != expected[-1]:
        return (
            'Checkpoint/model mismatch before generation: '
            f'checkpoint expects hidden size {expected[-1]}, but selected model '
            f'{model_path} has hidden size {hidden_size}. Use a model with hidden size '
            f'{expected[-1]} for this checkpoint or choose a matching checkpoint.'
        )
    return None


def _build_probing_answerability(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    **kwargs: Any,
) -> Any:
    from sirin.definitions import SideType
    from sirin.detection.probing import SequenceTabPFNProbingDetector
    from sirin.detection.processors import HiddensProcessor
    from sirin.inference.adapters import HfModelAdapter
    from sirin.models.detection import HiddensProcessorConfig, ProbingDetectorConfig
    from sirin.models.inference import HFConfig, TokenLocatorConfig

    checkpoint_dir = (
        checkpoint_dir
        or os.getenv('SIRIN_ANSWERABILITY_CKPT')
        or '/home/jovyan/parchiev/magistr/trust_assistant/checkpoints/probing/answerability_tabpfn/Hiddens_L_TabPFN'
    )
    extractor = HfModelAdapter(
        HFConfig(
            model_path='Qwen/Qwen3.5-4B',
            device=device,
            attn_implementation='sdpa',
            model_dtype='bf16',
            padding='longest',
            padding_side='left',
        )
    )
    # 6 layers auto-resolved by trust_assistant for Qwen3.5-4B (32 hidden
    # layers) from the checkpoint's compressor feature_shapes -> [16,27,28,29,30,31];
    # hardcoded, this ckpt is fixed.
    processor = HiddensProcessor(
        config=HiddensProcessorConfig(
            layers=[16, 27, 28, 29, 30, 31],
            separate=True,
            side=SideType.LEFT,
            pooling_type='none',
            max_length=2048,
            padding='longest',
            truncation=True,
            cache_features=False,
            token_locator_config=TokenLocatorConfig(locate_answer_start=True),
        ),
        extractor=extractor,
    )
    detector = SequenceTabPFNProbingDetector(
        config=ProbingDetectorConfig(
            num_classification_heads=2,
            device='cpu',
            batch_size=1,
        ),
        feature_processor=processor,
    )
    detector.load(checkpoint_dir)
    return _tag(detector, 'probing', 'sequence', calibrated=True, display_mode='gauge')


PRESETS: dict[str, Preset] = {
    "Probing — Sequence TabPFN (checkpoint)": Preset(
        name="Probing — Sequence TabPFN (checkpoint)",
        family='probing',
        level='sequence',
        calibrated=True,
        requires_checkpoint=True,
        description="TabPFN probe on hidden states — calibrated [0,1]. Needs a trained checkpoint directory.",
        build=_build_probing_sequence_tabpfn,
        display_mode='gauge',
        is_judge=False,
    ),
    "Uncertainty — Sequence (zero-shot)": Preset(
        name="Uncertainty — Sequence (zero-shot)",
        family='uncertainty',
        level='sequence',
        calibrated=False,
        requires_checkpoint=False,
        description="Local white-box uncertainty over the whole answer (mean token entropy + perplexity). No training.",
        build=_build_uncertainty_sequence,
        display_mode='raw',
        is_judge=False,
    ),
    "Uncertainty — Token (zero-shot)": Preset(
        name="Uncertainty — Token (zero-shot)",
        family='uncertainty',
        level='token',
        calibrated=False,
        requires_checkpoint=False,
        description="Per-token uncertainty highlighting over the generated answer. No training.",
        build=_build_uncertainty_token,
        display_mode='heatmap',
        is_judge=False,
    ),
    "Judge — API Sequence (zero-shot)": Preset(
        name="Judge — API Sequence (zero-shot)",
        family='judge',
        level='sequence',
        calibrated=False,
        requires_checkpoint=False,
        description="LLM-as-judge verdict via the OpenAI/OpenRouter API. No training.",
        build=_build_openai_judge,
        display_mode='verdict',
        is_judge=True,
    ),
    "Judge — API Token (zero-shot)": Preset(
        name="Judge — API Token (zero-shot)",
        family='judge',
        level='token',
        calibrated=True,
        requires_checkpoint=False,
        description="Per-character hallucination heatmap via the OpenAI/OpenRouter API (span-tag agreement across sampled generations). No training.",
        build=_build_openai_token_judge,
        display_mode='heatmap',
        is_judge=True,
    ),
    "Probing — Answerability TabPFN (checkpoint)": Preset(
        name="Probing — Answerability TabPFN (checkpoint)",
        family='probing',
        level='sequence',
        calibrated=True,
        requires_checkpoint=True,
        description="Answerability TabPFN probe on Qwen3.5-4B hidden states. Uses the fixed trust_assistant checkpoint by default.",
        build=_build_probing_answerability,
        display_mode='gauge',
        is_judge=False,
    ),
}


def list_presets() -> list[Preset]:
    return list(PRESETS.values())


def _level_of(detector: Any) -> str:
    level = getattr(detector, 'detection_level', None)
    if level is not None:
        return getattr(level, 'value', str(level)).lower()
    return 'sequence'


def _family_of(detector: Any) -> str:
    name = type(detector).__name__.lower()
    if 'uncertainty' in name:
        return 'uncertainty'
    if 'judge' in name:
        return 'judge'
    if 'probing' in name or 'probe' in name:
        return 'probing'
    return 'unknown'


def _display_mode_of(detector: Any, family: str, level: str) -> str:
    name = type(detector).__name__.lower()
    if level == 'token':
        return 'heatmap'
    if level == 'claim':
        return 'claim-cards'
    if family == 'uncertainty':
        return 'raw'
    if family == 'judge' and 'openai' in name:
        return 'verdict'
    if getattr(getattr(detector, 'config', None), 'num_classification_heads', 1) > 2:
        return 'multiclass'
    return 'gauge'


def _calibrated_of(detector: Any, family: str, level: str) -> bool:
    name = type(detector).__name__.lower()
    if family == 'uncertainty':
        return False
    if family == 'judge':
        return level == 'token' or 'openai' not in name
    return True


def describe_detector(detector: Any) -> dict[str, Any]:
    family = getattr(detector, '_ui_family', None) or _family_of(detector)
    level = getattr(detector, '_ui_level', None) or _level_of(detector)
    calibrated = getattr(detector, '_ui_calibrated', None)
    if calibrated is None:
        calibrated = _calibrated_of(detector, family, level)
    display_mode = getattr(detector, '_ui_display_mode', None)
    if display_mode is None:
        display_mode = _display_mode_of(detector, family, level)
    return {
        'family': family,
        'level': level,
        'calibrated': bool(calibrated),
        'display_mode': display_mode,
        'threshold': getattr(detector, 'threshold', None),
    }
