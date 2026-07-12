# <img src="sirin/ui/assets/logo.png" width="40" align="left" style="margin-right:8px" alt="SIRIN logo"/> SIRIN: Semantic Inconsistency Recognition and Inspection Nexus

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/🤗%20Transformers-4.50%2B-blue)](https://huggingface.co/docs/transformers)
[![Hydra](https://img.shields.io/badge/Hydra-1.3%2B-blue)](https://hydra.cc/)

SIRIN is a Python library for detecting and analyzing contextual inconsistencies in systems that use LLMs. The library provides state-of-the-art methods for two complementary tasks: (1) **hallucination detection** — identifying when LLM outputs contain information that contradicts or cannot be supported by the provided context, and (2) **query answerability detection** — determining whether a given prompt/question can be answered based on the provided context (i.e., whether the prompt is aligned with the context).

Both tasks are supported at **sequence-level** and **token-level** granularities, enabling researchers and practitioners to evaluate LLM outputs and inputs with high precision. SIRIN leverages three complementary detection paradigms: (1) **llm-as-a-judge** approaches that fine-tune lightweight adapters on model representations, (2) **probing-based methods** that train classifiers on frozen LLM internal features (hidden states, attention weights, etc.), and (3) **uncertainty quantification** techniques that analyze prediction uncertainty signals.

## 📑 Table of Contents

- [SIRIN: Semantic Inconsistency Recognition and Inspection Nexus](#sirin-semantic-inconsistency-recognition-and-inspection-nexus)
  - [📑 Table of Contents](#-table-of-contents)
  - [🌟 Key Features](#-key-features)
  - [🖼️ UI](#ui)
  - [🧩 Architecture \& Overview](#-architecture--overview)
    - [Detection Tasks](#detection-tasks)
    - [Detection Granularities](#detection-granularities)
    - [Target Approximation](#target-approximation)
    - [Context Splitting (Dynamic Context Segmentation + Aggregation)](#context-splitting-dynamic-context-segmentation--aggregation)
    - [Probing Detectors (`ProbingPipeline`)](#probing-detectors-probingpipeline)
    - [Judge-Based Detectors (`JudgePipeline`)](#judge-based-detectors-judgepipeline)
    - [Uncertainty Detectors (`UncertaintyPipeline`)](#uncertainty-detectors-uncertaintypipeline)
  - [📊 Experiment Tracking](#-experiment-tracking)
  - [⚙️ Configuration with Hydra](#️-configuration-with-hydra)
  - [📋 Dataset Format](#-dataset-format)
    - [Sequence-Level Format](#sequence-level-format)
    - [Token-Level Format](#token-level-format)
  - [📚 Usage Examples](#-usage-examples)
    - [Example 1: Sequence-Level Probing with Ensemble Features and Context Splitter](#example-1-sequence-level-probing-with-ensemble-features-and-context-splitter)
    - [Example 2: Token-Level Probing with Uncertainty Features](#example-2-token-level-probing-with-uncertainty-features)
    - [Example 3: Sequence-Level Uncertainty Aggregation](#example-3-sequence-level-uncertainty-aggregation)
    - [Example 4: Judge-Based Detection with LoRA](#example-4-judge-based-detection-with-lora)
    - [Example 5: Judge-Based Detection with API LLM](#example-5-judge-based-detection-with-api-llm)
  - [📄 License](#-license)
  - [References](#references)

## 🌟 Key Features

- 🎯 **Dual-task support**: Hallucination detection and query answerability detection using unified infrastructure
- 🔍 **Multi-granularity**: Sequence-level and token-level detection for precise localization
- 🔀 **Flexible classification**: Binary and ternary NLI-style classification modes
- 🛠 **Modular architecture**: Extensible detectors and feature processors with inheritance-based design
- 🎛 **Hydra configuration**: YAML-based configs for experiment management and reproducibility
- 📈 **Advanced features**: Layer-specific extraction, pooling strategies, normalization, and dimensionality reduction
- 🔄 **Target approximation**: Automatic label generation for unlabeled or noisy data
- 🌐 **Multi-backend**: Whitebox (HuggingFace) and blackbox (OpenAI API) inference support

## UI

Install and start the Streamlit UI from the repository root:

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[ui]'
python -m streamlit run sirin/ui/streamlit_app.py
```

Open the URL printed by Streamlit (for instance `http://localhost:8501`). In the sidebar, select a generator and detector (choose a zero-shot preset if you do not have a trained checkpoint), then enter a context and question in the chat box. API-backed options require the corresponding provider key and confirmation of external API calls. See [the UI guide](docs/ui.md) for details.

## 🧩 Architecture & Overview

SIRIN is organized around three main detector families, each designed to capture different aspects of model behavior for detecting contextual inconsistencies. Every detector is integrated with a high-level training and evaluation pipeline that automates common tasks such as data loading, feature extraction, model training, metric computation, checkpointing, and experiment logging.

### Detection Tasks

The library supports two primary detection tasks, which can be specified via the `task_type` parameter in pipeline configurations:

- **Hallucination Detection** (`DetectionTaskType.HALLUCINATION_DETECTION`): Evaluates whether model-generated responses contain factual inaccuracies, unsupported claims, or content that contradicts the provided context. This is the primary use case for identifying when LLMs 'hallucinate' information not present in the source material.
  
- **Query Answerability Detection** (`DetectionTaskType.QUERY_ANSWERABILITY`): Determines whether a given prompt/question can be answered based on the provided context. This task verifies prompt-context alignment — identifying cases where the prompt asks for information that isn't available in the context (i.e., unanswerable questions). This is particularly useful for evaluating retrieval-augmented generation (RAG) systems, ensuring that only answerable questions are processed.

Both tasks share the same detector infrastructure and can be addressed using any of the three detector families (probing, judge-based, or uncertainty-based methods), with appropriate task-specific labeling and evaluation metrics.

### Detection Granularities

The library supports detection at two complementary granularities, enabling users to choose the appropriate level of detail for their use case:

- **Sequence-level detectors**:  
  - **Input**: A complete input sequence, typically consisting of a context (prompt/document) and a response (model output) or query (for answerability tasks).  
  - **Output**: A single binary or multi-class label per sequence indicating whether the response contains hallucinations (or whether the query is answerable, depending on the task).
  - **Use cases**: Fast screening of entire responses or queries, batch processing, scenarios where fine-grained localization is not required.

- **Token-level detectors**:  
  - **Input**: A sequence along with target spans or token-level annotations indicating specific regions of interest (e.g., the model's generated answer, or specific parts of the query).  
  - **Output**: A prediction for every token (or character) in the sequence, producing dense annotations that enable precise localization of problematic content or unanswerable query segments.
  - **Use cases**: Detailed analysis of response quality or query structure, identifying specific hallucinated phrases or unanswerable query components, explainability and interpretability research, improving model outputs through targeted feedback.

Both detector types share the same unified pipeline infrastructure, ensuring consistent training procedures, evaluation metrics, and integration capabilities across the entire library.

### Target Approximation

When working with real-world datasets, ground-truth labels may be unavailable, expensive to obtain, or noisy. SIRIN addresses this challenge through **target approximation**: pipelines support an optional `target_approximator` component that automatically generates proxy labels using semantic uncertainty metrics, entropy-based approaches, or other unsupervised signals. This enables researchers to bootstrap detection models even when labeled data is scarce [[1]](https://arxiv.org/abs/2406.15927).

### Context Splitting (Dynamic Context Segmentation + Aggregation)

SIRIN now provides the **ContextSplitter**, a modular system for splitting long contexts into smaller units, running detectors independently on each segment, and then aggregating the results.

- **Supported Splitting Strategies**
  - **Character-level splitting**
  - **Sentence-level splitting**
  - **Paragraph-level splitting**
  - **Langchain chunking** (use Langchain splitting capabilities)

- **Aggregation Modes** — after running a detector on each split, SIRIN aggregates results via:
  - `max` — highlight any detected inconsistency
  - `min` — if any segment is consistent
  - `mean` — smooth confidence across segments
  - `vote` — voting-based decision

### Probing Detectors (`ProbingPipeline`)

Probing detectors train lightweight classifiers on **frozen** LLM internal representations, treating the underlying model as a fixed feature extractor. This approach is highly data-efficient, computationally efficient, and provides interpretable features that correspond to known model internals. By analyzing hidden states, attention patterns, and other intermediate representations without modifying the base model, probing methods can reveal which internal signals correlate with hallucination behavior.

**Classifier backends** (choose based on dataset size and feature characteristics):

- `TokenTabPFNProbingDetector` / `SequenceTabPFNProbingDetector`: Leverages TabPFN, an in-context learning transformer that excels with small datasets (often <1000 samples) by learning to generalize from few examples. Particularly effective when labeled data is scarce [[2]](https://arxiv.org/abs/2505.23299).  
- `TokenCatboostProbingDetector` / `SequenceCatboostProbingDetector`: Gradient-boosted decision trees that are robust to feature scale variations, multicollinearity, and mixed data types. Excellent default choice for medium-to-large datasets with complex feature interactions.  
- `TokenLinearProbingDetector` / `SequenceLinearProbingDetector`: Employs attention-weighted aggregation to pool sequences into a single vector representation, followed by a linear classifier. Inspired by attention-based pooling methods that learn to weight informative tokens [[3]](https://arxiv.org/abs/2312.17249).

**Feature processors** extract and transform internal model representations into usable features:

- `HiddensProcessor`: Extracts hidden states from feed-forward network (FFN) outputs at specified layers. These dense representations capture semantic and syntactic information encoded by the model.
- `SublayersProcessor`: Captures intermediate states after attention blocks but before FFN layers, providing access to post-attention representations that combine information from multiple positions.
- `AttentionsProcessor`: Aggregates attention weight matrices into summary statistics (e.g., entropy, max attention, mean attention) to quantify how the model distributes attention across the input sequence.
- `LookbacksProcessor`: Computes Lookback Lens features [[4]](https://arxiv.org/abs/2407.07071), which analyze attention patterns to detect when the model 'looks back' to earlier context tokens while generating responses, revealing potential inconsistencies.
- `MTopDivFeatureProcessor`: Computes Manifold Topology Divergence features [[5]](https://arxiv.org/abs/2504.10063) by analyzing the topological structure of attention graphs. These features capture geometric properties that may indicate hallucination patterns.
- `LogitsProcessor`: Extracts raw output logits (pre-softmax probabilities) from the model, providing direct access to the model's predicted token distributions for uncertainty and confidence analysis.

> All feature processors now support **configurable pooling strategies** over token dimensions. Specify `pooling_type` in your config (e.g., `'mean'`, `'max'`, `'last'`, or `'none'`) to control how token-level representations are aggregated into sequence-level inputs for classifiers. This enables fine-grained adaptation to task structure without modifying code.

**Customization options** for fine-tuning feature extraction:

- **Layer selection**: Specify arbitrary transformer layers using `layers=[5, 10, -1]` (where negative indices count from the end). This enables analysis of how representations evolve across model depth, or focusing on specific layers known to be informative for your task.
- **Token/position selection**: The `TokenLocator` system allows targeting specific token positions such as answer boundaries, end-of-sequence tokens, or custom substrings. This is crucial for sequence-level detection and ensures features are extracted from the relevant portions of the sequence.
- **Cleaners**: Preprocess raw text using the cleaner stack built from classes such as `RegexCleaner`, `HTMLCleaner`, `CodeCleaner` and `CustomCleaner`. These components normalize and sanitize inputs by removing markup, stripping code fences, filtering regex-defined noise, and applying user-defined cleanup logic.
- **Ensemble processing**: Combine multiple processors via `EnsembleProcessor` to create rich feature representations that capture complementary signals. Optionally apply per-processor MLPs to learn optimal feature combinations.
- **Feature scaling**: Built-in support for per-feature or per-layer normalization using `StandardScaler` (z-score normalization), `MinMaxScaler` (min-max scaling to [0,1]), or `RobustScaler` (robust to outliers using median and IQR). Essential for models sensitive to feature scale.
- **Adaptive compression**: Automatic dimensionality reduction via PCA or UMAP when feature dimensions exceed a configurable threshold. This prevents memory issues and can improve generalization by removing noise in high-dimensional spaces.


### Judge-Based Detectors (`JudgePipeline`)

Judge-based detectors **fine-tune lightweight adapter-based classifiers** directly on LLM representations, allowing the model to learn task-specific patterns while keeping most parameters frozen. This approach leverages the full representational power of pre-trained models while maintaining training efficiency and avoiding catastrophic forgetting.

- **Decoder-only models**: `TokenDecoderJudge` / `SequenceDecoderJudge` are designed for autoregressive models like Llama, Qwen, Mistral, and GPT-family models. They process sequences in a causal manner and can leverage generation-time representations.
- **Encoder models**: `TokenEncoderJudge` / `SequenceEncoderJudge` work with bidirectional encoder models such as BERT, ModernBERT, and RoBERTa. These are well-suited for understanding-based tasks where full bidirectional context is beneficial.
- **API-based models**: `TokenOpenAIJudge` / `SequenceOpenAIJudge` enable hallucination detection using OpenAI's API, allowing you to analyze proprietary models without local access while leveraging OpenAI's infrastructure for feature extraction.

All judge-based detectors support **LoRA (Low-Rank Adaptation)** and other Parameter-Efficient Fine-Tuning (PEFT) methods, enabling efficient training that modifies only a small subset of model parameters while preserving the original model's capabilities.

### Uncertainty Detectors (`UncertaintyPipeline`)

Uncertainty-based detectors leverage the principle that **uncertain predictions often correlate with hallucinations**: when a model is uncertain about its output, it may be more likely to generate content that contradicts the provided context. These detectors apply calibrated thresholds or simple statistical models to uncertainty scores computed via the `lm-polygraph` library [[6]](https://arxiv.org/abs/2311.07383), providing a lightweight and interpretable approach to hallucination detection that requires minimal training data.

**Uncertainty feature processors** extract uncertainty signals at different granularities:

- **`TokenUncertaintyFeatureProcessor`**: Computes token-level uncertainty metrics that quantify the model's confidence for individual tokens. 
  - Available methods include: `TokenEntropy` (Shannon entropy of token distribution), `MaximumTokenProbability` (confidence of the most likely token), and ensemble prediction-based methods (EPT and PET families) that analyze variance across multiple model forward passes or predictions.
  
- **`SequenceUncertaintyFeatureProcessor`**: Aggregates uncertainty signals across entire sequences to provide holistic estimates of response reliability.
  - Available methods include: `MonteCarloSequenceEntropy` (uncertainty via multiple sampling runs), `Perplexity` (average negative log-likelihood), `LexicalSimilarity` (consistency metrics), spectral graph methods (`EigValLaplacian`, `EigenScore`), and various sequence-level aggregation strategies (`SAR`, `PTrue`, `FisherRao`).

Both processors support **whitebox** (local HuggingFace models with full access to internals) and **blackbox** (OpenAI API with logprobs access) inference modes, making uncertainty-based detection applicable across a wide range of deployment scenarios.


## 📊 Experiment Tracking

SIRIN provides a pluggable experiment logging interface via `sirin.loggers.LoggerBase`. You can choose from:

- `WandbLogger` (Weights & Biases)  —  requires `wandb` 
- `TensorBoardLogger`  —  requires `tensorboard`
- `ClearMLLogger`  —  requires `clearml`
- `CometLogger`  —  requires `comet-ml`
- `MultipleLoggers`  —  combine multiple loggers for simultaneous logging to different backends

## ⚙️ Configuration with Hydra

You can instantiate the entire pipeline from YAML using Hydra. Example:

```
python scripts/train.py pipeline.detector.batch_size=32 pipeline.train_args.max_epochs=10
```

See `configs/` for modular YAML components:
- `model`: base model adapters
- `feature_processor`: processors (hiddens, attentions, lookbacks, etc.)
- `detector`: different detectors (probing-based, judges, uncertainty quantification, etc.)
- `pipeline`: train-evaluation pipelines

## 📋 Dataset Format

SIRIN expects **huggingface dataset** in a standardized format for both training and evaluation. Each sample must contain an `'input'` field and a `'target'` field, with the structure depending on the detection granularity (sequence-level vs. token-level).

### Sequence-Level Format

For sequence-level tasks (binary or ternary classification):

- **`'input'`**: A numpy array of conversation messages, where each message is a dictionary with:
  - `'content'`: The text content of the message
  - `'role'`: The role of the message sender (e.g., `'user'`, `'assistant'`)
  
  Example:
  ```python
  array([
      {'content': 'Context and question text...', 'role': 'user'},
      {'content': 'Model response text...', 'role': 'assistant'}
  ], dtype=object)
  ```

- **`'target'`**: A numpy integer label indicating the classification:
  - **Binary task**: `np.int64(0)` for negative class, `np.int64(1)` for positive class
  - **Ternary task**: `np.int64(0)`, `np.int64(1)`, or `np.int64(2)` for three-way (NLI-style) classification

### Token-Level Format

For token-level tasks (span-based hallucination detection):

- **`'input'`**: Same format as sequence-level (array of conversation messages with `'content'` and `'role'` fields)

- **`'target'`**: A numpy array containing lists of hallucination spans. Each span is represented as `[start_token_index, end_token_index]` (inclusive start, exclusive end):
  ```python
  array([array([61, 75])], dtype=object)  # Single span from character 61 to 75
  array([array([10, 20]), array([50, 60])], dtype=object)  # Multiple spans
  ```

The token indices refer to positions in the tokenized sequence, allowing precise localization of problematic content within the model's output.

## 📚 Usage Examples

Below are Python examples demonstrating how to use different detector types. You can also instantiate the entire pipeline using Hydra (see [Configuration with Hydra](#⚙️-configuration-with-hydra)).

### Example 1: Sequence-Level Probing with Ensemble Features and Context Splitter

Train a sequence-level detector using ensemble features from multiple processors:

```python
from sirin.definitions import AggregationMethod, ClassificationMetric, SplitStrategy
from sirin.detection.probing import ProbingPipeline, SequenceLinearProbingDetector
from sirin.detection.processors.ensemble import EnsembleProcessor
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig
from sirin.models.detection import *

# Token locator (answer boundary)
token_locator_config = TokenLocatorConfig(locate_answer_start=True)

# Define processors with pooling types
processor_configs = [
    HiddensProcessorConfig(token_locator_config=token_locator_config, layers=[14], pooling_type='mean'),
    HiddensProcessorConfig(token_locator_config=token_locator_config, layers=[14], pooling_type='max'),
]

# Backbone LLM adapter
extractor = HfModelAdapter(
    config=HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda')
)

# Ensemble processor
ensemble_processor = EnsembleProcessor(
    config=EnsembleProcessorConfig(processor_configs=processor_configs),
    extractor=extractor,
)

# Detector and pipeline
detector = SequenceLinearProbingDetector(
    config=ProbingDetectorConfig(
        max_length=128, # answer hiddens padding length
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
            metrics=[
                ClassificationMetric.F1,
                ClassificationMetric.ROC_AUC,
            ],
        ),
    ),
    detector=detector,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    generator_adapter=extractor,
)

train_results = pipeline.train()
detector.save('./models/ensemble_detector')
```

Inference:

```python
detector = SequenceLinearProbingDetector(
    config=ProbingDetectorConfig(),
    feature_processor=ensemble_processor,
)
detector.load('./models/ensemble_detector')

sample = [
    {'role': 'user', 'content': 'What is H2O?'},
    {'role': 'assistant', 'content': 'Water.'}
]
result = detector.detect([sample])
```

### Example 2: Token-Level Probing with Uncertainty Features

Train a token-level detector using uncertainty-based features:

```python
from sirin.detection.probing import ProbingPipeline
from sirin.detection.probing.detectors.token import TokenTabPFNProbingDetector
from sirin.detection.processors.uncertainty import TokenUncertaintyFeatureProcessor

from sirin.models.detection import (
    UncertaintyFeatureProcessorConfig, ProbingDetectorConfig,
    ProbingPipelineConfig, TrainingArgsConfig
)
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig

# Uncertainty features
extractor = HfModelAdapter(HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))
feature_processor = TokenUncertaintyFeatureProcessor( # you can use other processors like HiddensProcessor
    config=UncertaintyFeatureProcessorConfig(
        uncertainty_methods=['TokenEntropy', 'MaximumTokenProbability'],
    ),
    extractor=extractor
)

# Max pooling over token-level uncertainty
detector = TokenTabPFNProbingDetector(
    config=ProbingDetectorConfig(batch_size=16),
    feature_processor=feature_processor
)

pipeline = ProbingPipeline(
    config=ProbingPipelineConfig(train_args=TrainingArgsConfig(max_epochs=5)),
    detector=detector,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    generator_adapter=extractor
)
train_results = pipeline.train()
eval_results = pipeline.eval()
```

### Example 3: Sequence-Level Uncertainty Aggregation

Evaluate not calibrated (without any extra classification) uncertainty detector:

```python
from sirin.detection.uncertainty import SequenceUncertaintyDetector, UncertaintyPipeline
from sirin.detection.processors import SequenceUncertaintyFeatureProcessor
from sirin.inference.adapters import HfModelAdapter
from sirin.models.inference import HFConfig
from sirin.models.detection import *

# Uncertainty features
extractor = HfModelAdapter(HFConfig(model_path='Qwen/Qwen2.5-3B-Instruct', device='cuda'))
feature_processor = SequenceUncertaintyFeatureProcessor(
    config=UncertaintyFeatureProcessorConfig(uncertainty_methods=['MeanTokenEntropy', 'RAUQ']),
    extractor=extractor,
)

# Mean pooling over sequence-level uncertainty
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
eval_results = pipeline.eval() # do not need training but outputs are not calibrated uncertainty scores
```

### Example 4: Judge-Based Detection with LoRA

Train a decoder-based judge using LoRA for parameter-efficient fine-tuning:

```python
from peft import LoraConfig
from transformers import TrainingArguments

from sirin.detection.judging import JudgePipeline, SequenceDecoderJudge
from sirin.inference.adapters import HfModelAdapter
from sirin.models.detection import HfJudgeConfig, JudgePipelineConfig
from sirin.models.inference import HFConfig

lora_config = LoraConfig(
    r=16, lora_alpha=32, target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM'
)

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

### Example 5: Judge-Based Detection with API LLM

Detect with API-based models (openrouter, openai):

```python
from sirin.detection.judging import SequenceOpenAIJudge
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig
from sirin.models.inference import OpenAIConfig

model = OpenAIModelAdapter(OpenAIConfig(model_path='gpt-3.5-turbo'))
judge = SequenceOpenAIJudge(config=OpenAIJudgeConfig(user_prompt='your prompt'), model_adapter=model)

sample = [
    {'role': 'user', 'content': 'What is H2O?'},
    {'role': 'assistant', 'content': 'Water.'},
]
result = judge.detect([sample])
print(result)
```

## 📄 License

Apache License 2.0

## References

[1] Semantic-uncertainty/entropy-style target approximation (2024). arXiv:2406.15927. https://arxiv.org/abs/2406.15927

[2] Belikova, J., Polev, K., Parchiev, R., Simakov, D. Data-efficient Meta-models for Evaluation of Context-based Questions and Answers in LLMs (2025). arXiv:2505.23299. https://arxiv.org/abs/2505.23299

[3] CH-Wang, S., Van Durme, B., Eisner, J., Kedzie, C. Do Androids Know They're Only Dreaming of Electric Sheep? (2024). arXiv:2312.17249. https://arxiv.org/abs/2312.17249

[4] Chuang, Y.-S., Qiu, L., Hsieh, C.-Y., Krishna, R., Kim, Y., Glass, J. Lookback Lens: Detecting and Mitigating Contextual Hallucinations in Large Language Models Using Only Attention Maps (2024). arXiv:2407.07071. https://arxiv.org/abs/2407.07071

[5] Bazarova, A., Yugay, A., Shulga, A., et al. Hallucination Detection in LLMs with Topological Divergence on Attention Graphs (2025). arXiv:2504.10063. https://arxiv.org/abs/2504.10063

[6] Fadeeva, E., Vashurin, R., Tsvigun, A., Vazhentsev, A., Petrakov, S., Fedyanin, K., Vasilev, D., Goncharova, E., Panchenko, A., Panov, M., Baldwin, T., Shelmanov, A. LM-Polygraph: Uncertainty Estimation for Language Models (2023). arXiv:2311.07383. https://arxiv.org/abs/2311.07383  —  GitHub: https://github.com/IINemo/lm-polygraph
