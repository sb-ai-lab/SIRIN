# SKILL.md — SIRIN Framework Reference

This file provides a comprehensive reference for LLMs to operate with the SIRIN framework.

## Overview

**SIRIN** (Semantic Inconsistency Recognition and Inspection Nexus) detects hallucinations and query answerability in LLMs at sequence and token levels. Three detection paradigms:

1. **Probing** — Train lightweight classifiers (TabPFN, CatBoost, Linear) on frozen LLM internal features (hidden states, attention, logits)
2. **Judge** — Fine-tune LoRA adapters on LLM representations, or use API-based judges
3. **Uncertainty** — Leverage uncertainty signals from lm-polygraph (entropy, perplexity, spectral methods)

Python >=3.11, <3.13. Single quotes for strings, double quotes for docstrings.

---

## Architecture

### Inheritance Hierarchy

```
DetectorBase (ABC)
├── ProbingDetectorBase
│   ├── Sequence{Linear,Catboost,TabPFN}ProbingDetector
│   ├── Token{Linear,Catboost,TabPFN}ProbingDetector
│   └── Claim{Linear,Catboost,TabPFN}ProbingDetector
├── HfJudgeBase / OpenAIJudgeBase
│   ├── Sequence{Decoder,Encoder,OpenAI}Judge
│   └── Token{Decoder,Encoder,OpenAI}Judge
└── UncertaintyDetectorBase
    ├── SequenceUncertaintyDetector
    └── TokenUncertaintyDetector

PipelineBase (ABC)
├── ProbingPipeline
├── JudgePipeline
└── UncertaintyPipeline

ModelAdapterBase (ABC)
├── HfModelAdapter
├── OpenAIModelAdapter
└── VllmModelAdapter

FeatureProcessorBase (ABC)
├── HiddensProcessor
│   ├── AttentionsProcessor
│   ├── LogitsProcessor
│   ├── LookbacksProcessor
│   ├── SublayersProcessor
│   └── TokenUncertaintyFeatureProcessor
├── SequenceUncertaintyFeatureProcessor
└── EnsembleProcessor

LoggerBase (ABC)
├── WandbLogger, TensorBoardLogger, ClearMLLogger, CometLogger, MultipleLoggers

BaseCleaner (ABC)
├── RegexCleaner, HTMLCleaner, CodeCleaner, CustomCleaner

TargetApproximatorBase (ABC)
└── SEPTargetApproximator

TextSplitterBase (ABC)
├── SentenceSplitter, ParagraphSplitter, CharacterSplitter, LangChainSplitter, ClaimSplitter
```

### Training Dataflow

```
ConfigManager.build_pipeline()
  → ModelAdapter (HF/vLLM/OpenAI)
  → FeatureProcessor (Hiddens/Attention/Ensemble/...)
  → Detector (Probing/Judge/Uncertainty)
  → Pipeline (Probing/Judge/Uncertainty)

Pipeline.train():
  1. Load dataset (HuggingFace format)
  2. Generate missing assistant answers (if needed)
  3. Clean outputs (regex, html, code cleaners)
  4. Compute LM metrics (ROUGE, BLEU, BertScore)
  5. Split context (sentence/paragraph/character) if configured
  6. Extract features via FeatureProcessor → ModelStates
  7. Train detector meta-model
  8. Return TrainerOutput with metrics + threshold
```

### Inference Dataflow

```
detector.detect(sample)
  → feature_processor(sample)
    → extractor.generate_hiddens() → ModelStates
    → token_locator.locate() → positions
    → postprocess (pool, compress, scale)
  → detector.model.predict() → probability
  → apply threshold → prediction
```

---

## Public API — Import Paths

### Detectors

```python
from sirin.detection.probing import (
    ProbingPipeline,
    SequenceLinearProbingDetector, SequenceCatboostProbingDetector, SequenceTabPFNProbingDetector,
    TokenLinearProbingDetector, TokenCatboostProbingDetector, TokenTabPFNProbingDetector,
    ClaimLinearProbingDetector, ClaimCatboostProbingDetector, ClaimTabPFNProbingDetector,
)

from sirin.detection.judging import (
    JudgePipeline,
    SequenceDecoderJudge, SequenceEncoderJudge, SequenceOpenAIJudge,
    TokenDecoderJudge, TokenEncoderJudge, TokenOpenAIJudge,
    HfJudgeBase, OpenAIJudgeBase,
)

from sirin.detection.uncertainty import (
    UncertaintyPipeline,
    SequenceUncertaintyDetector, TokenUncertaintyDetector,
)
```

### Feature Processors

```python
from sirin.detection.processors import (
    FeatureProcessorBase,
    HiddensProcessor, AttentionsProcessor, LogitsProcessor,
    LookbacksProcessor, SublayersProcessor,
    EnsembleProcessor, LayerFeatureCacheSaver,
    MTopDivFeatureProcessor,  # optional, may be None if deps unavailable
    SequenceUncertaintyFeatureProcessor, TokenUncertaintyFeatureProcessor,
)
```

### Model Adapters

```python
from sirin.inference.adapters import (
    ModelAdapterBase, HfModelAdapter, OpenAIModelAdapter, VllmModelAdapter,
)
from sirin.inference import ModelManager, HfTokenLocator
```

### Configs

```python
from sirin.models.detection import (
    # Detector configs
    DetectorBaseConfig, ProbingDetectorConfig, UncertaintyDetectorConfig,
    # Judge configs
    JudgeBaseConfig, HfJudgeConfig, OpenAIJudgeConfig,
    # Pipeline configs
    PipelineBaseConfig, ProbingPipelineConfig, JudgePipelineConfig,
    # Feature processor configs
    FeatureProcessorBaseConfig, HiddensProcessorConfig, SublayersProcessorConfig,
    LogitsProcessorConfig, AttentionsProcessorConfig, LookbacksProcessorConfig,
    EnsembleProcessorConfig, UncertaintyFeatureProcessorConfig, MTopDivProcessorConfig,
    # Training & output
    TrainingArgsConfig, TrainerOutput,
    # Supporting configs
    SplitConfig, CompressionConfig, SamplingConfig, ModelManagerConfig,
    LmMetricsConfig, BertScoreConfig,
    # Data containers
    ModelStates,
)

from sirin.models.inference import (
    ModelAdapterBaseConfig, HFConfig, VLLMConfig, OpenAIConfig,
    TokenLocatorConfig, CleanerConfig, ModelManagerConfig,
)
```

### Definitions

```python
from sirin.definitions import (
    # Enums
    ModelType, ModelAdapterType, DetectionTaskType, FeatureType,
    SplitStrategy, AggregationMethod, SideType, AggregationType,
    DetectionLevel, Phase, CompressionMethod, ScalingMethod,
    LmMetric, ClassificationMetric, TokenLocation, LogLevel,
    # Constants
    INPUT_COL, INPUT_PROC_COL, REFERENCE_COL, TARGET_COL,
    ANSWER_INDICES, OFFSETS_COL, GROUP_ID_COL,
    HF_TOKEN_ENV, OPENAI_API_KEY_ENV,
    GENERATED_DSET_KEY, CLEANED_DSET_KEY, DSET_KEY,
    METRICS_KEY, TORCH_MODULE_KEY, HIDDENS_FILE_KEY,
    ARTIFACTS_YAML, SAVE_FEAT_TEMPLATE,
    # Types
    TorchDtype,
)
```

### Loggers

```python
from sirin.loggers import (
    LoggerBase, WandbLogger, TensorBoardLogger,
    ClearMLLogger, CometLogger, MultipleLoggers,
)
```

### Splitters & Approximators

```python
from sirin.detection.splitters.splitter import SplitManager
from sirin.detection.approximators.sep import SEPTargetApproximator
```

### Cleaners

```python
from sirin.inference.cleaners import BaseCleaner, RegexCleaner, HTMLCleaner, CodeCleaner, CustomCleaner
```

### Metrics

```python
from sirin.metrics.classification import calculate_classification_metrics
from sirin.metrics.language import calculate_lm_metrics
```

### Classification Module

```python
from sirin.classification import LinearClassifier
```

---

## Config Reference

### DetectorBaseConfig

```python
@dataclass
class DetectorBaseConfig:
    model_name: str = 'default_detector'
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
    threshold_method: Literal['percentile', 'fixed', 'optimal'] = 'optimal'
    threshold_percentile: float = 0.5
    fixed_threshold: float = 0.5
    num_classificaion_heads: int = 1
    context_split_config: Optional[SplitConfig] = None
```

### ProbingDetectorConfig (extends DetectorBaseConfig)

```python
@dataclass
class ProbingDetectorConfig(DetectorBaseConfig):
    embedding_dim: Optional[List[int]] = None       # auto-detected via cold run
    num_features: Optional[List[int]] = None         # auto-detected via cold run
    attention_pooling: Optional[List[bool]] = None
    compression: CompressionConfig = field(default_factory=CompressionConfig)
    dropout_rate: float = 0.1
    ensemble: Optional[List[int]] = None
    max_length: int = 128                            # answer hiddens padding length
    padding_side: str = 'right'
    truncation_side: str = 'right'
    use_contrastive: bool = False
    projection_dim: int = 128
    contrastive_layers: Optional[List[int]] = None
```

### UncertaintyDetectorConfig (extends DetectorBaseConfig)

```python
@dataclass
class UncertaintyDetectorConfig(DetectorBaseConfig):
    threshold_percentile: float = 0.8
    aggregation_method: str = 'mean'                 # mean, max, min, weighted
    method_weights: Optional[List[float]] = None
```

### FeatureProcessorBaseConfig

```python
@dataclass
class FeatureProcessorBaseConfig:
    cache_features: bool = True
    feature_cache_dir: Optional[str] = None
    max_features: Optional[int] = None
    normalize_features: bool = False
    feature_extraction_batch_size: int = 1
    token_locator_config: TokenLocatorConfig = field(default_factory=TokenLocatorConfig)
    separate: bool = True
    side: SideType = SideType.RIGHT
    pooling_type: Literal['mean', 'last', 'max', 'none'] = 'none'
    padding: Union[bool, str] = False
    truncation: bool = False
    max_length: Optional[int] = None
```

### HiddensProcessorConfig (extends FeatureProcessorBaseConfig)

```python
@dataclass
class HiddensProcessorConfig(FeatureProcessorBaseConfig):
    layers: Optional[List[int]] = None   # e.g. [5, 10, -1], negative indices count from end
```

### AttentionsProcessorConfig (extends HiddensProcessorConfig)

```python
@dataclass
class AttentionsProcessorConfig(HiddensProcessorConfig):
    attention_heads: Optional[List[int]] = None
```

### LookbacksProcessorConfig (extends HiddensProcessorConfig)

```python
@dataclass
class LookbacksProcessorConfig(HiddensProcessorConfig):
    attention_heads: Optional[List[int]] = None
    border: TokenLocation = TokenLocation.ANS_START
```

### LogitsProcessorConfig (extends HiddensProcessorConfig)

```python
@dataclass
class LogitsProcessorConfig(HiddensProcessorConfig):
    normalize_logits: bool = False
```

### EnsembleProcessorConfig (extends FeatureProcessorBaseConfig)

```python
@dataclass
class EnsembleProcessorConfig(FeatureProcessorBaseConfig):
    processor_configs: Optional[List[FeatureProcessorBaseConfig]] = None
```

### UncertaintyFeatureProcessorConfig (extends FeatureProcessorBaseConfig)

```python
@dataclass
class UncertaintyFeatureProcessorConfig(FeatureProcessorBaseConfig):
    uncertainty_methods: Optional[List[str]] = None
    max_new_tokens: int = 256
    use_blackbox: bool = False
    openai_api_key: Optional[str] = None
    supports_logprobs: bool = True
    top_logprobs: int = 5
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
```

Available token-level uncertainty methods: `TokenEntropy`, `MaximumTokenProbability`, `EPTtu`, `EPTdu`, `EPTmi`, `EPTrmi`, `EPTepkl`, `EPTent5`, `EPTent10`, `EPTent15`, `PETtu`, `PETdu`, `PETmi`, `PETrmi`, `PETepkl`, `PETent5`, `PETent10`, `PETent15`

Available sequence-level uncertainty methods: `MonteCarloSequenceEntropy`, `MonteCarloNormalizedSequenceEntropy`, `MaximumSequenceProbability`, `MeanTokenEntropy`, `Perplexity`, `LexicalSimilarity`, `ClaimConditionedProbability`, `RAUQ`, `SAR`, `TokenSAR`, `SentenceSAR`, `EigValLaplacian`, `DegMat`, `Eccentricity`, `EigenScore`, `AttentionScore`, `PTrue`, `FisherRao`, `SelfCertainty`

### PipelineBaseConfig

```python
@dataclass
class PipelineBaseConfig:
    _target_: str = ''
    save_dir: str = './outputs'
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    model_manager: ModelManagerConfig = field(default_factory=ModelManagerConfig)
    lm_metrics: Optional[LmMetricsConfig] = None
    classification_metrics: Optional[List[ClassificationMetric]] = None
    cleaner_configs: Optional[List[CleanerConfig]] = None
    save_intermediate: bool = True
    debug: bool = False
    experiment_name: Optional[str] = None
    f_beta: float = 1.0
    checkpoint_interval: Optional[int] = None
    split_context_train: bool = False
    shuffle_train: bool = True
```

### TrainingArgsConfig

```python
@dataclass
class TrainingArgsConfig:
    max_epochs: Optional[int] = 5
    validation_interval: int = 5
    save_interval: Optional[int] = None
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
    loss_function: Optional[str] = 'bce'
    threshold_method: str = 'optimal'
    threshold_percentile: float = 0.5
    fixed_threshold: float = 0.5
    use_contrastive: bool = False
    contrastive_weight: float = 0.5
    contrastive_temperature: float = 0.07
```

### SplitConfig

```python
@dataclass
class SplitConfig:
    strategy: SplitStrategy                          # SENTENCE, PARAGRAPH, CHARACTER, LANGCHAIN, ATOMIC
    chunk_size: int = 1000
    overlap: int = 0
    split_response: bool = False
    aggregation_method: AggregationMethod = AggregationMethod.MEAN   # MEAN, MAX, MIN, VOTE
    num_sentences: int = 1
    num_paragraphs: int = 1
    batch_size: Optional[int] = None
    max_tokens: int = 4096
    enable_high_recall: bool = True
```

### CompressionConfig

```python
@dataclass
class CompressionConfig:
    method: CompressionMethod = CompressionMethod.NONE    # NONE, PCA, UMAP
    scaling_method: ScalingMethod = ScalingMethod.NONE     # NONE, STANDARD, MINMAX, ROBUST
    n_components: Optional[int] = None
    auto_compress_threshold: Optional[int] = None
```

### HFConfig (extends ModelAdapterBaseConfig)

```python
@dataclass
class HFConfig(ModelAdapterBaseConfig):
    model_path: str                                  # HuggingFace model path (required)
    device: Optional[str] = 'cuda'
    max_length: int = 1024
    batch_size: Optional[int] = 4
    model_type: ModelType = ModelType.CAUSAL          # CAUSAL, BASE, TOKEN_CLASSIFICATION, SEQUENCE_CLASSIFICATION
    model_dtype: Optional[str] = 'bf16'
    tokenizer_path: Optional[str] = None
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    num_labels: int = 2
    truncation: bool = False
    padding: Union[bool, str] = 'longest'
    padding_side: str = 'right'
    device_map: Optional[Union[str, Dict]] = None    # 'auto', 'balanced', or custom dict
    max_memory: Optional[Dict] = None                # e.g. {0: '20GiB', 1: '20GiB'}
    offload_folder: Optional[str] = None
    low_cpu_mem_usage: bool = True
    attn_implementation: str = 'eager'               # 'eager', 'sdpa', 'flash_attention_2'
```

### OpenAIConfig (extends ModelAdapterBaseConfig)

```python
@dataclass
class OpenAIConfig(ModelAdapterBaseConfig):
    api_key: Optional[str] = None
    model_path: str = 'gpt-3.5-turbo'
    base_url: Optional[str] = 'https://openrouter.ai/api/v1'
    timeout: int = 30
    max_retries: int = 3
    proxy_url: Optional[str] = None
```

### VLLMConfig (extends ModelAdapterBaseConfig)

```python
@dataclass
class VLLMConfig(ModelAdapterBaseConfig):
    enforce_eager: bool = True
    gpu_memory_utilization: float = 0.8
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
```

### TokenLocatorConfig

```python
@dataclass
class TokenLocatorConfig:
    locate_answer_end: bool = False
    locate_answer_start: bool = True
    locate_answer_middle: bool = False
    locate_eos: bool = False
    locate_substring: bool = False
    n_to_answer_start: int = 0
    n_to_answer_end: int = 0
    substrings: Optional[List[str]] = None
    case_sensitive: bool = True
    first_substring: bool = True
```

### JudgeBaseConfig

```python
@dataclass
class JudgeBaseConfig:
    system_prompt: Optional[str] = None
    dialogue_format: Optional[str] = None
    user_prompt: Optional[str] = None
    max_new_tokens: int = 10
    temperature: float = 0.0
    truncation: bool = True
    top_p: float = 1.0
```

### HfJudgeConfig (extends JudgeBaseConfig)

```python
@dataclass
class HfJudgeConfig(JudgeBaseConfig):
    peft_config: Optional[Any] = None      # e.g. LoraConfig
    return_tensors: str = 'pt'
    max_length: int = 1024
    padding: Union[bool, str] = 'longest'
```

### ModelStates (data container)

```python
@dataclass
class ModelStates:
    hiddens: Optional[List[Tuple[torch.Tensor]]] = None
    attentions: Optional[List[Tuple[torch.Tensor]]] = None
    locations: Optional[Union[List[Dict], List[List[Dict]]]] = None
    logits: Optional[torch.Tensor] = None
    sublayers: Optional[List[Tuple[torch.Tensor]]] = None
    token_hallucinations: Optional[List[List[int]]] = None
    logprobs: Optional[torch.Tensor] = None
    masks: Optional[torch.Tensor] = None
```

### TrainerOutput (result container)

```python
@dataclass
class TrainerOutput:
    _metrics: Dict[str, Optional[Dict[str, float]]]   # phase → {metric_name → value}
    _probs: Dict[str, Optional[List[float]]]           # phase → probabilities
    threshold: Optional[float] = 0.5
    # Methods: get_metric(phase, metric), get_metrics(phase), get_probs(phase)
```

---

## Side Selection Guide (Critical for Task Performance)

Choosing the correct `SideType` for your feature processor is **critical** — the wrong side will produce near-random metrics regardless of detector quality.

### How `SideType` works with `locate_answer_start=True`

The token locator finds where the assistant's answer begins in the tokenized sequence. `SideType` then determines which tokens' features are extracted:

- **`LEFT`** = all tokens **before** the answer start (context + question)
- **`RIGHT`** = all tokens **from** the answer start onward (the model's response)
- **`INNER`** = tokens between two located positions (needs 2+ positions)
- **`OUTER`** = tokens outside the located range

### Task-specific recommendations

| Task | Correct Side | Pooling | Why |
|------|-------------|---------|-----|
| **Hallucination detection** | `RIGHT` | `mean` | The probe must analyze the **answer** to detect unfaithful content. LEFT-side features are identical for correct and incorrect answers (same context), so probes trained on LEFT have zero discriminative power within the answerable subset. |
| **Query answerability** | `LEFT` | `last` | The probe must assess **context quality** — whether retrieved memories contain enough information. The last LEFT token (right before generation) encodes the model's readiness state. |
| **LookbacksProcessor** | `RIGHT` (always) | `mean` | Lookback ratios are only computed for tokens **after** the `border` (answer start). LEFT-side lookback values are all zeros. |

### Common mistake

Using `SideType.LEFT` for hallucination detection is the most common error. It appears to work (AUC > 0.5) because unanswerable samples (always label=0) have different context features from answerable ones. But the classifier is really doing partial answerability detection, not hallucination detection — it cannot distinguish "answerable + correct" from "answerable + wrong."

### `max_length` with pooling

When `pooling_type` is `'mean'`, `'max'`, or `'last'`, the feature processor reduces the token dimension to 1. Set `ProbingDetectorConfig(max_length=1)` to match; the default `max_length=128` would pad zeros and cause a shape mismatch in `LinearClassifier`.

---

## Attention Implementation Guide

### `attn_implementation` and `output_attentions`

`HFConfig.attn_implementation` is set at model load time and **cannot be changed per-call**.

| Implementation | `output_attentions=True` | Speed | Use when |
|---|---|---|---|
| `'eager'` | Supported | Slowest | Need attention weights (LookbacksProcessor, AttentionsProcessor) |
| `'sdpa'` | **NOT supported** — returns `None`/empty tuple, causes `IndexError` | Fast | Only need hidden states or logits |
| `'flash_attention_2'` | NOT supported | Fastest | Only need hidden states or logits |

**Dual-adapter pattern** for mixed workloads: create two `HfModelAdapter` instances with different `attn_implementation`. `ModelManager` swaps between them automatically (unloads one to load the other). With feature caching, each adapter loads only once.

```python
adapter_sdpa = HfModelAdapter(config=HFConfig(..., attn_implementation='sdpa'))    # fast, hiddens only
adapter_eager = HfModelAdapter(config=HFConfig(..., attn_implementation='eager'))  # slower, supports attention

hiddens_proc = HiddensProcessor(config=..., extractor=adapter_sdpa)       # no attention needed
lookback_proc = LookbacksProcessor(config=..., extractor=adapter_eager)   # needs attention
ensemble_proc = EnsembleProcessor(config=..., extractor=adapter_eager)    # needs attention for lookback sub-processor
```

### Hybrid-attention models and `outputs.attentions` length

In hybrid-attention architectures (e.g., Qwen3.5 family), not every model block produces a standard attention map. `outputs.attentions` may be **shorter** than `num_hidden_layers`:

| Model | `num_hidden_layers` | `len(outputs.attentions)` | Layout |
|-------|--------------------|-----------------------------|--------|
| Qwen3.5-4B | 36 | 8 | Hybrid: 8 full-attention blocks |
| Qwen3.5-35B-A3B | 40 | 10 | Hybrid: 10 full-attention blocks (3:1 ratio) |

The `layers` parameter passed to `generate_hiddens` indexes **both** `outputs.hidden_states` (N+1 entries) and `outputs.attentions` (fewer entries). The adapter silently skips out-of-range attention indices.

**For lookback/attention processors**: set `layers` based on the actual attention output count, not `num_hidden_layers`. Use `list(range(n_attn))` where `n_attn` is the model's attention block count.

**For ensemble sub-processors**: all layer indices must be valid for attention since the ensemble generates hiddens and attention in a single call with a unified layer list. Compute ensemble hiddens layers from `n_attn`, not `num_hidden_layers`:

```python
# WRONG — indices from 36-layer hidden space, out of range for 8-layer attention
ensemble_hiddens_layers = get_several_layers(num_hidden_layers, 'middle+last:3', negative_only=True)

# CORRECT — indices within attention output range
ensemble_hiddens_layers = get_several_layers(n_attn_layers, 'middle+last:3', negative_only=True)
```

### EnsembleProcessor layer filtering

`EnsembleProcessor._unify_processor_args()` merges layer lists from all sub-processors into one unified list. `generate_features()` stores it as `self._unified_layers`. In `_extract_processor_features_subset()`, features from the unified output are filtered to only the sub-processor's own layers before caching. Without this filtering, the cache saver would receive N unified-layer features but validate against the sub-processor's M-layer list (N ≠ M → `ValueError`).

A bounds check raises a clear error if a sub-processor's layer indices exceed the actual feature count (can happen when attention returns fewer tensors than the unified layer list).

### LookbacksProcessor `attention_heads` field

`LookbacksProcessorConfig.attention_heads` selects specific attention heads by index. Useful for GQA models where heads within a KV group are correlated:

```python
# Qwen3.5-35B-A3B: 16 query heads, 2 KV groups → heads [0,8] are group representatives
lookback_config = LookbacksProcessorConfig(
    layers=list(range(10)),
    attention_heads=[0, 8],  # 2 independent heads × 10 layers = 20 features
    ...
)
```

### Lookback feature dimensions

Lookback output dimension = `num_attention_heads × num_layers` (or `len(attention_heads) × num_layers` if filtered). After pooling (`mean`/`max`/`last`), shape is `(1, dim)`.

| Model | Heads | Attention layers | Features (all heads) | Features (1/KV-group) |
|-------|-------|-----------------|---------------------|-----------------------|
| Qwen3.5-4B | 16 | 8 | 128 | 16 (2 heads × 8) |
| Qwen3.5-35B-A3B | 16 | 10 | 160 | 20 (2 heads × 10) |

For short-answer QA (e.g., LongMemEval, 67% answers ≤3 words), lookback features have limited discriminative power: mean lookback ratios cluster in 0.64–0.94, and GQA correlation reduces effective independent features. Use PCA denoising (`target_dimensions=32`) rather than `CompressionMethod.NONE`.

### PCA compression vs. feature dimensionality

`ProbingDetectorConfig.compression.target_dimensions` sets the PCA target. If the actual feature dimension is **smaller** than the target (e.g., LookbacksProcessor outputs ~32 features but target is 256), the cold run will misconfigure `LinearClassifier` with the wrong `embedding_dim`, causing a shape mismatch at training time.

**Fix**: use a smaller PCA target for low-dimensional feature processors:

```python
det_cfg = deepcopy(detector_config)
if feat_name.startswith('Lookback'):
    det_cfg.compression.method = CompressionMethod.PCA
    det_cfg.compression.target_dimensions = 32  # denoise GQA-correlated heads
```

---

## Enums Reference

### DetectionTaskType
`HALLUCINATION_DETECTION = 'hallucination'` | `QUERY_ANSWERABILITY = 'answerability'`

### ModelType
`CAUSAL` | `BASE` | `TOKEN_CLASSIFICATION` | `SEQUENCE_CLASSIFICATION`

### FeatureType
`HIDDEN` | `ATTENTION` | `LOOKBACK` | `LOGIT` | `SUBLAYER` | `TOKEN_UNCERTAINTY` | `SEQUENCE_UNCERTAINTY`

### DetectionLevel
`TOKEN = 'token'` | `SEQUENCE = 'sequence'` | `CLAIM = 'claim'`

### SplitStrategy
`SENTENCE` | `PARAGRAPH` | `CHARACTER` | `LANGCHAIN` | `ATOMIC = 'atomic_facts'`

### AggregationMethod
`MEAN` | `MAX` | `MIN` | `VOTE`

### CompressionMethod
`PCA` | `UMAP` | `NONE`

### ScalingMethod
`STANDARD` (z-score) | `MINMAX` (0-1) | `ROBUST` (median/IQR) | `NONE`

### ClassificationMetric
`ROC_AUC` | `F1` | `ACCURACY` | `PR_AUC` | `PRECISION` | `RECALL` | `FBETA` | `AP`

### LmMetric
`ROUGE_1` | `ROUGE_2` | `ROUGE_L` | `BLEU` | `TER` | `METEOR` | `BERT_SCORE` | `BERT_SCORE_PRECISION` | `BERT_SCORE_RECALL` | `BERT_SCORE_F1`

### TokenLocation
`ANS_END` | `ANS_START` | `ANS_MID` | `EOS` | `N_TO_ANS_START` | `N_TO_ANS_END` | `SUBSTRING`

### SideType
`LEFT` | `RIGHT` | `INNER` | `OUTER`

### Phase
`TRAIN` | `TEST` | `VAL`

---

## Constants

```python
# Dataset columns
INPUT_COL = 'input'
INPUT_PROC_COL = 'processed_input'
REFERENCE_COL = 'reference'
TARGET_COL = 'target'
ANSWER_INDICES = 'answer_indices'
OFFSETS_COL = 'offsets'
GROUP_ID_COL = 'group_id'

# Environment
HF_TOKEN_ENV = 'HF_TOKEN'
OPENAI_API_KEY_ENV = 'OPENAI_API_KEY'
```

---

## Dataset Format

### Sequence-Level

```python
dataset = Dataset.from_list([{
    'input': np.array([
        {'content': 'Context and question...', 'role': 'user'},
        {'content': 'Model response...', 'role': 'assistant'}
    ], dtype=object),
    'target': np.int64(0),  # 0 or 1 (binary), or 0/1/2 (ternary NLI)
}])
```

### Token-Level

```python
dataset = Dataset.from_list([{
    'input': np.array([
        {'content': '...', 'role': 'user'},
        {'content': '...', 'role': 'assistant'}
    ], dtype=object),
    'target': np.array([
        np.array([61, 75]),       # span [start, end) character indices
        np.array([10, 20]),
    ], dtype=object),
}])
```

---

## Usage Examples

### 1. Sequence-Level Probing with Ensemble Features

```python
from sirin.definitions import AggregationMethod, ClassificationMetric, SplitStrategy
from sirin.detection.probing import ProbingPipeline, SequenceLinearProbingDetector
from sirin.detection.processors.ensemble import EnsembleProcessor
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig
from sirin.models.detection import *

token_locator_config = TokenLocatorConfig(locate_answer_start=True)

processor_configs = [
    HiddensProcessorConfig(token_locator_config=token_locator_config, layers=[14], pooling_type='mean'),
    HiddensProcessorConfig(token_locator_config=token_locator_config, layers=[14], pooling_type='max'),
]

extractor = HfModelAdapter(config=HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))

ensemble_processor = EnsembleProcessor(
    config=EnsembleProcessorConfig(processor_configs=processor_configs),
    extractor=extractor,
)

detector = SequenceLinearProbingDetector(
    config=ProbingDetectorConfig(
        max_length=128,
        context_split_config=SplitConfig(
            strategy=SplitStrategy.SENTENCE,
            aggregation_method=AggregationMethod.MAX,
            num_sentences=4,
        ),
    ),
    feature_processor=ensemble_processor,
)

pipeline = ProbingPipeline(
    config=ProbingPipelineConfig(
        train_args=TrainingArgsConfig(
            max_epochs=5,
            metrics=[ClassificationMetric.F1, ClassificationMetric.ROC_AUC],
        ),
    ),
    detector=detector,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    generator_adapter=extractor,
)

train_results = pipeline.train()
detector.save('./models/ensemble_detector')

# Inference
detector.load('./models/ensemble_detector')
sample = [
    {'role': 'user', 'content': 'What is H2O?'},
    {'role': 'assistant', 'content': 'Water.'}
]
result = detector.detect([sample])
```

### 2. Token-Level Probing with Uncertainty

```python
from sirin.detection.probing import ProbingPipeline
from sirin.detection.probing.detectors.token import TokenTabPFNProbingDetector
from sirin.detection.processors.uncertainty import TokenUncertaintyFeatureProcessor
from sirin.models.detection import UncertaintyFeatureProcessorConfig, ProbingDetectorConfig, ProbingPipelineConfig, TrainingArgsConfig
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig

extractor = HfModelAdapter(HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))
feature_processor = TokenUncertaintyFeatureProcessor(
    config=UncertaintyFeatureProcessorConfig(
        uncertainty_methods=['TokenEntropy', 'MaximumTokenProbability'],
        feature_extraction_batch_size=16,
    ),
    extractor=extractor,
)

detector = TokenTabPFNProbingDetector(
    config=ProbingDetectorConfig(batch_size=32),
    feature_processor=feature_processor,
)

pipeline = ProbingPipeline(
    config=ProbingPipelineConfig(train_args=TrainingArgsConfig(max_epochs=5)),
    detector=detector,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    generator_adapter=extractor,
)
train_results = pipeline.train()
eval_results = pipeline.eval()
```

### 3. Sequence-Level Uncertainty (no training needed)

```python
from sirin.detection.uncertainty import SequenceUncertaintyDetector, UncertaintyPipeline
from sirin.detection.processors import SequenceUncertaintyFeatureProcessor
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig
from sirin.models.detection import *

extractor = HfModelAdapter(HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))
feature_processor = SequenceUncertaintyFeatureProcessor(
    config=UncertaintyFeatureProcessorConfig(uncertainty_methods=['MeanTokenEntropy', 'RAUQ']),
    extractor=extractor,
)

detector = SequenceUncertaintyDetector(
    config=UncertaintyDetectorConfig(batch_size=4, aggregation_method='mean'),
    feature_processor=feature_processor,
)

pipeline = UncertaintyPipeline(
    config=PipelineBaseConfig(),
    detector=detector,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)
eval_results = pipeline.eval()  # uncalibrated uncertainty scores, no training needed
```

### 4. Judge with LoRA

```python
from peft import LoraConfig
from transformers import TrainingArguments
from sirin.detection.judging import JudgePipeline, SequenceDecoderJudge
from sirin.inference.adapters import HfModelAdapter
from sirin.models.detection import HfJudgeConfig, JudgePipelineConfig
from sirin.models.inference import HFConfig

lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM')
model = HfModelAdapter(HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))
judge = SequenceDecoderJudge(config=HfJudgeConfig(peft_config=lora_config), model_adapter=model)

pipeline = JudgePipeline(
    config=JudgePipelineConfig(),
    judge=judge,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    training_args=TrainingArguments(num_train_epochs=3),
)
train_results = pipeline.train()
eval_results = pipeline.eval()
```

### 5. API-Based Judge

```python
from sirin.detection.judging import SequenceOpenAIJudge
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig
from sirin.models.inference import OpenAIConfig

model = OpenAIModelAdapter(OpenAIConfig(model_path='gpt-3.5-turbo'))
judge = SequenceOpenAIJudge(config=OpenAIJudgeConfig(user_prompt='your prompt'), model_adapter=model)

sample = [
    {'role': 'user', 'content': 'What is H2O?'},
    {'role': 'assistant', 'content': 'Water.'}
]
result = judge.detect(sample)
```

---

## Hydra Configuration

### Entry Point

```bash
python scripts/train.py
python scripts/train.py pipeline.detector.batch_size=32 pipeline.train_args.max_epochs=10
```

### Config Structure (`sirin/configs/`)

```
train.yaml                          # top-level, composes defaults
├── model_adapter/
│   ├── default.yaml                # HF Qwen2.5-3B-Instruct
│   ├── hf_with_batching.yaml       # HF with batch_size for OOM prevention
│   ├── hf_large_model.yaml         # HF with device_map for multi-GPU
│   ├── vllm_with_batching.yaml     # vLLM backend
│   ├── openai_with_parallel.yaml   # OpenAI API
│   └── openrouter.yaml             # OpenRouter API endpoint
├── token_locator_config/
│   └── default.yaml                # locate_answer_start: true
├── feature_processor/
│   └── hiddens.yaml                # HiddensProcessor
├── detector/
│   └── probing.yaml                # SequenceTabPFNProbingDetector
├── pipeline/
│   └── probing.yaml                # ProbingPipeline
└── train_args/
    └── default.yaml                # 5 epochs, 0.001 lr, bce loss
```

### train.yaml defaults

```yaml
defaults:
  - model_adapter: default
  - token_locator_config: default
  - feature_processor: hiddens
  - detector: probing
  - pipeline: probing
  - train_args: default

cuda_visible_devices: "0"
cache_dir: "./cache"
use_cache: true
task_type: null
log_level: DEBUG
random_seed: 42
train_dataset_path: ???       # required
eval_dataset_path: ???        # required
hf_token: null
openai_api_key: null
```

---

## Component Reference

### Feature Processors — What Each Extracts

| Processor | Feature | Config | Key Params |
|-----------|---------|--------|------------|
| `HiddensProcessor` | FFN output hidden states | `HiddensProcessorConfig` | `layers`, `pooling_type` |
| `SublayersProcessor` | Post-attention, pre-FFN states | `SublayersProcessorConfig` | `layers` |
| `AttentionsProcessor` | Attention weight matrices | `AttentionsProcessorConfig` | `layers`, `attention_heads` |
| `LookbacksProcessor` | Lookback Lens ratios | `LookbacksProcessorConfig` | `layers`, `border` (TokenLocation), `attention_heads` |
| `LogitsProcessor` | Output logits (pre-softmax) | `LogitsProcessorConfig` | `normalize_logits` |
| `MTopDivFeatureProcessor` | Manifold Topology Divergence | `MTopDivProcessorConfig` | `n_jobs`, `heads_to_analyze` |
| `EnsembleProcessor` | Combines multiple processors | `EnsembleProcessorConfig` | `processor_configs` (list) |
| `TokenUncertaintyFeatureProcessor` | Token-level uncertainty | `UncertaintyFeatureProcessorConfig` | `uncertainty_methods` |
| `SequenceUncertaintyFeatureProcessor` | Sequence-level uncertainty | `UncertaintyFeatureProcessorConfig` | `uncertainty_methods` |

### Model Adapters — Capabilities

| Adapter | Internal Access | Generation | Multi-GPU | API |
|---------|----------------|------------|-----------|-----|
| `HfModelAdapter` | hiddens, attention, logits, sublayers | yes | device_map | no |
| `VllmModelAdapter` | limited | high-throughput | yes | no |
| `OpenAIModelAdapter` | logprobs only | yes | n/a | yes |

### Detectors — 3×3 Matrix

| Classifier | Sequence | Token | Claim |
|-----------|----------|-------|-------|
| **TabPFN** | `SequenceTabPFNProbingDetector` | `TokenTabPFNProbingDetector` | `ClaimTabPFNProbingDetector` |
| **CatBoost** | `SequenceCatboostProbingDetector` | `TokenCatboostProbingDetector` | `ClaimCatboostProbingDetector` |
| **Linear** | `SequenceLinearProbingDetector` | `TokenLinearProbingDetector` | `ClaimLinearProbingDetector` |

### Judges

| Backend | Sequence | Token |
|---------|----------|-------|
| **Decoder (Llama, Qwen, etc.)** | `SequenceDecoderJudge` | `TokenDecoderJudge` |
| **Encoder (BERT, ModernBERT)** | `SequenceEncoderJudge` | `TokenEncoderJudge` |
| **OpenAI API** | `SequenceOpenAIJudge` | `TokenOpenAIJudge` |

---

## Key Patterns

### Save/Load Detector

```python
# Save
detector.save('./models/my_detector')

# Load
detector = SequenceTabPFNProbingDetector(
    config=ProbingDetectorConfig(),
    feature_processor=processor,
)
detector.load('./models/my_detector')
result = detector.detect([sample])
```

### Context Splitting

```python
detector = SequenceLinearProbingDetector(
    config=ProbingDetectorConfig(
        context_split_config=SplitConfig(
            strategy=SplitStrategy.SENTENCE,
            aggregation_method=AggregationMethod.MAX,
            num_sentences=4,
        ),
    ),
    feature_processor=processor,
)
```

### Multi-GPU Loading

```python
extractor = HfModelAdapter(
    config=HFConfig(
        model_path='meta-llama/Llama-3-70B-Instruct',
        device_map='auto',
        max_memory={0: '40GiB', 1: '40GiB'},
    )
)
```

### Feature Caching

```python
processor = HiddensProcessor(
    config=HiddensProcessorConfig(
        cache_features=True,
        feature_cache_dir='./cache/hiddens',
        layers=[10, 20, -1],
    ),
    extractor=extractor,
)
```

### Experiment Logging

```python
from sirin.loggers import WandbLogger

logger = WandbLogger(project='sirin-experiments', run_name='my-run')
pipeline = ProbingPipeline(
    config=ProbingPipelineConfig(...),
    detector=detector,
    train_dataset=train_ds,
    eval_dataset=eval_ds,
    generator_adapter=extractor,
    experiment_logger=logger,
)
```

---

## Critical Pitfalls

### 1. Data Leakage with `side=RIGHT`

When probing for hallucination/answerability where the **target label is derived from the prediction text** (e.g. F1 of prediction vs gold), using `side=RIGHT` (answer tokens) causes data leakage — the hidden states encode the answer string, so a classifier trivially learns "which answers are correct" and gets ROC-AUC=1.0.

**Fix**: Use `side=LEFT` with `pooling_type='last'` to probe the model's internal state at the last context token *before* the answer starts. This captures whether the model "knows" the context is sufficient — the actual research question.

```python
# WRONG — leaks the answer into features
processor_config = HiddensProcessorConfig(
    separate=True,
    side=SideType.RIGHT,   # answer tokens → data leakage
    pooling_type='mean',
)

# CORRECT — probes pre-answer state
processor_config = HiddensProcessorConfig(
    separate=True,
    side=SideType.LEFT,    # context+question tokens
    pooling_type='last',   # last token before answer
)
```

### 2. Layer Indices Must Match Model Architecture

`PROBE_LAYERS` indices must be valid for the model's `hidden_states` output (0..num_hidden_layers). Out-of-range indices cause `IndexError: tuple index out of range` in `hf_adapter.py:454`.

**For attention-based processors** (lookback, attention, ensemble), indices must be valid for `outputs.attentions`, which can be shorter than `hidden_states` in hybrid-attention models. See "Hybrid-attention models" section above.

Check the model first:
```python
from transformers import AutoConfig
config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
# May be in config.text_config for hybrid/MoE models
num_layers = config.num_hidden_layers  # or config.text_config.num_hidden_layers
# hidden_states has num_layers+1 entries (index 0 = embeddings)
# outputs.attentions may have FEWER entries in hybrid-attention models
```

Examples:
- Qwen3.5-35B-A3B: 40 hidden layers, 10 attention blocks → hiddens indices 0..40, attention indices 0..9
- Qwen3.5-4B: 36 hidden layers, 8 attention blocks → hiddens indices 0..36, attention indices 0..7
- Qwen2.5-3B-Instruct: 36 layers (dense) → all indices 0..36

### 3. Instantiation Order is Strict

Components must be created in this exact order (each depends on the previous):

```python
# 1. Model adapter (extractor)
adapter = HfModelAdapter(config=model_config)

# 2. Feature processor (needs extractor)
processor = HiddensProcessor(config=proc_config, extractor=adapter)

# 3. Detector (needs feature_processor — calls setup_extractor() + _cold_run())
detector = SequenceCatboostProbingDetector(config=det_config, feature_processor=processor)

# 4. Pipeline (needs detector + dataset)
pipeline = ProbingPipeline(config=pipe_config, detector=detector, train_dataset=dataset)

# 5. Train (no arguments)
result = pipeline.train()
```

`feature_processor` is a **required positional argument** for all probing and uncertainty detectors, not optional. The `_cold_run()` during detector init loads the model and extracts a test sample to discover feature dimensions.

### 4. TrainingArgsConfig Goes Inside ProbingPipelineConfig

`ProbingPipelineConfig` has a `train_args: TrainingArgsConfig` field. Do NOT pass `train_args` separately:

```python
pipeline_config = ProbingPipelineConfig(
    save_dir='./outputs',
    train_args=TrainingArgsConfig(    # nested inside pipeline config
        max_epochs=10,
        val_size=0.2,
        target_metric='roc_auc',
    ),
    classification_metrics=[ClassificationMetric.ROC_AUC, ClassificationMetric.F1],
)
```

### 5. ProbingPipeline Requires DatasetDict for Validation

`ProbingPipeline.train()` (line 87-88 of `probing/pipeline.py`) **only creates `val_loader` when `train_dataset` is a `DatasetDict`** with a `'val'` or `'validation'` key. If you pass a plain `Dataset`, `val_loader` stays `None`, and CatBoost/TabPFN silently fall back to evaluating on training data (`val_loader = val_loader or train_loader`), giving artificially perfect metrics.

```python
# WRONG — no validation, CatBoost reports train metrics (ROC-AUC=1.0)
pipeline = ProbingPipeline(
    ...,
    train_dataset=Dataset.from_dict({...}),
)

# CORRECT — proper train/val split, realistic metrics
from sklearn.model_selection import train_test_split

train_idx, val_idx = train_test_split(range(len(ds)), test_size=0.2, stratify=ds['target'])
dd = DatasetDict({
    'train': ds.select(train_idx),
    'val': ds.select(val_idx),
})
pipeline = ProbingPipeline(
    ...,
    train_dataset=dd,
)
```

The `val_size` field in `TrainingArgsConfig` does NOT create this split — it's only used by the Linear probe's internal training loop for epoch-level early stopping, not for final metric evaluation.

### 6. Pre-Computed Answers Skip Generation (but break Uncertainty)

If the dataset's `input` column already has `role: 'assistant'` as the last message, the **probing** pipeline skips answer generation automatically. For `task_type=QUERY_ANSWERABILITY`, generation is always skipped regardless.

**However, the uncertainty pipeline always generates its own answers** (lm-polygraph's `GreedyProbsCalculator` calls `model.generate()`, ignoring pre-computed text in `target_texts`). If you pass pre-computed answers to the uncertainty pipeline, they are silently ignored — uncertainty is computed on different text than your labels describe, giving ROC-AUC=0.5.

For uncertainty: strip `role: 'assistant'` messages from the input and let the model generate.

**Critical:** `SequenceUncertaintyFeatureProcessor.generate_features()` takes `sample[0]['content']` as the prompt and `sample[1]['content']` as the (ignored) pre-computed answer. If your input has `[system, user, ...]` format, the model only sees the system prompt — the context and question are never sent to the model. Fix: merge system + user into `sample[0]`:

```python
# WRONG — model only sees "You are a helpful assistant..."
[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': prompt}]

# CORRECT — model sees the full prompt with context + question
[{'role': 'user', 'content': f"{SYSTEM_PROMPT}\n\n{prompt}"}, {'role': 'assistant', 'content': ''}]
```

**Also critical:** lm-polygraph's `WhiteboxModel` defaults to `instruct=False`, which raw-tokenizes strings without applying the chat template. Instruct models (Qwen, Llama-3, etc.) need `<|im_start|>`/`<|im_end|>` markers to understand the prompt. Without them, the model generates incoherent text and uncertainty is random. Fix: pass `instruct=True` via `model_kwargs`:

```python
# WRONG — raw tokenization, no chat template markers
UncertaintyFeatureProcessorConfig(
    uncertainty_methods=methods,
    max_new_tokens=64,
)

# CORRECT — applies tokenizer.apply_chat_template() before tokenizing
UncertaintyFeatureProcessorConfig(
    uncertainty_methods=methods,
    max_new_tokens=64,
    model_kwargs={'instruct': True},
)
```

### 6. Attention Implementation Constraints

| Implementation | Speed | Returns attention? | Uncertainty methods |
|---------------|-------|-------------------|-------------------|
| `eager` | Slowest | Yes | All methods work |
| `sdpa` | Fast | Yes | All methods work |
| `flash_attention_2` | Fastest | **No** | `SelfCertainty` and `AttentionScore` **fail** |

lm-polygraph examples default to `eager`. Use `sdpa` as the best balance of speed and compatibility.

### 7. Feature Cache Invalidation

When changing `side`, `pooling_type`, or `layers` in the processor config, **delete the feature cache directory** before re-running. Cached features from a previous config will be silently reused with wrong settings:

```python
import shutil
cache_dir = Path('./feature_cache')
if cache_dir.exists():
    shutil.rmtree(cache_dir)
```

### 8. Three Different batch_size Configs

There are 3 `batch_size` parameters at different levels — they are NOT interchangeable:

```
pipeline.train()
│
├─ DetectorConfig.batch_size (default=1)
│  How many samples are sent to the feature processor per iteration.
│
│  └─ HFConfig.batch_size (default=4)
│     How many samples the LLM forward-passes at once (GPU memory bottleneck).
│     If detector sends more, the @batch_processor decorator auto-chunks.
│
└─ TrainingArgsConfig.train_batch_size (default=256)
   DataLoader batch size for training the classifier (CPU/RAM, not GPU).
```

| Config | Controls | Memory impact | Recommendation |
|--------|----------|--------------|----------------|
| `HFConfig.batch_size` | Model forward pass | **GPU VRAM** | **1** for 30B+ models, **4-8** for 3B |
| `DetectorConfig.batch_size` | Feature extraction loop | Intermediate tensors | Same as HFConfig or slightly higher |
| `TrainingArgsConfig.train_batch_size` | Classifier training | CPU/RAM only | **64-256** (default is fine) |

### 9. Cold_run n_features Bug with Multiple Probe Layers (FIXED in base.py:75)

When using multiple probe layers (`PROBE_LAYERS = [layer_a, layer_b]`), `ProbingDetectorBase._cold_run()` computes a different `n_features` denominator than `FeaturePreprocessor.fit()`, causing the `LinearClassifier` to be initialized with wrong query dimensions.

- **`_cold_run` (base.py:75)**: `n_features = sum(feature[0].shape[-1])` — uses `emb_dim` only
- **`FeaturePreprocessor.fit()` (preprocessor.py:124)**: `feature_n_features = num_tokens * emb_dim * num_layers`

With 2 layers and 2560 hidden dim: cold_run gets `n_features=2560`, preprocessor gets `5120`. This produces query dim=256 but PCA output=128, causing `RuntimeError: mat1 and mat2 shapes cannot be multiplied`.

**Fix applied**: Changed `base.py:75` from `.shape[-1]` to `.numel()` to match the preprocessor's calculation.

Additionally: set `max_length=1` in `ProbingDetectorConfig` when using `pooling_type='last'` to avoid padding pooled features to 128 positions.

### 10. CompressionConfig Field Names

`CompressionConfig` uses `threshold` and `target_dimensions` (not `auto_compress_threshold` or `n_components`):

```python
CompressionConfig(
    method=CompressionMethod.PCA,     # PCA, UMAP, NONE
    scaling_method=ScalingMethod.STANDARD,  # STANDARD, MINMAX, ROBUST, NONE
    threshold=500,           # auto-compress if dim > threshold
    target_dimensions=300,   # PCA/UMAP target dim
)
```

---

## Vendored Dependencies

- **lm-polygraph** at `sirin/detection/lm-polygraph/` — uncertainty estimation. Compatibility with transformers 5.x handled by `sirin/detection/_lm_polygraph_compat.py` (patches old class names, adds `BlackboxModel.base_url`, fixes `top_logprobs` builder)
- **TabPFN-Wide** at `sirin/detection/tabpfn_wide` — git submodule from `github.com/pfeiferAI/TabPFN-Wide.git`

## Environment

```bash
conda activate sirin_exps
export HF_TOKEN=...
export OPENAI_API_KEY=...
export CUDA_VISIBLE_DEVICES=0
```
