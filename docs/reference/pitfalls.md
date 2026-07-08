# Pitfalls, Compatibility, and Environment

## Contents

- [Critical Pitfalls](#critical-pitfalls)
- [Vendored Dependencies](#vendored-dependencies)
- [Environment](#environment)

## Critical Pitfalls

### 1. Data Leakage with `side=RIGHT`

When probing for hallucination/answerability where the **target label is derived from the prediction text** (e.g. F1 of prediction vs gold), using `side=RIGHT` (answer tokens) causes data leakage - the hidden states encode the answer string, so a classifier trivially learns "which answers are correct" and gets ROC-AUC=1.0.

**Fix**: Use `side=LEFT` with `pooling_type='last'` to probe the model's internal state at the last context token *before* the answer starts. This captures whether the model "knows" the context is sufficient - the actual research question.

```python
# WRONG - leaks the answer into features
processor_config = HiddensProcessorConfig(
    separate=True,
    side=SideType.RIGHT,   # answer tokens -> data leakage
    pooling_type='mean',
)

# CORRECT - probes pre-answer state
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
- Qwen3.5-35B-A3B: 40 hidden layers, 10 attention blocks -> hiddens indices 0..40, attention indices 0..9
- Qwen3.5-4B: 36 hidden layers, 8 attention blocks -> hiddens indices 0..36, attention indices 0..7
- Qwen2.5-3B-Instruct: 36 layers (dense) -> all indices 0..36

### 3. Instantiation Order is Strict

Components must be created in this exact order (each depends on the previous):

```python
# 1. Model adapter (extractor)
adapter = HfModelAdapter(config=model_config)

# 2. Feature processor (needs extractor)
processor = HiddensProcessor(config=proc_config, extractor=adapter)

# 3. Detector (needs feature_processor - calls setup_extractor() + _cold_run())
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
# WRONG - no validation, CatBoost reports train metrics (ROC-AUC=1.0)
pipeline = ProbingPipeline(
    ...,
    train_dataset=Dataset.from_dict({...}),
)

# CORRECT - proper train/val split, realistic metrics
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

The `val_size` field in `TrainingArgsConfig` does NOT create this split - it's only used by the Linear probe's internal training loop for epoch-level early stopping, not for final metric evaluation.

### 6. Pre-Computed Answers Skip Generation (but break Uncertainty)

If the dataset's `input` column already has `role: 'assistant'` as the last message, the **probing** pipeline skips answer generation automatically. For `task_type=QUERY_ANSWERABILITY`, generation is always skipped regardless.

**However, the uncertainty pipeline always generates its own answers** (lm-polygraph's `GreedyProbsCalculator` calls `model.generate()`, ignoring pre-computed text in `target_texts`). If you pass pre-computed answers to the uncertainty pipeline, they are silently ignored - uncertainty is computed on different text than your labels describe, giving ROC-AUC=0.5.

For uncertainty: strip `role: 'assistant'` messages from the input and let the model generate.

**Critical:** For inputs with `[system, user, assistant]` format, `SequenceUncertaintyFeatureProcessor` and `TokenUncertaintyFeatureProcessor` automatically merge all non-assistant messages into the prompt. The canonical 2-message `[user, assistant]` format is passed through unchanged. You no longer need to manually merge system + user into `sample[0]`.

```python
# Both formats work - processor handles merging automatically
[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': answer}]
[{'role': 'user', 'content': f"{SYSTEM_PROMPT}\n\n{prompt}"}, {'role': 'assistant', 'content': answer}]
```

**Also critical:** lm-polygraph's `WhiteboxModel` defaults to `instruct=False`, which raw-tokenizes strings without applying the chat template. Instruct models (Qwen, Llama-3, etc.) need `<|im_start|>`/`<|im_end|>` markers to understand the prompt. Without them, the model generates incoherent text and uncertainty is random. Fix: pass `instruct=True` via `model_kwargs`:

```python
# WRONG - raw tokenization, no chat template markers
UncertaintyFeatureProcessorConfig(
    uncertainty_methods=methods,
    max_new_tokens=64,
)

# CORRECT - applies tokenizer.apply_chat_template() before tokenizing
UncertaintyFeatureProcessorConfig(
    uncertainty_methods=methods,
    max_new_tokens=64,
    model_kwargs={'instruct': True},
)
```

### 7. Attention Implementation Constraints

| Implementation | Speed | Returns attention tensors? | Use for |
|---------------|-------|----------------------------|---------|
| `eager` | Slowest | Yes | LookbacksProcessor, AttentionsProcessor, `SelfCertainty`, `AttentionScore`, RAUQ/focus-style methods |
| `sdpa` | Fast | No in the HF `output_attentions` path | Hidden/logit features and uncertainty methods that do not need attention tensors |
| `flash_attention_2` | Fastest | No | Same as `sdpa`, when installed and supported |

The UI zero-shot uncertainty presets deliberately use only sdpa-safe methods (`MeanTokenEntropy`, `Perplexity`, `TokenEntropy`, `MaximumTokenProbability`). Switch the extractor to `attn_implementation='eager'` before using attention-dependent processors or uncertainty methods.

### 8. Feature Cache Invalidation

When changing `side`, `pooling_type`, or `layers` in the processor config, **delete the feature cache directory** before re-running. Cached features from a previous config will be silently reused with wrong settings:

```python
import shutil
cache_dir = Path('./feature_cache')
if cache_dir.exists():
    shutil.rmtree(cache_dir)
```

### 9. Three Different batch_size Configs

There are 3 `batch_size` parameters at different levels - they are NOT interchangeable:

```
pipeline.train()
|
|- DetectorConfig.batch_size (default=1)
|  How many samples are sent to the feature processor per iteration.
|
|  `- HFConfig.batch_size (default=4)
|     How many samples the LLM forward-passes at once (GPU memory bottleneck).
|     If detector sends more, the @batch_processor decorator auto-chunks.
|
`- TrainingArgsConfig.train_batch_size (default=256)
   DataLoader batch size for training the classifier (CPU/RAM, not GPU).
```

| Config | Controls | Memory impact | Recommendation |
|--------|----------|--------------|----------------|
| `HFConfig.batch_size` | Model forward pass | **GPU VRAM** | **1** for 30B+ models, **4-8** for 3B |
| `DetectorConfig.batch_size` | Feature extraction loop | Intermediate tensors | Same as HFConfig or slightly higher |
| `TrainingArgsConfig.train_batch_size` | Classifier training | CPU/RAM only | **64-256** (default is fine) |

### 10. Cold_run n_features Bug with Multiple Probe Layers (FIXED in base.py:75)

When using multiple probe layers (`PROBE_LAYERS = [layer_a, layer_b]`), `ProbingDetectorBase._cold_run()` computes a different `n_features` denominator than `FeaturePreprocessor.fit()`, causing the `LinearClassifier` to be initialized with wrong query dimensions.

- **`_cold_run` (base.py:75)**: `n_features = sum(feature[0].shape[-1])` - uses `emb_dim` only
- **`FeaturePreprocessor.fit()` (preprocessor.py:124)**: `feature_n_features = num_tokens * emb_dim * num_layers`

With 2 layers and 2560 hidden dim: cold_run gets `n_features=2560`, preprocessor gets `5120`. This produces query dim=256 but PCA output=128, causing `RuntimeError: mat1 and mat2 shapes cannot be multiplied`.

**Fix applied**: Changed `base.py:75` from `.shape[-1]` to `.numel()` to match the preprocessor's calculation.

Additionally: set `max_length=1` in `ProbingDetectorConfig` when using `pooling_type='last'` to avoid padding pooled features to 128 positions.

### 11. CompressionConfig Field Names

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

- `sirin/detection/lm-polygraph/` is vendored for uncertainty estimation. Do not edit it directly; add runtime compatibility patches in `sirin/detection/_lm_polygraph_compat.py`.
- `_lm_polygraph_compat.py` currently patches transformer generation aliases, `HybridCache`, DeBERTa tokenization, blackbox `base_url`/`top_logprobs`, and log-softmax generation scores.
- Legacy TabPFN fitted checkpoints are loaded through `sirin/detection/probing/detectors/utils/tabpfn_compat.py`; keep checkpoint compatibility there rather than editing saved archives or vendor packages.
- `sirin/detection/tabpfn_wide/` is a git submodule from `github.com/pfeiferAI/TabPFN-Wide.git`.

## Environment

Activate your preferred Python environment first, then set the credentials and device variables you need:

```bash
export HF_TOKEN=...
export OPENAI_API_KEY=...
export CUDA_VISIBLE_DEVICES=0
```
