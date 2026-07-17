"""Character-level span probe metrics.

Pure numpy/sklearn helpers lifted from ``scripts/train_psiloqa_span_linear.py`` so
the PsiloQA span pipeline and the wider campaign can share one implementation.
No torch / GPU dependency: everything here operates on plain arrays.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

__all__ = [
    "span_labels",
    "token_labels",
    "character_scores",
    "f1_optimal_threshold",
    "mean_iou",
    "span_classification_metrics",
]


def span_labels(length: int, spans: Sequence[Sequence[int]]) -> np.ndarray:
    labels = np.zeros(length, dtype=np.uint8)
    for start, end in spans:
        if not 0 <= start <= end <= length:
            raise ValueError(f"invalid half-open span [{start}, {end}) for length {length}")
        labels[start:end] = 1
    return labels


def token_labels(
    offsets: Sequence[tuple[int, int]], spans: Sequence[Sequence[int]]
) -> np.ndarray:
    return np.asarray(
        [
            any(token_end > span_start and token_start < span_end for span_start, span_end in spans)
            for token_start, token_end in offsets
        ],
        dtype=np.uint8,
    )


def character_scores(
    answer: str, offsets: Sequence[tuple[int, int]], scores: Sequence[float]
) -> np.ndarray:
    if len(offsets) != len(scores):
        raise ValueError(f"offset/score mismatch: {len(offsets)} != {len(scores)}")
    result = np.full(len(answer), np.nan, dtype=np.float64)
    for (start, end), score in zip(offsets, scores):
        if not 0 <= start < end <= len(answer):
            raise ValueError(f"invalid token offset [{start}, {end})")
        result[start:end] = float(score)
    missing = np.flatnonzero(~np.isfinite(result))
    if len(missing):
        raise ValueError(f"token offsets leave {len(missing)} uncovered characters")
    return result


def f1_optimal_threshold(labels: np.ndarray, scores: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(labels, scores)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(
        precision[:-1] + recall[:-1], 1e-12
    )
    threshold = float(thresholds[int(np.argmax(f1))])
    # SIRIN predicts with score > threshold; move one float below sklearn's >= cut.
    return float(np.nextafter(threshold, -np.inf))


def mean_iou(labels: Sequence[np.ndarray], predictions: Sequence[np.ndarray]) -> float:
    values = []
    for truth, pred in zip(labels, predictions):
        if len(truth) != len(pred):
            raise ValueError(f"character alignment mismatch: {len(truth)} != {len(pred)}")
        union = np.logical_or(truth, pred).sum()
        values.append(1.0 if union == 0 else np.logical_and(truth, pred).sum() / union)
    return float(np.mean(values))


def span_classification_metrics(
    per_answer_labels: Sequence[np.ndarray],
    per_answer_scores: Sequence[np.ndarray],
    threshold: float,
) -> dict:
    """Char-flat classification metrics plus per-answer mean IoU.

    Faithful to the demo script's ``metrics()``: inputs are per-answer character
    label / score arrays (from ``character_scores`` / ``span_labels``); output
    matches the recorded ``metrics.json`` schema.
    """
    if not per_answer_scores or sum(len(s) for s in per_answer_scores) == 0:
        raise ValueError('span metrics need at least one scored character')
    flat_scores = np.concatenate(per_answer_scores)
    flat_labels = np.concatenate(per_answer_labels)
    flat_predictions = (flat_scores > threshold).astype(np.uint8)
    per_predictions = [(score > threshold).astype(np.uint8) for score in per_answer_scores]
    precision, recall, _ = precision_recall_curve(flat_labels, flat_scores)
    both_classes = len(np.unique(flat_labels)) > 1
    trapz = np.trapezoid if hasattr(np, 'trapezoid') else np.trapz  # np.trapz removed in NumPy 2.x
    return {
        "n_rows": len(per_answer_labels),
        "n_characters": int(len(flat_labels)),
        "positive_rate": float(flat_labels.mean()),
        # ROC-AUC / AP are undefined on a single-class batch (e.g. no hallucinated
        # characters at all) -- report nan rather than crashing the whole metric set.
        "roc_auc": float(roc_auc_score(flat_labels, flat_scores)) if both_classes else float('nan'),
        "average_precision": float(average_precision_score(flat_labels, flat_scores)) if both_classes else float('nan'),
        "pr_auc": float(trapz(precision[::-1], recall[::-1])),
        "f1": float(f1_score(flat_labels, flat_predictions)),
        "accuracy": float(accuracy_score(flat_labels, flat_predictions)),
        "precision": float(precision_score(flat_labels, flat_predictions, zero_division=0)),
        "recall": float(recall_score(flat_labels, flat_predictions, zero_division=0)),
        "mean_per_answer_iou": mean_iou(per_answer_labels, per_predictions),
    }
