from typing import Dict, List, Optional, Union

import numpy as np
from loguru import logger as lg

from sirin.definitions import ClassificationMetric


def calculate_classification_metrics(
    y_true: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    y_pred: Optional[np.ndarray] = None,
    metrics: Optional[List[ClassificationMetric]] = None,
    beta: Optional[float] = 1.0,
) -> Dict[str, float]:
    results = {}

    if not metrics:
        return results
    
    unique_classes = np.unique(y_true).size
    is_multiclass = unique_classes > 2
    
    for metric in metrics:
        metric_func = ClassificationMetric.get_metric_function(metric.value)
        
        try:
            if metric in [
                ClassificationMetric.ROC_AUC,
                ClassificationMetric.PR_AUC,
            ]:
                if unique_classes > 1:
                    if is_multiclass:
                        if y_prob is not None and y_prob.ndim > 1:
                            results[metric.value] = metric_func(y_true, y_prob, multi_class='ovr', average='macro')
                        else:
                            results[metric.value] = metric_func(y_true, y_prob)
                    else:
                        results[metric.value] = metric_func(y_true, y_prob)
                else:
                    results[metric.value] = -1
                    
            elif metric == ClassificationMetric.FBETA:
                if is_multiclass:
                    results[metric.value] = metric_func(y_true, y_pred, beta=beta, average='macro')
                else:
                    results[metric.value] = metric_func(y_true, y_pred, beta=beta)
                    
            else:
                if is_multiclass:
                    if hasattr(metric_func, '__name__') and any(avg in metric_func.__name__ for avg in ['precision', 'recall', 'f1']):
                        results[metric.value] = metric_func(y_true, y_pred, average='macro')
                    else:
                        results[metric.value] = metric_func(y_true, y_pred)
                else:
                    results[metric.value] = metric_func(y_true, y_pred)
        except Exception as e:
            lg.warning(f"Metric {metric} failed: {e}")
            results[metric.value] = None
    
    return results


def calculate_per_sample_metrics(
    y_true_list: List[np.ndarray],
    y_prob_list: Optional[List[np.ndarray]] = None,
    y_pred_list: Optional[List[np.ndarray]] = None,
    metrics: Optional[List[ClassificationMetric]] = None,
    beta: Optional[float] = 1.0,
) -> Dict[str, float]:
    """
    Calculate classification metrics per sample and then average.
    
    This gives equal weight to each sample regardless of its length,
    unlike flattening which gives more weight to longer samples.
    
    Args:
        y_true_list: List of label arrays, one per sample
        y_prob_list: List of probability arrays, one per sample
        y_pred_list: List of prediction arrays, one per sample
        metrics: List of metrics to calculate
        beta: Beta parameter for F-beta score
    
    Returns:
        Dictionary with averaged metrics across samples
    """
    if not metrics:
        return {}
    
    n_samples = len(y_true_list)
    if n_samples == 0:
        return {}
    
    # Initialize accumulators for each metric
    metric_accumulators = {metric.value: [] for metric in metrics}
    
    # Calculate metrics for each sample
    for idx in range(n_samples):
        y_true_sample = np.array(y_true_list[idx])
        y_prob_sample = np.array(y_prob_list[idx]) if y_prob_list is not None else None
        y_pred_sample = np.array(y_pred_list[idx]) if y_pred_list is not None else None
        
        # Skip empty samples
        if len(y_true_sample) == 0:
            continue
        
        # Calculate metrics for this sample
        sample_metrics = calculate_classification_metrics(
            y_true=y_true_sample,
            y_prob=y_prob_sample,
            y_pred=y_pred_sample,
            metrics=metrics,
            beta=beta,
        )
        
        # Accumulate valid metrics
        for metric_name, metric_value in sample_metrics.items():
            if metric_value is not None and not np.isnan(metric_value):
                metric_accumulators[metric_name].append(metric_value)
    
    # Average metrics across samples
    results = {}
    for metric_name, values in metric_accumulators.items():
        if len(values) > 0:
            results[metric_name] = float(np.mean(values))
        else:
            results[metric_name] = None
    
    return results
