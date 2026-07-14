from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, Literal

import torch

from sirin.definitions import (
    ClassificationMetric,
    CompressionMethod,
    ScalingMethod,
    SideType,
    TokenLocation,
    SplitStrategy,
    AggregationMethod,
)
from sirin.models.inference import ModelManagerConfig, TokenLocatorConfig, CleanerConfig

if TYPE_CHECKING:
    from peft import PeftConfig


@dataclass
class TrainingHistory:
    """Per-epoch training curves from a single training run."""

    epochs: List[int] = field(default_factory=list)
    train_loss: List[float] = field(default_factory=list)
    learning_rate: List[float] = field(default_factory=list)
    val_epochs: List[int] = field(default_factory=list)
    val_loss: List[float] = field(default_factory=list)
    val_metrics: Dict[str, List[float]] = field(default_factory=dict)
    contrastive: Dict[str, List[float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, List[float]]:
        """Return flat dict compatible with the legacy plotting utilities."""
        d: Dict[str, Any] = {
            'epoch': self.epochs,
            'train_loss': self.train_loss,
            'learning_rate': self.learning_rate,
            'val_epochs': self.val_epochs,
            'val_loss': self.val_loss,
        }
        for metric, values in self.val_metrics.items():
            d[f"val_{metric}"] = values
        d.update(self.contrastive)
        return d


@dataclass
class DetectionResult:
    """Result of a detection evaluation or training run.

    All fields are flat and optional – no phase-keyed nesting.
    ``history`` is only populated for training runs.
    """

    metrics: Optional[Dict[str, float]] = None
    probs: Optional[List[float]] = None
    labels: Optional[List[float]] = None
    threshold: float = 0.5
    history: Optional[TrainingHistory] = None

    def get_metric(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Return a single metric by name."""
        return (self.metrics or {}).get(name, default)

    def to_dict(self) -> Dict[str, Any]:
        return {'metrics': self.metrics, 'threshold': self.threshold}


@dataclass
class SplitConfig:
    strategy: SplitStrategy
    chunk_size: int = 1000
    overlap: int = 0
    split_response: bool = False
    aggregation_method: AggregationMethod = AggregationMethod.MEAN
    sentence_delimiters: List[str] = None
    num_sentences: int = 1
    num_paragraphs: int = 1
    paragraph_delimiters: List[str] = None
    langchain_splitter_type: Optional[str] = None
    langchain_splitter_kwargs: Optional[Dict[str, Any]] = None
    batch_size: Optional[int] = None
    max_tokens: int = 4096
    temperature: float = 0.1
    prefix: Optional[str] = None
    stop_tokens: Optional[List[str]] = None
    enable_high_recall: bool = True
    prompt: Optional[str] = """
    You must output EXACTLY one JSON object and NOTHING ELSE.
    The output MUST start with '{{' and end with '}}'.
    The JSON must contain a single key: "atomic_facts".

    "atomic_facts" MUST be a JSON array of declarative sentences.
    Each sentence MUST be a single atomic fact explicitly stated or directly entailed by the input.
    No commentary, no markdown, no code fences.

    Example:
    {{
      "atomic_facts": [
        "First fact.",
        "Second fact."
      ]
    }}

    INPUT:
    {text}
"""


@dataclass
class BertScoreConfig:
    """Configuration for BertScore metric calculation."""

    model_path: str
    batch_size: int = 32
    nthreads: int = 4
    device: Optional[str] = None
    lang: str = 'en'


@dataclass
class LmMetricsConfig:
    """Configuration for which metrics to calculate."""

    rouge: bool = False
    bleu: bool = False
    meteor: bool = False
    ter: bool = False
    bert_score: Optional[BertScoreConfig] = None


@dataclass
class SamplingConfig:
    """Configuration for text generation sampling."""

    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 50
    max_length: int = 512
    min_length: int = 1
    do_sample: bool = True
    num_beams: int = 1
    kwargs: Dict[str, Any] = field(default_factory=dict)
    num_return_sequences: int = 1
    repetition_penalty: float = 1.0
    length_penalty: float = 1.0
    early_stopping: bool = False


@dataclass
class FeatureProcessorBaseConfig:
    """Base configuration for feature processors."""

    cache_features: bool = True
    feature_cache_dir: Optional[str] = None
    max_features: Optional[int] = None
    normalize_features: bool = False
    token_locator_config: TokenLocatorConfig = field(default_factory=TokenLocatorConfig)
    separate: bool = True
    side: SideType = field(default=SideType.RIGHT)
    pooling_type: Literal['mean', 'last', 'max', 'none'] = 'none'
    padding: Union[bool, str] = False
    truncation: bool = False
    max_length: Optional[int] = None
    feature_extraction_batch_size: int = 1


@dataclass
class DetectorBaseConfig:
    """Base configuration for detectors."""

    model_save_path: Optional[str] = None
    model_load_path: Optional[str] = None
    checkpoint_path: Optional[str] = None
    threshold: float = 0.5
    device: str = 'cuda'
    seed: int = 42
    num_cpus: int = 1
    use_multiprocessing: bool = True
    batch_size: int = 1
    kwargs: Dict[str, Any] = field(default_factory=dict)
    threshold_method: Literal['percentile', 'fixed', 'optimal', 'f1_optimal', 'prior'] = 'optimal'
    threshold_percentile: float = 0.5
    fixed_threshold: float = 0.5
    num_classification_heads: int = 1
    context_split_config: Optional[SplitConfig] = None
    classification_metrics: Optional[List[ClassificationMetric]] = None


@dataclass
class PipelineBaseConfig:
    """Base configuration for pipeline."""

    _target_: str = ''
    save_dir: str = './outputs'
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    model_manager: ModelManagerConfig = field(default_factory=ModelManagerConfig)
    lm_metrics: Optional[LmMetricsConfig] = None
    classification_metrics: Optional[List[ClassificationMetric]] = None
    cleaner_configs: Optional[List[CleanerConfig]] = None
    save_intermediate: bool = True
    experiment_name: Optional[str] = None
    f_beta: float = 1.0
    split_context_train: bool = False
    shuffle_train: bool = False
    per_sample_metrics: bool = (
        False  # If True, calculate metrics per sample then average
    )


@dataclass
class JudgeBaseConfig(DetectorBaseConfig):
    """Base configuration for judges."""

    system_prompt: str = (
        "You are a precise hallucination detector for AI-generated dialogue. "
        "Your only task is to analyze the given user-assistant exchange and output "
        "a single binary digit: 1 if the assistant's response contains any factual "
        "inaccuracy, unsupported claim, or hallucinated content - 0 if it is fully "
        "grounded and correct. Do not explain, justify, or add any text. "
        "Output only '1' or '0'."
    )
    dialogue_format: str = "Question: {question}.\n Answer: {answer}"
    user_prompt: str = (
        "I give you a dialogue consisting of a user prompt and an assistant answer. "
        "Your task is to evaluate whether this dialogue contains hallucination. "
        'Answer only 0 or 1.\nDialogue: "{sample}".\n'
        "Respond with 1 if the assistant's answer contains hallucination, 0 otherwise: "
    )
    max_new_tokens: int = 2048
    # Completion budget for single-verdict judges: >1 lets reasoning models think before
    # the digit; default 1 preserves the strict one-token protocol (campaign scripts,
    # local vLLM).
    verdict_max_tokens: int = 1
    temperature: float = 1.0
    top_p: float = 1.0
    diversity_penalty: float = 1.0
    num_beam_groups: int = 5
    num_beams: int = 5


@dataclass
class HfJudgeConfig(JudgeBaseConfig):
    """Base configuration for Hf judges."""

    peft_config: Optional[PeftConfig] = None
    return_tensors: str = 'pt'


@dataclass
class OpenAIJudgeConfig(JudgeBaseConfig):
    """Base configuration for Open AI judges."""

    # Reasoning-era endpoints reject tiny completion budgets outright (GPT-5.x:
    # "Expected a value >= 16"), so API judges default higher than the base's strict
    # one-token protocol.
    verdict_max_tokens: int = 16
    # Read >2 alternatives so both class tokens usually appear even when the model is very
    # confident; when only one does, `probability_of_positive_class` degrades gracefully.
    top_logprobs: int = 5
    # Concurrency for the adapter's async batch path.
    max_concurrent: int = 10
    # Verbalized-confidence protocol (SequenceOpenAIVerbalizedJudge): models that expose
    # no logprobs still need a threshold-free score.
    confidence_system_prompt: str = (
        'You are a precise hallucination detector for AI-generated dialogue. Analyze the '
        'given user-assistant exchange and output exactly two space-separated values: a '
        'binary digit (1 if the assistant\'s response contains any factual inaccuracy, '
        'unsupported claim, or hallucinated content; 0 if it is fully grounded) followed '
        'by your confidence as an integer 0-100. Example: "1 87". Output nothing else.'
    )
    confidence_user_prompt: str = (
        'I give you a dialogue that consists of a user prompt and an assistant answer.\n'
        'Dialogue: "{sample}".\n'
        'Respond with the label (1 = hallucinated, 0 = grounded) and your confidence 0-100: '
    )


@dataclass
class JudgePipelineConfig(PipelineBaseConfig):
    """Configuration for probing pipeline."""

    _target_: str = 'sirin.detection.judging.JudgePipeline'


@dataclass
class HiddensProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for hidden states feature processor."""

    layers: Optional[List[int]] = None  # None means use all layers


@dataclass
class SublayersProcessorConfig(HiddensProcessorConfig):
    """Configuration for sublayers feature processor."""

    pass


@dataclass
class LogitsProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for logits feature processor."""

    normalize_logits: bool = False


@dataclass
class EnsembleProcessorConfig(FeatureProcessorBaseConfig):
    processor_configs: Optional[List[FeatureProcessorBaseConfig]] = None


@dataclass
class AttentionsProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for attention weights feature processor."""

    layers: Optional[List[int]] = None  # None means use all layers
    attention_heads: Optional[List[int]] = None  # None means use all heads


@dataclass
class LookbacksProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for lookbacks feature processor."""

    layers: Optional[List[int]] = None  # None means use all layers
    attention_heads: Optional[List[int]] = None  # None means use all heads
    border: Optional[TokenLocation] = field(default=TokenLocation.ANS_START)


@dataclass
class ModelStates:
    hiddens: Optional[List[Tuple[torch.Tensor]]] = None
    attentions: Optional[List[Tuple[torch.Tensor]]] = None
    locations: Optional[Union[List[Dict[str, Any]], List[List[Dict[str, Any]]]]] = None
    logits: Optional[torch.Tensor] = None
    sublayers: Optional[List[Tuple[torch.Tensor]]] = None
    token_hallucinations: Optional[List[List[int]]] = None
    logprobs: Optional[torch.Tensor] = None
    masks: Optional[torch.Tensor] = None


@dataclass
class CompressionConfig:
    """Configuration for feature compression and scaling."""

    method: CompressionMethod = CompressionMethod.NONE
    scaling_method: ScalingMethod = ScalingMethod.STANDARD
    threshold: int = 500
    target_dimensions: int = 300
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProbingDetectorConfig(DetectorBaseConfig):
    """Configuration for probing-based detector."""

    embedding_dim: Optional[List[int]] = None
    num_features: Optional[List[int]] = None
    attention_pooling: Optional[List[bool]] = None
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    dropout_rate: float = 0.1
    ensemble: Optional[List[int]] = None
    max_length: int = 128
    padding_side: str = 'right'
    truncation_side: str = 'right'

    # Contrastive learning parameters
    use_contrastive: bool = False
    projection_dim: int = 128
    contrastive_layers: Optional[List[int]] = None
    projection_hidden_dim: Optional[int] = None  # Default: projection_dim * 2
    projection_num_layers: int = 2
    use_projection_dropout: bool = False
    projection_dropout: float = 0.1


@dataclass
class TrainingArgsConfig:
    """Configuration for training arguments."""

    max_epochs: Optional[int] = 5
    validation_interval: int = 5
    val_size: Optional[float] = None
    step_size: Optional[int] = None
    device: Optional[str] = 'cuda'
    learning_rate: Optional[float] = 0.001
    max_learning_rate: Optional[float] = 1
    weight_decay: Optional[float] = 0
    metrics: Optional[List[ClassificationMetric]] = None
    target_metric: Optional[str] = None
    train_batch_size: Optional[int] = 256
    val_batch_size: Optional[int] = 256
    shuffle: Optional[bool] = None
    threshold: Optional[float] = 0.5
    alpha_start: Optional[float] = 1.0
    alpha_gamma: Optional[float] = 0.9
    loss_function: Optional[str] = 'bce'
    alpha_scheduler: Optional[str] = 'exp'
    beta: Optional[float] = 1.0
    weight: Optional[float] = 0.5
    gamma: Optional[float] = 0.5
    threshold_method: str = 'optimal'
    threshold_percentile: float = 0.5
    fixed_threshold: float = 0.5

    # Contrastive learning parameters
    use_contrastive: bool = False
    contrastive_loss_type: str = (
        'supervised'  # 'supervised', 'triplet', 'infonce', 'circle', 'hard_negative'
    )
    contrastive_weight: float = 0.5
    contrastive_temperature: float = 0.07
    contrastive_margin: float = 0.3
    use_hard_negative_mining: bool = True
    hard_negative_weight: float = 2.0
    hard_mining_ratio: float = 0.3
    triplet_mining_strategy: str = 'hard'  # 'hard', 'semi-hard', 'all'
    circle_loss_gamma: float = 256
    zero_bce: bool = False
    use_lr_scheduler: bool = False
    log_contrastive_metrics: bool = True  # Log contrastive-learning metrics


@dataclass
class ProbingPipelineConfig(PipelineBaseConfig):
    """Configuration for probing pipeline."""

    _target_: str = 'sirin.detection.probing.ProbingPipeline'
    train_args: TrainingArgsConfig = field(default_factory=TrainingArgsConfig)


@dataclass
class UncertaintyFeatureProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for uncertainty feature processor"""

    uncertainty_methods: Optional[List[str]] = None
    # Constructor arguments per estimator, e.g. {"Focus": {"gamma": 0.9, ...}}. Focus has
    # no defaults (IDF corpus, spaCy model), so listing it without kwargs raises TypeError.
    method_kwargs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    max_new_tokens: int = 256
    openai_api_key: Optional[str] = None
    supports_logprobs: bool = True
    top_logprobs: int = 5
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    output_attentions: bool = False  # Auto-enabled when RAUQ/Focus/AttentionScore in methods
    # Score the assistant turn already present in the sample instead of letting the
    # model regenerate one. Required when the label refers to the stored response.
    teacher_forced: bool = False
    # Extra kwargs for tokenizer.apply_chat_template, e.g. {"enable_thinking": False}.
    chat_template_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UncertaintyDetectorConfig(DetectorBaseConfig):
    """Configuration for uncertainty detector"""

    threshold_percentile: float = 0.8
    fixed_threshold: float = 0.5
    # "auto" selects the estimator subset + aggregation on the train split by ROC-AUC
    # instead of fixing them a priori; see SequenceUncertaintyDetector.fit_score_selection.
    aggregation_method: Literal['mean', 'max', 'min', 'weighted', 'auto'] = 'mean'
    method_weights: Optional[Dict[str, float]] = None
    # Estimators live on incompatible scales (MeanTokenEntropy ~1e-2, RAUQ ~3,
    # Focus ~10), so aggregating raw scores lets the largest-scale one dominate.
    # Normalize each estimator first, with statistics fit on train (no labels used).
    #   zscore  standardize by train mean/std
    #   rank    map onto the train-empirical CDF -> [0, 1] (scale-free, outlier-robust)
    # Ignored for a single estimator, where aggregation is the identity.
    score_normalization: Literal['none', 'zscore', 'rank'] = 'none'


@dataclass
class MTopDivProcessorConfig(FeatureProcessorBaseConfig):
    """Configuration for MTopDiv feature processor."""

    n_jobs: Optional[int] = None
    zero_out: str = 'prompt'  # whether to zero out distances between prompt tokens or response tokens
    heads_to_analyze: Optional[Tuple[int, int]] = (
        None  # [(layer_index, head_index), ...]
    )
    critical_size: Optional[int] = (
        None  # limits n_jobs to 1 if sample_size > critical_size
    )
    normalize_by_length: Optional[bool] = (
        True  # whether to divide the obtained MTopDiv values by the length of the response or prompt (depending on which is zeroed out)
    )
    separate_token: Optional[str] = None
    layers: Optional[List[int]] = None
