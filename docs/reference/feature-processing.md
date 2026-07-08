# Feature Processing and Model Internals

## Contents

- [Side Selection Guide (Critical for Task Performance)](#side-selection-guide-critical-for-task-performance)
- [Attention Implementation Guide](#attention-implementation-guide)
- [Component Reference](#component-reference)

## Side Selection Guide (Critical for Task Performance)

Choosing the correct `SideType` for your feature processor is **critical** - the wrong side will produce near-random metrics regardless of detector quality.

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
| **Query answerability** | `LEFT` | `last` | The probe must assess **context quality** - whether retrieved memories contain enough information. The last LEFT token (right before generation) encodes the model's readiness state. |
| **LookbacksProcessor** | `RIGHT` (always) | `mean` | Lookback ratios are only computed for tokens **after** the `border` (answer start). LEFT-side lookback values are all zeros. |

### Common mistake

Using `SideType.LEFT` for hallucination detection is the most common error. It appears to work (AUC > 0.5) because unanswerable samples (always label=0) have different context features from answerable ones. But the classifier is really doing partial answerability detection, not hallucination detection - it cannot distinguish "answerable + correct" from "answerable + wrong."

### `max_length` with pooling

When `pooling_type` is `'mean'`, `'max'`, or `'last'`, the feature processor reduces the token dimension to 1. Set `ProbingDetectorConfig(max_length=1)` to match; the default `max_length=128` would pad zeros and cause a shape mismatch in `LinearClassifier`.

---

## Attention Implementation Guide

### `attn_implementation` and `output_attentions`

`HFConfig.attn_implementation` is set at model load time and **cannot be changed per-call**.

| Implementation | `output_attentions=True` | Speed | Use when |
|---|---|---|---|
| `'eager'` | Supported | Slowest | Need attention weights (LookbacksProcessor, AttentionsProcessor) |
| `'sdpa'` | **NOT supported** - returns `None`/empty tuple, causes `IndexError` | Fast | Only need hidden states or logits |
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
# WRONG - indices from 36-layer hidden space, out of range for 8-layer attention
ensemble_hiddens_layers = get_several_layers(num_hidden_layers, 'middle+last:3', negative_only=True)

# CORRECT - indices within attention output range
ensemble_hiddens_layers = get_several_layers(n_attn_layers, 'middle+last:3', negative_only=True)
```

### EnsembleProcessor layer filtering

`EnsembleProcessor._unify_processor_args()` merges layer lists from all sub-processors into one unified list. `generate_features()` stores it as `self._unified_layers`. In `_extract_processor_features_subset()`, features from the unified output are filtered to only the sub-processor's own layers before caching. Without this filtering, the cache saver would receive N unified-layer features but validate against the sub-processor's M-layer list (N != M -> `ValueError`).

A bounds check raises a clear error if a sub-processor's layer indices exceed the actual feature count (can happen when attention returns fewer tensors than the unified layer list).

### LookbacksProcessor `attention_heads` field

`LookbacksProcessorConfig.attention_heads` selects specific attention heads by index. Useful for GQA models where heads within a KV group are correlated:

```python
# Qwen3.5-35B-A3B: 16 query heads, 2 KV groups -> heads [0,8] are group representatives
lookback_config = LookbacksProcessorConfig(
    layers=list(range(10)),
    attention_heads=[0, 8],  # 2 independent heads x 10 layers = 20 features
    ...
)
```

### Lookback feature dimensions

Lookback output dimension = `num_attention_heads x num_layers` (or `len(attention_heads) x num_layers` if filtered). After pooling (`mean`/`max`/`last`), shape is `(1, dim)`.

| Model | Heads | Attention layers | Features (all heads) | Features (1/KV-group) |
|-------|-------|-----------------|---------------------|-----------------------|
| Qwen3.5-4B | 16 | 8 | 128 | 16 (2 heads x 8) |
| Qwen3.5-35B-A3B | 16 | 10 | 160 | 20 (2 heads x 10) |

For short-answer QA (e.g., LongMemEval, 67% answers <=3 words), lookback features have limited discriminative power: mean lookback ratios cluster in 0.64-0.94, and GQA correlation reduces effective independent features. Use PCA denoising (`target_dimensions=32`) rather than `CompressionMethod.NONE`.

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

## Component Reference

### Feature Processors - What Each Extracts

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

### Model Adapters - Capabilities

| Adapter | Internal Access | Generation | Multi-GPU | API |
|---------|----------------|------------|-----------|-----|
| `HfModelAdapter` | hiddens, attention, logits, sublayers | yes | device_map | no |
| `VllmModelAdapter` | limited | high-throughput | yes | no |
| `OpenAIModelAdapter` | logprobs only | yes | n/a | yes |

### Detectors - 3x3 Matrix

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
