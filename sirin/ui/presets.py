"""Detector presets for the SIRIN UI.

Each preset builds a ready detector (adapter -> feature processor -> detector) directly in
Python, so the UI can offer zero-shot detectors without the Hydra ``train`` composition (which
only yields a checkpoint-only TabPFN probe). Heavy sirin imports live inside ``build`` callables
so importing this module stays cheap and never loads torch.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from sirin.definitions import DetectionTaskType
from sirin.ui.path_policy import is_hosted
from sirin.ui.providers import (
    CUSTOM_PROVIDER,
    OPENROUTER_PROVIDER,
    custom_openai_base_url,
    openrouter_reasoning_extra_body,
    provider_models,
    require_shared_key_model,
    resolve_api_provider,
)

# default zero-shot uncertainty methods that need no attention maps (sdpa-safe).
_SEQ_UNC_METHODS = ['MeanTokenEntropy', 'Perplexity']
# Single-pass greedy sequence log-probability. sdpa-safe, no sampling, no attention — the only one of
# the two brief candidates that qualifies (MonteCarloSequenceEntropy needs multiple sampled generations).
_SEQ_UNC_METHODS_MSP = ['MaximumSequenceProbability']
_TOK_UNC_METHODS = ['MaximumTokenProbability', 'TokenEntropy']
_DEFAULT_HF_MODEL = 'Qwen/Qwen3-4B'
PSILOQA_TOKEN_LINEAR_PRESET = 'Probing — Token Linear · PsiloQA/Qwen3-4B'
# The paste-a-key span judge is the demo headline: the sidebar pins it right under the hero probe.
JUDGE_SPAN_PRESET = 'Judge — API Span (zero-shot)'
JUDGE_SEQUENCE_PRESET = 'Judge — API Sequence (zero-shot)'
JUDGE_SEQUENCE_VERBALIZED_PRESET = 'Judge — API Sequence (verbalized confidence)'
PSILOQA_MODEL_ID = 'Qwen/Qwen3-4B'
PSILOQA_MODEL_REVISION = '1cfa9a7208912126459214e8b04321603b3df60c'
PSILOQA_CHECKPOINT_DIR = str(
    Path(__file__).resolve().parents[2]
    / 'demo/checkpoints/qwen3_4b_psiloqa_span_linear'
)
# Second live PsiloQA probe on the Qwen3.5-4B campaign checkpoint. Distinct constants so the landing
# seed (pinned to the Qwen3-4B probe above) is never mutated; this preset is selectable, not default.
PSILOQA_TOKEN_LINEAR_PRESET_QWEN35 = 'Probing — Token Linear · PsiloQA/Qwen3.5-4B'
PSILOQA_QWEN35_MODEL_ID = 'Qwen/Qwen3.5-4B'
PSILOQA_QWEN35_MODEL_REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
PSILOQA_QWEN35_CHECKPOINT_DIR = str(
    Path(__file__).resolve().parents[2]
    / 'demo/checkpoints/qwen35_4b_psiloqa_span_linear'
)
# preset name -> (locked model id, revision, bundled checkpoint). Both entries build their own HF
# adapter pinned to their model, so the dispatch must NOT hand them a generator adapter.
PSILOQA_TOKEN_LINEAR_PRESETS: dict[str, tuple[str, str, str]] = {
    PSILOQA_TOKEN_LINEAR_PRESET: (
        PSILOQA_MODEL_ID,
        PSILOQA_MODEL_REVISION,
        PSILOQA_CHECKPOINT_DIR,
    ),
    PSILOQA_TOKEN_LINEAR_PRESET_QWEN35: (
        PSILOQA_QWEN35_MODEL_ID,
        PSILOQA_QWEN35_MODEL_REVISION,
        PSILOQA_QWEN35_CHECKPOINT_DIR,
    ),
}
# External (unbundled) sibling checkpoint. Derived from the repo location instead of a hardcoded
# home path; honored only as a last-resort fallback after the env override. Not bundled/verified,
# so it is deliberately NOT exposed as a preset ``builtin_checkpoint`` (no false availability).
_PRESETS_PARENTS = Path(__file__).resolve().parents
ANSWERABILITY_CHECKPOINT_DIR = str(
    # parents[4] when the tree is deep enough; shallow installs (e.g. /app on a hosted
    # Space) fall back to the outermost parent, yielding a path that simply never exists.
    _PRESETS_PARENTS[min(4, len(_PRESETS_PARENTS) - 1)]
    / 'trust_assistant/checkpoints/probing/answerability_tabpfn/Hiddens_L_TabPFN'
)
_SEQUENCE_TABPFN_LAYERS = [20, 35, 36, 37, 38, 39]
# The sequence API judge formats this as the user_prompt via build_prompt_messages(sample=dialogue),
# so it MUST carry the {sample} slot — without it the dialogue is never inserted and the judge scores
# an empty conversation. The trailing single-digit clause forces token 0 to be a bare '0'/'1': on long
# structured prompts the model otherwise opens a JSON object ('{' as token 0) and the max_tokens=1
# logprob verdict collapses. Mirrors psiloqa_span_judge_eval.py::SEQUENCE_VERDICT_PROMPT in sirin_deploy (verified
# live to yield clean 0/1 top-2 logprobs). System prompt stays the JudgeBaseConfig default.
_JUDGE_PROMPT = (
    "You verify whether the assistant response is faithful to the provided context. "
    "Reply with 1 if it contains hallucinated, unsupported, or contradicted claims, "
    "otherwise reply with 0.\n"
    'Dialogue: "{sample}"\n'
    "Answer with a SINGLE character that is the digit 1 or the digit 0. Do not output JSON, "
    "quotes, spaces, reasoning, or any other character. Your entire reply must be exactly one "
    "digit: "
)
# Same shape as _JUDGE_PROMPT (single-digit forcing, {sample} slot) but for answerability: the
# dialogue is a context + question with NO answer. Polarity: 1 when the context is NOT sufficient
# to answer the question (unanswerable), 0 when it IS sufficient. The trailing single-digit clause
# forces token 0 to a bare '0'/'1' just as the faithfulness prompt does.
_ANSWERABILITY_JUDGE_PROMPT = (
    "You are given a context passage and a question, with no answer. Decide whether the "
    "context contains enough information to answer the question.\n"
    'Dialogue: "{sample}"\n'
    "Reply with 1 if the context is NOT sufficient to answer the question, or 0 if it IS "
    "sufficient. Answer with a SINGLE character that is the digit 1 or the digit 0. Do not "
    "output JSON, quotes, spaces, reasoning, or any other character. Your entire reply must "
    "be exactly one digit: "
)


@dataclass
class Preset:
    name: str
    family: str  # 'uncertainty' | 'judge' | 'probing'
    level: str  # 'sequence' | 'token' | 'claim'
    calibrated: bool  # True only when the score has calibrated probability semantics.
    requires_checkpoint: bool
    description: str
    build: Callable[..., Any]
    task: str = DetectionTaskType.HALLUCINATION_DETECTION.value
    display_mode: str = 'gauge'
    is_judge: bool = False
    builtin_checkpoint: str | None = None  # bundled checkpoint (hash-pinned in its manifest); no path input needed.
    # One-line census-sidebar truth about the method (names it + its honest score scale). Used only when
    # the preset exposes no dynamic checkpoint meta (layer/τ/SHA); '' falls back to the description.
    census_caption: str | None = None


def _hf_adapter(device: str, generator_adapter: Any) -> Any:
    if callable(getattr(generator_adapter, 'generate_hiddens', None)):
        return generator_adapter  # reuse the loaded generator; one model in VRAM.
    from sirin.inference.adapters import HfModelAdapter
    from sirin.models.inference import HFConfig

    return HfModelAdapter(
        HFConfig(
            model_path=_DEFAULT_HF_MODEL, device=device, attn_implementation='sdpa'
        )
    )


def _uncertainty_adapter(device: str, generator_adapter: Any) -> Any:
    if generator_adapter is not None:
        return generator_adapter
    return _hf_adapter(device, None)


def _tag(
    detector: Any,
    family: str,
    level: str,
    calibrated: bool,
    display_mode: str | None = None,
    task: str = DetectionTaskType.HALLUCINATION_DETECTION.value,
) -> Any:
    detector._ui_family = family
    detector._ui_level = level
    detector._ui_calibrated = calibrated
    detector._ui_display_mode = display_mode
    detector._ui_task = task
    return detector


def _resolve_judge(
    judge_model: str | None,
    judge_api_key: str | None,
    api_provider: str = OPENROUTER_PROVIDER,
) -> tuple[str, str, str]:
    # A trusted-local Custom judge resolves its base URL from SIRIN_CUSTOM_OPENAI_BASE_URL, falling
    # back to the local vLLM default (the pasted key wins, else SIRIN_CUSTOM_OPENAI_API_KEY, else
    # 'EMPTY' — resolve_api_provider handles that).
    custom_base_url = (
        custom_openai_base_url() if api_provider == CUSTOM_PROVIDER else ''
    )
    provider = resolve_api_provider(
        api_provider, custom_base_url, api_key=judge_api_key
    )
    model_path = judge_model or provider_models(api_provider)[0]
    require_shared_key_model(api_provider, model_path, judge_api_key)
    return model_path, provider.api_key, provider.base_url


def _judge_extra_body(api_provider: str, model: str = '') -> dict[str, Any] | None:
    """Per-provider request extension for a judge endpoint; None when nothing is needed.

    Custom (trusted-local vLLM): a Qwen judge otherwise lands every generation in its reasoning
    channel, so every verbatim echo is invalid (JudgeAnnotationError); disabling thinking makes the
    verdict/annotation stable. Opt back in with SIRIN_CUSTOM_JUDGE_THINKING=1.
    OpenRouter: model-aware ``reasoning`` extension (off for the verified demo model, capped
    otherwise) — an uncapped chain-of-thought overruns the completion budget,
    finish_reason='length', and OpenRouter mirrors the truncated reasoning into content, which
    then fails the verbatim echo check.
    OpenAI/Anthropic: None — they may reject unknown fields.
    """
    if api_provider == CUSTOM_PROVIDER:
        if os.getenv('SIRIN_CUSTOM_JUDGE_THINKING') == '1':
            return None
        return {'chat_template_kwargs': {'enable_thinking': False}}
    if api_provider == OPENROUTER_PROVIDER:
        return openrouter_reasoning_extra_body(model)
    return None


def _build_uncertainty(
    level: str,
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    uncertainty_threshold: float | None = None,
    uncertainty_max_new_tokens: int | None = None,
    uncertainty_threshold_source: str | None = None,
    methods: list[str] | None = None,
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

    extractor = _uncertainty_adapter(device, generator_adapter)
    feature_config = UncertaintyFeatureProcessorConfig(
        uncertainty_methods=methods
        or (_TOK_UNC_METHODS if level == 'token' else _SEQ_UNC_METHODS),
        model_kwargs={'instruct': True},  # apply the chat template inside lm-polygraph
        max_new_tokens=uncertainty_max_new_tokens or 256,
        # Demo convention (same as the stream path and the judges): thinking off. A Qwen3
        # otherwise spends the whole budget inside <think>, and the truncated reasoning
        # becomes the scored generation — token alignment then fails outright.
        chat_template_kwargs={'enable_thinking': False},
    )
    detector_config = UncertaintyDetectorConfig(aggregation_method='mean')
    if level == 'token':
        processor = TokenUncertaintyFeatureProcessor(
            config=feature_config, extractor=extractor
        )
        detector = TokenUncertaintyDetector(
            config=detector_config, feature_processor=processor
        )
    else:
        processor = SequenceUncertaintyFeatureProcessor(
            config=feature_config, extractor=extractor
        )
        detector = SequenceUncertaintyDetector(
            config=detector_config, feature_processor=processor
        )
    detector = _tag(
        detector,
        'uncertainty',
        level,
        calibrated=False,
        display_mode='heatmap' if level == 'token' else 'raw',
    )
    detector._ui_threshold = uncertainty_threshold
    if uncertainty_threshold is not None:
        detector.threshold = float(uncertainty_threshold)
        detector._ui_threshold_source = uncertainty_threshold_source
    return detector


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


def _build_uncertainty_sequence_msp(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    **kwargs: Any,
) -> Any:
    # MaximumSequenceProbability only. Never wire a generation_trace to this preset: the sequence
    # detector's trace fast-path supports MeanTokenEntropy/Perplexity only. The UI never passes one.
    return _build_uncertainty(
        'sequence',
        methods=_SEQ_UNC_METHODS_MSP,
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


def _build_openai_sequence_judge(
    *,
    user_prompt: str,
    task: str,
    dialogue_format: str | None = None,
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

    model_path, api_key, base_url = _resolve_judge(
        judge_model, judge_api_key, api_provider
    )
    model = OpenAIModelAdapter(
        OpenAIConfig(
            model_path=model_path,
            api_key=api_key,
            base_url=base_url,
            extra_body=_judge_extra_body(api_provider, model_path),
        )
    )
    # temperature 0 keeps the verdict deterministic; verdict_max_tokens=512 lets the hosted demo's
    # reasoning judges think before the digit (UI-only; scripts stay at 1).
    config_kwargs: dict[str, Any] = dict(
        user_prompt=user_prompt, temperature=0.0, verdict_max_tokens=512
    )
    if dialogue_format is not None:
        config_kwargs['dialogue_format'] = dialogue_format
    judge = SequenceOpenAIJudge(
        config=OpenAIJudgeConfig(**config_kwargs), model_adapter=model
    )
    return _tag(
        judge, 'judge', 'sequence', calibrated=False, display_mode='verdict', task=task
    )


def _build_openai_judge(**kwargs: Any) -> Any:
    return _build_openai_sequence_judge(
        user_prompt=_JUDGE_PROMPT,
        task=DetectionTaskType.HALLUCINATION_DETECTION.value,
        **kwargs,
    )


def _build_openai_verbalized_judge(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    **kwargs: Any,
) -> Any:
    # For endpoints that expose no logprobs (common on OpenRouter free routes): the judge
    # states its own confidence next to the label, so a score exists where the logprob
    # protocol would honestly show none. Coarser than a logprob — prefer the plain
    # sequence judge when the provider returns logprobs.
    from sirin.detection.judging import SequenceOpenAIVerbalizedJudge
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.detection import OpenAIJudgeConfig
    from sirin.models.inference import OpenAIConfig

    model_path, api_key, base_url = _resolve_judge(
        judge_model, judge_api_key, api_provider
    )
    model = OpenAIModelAdapter(
        OpenAIConfig(
            model_path=model_path,
            api_key=api_key,
            base_url=base_url,
            extra_body=_judge_extra_body(api_provider, model_path),
        )
    )
    judge = SequenceOpenAIVerbalizedJudge(
        # temperature 0 keeps the verdict deterministic; 512 tokens let reasoning judges
        # think before the "<label> <confidence>" pair (UI-only; scripts stay at 16).
        config=OpenAIJudgeConfig(temperature=0.0, verdict_max_tokens=512),
        model_adapter=model,
    )
    return _tag(
        judge,
        'judge',
        'sequence',
        calibrated=False,
        display_mode='verdict',
        task=DetectionTaskType.HALLUCINATION_DETECTION.value,
    )


def _build_openai_answerability_judge(**kwargs: Any) -> Any:
    # Same sequence judge, but scores a context+question (no answer) for answerability. The UI's
    # Task=Answerability flow feeds build_sample(context+question, '') so the judge never sees an
    # answer that isn't there; polarity is 1 == not answerable (see _ANSWERABILITY_JUDGE_PROMPT).
    # dialogue_format='{question}' feeds the context+question straight through: the default
    # 'Question: … Answer: {answer}' wrapper would append an empty 'Answer:' trailer (there is no
    # answer) and nest a second 'Question:' label, which measurably worsened the offline AUC.
    return _build_openai_sequence_judge(
        user_prompt=_ANSWERABILITY_JUDGE_PROMPT,
        task=DetectionTaskType.QUERY_ANSWERABILITY.value,
        dialogue_format='{question}',
        **kwargs,
    )


def _build_openai_claim_judge(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    judge_model: str | None = None,
    judge_api_key: str | None = None,
    api_provider: str = OPENROUTER_PROVIDER,
    **kwargs: Any,
) -> Any:
    from sirin.definitions import AggregationMethod, SplitStrategy
    from sirin.detection.judging import ClaimOpenAIJudge
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.detection import OpenAIJudgeConfig, SplitConfig
    from sirin.models.inference import OpenAIConfig

    model_path, api_key, base_url = _resolve_judge(
        judge_model, judge_api_key, api_provider
    )
    model = OpenAIModelAdapter(
        OpenAIConfig(
            model_path=model_path,
            api_key=api_key,
            base_url=base_url,
            extra_body=_judge_extra_body(api_provider, model_path),
        )
    )
    judge = ClaimOpenAIJudge(
        # Faithfulness prompt: each atomic claim is judged (0/1) against the context as its own
        # one-line "answer". temperature 0 keeps every per-claim verdict deterministic.
        config=OpenAIJudgeConfig(user_prompt=_JUDGE_PROMPT, temperature=0.0),
        model_adapter=model,
        # ATOMIC splitter decomposes the answer into self-contained claims via the SAME API adapter
        # (split_model defaults to model_adapter) — no local model, no extra plumbing. VOTE (majority
        # of per-claim verdicts) is the response summary: it stays meaningful even when a provider
        # returns no logprobs and the per-claim score is nan (the verdict digits still vote).
        response_splitter_config=SplitConfig(
            strategy=SplitStrategy.ATOMIC,
            aggregation_method=AggregationMethod.VOTE,
            split_response=True,
            temperature=0.0,
        ),
    )
    judge = _tag(judge, 'judge', 'claim', calibrated=False, display_mode='claim-cards')
    judge._ui_judge_provider = api_provider
    judge._ui_judge_model = model_path
    return judge


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
    from sirin.detection.judging.judges.utils.prompts import (
        SPAN_TAG_SYSTEM_PROMPT,
        SPAN_TAG_USER_PROMPT,
    )
    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.detection import OpenAIJudgeConfig
    from sirin.models.inference import OpenAIConfig

    model_path, api_key, base_url = _resolve_judge(
        judge_model, judge_api_key, api_provider
    )
    model = OpenAIModelAdapter(
        OpenAIConfig(
            model_path=model_path,
            api_key=api_key,
            base_url=base_url,
            extra_body=_judge_extra_body(api_provider, model_path),
        )
    )
    judge = TokenOpenAIJudge(
        # Span-tag prompts make the model echo the answer verbatim with [SPAN]…[/SPAN] around
        # hallucinated parts (the 0/1 verdict prompt emitted no tags -> always all-clear).
        # temperature > 0 so the num_beams generations DIFFER — a character's score is their
        # span-tag agreement (a [0,1] consensus). At temperature 0 the consensus collapses to a
        # single deterministic 0/1 pass.
        config=OpenAIJudgeConfig(
            system_prompt=SPAN_TAG_SYSTEM_PROMPT,
            user_prompt=SPAN_TAG_USER_PROMPT,
            temperature=0.7,
            # 3 samples matches the campaign protocol (temp 0.7, 3 samples) and halves per-click
            # cost/latency vs the default 5 on providers that ignore n>1 (each vote is one request
            # on OpenRouter free routes).
            num_beams=3,
        ),
        model_adapter=model,
    )
    # calibrated=True: the char scores are already fraction-in-[0,1], so show them absolute (a clean
    # answer reads all-clear) instead of min-max-stretching a near-binary array to a misleading mid-grey.
    judge = _tag(judge, 'judge', 'token', calibrated=True, display_mode='heatmap')
    # Honest disclosure fields for the run record (NEVER the base_url or the api key).
    judge._ui_judge_provider = api_provider
    judge._ui_judge_model = model_path
    return judge


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
        config=ProbingDetectorConfig(device=device, max_length=1),
        feature_processor=processor,
    )
    detector.load(checkpoint_dir)
    return _tag(detector, 'probing', 'sequence', calibrated=False, display_mode='gauge')


def load_psiloqa_probe_manifest(
    checkpoint_dir: str | None = None,
    *,
    model_id: str = PSILOQA_MODEL_ID,
    model_revision: str = PSILOQA_MODEL_REVISION,
) -> dict[str, Any]:
    checkpoint = Path(checkpoint_dir or PSILOQA_CHECKPOINT_DIR)
    manifest_path = checkpoint / 'manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'PsiloQA probe manifest not found: {manifest_path}')
    manifest = json.loads(manifest_path.read_text())
    expected = {
        'detector': 'token_linear_probe',
        'model_id': model_id,
        'model_revision': model_revision,
        'use_chat_template': False,
        'checkpoint_format': 'sirin_token_linear_v1',
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(
                f'Invalid PsiloQA probe manifest {key}: expected {value!r}, '
                f'got {manifest.get(key)!r}'
            )
    int(manifest['hidden_state_index'])
    float(manifest['threshold'])
    return manifest


def _build_token_linear_probe(
    model_id: str,
    model_revision: str,
    default_checkpoint: str,
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    **kwargs: Any,
) -> Any:
    """Build a locked live PsiloQA token-linear probe; layer and threshold come from its manifest."""
    from sirin.definitions import SideType
    from sirin.detection.probing import TokenLinearProbingDetector
    from sirin.detection.processors import HiddensProcessor
    from sirin.inference.adapters import HfModelAdapter
    from sirin.models.detection import HiddensProcessorConfig, ProbingDetectorConfig
    from sirin.models.inference import HFConfig, TokenLocatorConfig

    checkpoint = checkpoint_dir or default_checkpoint
    manifest = load_psiloqa_probe_manifest(
        checkpoint, model_id=model_id, model_revision=model_revision
    )
    adapter_config = getattr(generator_adapter, 'config', None)
    if (
        getattr(adapter_config, 'model_path', None) == model_id
        and getattr(adapter_config, 'revision', None) == model_revision
        and getattr(adapter_config, 'use_chat_template', None) is False
    ):
        extractor = generator_adapter
    else:
        extractor = HfModelAdapter(
            HFConfig(
                model_path=model_id,
                revision=model_revision,
                device=device,
                model_dtype='bf16',
                attn_implementation='sdpa',
                use_chat_template=False,
                padding='longest',
                padding_side='right',
            )
        )
    processor = HiddensProcessor(
        config=HiddensProcessorConfig(
            layers=[int(manifest['hidden_state_index'])],
            side=SideType.RIGHT,
            pooling_type='none',
            cache_features=False,
            token_locator_config=TokenLocatorConfig(locate_answer_start=True),
        ),
        extractor=extractor,
    )
    detector = TokenLinearProbingDetector(
        config=ProbingDetectorConfig(
            device=device,
            batch_size=1,
            threshold=float(manifest['threshold']),
        ),
        feature_processor=processor,
    )
    detector.load(checkpoint)
    detector.threshold = float(manifest['threshold'])
    detector._ui_threshold = detector.threshold
    detector._ui_threshold_source = str(manifest.get('threshold_method') or 'manifest')
    detector._ui_score_semantics = str(manifest.get('score_semantics') or '')
    detector._ui_manifest = manifest
    return _tag(
        detector,
        'probing',
        'token',
        calibrated=False,
        display_mode='threshold-spans',
    )


def _build_probing_token_linear_psiloqa(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    **kwargs: Any,
) -> Any:
    return _build_token_linear_probe(
        PSILOQA_MODEL_ID,
        PSILOQA_MODEL_REVISION,
        PSILOQA_CHECKPOINT_DIR,
        device=device,
        checkpoint_dir=checkpoint_dir,
        generator_adapter=generator_adapter,
        **kwargs,
    )


def _build_probing_token_linear_psiloqa_qwen35(
    *,
    device: str = 'cuda',
    checkpoint_dir: str | None = None,
    generator_adapter: Any = None,
    **kwargs: Any,
) -> Any:
    return _build_token_linear_probe(
        PSILOQA_QWEN35_MODEL_ID,
        PSILOQA_QWEN35_MODEL_REVISION,
        PSILOQA_QWEN35_CHECKPOINT_DIR,
        device=device,
        checkpoint_dir=checkpoint_dir,
        generator_adapter=generator_adapter,
        **kwargs,
    )


def _hf_hidden_size(model_path: str) -> int | None:
    if not model_path:
        return None
    try:
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(model_path, trust_remote_code=False)
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
        or ANSWERABILITY_CHECKPOINT_DIR
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
    return _tag(
        detector,
        'probing',
        'sequence',
        calibrated=False,
        display_mode='gauge',
        task=DetectionTaskType.QUERY_ANSWERABILITY.value,
    )


PRESETS: dict[str, Preset] = {
    "Probing — Sequence TabPFN (checkpoint)": Preset(
        name="Probing — Sequence TabPFN (checkpoint)",
        family='probing',
        level='sequence',
        calibrated=False,
        requires_checkpoint=True,
        description="TabPFN hidden-state probe — raw score with a validation-selected decision threshold. Needs a trained checkpoint directory.",
        build=_build_probing_sequence_tabpfn,
        display_mode='gauge',
        is_judge=False,
    ),
    PSILOQA_TOKEN_LINEAR_PRESET: Preset(
        name=PSILOQA_TOKEN_LINEAR_PRESET,
        family='probing',
        level='token',
        calibrated=False,
        requires_checkpoint=True,
        description=(
            'Live token linear probe on fresh Qwen3-4B hidden states for the curated '
            'PsiloQA span demo. Raw sigmoid score; not a calibrated probability.'
        ),
        build=_build_probing_token_linear_psiloqa,
        display_mode='threshold-spans',
        is_judge=False,
        builtin_checkpoint=PSILOQA_CHECKPOINT_DIR,
    ),
    PSILOQA_TOKEN_LINEAR_PRESET_QWEN35: Preset(
        name=PSILOQA_TOKEN_LINEAR_PRESET_QWEN35,
        family='probing',
        level='token',
        calibrated=False,
        requires_checkpoint=True,
        description=(
            'Live token linear probe on fresh Qwen3.5-4B hidden states for the curated '
            'PsiloQA span demo. Raw sigmoid score; not a calibrated probability.'
        ),
        build=_build_probing_token_linear_psiloqa_qwen35,
        display_mode='threshold-spans',
        is_judge=False,
        builtin_checkpoint=PSILOQA_QWEN35_CHECKPOINT_DIR,
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
        census_caption='MeanTokenEntropy + Perplexity · relative within-answer, uncalibrated',
    ),
    "Uncertainty — Sequence · Sequence Probability (zero-shot)": Preset(
        name="Uncertainty — Sequence · Sequence Probability (zero-shot)",
        family='uncertainty',
        level='sequence',
        calibrated=False,
        requires_checkpoint=False,
        description=(
            'Single greedy-pass sequence log-probability (MaximumSequenceProbability). Raw, '
            'length-sensitive score comparable only within one answer; not a calibrated probability. '
            'No training.'
        ),
        build=_build_uncertainty_sequence_msp,
        display_mode='raw',
        is_judge=False,
        census_caption='MaximumSequenceProbability · raw sequence log-prob, uncalibrated',
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
        census_caption='MaximumTokenProbability + TokenEntropy · relative within-answer, uncalibrated',
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
        census_caption='single-digit hallucination verdict · one judge pass, not calibrated',
    ),
    "Judge — API Answerability (zero-shot)": Preset(
        name="Judge — API Answerability (zero-shot)",
        family='judge',
        level='sequence',
        calibrated=False,
        requires_checkpoint=False,
        description="LLM-as-judge answerability verdict (context + question, no answer) via the OpenAI/OpenRouter API. No training.",
        build=_build_openai_answerability_judge,
        task=DetectionTaskType.QUERY_ANSWERABILITY.value,
        display_mode='verdict',
        is_judge=True,
        census_caption='single-digit answerability verdict · one judge pass, not calibrated',
    ),
    "Judge — API Claim (zero-shot)": Preset(
        name="Judge — API Claim (zero-shot)",
        family='judge',
        level='claim',
        calibrated=False,
        requires_checkpoint=False,
        description="LLM-as-judge claim-level faithfulness via the OpenAI/OpenRouter API: the answer is split into atomic claims and each is judged against the context. No training.",
        build=_build_openai_claim_judge,
        display_mode='claim-cards',
        is_judge=True,
        census_caption='per-claim faithfulness verdicts · atomic-fact split, not calibrated',
    ),
    "Judge — API Span (zero-shot)": Preset(
        name="Judge — API Span (zero-shot)",
        family='judge',
        level='token',
        calibrated=True,
        requires_checkpoint=False,
        description="Per-character hallucination heatmap via the OpenAI/OpenRouter API (span-tag agreement across sampled generations). No training.",
        build=_build_openai_token_judge,
        display_mode='heatmap',
        is_judge=True,
        census_caption='verbatim span-tag annotation · k/n consensus, not calibrated',
    ),
    "Judge — API Sequence (verbalized confidence)": Preset(
        name="Judge — API Sequence (verbalized confidence)",
        family='judge',
        level='sequence',
        calibrated=False,
        requires_checkpoint=False,
        description="LLM-as-judge verdict with self-stated confidence 0-100 — works on endpoints without logprobs. No training.",
        build=_build_openai_verbalized_judge,
        display_mode='verdict',
        is_judge=True,
        census_caption='verdict + self-stated confidence · one judge pass, not calibrated',
    ),
    "Probing — Answerability TabPFN (checkpoint)": Preset(
        name="Probing — Answerability TabPFN (checkpoint)",
        family='probing',
        level='sequence',
        calibrated=False,
        requires_checkpoint=True,
        description="Answerability TabPFN hidden-state probe — raw thresholded score, not a calibrated probability.",
        build=_build_probing_answerability,
        task=DetectionTaskType.QUERY_ANSWERABILITY.value,
        display_mode='gauge',
        is_judge=False,
    ),
}


def list_presets() -> list[Preset]:
    return list(PRESETS.values())


# Every non-judge preset with a bundled recorded result (landing seed or recorded-run
# asset) — hosted visitors select these and replay the verified recording; live scoring
# needs weights/checkpoints the CPU Space does not ship. tests/test_ui_hosted.py pins
# this list against the actually bundled assets (no false availability). Deliberately
# absent: 'Probing — Answerability TabPFN (checkpoint)' — its external checkpoint cannot
# currently be loaded faithfully (its pipeline needs a tabpfn SquashingScaler no
# installable build reproduces), so it has no honest recording to serve.
HOSTED_REPLAY_PRESETS: tuple[str, ...] = (
    'Probing — Sequence TabPFN (checkpoint)',
    PSILOQA_TOKEN_LINEAR_PRESET,
    PSILOQA_TOKEN_LINEAR_PRESET_QWEN35,
    'Uncertainty — Sequence (zero-shot)',
    'Uncertainty — Sequence · Sequence Probability (zero-shot)',
    'Uncertainty — Token (zero-shot)',
)


def visible_presets() -> list[Preset]:
    """Presets offered by the UI.

    Hosted (CPU, public) profile: the API judges run live; every preset in
    ``HOSTED_REPLAY_PRESETS`` is selectable as REPLAY-ONLY — its landing card and Replay
    serve the verified recorded result (the Space bundles neither weights nor a GPU).
    """
    if is_hosted():
        visible = [
            p for p in list_presets()
            if p.family == 'judge' or p.name in HOSTED_REPLAY_PRESETS
        ]
        return _verbalized_sequence_first(visible)
    return list_presets()


def _verbalized_sequence_first(visible: list[Preset]) -> list[Preset]:
    """Lead the sequence-judge pair with the verbalized judge (hosted only).

    The free OpenRouter route often returns no logprobs, so the plain (class-token)
    sequence judge honestly shows a verdict with no score. The verbalized judge always
    yields an autoregressive 0-100 confidence, so a visitor who reaches for a sequence
    judge lands on one that scores. Only reorders within the judge group — the span judge
    stays the sidebar default and the replay-only presets keep their order.
    """
    names = [p.name for p in visible]
    if JUDGE_SEQUENCE_VERBALIZED_PRESET in names and JUDGE_SEQUENCE_PRESET in names:
        verbal = names.index(JUDGE_SEQUENCE_VERBALIZED_PRESET)
        plain = names.index(JUDGE_SEQUENCE_PRESET)
        if verbal > plain:
            visible.insert(plain, visible.pop(verbal))
    return visible


def hosted_replay_only(preset_family: str) -> bool:
    """True when the active preset cannot score live on the hosted profile.

    Non-judge presets need local model weights (and probes their checkpoints), neither of
    which ships with the CPU Space — they serve their recorded seed results instead.
    """
    return is_hosted() and preset_family != 'judge'


def _preset_layer_threshold(
    preset: Preset, checkpoint_dir: str | None
) -> tuple[int | None, float | None]:
    """Layer and decision threshold a preset statically exposes, without loading the model.

    Only the PsiloQA token-linear probes publish a single hidden-state layer and threshold (via their
    manifest); every other preset resolves them at build time, so returns ``(None, None)`` here.
    """
    spec = PSILOQA_TOKEN_LINEAR_PRESETS.get(preset.name)
    if spec is None:
        return None, None
    model_id, model_revision, default_checkpoint = spec
    source = checkpoint_dir or preset.builtin_checkpoint or default_checkpoint
    try:
        manifest = load_psiloqa_probe_manifest(
            source, model_id=model_id, model_revision=model_revision
        )
        return int(manifest['hidden_state_index']), float(manifest['threshold'])
    except Exception:
        return None, None


def detector_census_caption(preset: Preset, checkpoint_dir: str | None = None) -> str:
    """One-line sidebar census meta in the recovered demo's language.

    Shows only facts the preset actually provides: the resolved probe layer, its decision threshold,
    and (for a bundled, integrity-checked checkpoint) the SHA-256 provenance. Returns '' when a preset
    has nothing census-worthy to add, so the caller can fall back to the preset description.
    """
    parts: list[str] = []
    layer, threshold = _preset_layer_threshold(preset, checkpoint_dir)
    if layer is not None:
        parts.append(f'layer {layer}')
    if threshold is not None:
        parts.append(f'τ = {threshold:.2f}')
    if preset.builtin_checkpoint:
        parts.append('bundled checkpoint')
    # Presets with no dynamic checkpoint meta (uncertainty/judge) carry a static one-line method truth.
    return ' · '.join(parts) or (getattr(preset, 'census_caption', None) or '')


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
        'threshold': getattr(
            detector, '_ui_threshold', getattr(detector, 'threshold', None)
        ),
        'threshold_source': getattr(detector, '_ui_threshold_source', None),
        'task': getattr(
            detector,
            '_ui_task',
            DetectionTaskType.HALLUCINATION_DETECTION.value,
        ),
    }
