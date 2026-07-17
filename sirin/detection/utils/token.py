from typing import Dict, List, Tuple

import numpy as np
import torch

from sirin.inference.adapters import ModelAdapterBase


def rearrange_token_predictions(
    probs: np.ndarray,
    preds: np.ndarray,
    offsets: torch.Tensor | np.ndarray,
    all_lengths: List[int],
) -> Tuple[List[List[float]], List[List[int]]]:
    """
    Rearrange flat token-level predictions back to character-level per sample.
    
    Token-level models predict on compressed tokens, but we need character-level
    predictions. This function places each token's prediction at its character offsets.
    
    Used by all token-level probing detectors (tabpfn, catboost, linear) and uncertainty detector.
    
    Args:
        probs: Flat array of probabilities [total_tokens]
        preds: Flat array of predictions [total_tokens]
        offsets: Character offsets for each token (start, end) [total_tokens, 2]
        all_lengths: Cumulative token counts per sample [0, len1, len1+len2, ...]
    
    Returns:
        tuple of (probs_per_sample, preds_per_sample) where each is a list of lists
    """
    if isinstance(probs, torch.Tensor):
        probs = probs.detach().cpu().numpy()
    if isinstance(preds, torch.Tensor):
        preds = preds.detach().cpu().numpy()

    # Convert offsets to numpy if needed
    if isinstance(offsets, torch.Tensor):
        offsets = offsets.numpy()
    else:
        offsets = np.asarray(offsets)

    boundaries = [int(value) for value in all_lengths]
    if not boundaries or boundaries[0] != 0 or any(
        left > right for left, right in zip(boundaries, boundaries[1:])
    ):
        raise ValueError(f'Invalid token sample boundaries: {boundaries!r}.')
    expected = boundaries[-1]
    if len(probs) != expected or len(preds) != expected or len(offsets) != expected:
        raise ValueError(
            'Token prediction alignment mismatch: '
            f'{expected} features, {len(probs)} probabilities, '
            f'{len(preds)} predictions, and {len(offsets)} offsets.'
        )
    
    probs_list = []
    preds_list = []
    for start, end in zip(boundaries, boundaries[1:]):
        sample_offsets = offsets[start:end]
        char_count = int(sample_offsets[:, 1].max()) if len(sample_offsets) else 0
        sample_probs = probs[start:end]
        gap_value = sample_probs.min() if len(sample_probs) else 0
        char_probs = np.full(char_count, gap_value, dtype=probs.dtype)
        char_preds = np.zeros(char_count, dtype=preds.dtype)
        for prob, pred, (span_start, span_end) in zip(
            sample_probs, preds[start:end], sample_offsets
        ):
            char_probs[int(span_start) : int(span_end)] = prob
            char_preds[int(span_start) : int(span_end)] = pred
        probs_list.append(char_probs.tolist())
        preds_list.append(char_preds.tolist())
    
    return probs_list, preds_list


def get_answer_offsets(
    samples: List[List[Dict[str, str]]], model: ModelAdapterBase
) -> Tuple[List[List[Tuple[int, int]]], Dict, List[List[int]]]:
    """
    Get token offsets for answer tokens, aligned with prepare_tokenized_input logic.
    Returns character-level offsets relative to the answer text for each answer token.
    
    Returns:
        - answer_offsets: List of lists of (start, end) character offsets relative to answer
        - encoded_sample: Full tokenized batch with offset_mapping
        - answer_indices: List of lists of token indices where answer tokens are located
    """
    preprocessed_samples = model._preprocess_input(samples)

    # Tokenize full samples with offset mapping
    encoded_sample = model.tokenizer(
        preprocessed_samples,
        return_offsets_mapping=True,
        add_special_tokens=False,
        truncation=model.config.truncation,
        padding=False,
    )

    full_offsets = encoded_sample['offset_mapping']
    answer_offsets = []
    answer_indices = []
    for sample_idx, (sample, rendered, sample_offsets) in enumerate(
        zip(samples, preprocessed_samples, full_offsets)
    ):
        answer_content = sample[-1]['content']
        if not answer_content:
            answer_offsets.append([])
            answer_indices.append([])
            continue

        answer_start_char = rendered.rfind(answer_content)
        if answer_start_char < 0:
            raise ValueError(
                f'Assistant answer not found in preprocessed sample {sample_idx}; '
                'token scores cannot be aligned safely.'
            )
        answer_end_char = answer_start_char + len(answer_content)

        indices = []
        adjusted_offsets = []
        for token_idx, (token_start, token_end) in enumerate(sample_offsets):
            if (token_start, token_end) == (0, 0):
                continue
            if token_end <= answer_start_char or token_start >= answer_end_char:
                continue
            indices.append(token_idx)
            adjusted_offsets.append(
                (
                    max(token_start, answer_start_char) - answer_start_char,
                    min(token_end, answer_end_char) - answer_start_char,
                )
            )

        answer_offsets.append(adjusted_offsets)
        answer_indices.append(indices)

    return answer_offsets, encoded_sample, answer_indices


def get_token_labels(
    answer_offsets: List[List[Tuple[int, int]]], target_spans: List[List[Tuple[int, int]]]
) -> List[List[int]]:
    """
    Create token-level labels based on character-level span overlap.
    Aligned with _process_token_level_labels logic.
    
    Args:
        answer_offsets: List of lists of (start, end) character offsets for each token (relative to answer)
        target_spans: List of lists of (start, end) character spans marking hallucinations
        
    Returns:
        List of lists of labels (0 for supported, 1 for hallucinated)
    """
    result = []
    for offsets, spans in zip(answer_offsets, target_spans):
        # Initialize all tokens as 0 (supported content)
        sample_labels = [0] * len(offsets)
        
        # For each token, check if it overlaps with any hallucination span
        for token_idx, (token_start, token_end) in enumerate(offsets):
            for span_start, span_end in spans:
                if token_end > span_start and token_start < span_end:
                    sample_labels[token_idx] = 1
                    break 
        
        result.append(sample_labels)

    return result


def convert_spans_to_labels(
    labels: np.ndarray,
    probs: List[List[float]],
) -> List[List[int]]:
    """
    Convert span annotations to character-level binary labels.

    Each span (start, end) is converted to binary labels where positions
    within spans are 1 and outside are 0.

    Args:
        labels: Span annotations for each sample [num_samples][num_spans, 2]
               where each span is (start_char, end_char)
        probs: Probabilities to determine output length [num_samples][num_chars]

    Returns:
        Binary labels for each character position [num_samples][num_chars]
    """
    char_labels = []
    for i, sample_spans in enumerate(labels):
        sample_labels = [0] * len(probs[i])
        for start, end in sample_spans:
            sample_labels[start:end] = [1] * (end - start)
        sample_labels = sample_labels[: len(probs[i])]
        char_labels.append(sample_labels)
    return char_labels
