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
    method: Literal['optimal', 'percentile', 'fixed'] = 'optimal',
    percentile: float = 0.5,
    fixed_threshold: float = 0.5,
) -> float:
    try:
        if method == 'percentile':
            if probs is None or len(probs) == 0:
                raise ValueError("probs cannot be None or empty for percentile method") 
            valid_probs = probs[np.isfinite(probs)]
            if len(valid_probs) == 0:
                raise ValueError("All probability values are inf/nan")
            threshold = np.percentile(valid_probs, percentile * 100)
            
        elif method == 'fixed':
            threshold = fixed_threshold
            
        elif method == 'optimal':
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
