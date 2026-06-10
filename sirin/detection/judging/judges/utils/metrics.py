from typing import Any, Dict, List, Optional

import numpy as np
import torch
from loguru import logger as lg

from sirin.definitions import ClassificationMetric
from sirin.detection.utils.basic import calibrate_threshold
from sirin.metrics.classification import calculate_classification_metrics


def process_logits_to_probs(
    logits: np.ndarray,
    labels: Optional[np.ndarray] = None,
    filter_padding: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert logits to probabilities, handling binary/multiclass cases.
    
    Args:
        logits: Raw logits from model (shape: [batch, num_classes] or [batch, seq, num_classes])
        labels: Optional labels for filtering padding tokens (token-level only)
        filter_padding: Whether to filter out -100 padding labels (for token-level)
    
    Returns:
        tuple of (probs, active_labels) where:
        - probs: probability values
        - active_labels: filtered labels (only if filter_padding=True, else original labels)
    """
    # Handle token-level: flatten and filter padding
    if filter_padding and labels is not None:
        logits_flat = logits.reshape(-1, logits.shape[-1])
        labels_flat = labels.reshape(-1)
        
        active_mask = labels_flat != -100
        logits = logits_flat[active_mask]
        labels = labels_flat[active_mask]
    
    logits_tensor = torch.from_numpy(logits) if isinstance(logits, np.ndarray) else logits
    
    num_classes = logits_tensor.shape[-1]
    
    if num_classes == 1:
        # Binary classification with single output
        probs = torch.sigmoid(logits_tensor).squeeze(-1)
    elif num_classes == 2:
        # Binary classification with two outputs
        probs = torch.softmax(logits_tensor, dim=-1)[:, 1]
    else:
        # Multiclass classification
        probs_full = torch.softmax(logits_tensor, dim=-1)
        probs = torch.max(probs_full, dim=-1).values
    
    probs_np = probs.numpy() if isinstance(probs, torch.Tensor) else probs
    
    return probs_np, labels


def calibrate_and_compute_metrics(
    probs: np.ndarray,
    labels: np.ndarray,
    config: Any,
    metrics_to_compute: List[ClassificationMetric],
    is_binary: bool = True,
) -> tuple[Dict[str, Any], Optional[float]]:
    """
    Calibrate threshold and compute classification metrics.
    
    Args:
        probs: Probability predictions
        labels: Ground truth labels
        config: Judge configuration with threshold settings
        metrics_to_compute: List of metrics to calculate
        is_binary: Whether this is binary classification (affects threshold usage)
    
    Returns:
        tuple of (metrics_dict, threshold) where:
        - metrics_dict: Computed metric values
        - threshold: Calibrated threshold (None for multiclass)
    """
    if is_binary:
        threshold = calibrate_threshold(
            probs,
            labels,
            config.threshold_method,
            config.threshold_percentile,
            config.fixed_threshold,
        )
        preds = (probs > threshold).astype(int)
    else:
        threshold = None
        if len(probs.shape) > 1:
            # Multiclass: use argmax for predictions
            preds = np.argmax(probs, axis=-1)
        else:
            preds = probs.astype(int)
    
    metrics = calculate_classification_metrics(
        labels,
        probs,
        preds,
        metrics=metrics_to_compute,
    )
    lg.info(f"Evaluation metrics: {metrics}")
    
    return metrics, threshold
