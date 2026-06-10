from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader
from loguru import logger as lg

from sirin.definitions import TARGET_COL
from sirin.detection.utils.basic import calibrate_threshold
from sirin.metrics.classification import calculate_classification_metrics


def preprocess_dataloader_to_numpy(
    data_loader: DataLoader, max_features_per_layer: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract and preprocess features from DataLoader to numpy arrays.

    Used by catboost and tabpfn detectors for training.

    Args:
        data_loader: DataLoader with batch structure containing hidden features
        max_features_per_layer: Optional limit on features per hidden layer (for TabPFN)

    Returns:
        tuple of (X_np, y_np) where:
        - X_np: Features array of shape [N, total_features]
        - y_np: Target labels array of shape [N]
    """
    features_list, targets_list = [], []

    for batch in data_loader:
        hidden_features = []

        # Extract hidden features from batch
        for key in batch.keys():
            if key.startswith("hidden"):
                hidden_features.append(batch[key])

        # Reshape each hidden layer to 2D
        for index in range(len(hidden_features)):
            hidden_features[index] = hidden_features[index].reshape(
                hidden_features[index].shape[0], -1
            )

            # Apply feature limiting if specified (for TabPFN)
            if max_features_per_layer is not None:
                hidden_features[index] = (
                    hidden_features[index].detach().clone()[:, :max_features_per_layer]
                )

        # Concatenate all hidden layers
        combined_features = torch.cat(hidden_features, dim=-1)
        features_list.append(combined_features)
        targets_list.append(batch[TARGET_COL])

    # Combine all batches
    X = torch.cat(features_list, dim=0)
    y = torch.cat(targets_list, dim=0)

    # Convert to numpy
    X_np = X.cpu().numpy()
    y_np = y.cpu().numpy()

    # Ensure proper shape
    if len(X_np.shape) > 2:
        X_np = X_np.reshape(X_np.shape[0], -1)

    return X_np, y_np


def calibrate_and_evaluate(
    val_probs_full: np.ndarray,
    y_val_np: np.ndarray,
    config: Any,
    metrics_list: List[Any],
) -> Tuple[np.ndarray, np.ndarray, float, Dict[str, Any]]:
    """
    Calibrate threshold and evaluate model predictions on validation data.

    Handles both binary and multiclass classification.

    Args:
        val_probs_full: Full probability predictions from model [N, num_classes]
        y_val_np: Validation target labels [N]
        config: Detector configuration with threshold settings
        metrics_list: List of metrics to compute

    Returns:
        tuple of (val_probs, val_predictions, threshold, metrics) where:
        - val_probs: Probabilities for metric calculation (shape depends on binary/multiclass)
        - val_predictions: Model predictions [N]
        - threshold: Calibrated threshold (or 0.5 for multiclass)
        - metrics: Computed classification metrics dictionary
    """
    # Handle binary vs multiclass
    if val_probs_full.shape[1] == 2:
        # Binary classification: extract positive class probability
        val_probs = val_probs_full[:, 1]

        threshold = calibrate_threshold(
            val_probs,
            y_val_np,
            config.threshold_method,
            config.threshold_percentile,
            config.fixed_threshold,
        )

        val_predictions = (val_probs > threshold).astype(int)
    else:
        # Multiclass classification
        val_probs = val_probs_full
        threshold = 0.5  # Not used for multiclass, but set for consistency
        val_predictions = np.argmax(val_probs_full, axis=-1)

    # Calculate metrics
    metrics = calculate_classification_metrics(
        y_val_np, val_probs, val_predictions, metrics_list
    )

    return val_probs, val_predictions, threshold, metrics


def setup_linear_model_config(config: Any) -> Tuple[List[bool], List[int]]:
    """
    Setup and validate configuration for LinearClassifier models.

    Ensures attention_pooling and ensemble parameters are properly configured.

    Args:
        config: Detector configuration with embedding_dim, attention_pooling, ensemble

    Returns:
        tuple of (attention_pooling, ensemble) with validated values
    """
    attention_pooling = config.attention_pooling
    ensemble = config.ensemble

    # Validate attention_pooling
    if attention_pooling is None or len(attention_pooling) != len(config.embedding_dim):
        lg.warning(
            "Parameter attention_pooling is not chosen for each FeatureProcessor. "
            "Setting to default attention pooling for each processor"
        )
        attention_pooling = [True] * len(config.embedding_dim)

    # Validate ensemble
    if ensemble is None or (
        len(ensemble) > 0 and max(ensemble) < len(config.embedding_dim)
    ):
        lg.warning(
            "Parameter ensemble is not chosen correctly. "
            "Setting to default (concat ensembling) for each processor"
        )
        ensemble = []

    return attention_pooling, ensemble
