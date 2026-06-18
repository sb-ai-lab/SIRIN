from typing import Any, List, Literal, Optional

import numpy as np
from loguru import logger as lg


def flatten_array(nested_list: List[Any], drop_none: bool = False) -> List[Any]:
    flat_list = []
    for item in nested_list:
        if isinstance(item, (list, np.ndarray)):
            flat_list.extend(flatten_array(list(item), drop_none=drop_none))
        elif drop_none and item is None:
            continue
        else:
            flat_list.append(item)
    return flat_list


def calibrate_threshold(
    probs: Optional[np.ndarray] = None,
    labels: Optional[np.ndarray] = None,
    method: Literal['optimal', 'f1_optimal', 'percentile', 'fixed'] = 'optimal',
    percentile: float = 0.5,
    fixed_threshold: float = 0.5,
) -> float:
    """Pick a decision threshold from predicted scores.

    Methods
    -------
    optimal
        Maximises Youden's J = TPR - FPR. Cheap but on small / imbalanced
        data can collapse to near-extreme thresholds that classify everything
        as one class.
    f1_optimal
        Maximises F1 on the positive class using the precision-recall curve.
        Much more stable than Youden's J when one class dominates or scores
        are noisy — it cannot be won by predicting a constant class.
    percentile
        Uses `np.percentile(probs, percentile * 100)` — label-free.
    prior
        Label-free. Picks the threshold that makes the fraction of positive
        predictions equal `percentile` (defaults to 0.5, i.e. median).
    fixed
        Returns `fixed_threshold` verbatim.
    """
    try:
        if probs is not None:
            probs = np.asarray(probs, dtype=float)
        if labels is not None:
            labels = np.asarray(labels)

        if method == 'percentile':
            if probs is None or len(probs) == 0:
                raise ValueError("probs cannot be None or empty for percentile method")
            valid_probs = probs[np.isfinite(probs)]
            if len(valid_probs) == 0:
                raise ValueError("All probability values are inf/nan")
            threshold = np.percentile(valid_probs, percentile * 100)

        elif method == 'prior':
            if probs is None or len(probs) == 0:
                raise ValueError("probs cannot be None or empty for prior method")
            valid_probs = probs[np.isfinite(probs)]
            if len(valid_probs) == 0:
                raise ValueError("All probability values are inf/nan")
            # percentile ∈ [0, 1] is the desired positive rate.
            threshold = np.quantile(valid_probs, 1.0 - percentile)

        elif method == 'fixed':
            threshold = fixed_threshold
            
        elif method in ('optimal', 'f1_optimal'):
            if probs is None or labels is None:
                raise ValueError("Both probs and labels required for optimal method")
            if len(probs) != len(labels):
                raise ValueError("probs and labels must have same length")

            # Filter out inf/nan values
            valid_mask = np.isfinite(probs)
            valid_probs = probs[valid_mask]
            valid_labels = labels[valid_mask]

            if len(valid_probs) == 0:
                raise ValueError("All probability values are inf/nan")

            if method == 'f1_optimal':
                from sklearn.metrics import precision_recall_curve
                precision, recall, thresholds = precision_recall_curve(valid_labels, valid_probs)
                # precision_recall_curve returns n+1 precision/recall but n thresholds
                f1_scores = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-8)
                best_idx = np.argmax(f1_scores)
                threshold = thresholds[best_idx]
            else:
                from sklearn.metrics import roc_curve
                fpr, tpr, thresholds = roc_curve(valid_labels, valid_probs)
                j_scores = tpr - fpr
                best_idx = np.argmax(j_scores)
                threshold = thresholds[best_idx]
        
        if not np.isfinite(threshold):
            raise ValueError(f"Computed threshold is {threshold}")

        return float(threshold)

    except Exception as e:
        lg.warning(f"Threshold calibration failed ({e}), using default value {fixed_threshold}")
        return fixed_threshold
