# Architecture and Public API

## Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Public API Import Paths](#public-api-import-paths)

## Overview

**SIRIN** detects hallucinations and query answerability at sequence, token, and claim levels.

Three detection families:

1. **Probing** - trains lightweight classifiers on frozen LLM features.
2. **Judge** - uses local HF judges or OpenAI-compatible API judges.
3. **Uncertainty** - uses lm-polygraph uncertainty estimators.

Python >=3.11, <3.14.

---

## Architecture

### Core Composition

```text
Hydra config or direct Python
  -> ModelAdapter
     Owns model/tokenizer/API client access.
  -> FeatureProcessor
     Extracts hidden states, logits, attention, lookback, uncertainty, or ensemble features.
  -> Detector or Judge
     Owns prediction, calibration, save/load, and training behavior.
  -> Pipeline
     Owns dataset stages, train/eval orchestration, metrics, logging, and intermediate saves.
```

`ConfigManager.build_pipeline()` composes the Hydra training path as adapter -> feature processor -> detector -> pipeline. UI presets and direct Python constructors can build the same components explicitly, including judge-only paths that use a model adapter directly.

### Main Families

```text
Probing detectors
  Sequence/Token/Claim x Linear/CatBoost/TabPFN

Judges
  Sequence/Token/Claim x Decoder/Encoder/OpenAI

Uncertainty detectors
  Sequence/Token

Feature processors
  Hiddens, Attentions, Logits, Lookbacks, Sublayers, MTopDiv, Uncertainty, Ensemble

Support components
  Model adapters, token locators, splitters, target approximators, cleaners, loggers, savers
```

### Dataflow By Pipeline

```text
Shared dataset loading:
  Dataset/DatasetDict
    -> generate missing assistant answers unless answerability task
    -> clean generated outputs
    -> compute requested LM metrics
    -> optionally split context for train
    -> InputsDataset

ProbingPipeline.train():
  optional target approximation
    -> shared dataset loading
    -> FeatureProcessor
    -> ProbingDetectorBase.train()
    -> DetectionResult

JudgePipeline.train():
  shared dataset loading
    -> HfJudgeBase.train(TrainingArguments)
    -> DetectionResult

UncertaintyPipeline.train():
  shared dataset loading
    -> UncertaintyDetectorBase.train()
    -> DetectionResult

Inference:
  detect(sample)
    -> feature/model/API call
    -> probabilities and predictions
    -> optional context aggregation
```

---

## Public API Import Paths

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
    ClaimDecoderJudge, ClaimEncoderJudge, ClaimOpenAIJudge,
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
    MTopDivFeatureProcessor,  # optional; may be None if extra deps are unavailable
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
    # Training and output
    TrainingArgsConfig, DetectionResult,
    # Supporting configs
    SplitConfig, CompressionConfig, SamplingConfig,
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

### Utilities

```python
from sirin.utils.config_manager import ConfigManager
from sirin.loggers import (
    LoggerBase, WandbLogger, TensorBoardLogger,
    ClearMLLogger, CometLogger, MultipleLoggers,
)
from sirin.detection.splitters.splitter import SplitManager
from sirin.detection.approximators.sep import SEPTargetApproximator
from sirin.inference.cleaners import BaseCleaner, RegexCleaner, HTMLCleaner, CodeCleaner, CustomCleaner
from sirin.metrics.classification import calculate_classification_metrics
from sirin.metrics.language import calculate_lm_metrics
from sirin.classification import LinearClassifier
```
