from typing import Dict, List, Tuple

import numpy as np
from loguru import logger as lg

from sirin.inference.adapters import ModelAdapterBase


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

    # Tokenize context only (without assistant message) to find answer start
    preprocessed_prefixes = model._preprocess_input([sample[:-1] for sample in samples])
    encoded_prefixes = model.tokenizer(
        preprocessed_prefixes,
        padding=False,
        truncation=model.config.truncation,
        add_special_tokens=False,
    )

    # Find answer token indices
    answer_indices = [
        list(range(len(prefix), len(sample)))
        for prefix, sample in zip(
            encoded_prefixes['input_ids'], encoded_sample['input_ids']
        )
    ]

    # Get offset mapping for full sequence
    full_offsets = encoded_sample['offset_mapping']
    
    # Extract answer offsets adjusted relative to answer text
    answer_offsets = []
    for sample_idx, (sample, indices) in enumerate(zip(samples, answer_indices)):
        answer_content = sample[-1]['content']
        sample_offsets = full_offsets[sample_idx]
        
        # Edge case: no answer tokens (empty or fully truncated)
        if not indices:
            answer_offsets.append([])
            continue
        
        # Edge case: index out of bounds
        if indices[0] >= len(sample_offsets):
            lg.warning(
                f"Sample {sample_idx}: Answer token index {indices[0]} out of bounds "
                f"(offset mapping length: {len(sample_offsets)}). Skipping sample."
            )
            answer_offsets.append([])
            continue
        
        # Get the character offset where the first answer token starts
        first_token_offset = sample_offsets[indices[0]]
        
        # Edge case: special token or invalid offset (0, 0)
        if first_token_offset == (0, 0) and len(indices) > 1:
            lg.warning(
                f"Sample {sample_idx}: First answer token has (0, 0) offset. "
                f"Trying next token as answer start."
            )
            # Try to find first non-zero offset
            answer_start_char = None
            for idx in indices:
                if idx < len(sample_offsets) and sample_offsets[idx] != (0, 0):
                    answer_start_char = sample_offsets[idx][0]
                    break
            
            if answer_start_char is None:
                lg.warning(
                    f"Sample {sample_idx}: All answer tokens have (0, 0) offsets. "
                    f"Using 0 as fallback."
                )
                answer_start_char = 0
        else:
            answer_start_char = first_token_offset[0]
        
        # Adjust all answer token offsets to be relative to answer start
        adjusted_offsets = []
        for token_idx in indices:
            # Edge case: token index out of bounds
            if token_idx >= len(sample_offsets):
                lg.warning(
                    f"Sample {sample_idx}: Token index {token_idx} out of bounds. "
                    f"Skipping this token."
                )
                continue
                
            token_start, token_end = sample_offsets[token_idx]
            
            # Edge case: special token with (0, 0) offset
            if (token_start, token_end) == (0, 0):
                # Skip special tokens - they don't correspond to actual text
                continue
            
            # Adjust offsets to be relative to answer text (0-indexed from answer start)
            adjusted_start = token_start - answer_start_char
            adjusted_end = token_end - answer_start_char
            
            # Edge case: negative offsets (preprocessing mismatch)
            if adjusted_start < 0 or adjusted_end < 0:
                lg.warning(
                    f"Sample {sample_idx}, token {token_idx}: Negative offset detected "
                    f"({adjusted_start}, {adjusted_end}). This may indicate preprocessing mismatch. "
                    f"Clamping to 0."
                )
                adjusted_start = max(0, adjusted_start)
                adjusted_end = max(0, adjusted_end)
            
            adjusted_offsets.append((adjusted_start, adjusted_end))
        
        answer_offsets.append(adjusted_offsets)

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
