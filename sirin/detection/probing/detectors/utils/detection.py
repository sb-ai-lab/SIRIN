from typing import List, Any, Tuple, Optional

import numpy as np
import torch


def check_features_for_nan(features: List[Any], samples: List[Any]) -> None:
    """
    Check if features contain NaN values and raise an error if found.

    This validation is performed in all probing detectors to catch truncation issues.

    Args:
        features: List of feature tensors from feature processor
        samples: Original samples (used only for error messages)

    Raises:
        ValueError: If any sample's features contain NaN values
    """
    hasnan_mask = (
        torch.tensor(
            [
                [torch.tensor(sample).isnan().sum() > 0 for sample in samples]
                for samples in features
            ]
        ).sum(dim=0)
        > 0
    ).bool()

    for index, hasnan in enumerate(hasnan_mask):
        if hasnan:
            raise ValueError(
                f"Features of sample {index} contain NaN. "
                f"Probably the sample is too long and was truncated improperly."
            )


def check_features_for_nan_with_indices(
    features: List[Any], samples: List[Any], answer_indices: List[List[int]]
) -> None:
    """
    Check features for NaN values and empty answer indices (token-level variant).

    Token-level detectors also need to check if answer indices are empty.

    Args:
        features: List of feature tensors from feature processor
        samples: Original samples (used only for error messages)
        answer_indices: List of answer token indices for each sample

    Raises:
        ValueError: If any sample's features contain NaN or have no answer tokens
    """
    hasnan_mask = (
        torch.tensor(
            [
                [torch.tensor(sample).isnan().sum() > 0 for sample in samples]
                for samples in features
            ]
        ).sum(dim=0)
        > 0
    ).bool() | torch.tensor([len(indices) == 0 for indices in answer_indices])

    for index, hasnan in enumerate(hasnan_mask):
        if hasnan:
            raise ValueError(
                f"Features of sample {index} contain NaN or have no answer tokens. "
                f"Probably the sample is too long."
            )


def handle_binary_multiclass_probs(
    probs: np.ndarray, threshold: float, is_binary: bool = True
) -> tuple[np.ndarray, np.ndarray]:
    """
    Handle probability predictions for binary vs multiclass classification.

    Used by catboost and tabpfn detectors which return predict_proba directly.

    Args:
        probs: Raw probability array from model (shape: [N, num_classes])
        threshold: Classification threshold for binary case
        is_binary: Whether this is binary (2 classes) or multiclass (>2 classes)

    Returns:
        tuple of (processed_probs, predictions) where:
        - Binary: probs is 1D array of positive class probabilities
        - Multiclass: probs is 2D array, predictions use argmax
    """
    if is_binary and probs.shape[1] == 2:
        # Binary classification: extract positive class probability
        probs = probs[:, 1]
        preds = (probs > threshold).astype(int)
    else:
        # Multiclass classification: use argmax for predictions
        preds = np.argmax(probs, axis=-1)

    return probs, preds


def compute_token_cumulative_lengths(features: List[Any]) -> List[int]:
    """
    Compute cumulative token lengths for token-level detection.
    
    Used by token-level probing detectors to track token positions across layers.
    
    Args:
        features: List of feature tensors from feature processor (per layer)
    
    Returns:
        List of cumulative token counts [0, len1, len1+len2, ...]
    """
    all_lengths = [0] + [torch.tensor(hidden).shape[1] for hidden in features[0]]
    for i in range(1, len(all_lengths)):
        all_lengths[i] += all_lengths[i - 1]
    return all_lengths


def rearrange_token_predictions(
    probs: np.ndarray,
    preds: np.ndarray,
    offsets: torch.Tensor | np.ndarray,
    all_lengths: List[int],
) -> Tuple[List[List[float]], List[List[int]]]:
    """
    Rearrange flat token-level predictions back to character-level per sample.
    
    Token-level models predict on compressed tokens, but we need character-level
    predictions. This function repeats each token's prediction across its character span.
    
    Used by all token-level probing detectors (tabpfn, catboost, linear).
    
    Args:
        probs: Flat array of probabilities [total_tokens]
        preds: Flat array of predictions [total_tokens]
        offsets: Character offsets for each token (start, end) [total_tokens, 2]
        all_lengths: Cumulative token counts per sample [0, len1, len1+len2, ...]
    
    Returns:
        tuple of (probs_per_sample, preds_per_sample) where each is a list of lists
    """
    # Convert offsets to numpy if needed
    if isinstance(offsets, torch.Tensor):
        offsets = offsets.numpy()
    
    # Calculate character span length for each token
    repeats = offsets[:, 1] - offsets[:, 0]
    
    # Rearrange probabilities: slice by sample and repeat by character spans
    probs_list = [
        probs[all_lengths[i] : all_lengths[i + 1]]
        .repeat(repeats[all_lengths[i] : all_lengths[i + 1]])
        .tolist()
        for i in range(len(all_lengths) - 1)
    ]
    
    # Rearrange predictions: slice by sample and repeat by character spans
    preds_list = [
        preds[all_lengths[i] : all_lengths[i + 1]]
        .repeat(repeats[all_lengths[i] : all_lengths[i + 1]])
        .tolist()
        for i in range(len(all_lengths) - 1)
    ]
    
    return probs_list, preds_list
