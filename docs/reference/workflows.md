# Workflows and Examples

## Contents

- [Dataset Format](#dataset-format)
- [Usage Examples](#usage-examples)
- [Hydra Configuration](#hydra-configuration)
- [Key Patterns](#key-patterns)

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
result = judge.detect([sample])
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
|-- model_adapter/
|   |-- default.yaml                # HF Qwen2.5-3B-Instruct
|   |-- hf_with_batching.yaml       # HF with batch_size for OOM prevention
|   |-- hf_large_model.yaml         # HF with device_map for multi-GPU
|   |-- vllm_with_batching.yaml     # vLLM backend
|   |-- openai_with_parallel.yaml   # OpenAI API
|   `-- openrouter.yaml             # OpenRouter API endpoint
|-- token_locator_config/
|   `-- default.yaml                # locate_answer_start: true
|-- feature_processor/
|   `-- hiddens.yaml                # HiddensProcessor
|-- detector/
|   `-- probing.yaml                # SequenceTabPFNProbingDetector
|-- pipeline/
|   `-- probing.yaml                # ProbingPipeline
`-- train_args/
    `-- default.yaml                # 5 epochs, 0.001 lr, bce loss
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
