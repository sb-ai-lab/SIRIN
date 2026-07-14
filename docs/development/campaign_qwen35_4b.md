# Qwen3.5-4B campaign — metrics summary

Probe/UE/judge results for the Qwen3.5-4B detector campaign packaged into the SIRIN UI
(PsiloQA span stage P5, LongMemEval stages P5+L5). Every number is transcribed verbatim from the
recorded `sirin_metrics.json` / checkpoint `metrics.json` files (rounded to 4 digits, no
cherry-picking). Probe model / hidden-state extractor: **Qwen/Qwen3.5-4B** rev
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

## PsiloQA span (`psiloqa_en_span`)

Held-out split: `validation` n=298, `test` n=1098. Positive rate is high (≈0.96 of answers carry at
least one hallucinated span), so **ROC** and per-character **IoU** are the honest signals; the
sequence average-precision (~0.99) is inflated by that class imbalance.

### Token / character level (per-character hallucination)

| detector | ROC (test) | AP (test) | F1 (test) | IoU (test) | ROC (val) | IoU (val) |
|---|---|---|---|---|---|---|
| Token Linear probe (layer 16, seed 13, τ=0.3851) | 0.7656 | 0.7725 | 0.7542 | 0.6273 | 0.8229 | 0.6349 |
| Token CatBoost (layer 16) | 0.7633 | 0.7689 | 0.7576 | 0.6364 | 0.8152 | 0.6348 |
| Token TabPFN (layer 16, 25k-token stratified subsample, PCA-100, GPU) | 0.7511 | 0.7650 | 0.7492 | 0.6174 | 0.7916 | 0.6239 |
| UE · MaximumTokenProbability | 0.5585 | 0.5784 | 0.6964 | 0.4572 | 0.5647 | 0.4626 |
| UE · TokenEntropy | 0.5650 | 0.5984 | 0.6964 | 0.4572 | 0.5712 | 0.4626 |
| Judge · API Token (span-tag, test) | 0.6469 | 0.6358 | 0.7154 | 0.5220 | — | — |

Token Linear is the probe bundled at `demo/checkpoints/qwen35_4b_psiloqa_span_linear` and wired into
the `Probing — Token Linear · PsiloQA/Qwen3.5-4B` preset. τ is `validation_f1_optimal`.

### Sequence / answer level (answer-level hallucination classification)

| detector | ROC (test) | AP (test) | F1 (test) | ROC (val) | threshold |
|---|---|---|---|---|---|
| Sequence CatBoost | 0.9330 | 0.9967 | 0.9859 | 0.9126 | 0.8362 |
| Sequence Linear | 0.9260 | 0.9966 | 0.9825 | 0.8907 | 0.8927 |
| Sequence TabPFN | 0.9362 | 0.9969 | 0.9859 | 0.8910 | 0.4233 |
| UE · MeanTokenEntropy | 0.7210 | 0.9710 | 0.9805 | 0.8118 | 0.2571 |
| UE · Perplexity | 0.7339 | 0.9734 | 0.9794 | 0.8881 | 0.6650 |
| Judge · API Sequence (verdict, test) | 0.8638 | 0.9922 | 0.9864 | — | 0.5 (default) |

Judge (test split): **52** of 1098 samples failed the verbatim reference-echo check and were recorded
as failed, never zero-filled (token judge scored 1046 rows, sequence judge 1098). The judge never
sees gold spans or labels.

## LongMemEval (`longmemeval`, 500 samples per variant)

Per-detector metrics are **5-fold CV** aggregates (mean). Thresholds come from each detector's
`config.joblib` (`validation_f1_optimal`), not from a held-out test split. Probe geometry (4B): 32
hidden layers → probe layers `[16, 27, 28, 29, 30, 31]`, hidden size 2560, feature shape `[6, 1,
2560]`. `hallucination_strict` uses `Hiddens_R` (RIGHT, mean pooling); `answerability_strict` uses
`Hiddens_L` (LEFT). `best` = TabPFN in every variant/task.

### hallucination_strict (ROC · AP · F1)

| variant (n, pos) | Linear | CatBoost | TabPFN | UQ (sequence) | Judge seq | Judge tok (max/mean) |
|---|---|---|---|---|---|---|
| SimpleMem (409, 0.274) | 0.694 · 0.371 · 0.518 | 0.776 · 0.422 · 0.572 | 0.794 · 0.437 · 0.590 | — (not run) | 0.555 | 0.489 / 0.503 |
| LightMem (384, 0.268) | 0.705 · 0.380 · 0.530 | 0.784 · 0.429 · 0.585 | 0.795 · 0.460 · 0.617 | 0.641 · 0.328 · 0.458 | 0.743 | 0.629 / 0.639 |
| Mem0 (295, 0.373) | 0.731 · 0.523 · 0.644 | 0.865 · 0.685 · 0.767 | 0.872 · 0.686 · 0.773 | 0.663 · 0.461 · 0.594 | 0.793 | 0.630 / 0.652 |

### answerability_strict (ROC · AP · F1)

| variant (n, pos) | Linear | CatBoost | TabPFN | UQ (sequence) |
|---|---|---|---|---|
| SimpleMem (469, 0.179) | 0.717 · 0.312 · 0.466 | 0.748 · 0.306 · 0.467 | 0.758 · 0.363 · 0.523 | — (not run) |
| LightMem (444, 0.313) | 0.728 · 0.449 · 0.565 | 0.783 · 0.505 · 0.632 | 0.785 · 0.489 · 0.607 | 0.669 · 0.383 · 0.499 |
| Mem0 (342, 0.398) | 0.670 · 0.511 · 0.584 | 0.716 · 0.520 · 0.617 | 0.732 · 0.553 · 0.644 | 0.620 · 0.455 · 0.578 |

Judge-span ROC (n = strict-positive-eligible rows, temperature 0.7, num_beams 3):

| variant | sequence judge | token judge (max) | token judge (mean) |
|---|---|---|---|
| SimpleMem | 0.555 (n=409) | 0.489 (n=395) | 0.503 (n=395) |
| LightMem | 0.743 (n=384) | 0.629 (n=336) | 0.639 (n=336) |
| Mem0 | 0.793 (n=295) | 0.630 (n=240) | 0.652 (n=240) |

TrustMem answerability judges (same 4B model through the trustmem runner; `LLM` = binary verdict,
`LLM_probs` = verdict-token logprob score):

| variant | LLM (binary) ROC | LLM_probs ROC |
|---|---|---|
| SimpleMem | 0.616 | 0.769 |
| LightMem | 0.616 | 0.805 |

## Provenance notes

- **Threshold scope.** PsiloQA probe/UE thresholds are `validation_f1_optimal` on the 298-row
  validation split; the reported ROC/AP/F1 are on the held-out test split. LongMemEval thresholds are
  `validation_f1_optimal` inside 5-fold CV (no separate held-out test) and are read from each
  detector's `config.joblib`.
- **Label / judge asymmetry.** Probes and UE are graded against PsiloQA/LongMemEval gold labels. The
  API judge is an independent annotator that never sees gold; a sample whose sampled generations all
  fail the verbatim reference-echo check is recorded as failed (not zero-filled), so judge row counts
  are below the probe sample counts. Judge failures — PsiloQA test: 52/1098. LongMemEval token judge
  drops per variant follow from the same rule (e.g. Mem0 240 of 295 hallucination rows scored).
- **SimpleMem has no UQ.** SimpleMem's `sirin_datasets/qwen35_4b` run is probing-only (6 detectors);
  LightMem and Mem0 add a single aggregated sequence `Uncertainty` method (MeanTokenEntropy +
  Perplexity, mean-aggregated) per task, which carries metrics but no calibrated threshold. No
  token-level UQ (MaximumTokenProbability / TokenEntropy) calibration was run for LongMemEval.
- **Class imbalance.** PsiloQA sequence positive rate ≈0.96 inflates sequence AP toward 1.0; ROC is
  the comparable signal there. LongMemEval strict positive rates (0.18–0.40) are reported per row.

## Artifacts

- PsiloQA checkpoint: `demo/checkpoints/qwen35_4b_psiloqa_span_linear/` (manifest, `SHA256SUMS`).
- PsiloQA metrics: `output/psiloqa_span_qwen35_4b/{probes,ue,judge}/sirin_metrics.json`,
  `.../experiment/{metrics.json, top5_demo_cases.json, provenance.json}`.
- LongMemEval per variant: `<run>/sirin_datasets/qwen35_4b/{sirin_metrics.json, saved_detectors/,
  judge_span/sirin_metrics.json, config_resolved.yaml}` for SimpleMem / LightMem / Mem0.
- UI profiles: `sirin/ui/assets/longmemeval_qwen35_4b_{simplemem,lightmem,mem0}.json`.
- Landing seeds: `sirin/ui/assets/psiloqa_span_seed_qwen35_4b.json` (probe),
  `sirin/ui/assets/judge_span_seed.json` (judge).
