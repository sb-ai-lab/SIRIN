# Configs, Enums, and Constants

## Contents

- [Config Reference](#config-reference)
- [Enums Reference](#enums-reference)
- [Constants](#constants)

## Config Reference

### SamplingConfig

```python
@dataclass
class SamplingConfig:
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
```

`PipelineBase._generate_answers()` forwards only `max_length` as `max_tokens`, `temperature`, `top_p`, `top_k`, and `kwargs`. Put provider-specific OpenAI/vLLM extensions under `kwargs`, for example `{'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}}`.

### DetectorBaseConfig

```python
@dataclass
class DetectorBaseConfig:
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
    method_weights: Optional[Dict[str, float]] = None
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
    experiment_name: Optional[str] = None
    f_beta: float = 1.0
    split_context_train: bool = False
    shuffle_train: bool = False
    per_sample_metrics: bool = False
```

### TrainingArgsConfig

```python
@dataclass
class TrainingArgsConfig:
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
    scaling_method: ScalingMethod = ScalingMethod.STANDARD  # NONE, STANDARD, MINMAX, ROBUST
    threshold: int = 500
    target_dimensions: int = 300
    kwargs: Dict[str, Any] = field(default_factory=dict)
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
    system_prompt: str = 'You are a precise hallucination detector for AI-generated dialogue. Your only task is to analyze the given user-assistant exchange and output a single binary digit: 1 if the assistant's response contains any factual inaccuracy, unsupported claim, or hallucinated content - 0 if it is fully grounded and correct. Do not explain, justify, or add any text. Output only "1" or "0".'
    dialogue_format: str = 'Question: {question}.\n Answer: {answer}'
    user_prompt: str = "I give you a dialogue consisting of a user prompt and an assistant answer. Your task is to evaluate whether this dialogue contains hallucination. Answer only 0 or 1.\nDialogue: \"{sample}\".\nRespond with 1 if the assistant's answer contains hallucination, 0 otherwise: "
    max_new_tokens: int = 2048
    temperature: float = 1.0
    top_p: float = 1.0
    diversity_penalty: float = 1.0
    num_beam_groups: int = 5
    num_beams: int = 5
```

### HfJudgeConfig (extends JudgeBaseConfig)

```python
@dataclass
class HfJudgeConfig(JudgeBaseConfig):
    peft_config: Optional[Any] = None      # e.g. LoraConfig
    return_tensors: str = 'pt'
```

### OpenAIJudgeConfig (extends JudgeBaseConfig)

```python
@dataclass
class OpenAIJudgeConfig(JudgeBaseConfig):
    pass
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

### DetectionResult (result container)

```python
@dataclass
class DetectionResult:
    metrics: Optional[Dict[str, float]] = None
    probs: Optional[List[float]] = None
    labels: Optional[List[float]] = None
    threshold: float = 0.5
    history: Optional[TrainingHistory] = None
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
