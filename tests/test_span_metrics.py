"""Pure numpy/sklearn checks for sirin.metrics.span (no torch / GPU)."""

import numpy as np
import pytest

from sirin.metrics.span import (
    character_scores,
    f1_optimal_threshold,
    mean_iou,
    span_classification_metrics,
    span_labels,
    token_labels,
)


def test_span_and_token_labels_half_open():
    assert span_labels(8, [[2, 5]]).tolist() == [0, 0, 1, 1, 1, 0, 0, 0]
    assert token_labels([(0, 2), (2, 4), (4, 7)], [[2, 5]]).tolist() == [0, 1, 1]


def test_mean_iou_hand_computed_including_empty_spans():
    # partial overlap: intersection 1 / union 2
    assert mean_iou([np.array([1, 1, 0, 0])], [np.array([1, 0, 0, 0])]) == 0.5
    # both empty -> perfect agreement by convention
    assert mean_iou([np.zeros(3)], [np.zeros(3)]) == 1.0
    # empty on one side only -> zero
    assert mean_iou([np.array([1, 1, 0])], [np.zeros(3)]) == 0.0
    assert mean_iou([np.zeros(3)], [np.array([1, 1, 0])]) == 0.0
    # averages per-answer values (0.5 and 1.0)
    assert mean_iou(
        [np.array([1, 1, 0, 0]), np.zeros(3)],
        [np.array([1, 0, 0, 0]), np.zeros(3)],
    ) == 0.75


def test_mean_iou_rejects_length_mismatch():
    with pytest.raises(ValueError, match="alignment mismatch"):
        mean_iou([np.array([1, 0])], [np.array([1, 0, 0])])


def test_character_scores_expand_tokens_to_chars():
    scores = character_scores("hello", [(0, 2), (2, 5)], [0.1, 0.9])
    np.testing.assert_allclose(scores, [0.1, 0.1, 0.9, 0.9, 0.9])


def test_character_scores_require_full_coverage_and_matching_lengths():
    with pytest.raises(ValueError, match="uncovered characters"):
        character_scores("hello", [(0, 2), (3, 5)], [0.1, 0.9])
    with pytest.raises(ValueError, match="offset/score mismatch"):
        character_scores("hi", [(0, 2)], [0.1, 0.9])


def test_f1_optimal_threshold_separates_tiny_case():
    labels = np.array([0, 0, 1, 1], dtype=np.uint8)
    scores = np.array([0.1, 0.2, 0.8, 0.9])
    threshold = f1_optimal_threshold(labels, scores)
    assert 0.2 < threshold < 0.8
    # SIRIN predicts with strict >; the threshold must recover the labels.
    assert ((scores > threshold).astype(np.uint8) == labels).all()


def test_span_classification_metrics_perfect_synthetic():
    per_labels = [np.array([0, 0, 1, 1], np.uint8), np.array([1, 1, 0], np.uint8)]
    per_scores = [np.array([0.1, 0.2, 0.9, 0.8]), np.array([0.7, 0.6, 0.3])]
    result = span_classification_metrics(per_labels, per_scores, 0.5)
    assert result["n_rows"] == 2
    assert result["n_characters"] == 7
    assert result["positive_rate"] == pytest.approx(4 / 7)
    for key in ("roc_auc", "average_precision", "pr_auc", "f1", "accuracy",
                "precision", "recall", "mean_per_answer_iou"):
        assert result[key] == pytest.approx(1.0)


def test_span_classification_metrics_mixed_scores_in_range():
    per_labels = [np.array([0, 1, 1, 0], np.uint8)]
    per_scores = [np.array([0.6, 0.9, 0.2, 0.4])]  # one FP, one FN at 0.5
    result = span_classification_metrics(per_labels, per_scores, 0.5)
    assert result["accuracy"] == pytest.approx(0.5)
    for key in ("roc_auc", "average_precision", "pr_auc", "f1",
                "precision", "recall", "mean_per_answer_iou"):
        assert 0.0 <= result[key] <= 1.0
