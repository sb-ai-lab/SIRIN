from typing import List, Tuple

import numpy as np
import torch
from loguru import logger as lg


# ============================================================================
# SPAN WRAPPING & MANIPULATION
# ============================================================================

def wrap_spans(
    sequence: str, spans: List[Tuple[int, int]]
) -> Tuple[str, List[Tuple[int, int]]]:
    """
    Wraps hallucination spans in a sequence with [SPAN] and [/SPAN] tags,
    and updates the spans according to new positions with tags.

    Args:
        sequence (str): The input sequence
        spans (list of tuples): List of (start, end) positions for hallucination spans

    Returns:
        tuple: (updated_sequence, updated_spans)
    """
    result_sequence = sequence
    cumulative_offset = 0

    for start, end in spans:
        adjusted_start = start + cumulative_offset
        adjusted_end = end + cumulative_offset
        result_sequence = (
            result_sequence[:adjusted_start]
            + '[SPAN]'
            + result_sequence[adjusted_start:]
        )

        new_end = adjusted_end + len('[SPAN]')
        result_sequence = (
            result_sequence[:new_end] + '[/SPAN]' + result_sequence[new_end:]
        )

        cumulative_offset += len('[SPAN]') + len('[/SPAN]')

    return result_sequence


def find_span_segments(text: str) -> List[Tuple[int, int]]:
    """
    Find all [SPAN]...[/SPAN] segments in text and return (start, end) positions.
    """
    import re

    pattern = r'\[SPAN\](.*?)\[/SPAN\]'
    matches = []
    for match in re.finditer(pattern, text):
        matches.append((match.start(1), match.end(1)))
    return matches


def merge_overlapping_spans(spans: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Merge overlapping spans.
    """
    if not spans:
        return []

    sorted_spans = sorted(spans)
    merged = [sorted_spans[0]]

    for current in sorted_spans[1:]:
        last = merged[-1]
        if current[0] <= last[1]:  # Overlapping
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)

    return merged


# ============================================================================
# CHARACTER-LEVEL PROBABILITY CALCULATIONS
# ============================================================================

def calculate_character_probabilities(
    generated_texts: List[str], reference: str | None = None
) -> List[float]:
    """
    Calculate character-level probabilities based on span tags in generated texts.

    Each generation independently marks hallucinated spans with [SPAN][/SPAN]; a character's
    score is the fraction of generations that flagged it (a [0, 1] consensus).

    Args:
        generated_texts: List of generated texts with potential [SPAN][/SPAN] tags
        reference: When given, scores are computed over the REFERENCE answer's characters
            (each vote vector is padded/truncated to ``len(reference)``). This is the
            reference-aligned path used after echo validation. When None (backward compatible),
            the first generation's tag-stripped length sets the alignment.

    Returns:
        List of probabilities, one per character position, representing the mean
        span-tag agreement across all generated texts.
    """
    all_char_vectors = []

    for gen_text in generated_texts:
        extracted_answer = extract_answer_from_generation(gen_text)

        char_vector = create_char_binary_vector(extracted_answer)
        all_char_vectors.append(char_vector)

    if reference is not None:
        max_len = len(reference)
    elif all_char_vectors:
        max_len = len(all_char_vectors[0])
    else:
        return [0.0] * len(generated_texts[0]) if generated_texts else []

    padded_vectors = []
    for vec in all_char_vectors:
        if len(vec) < max_len:
            padded_vec = vec + [0.0] * (max_len - len(vec))
        elif len(vec) > max_len:
            padded_vec = vec[:max_len]
        else:
            padded_vec = vec
        padded_vectors.append(padded_vec)

    mean_vector = []
    for i in range(max_len):
        pos_probs = [vec[i] for vec in padded_vectors if i < len(vec)]
        if pos_probs:
            mean_vector.append(sum(pos_probs) / len(pos_probs))
        else:
            mean_vector.append(0.0)

    return mean_vector


def extract_answer_from_generation(generated_text: str) -> str:
    """
    Extract the answer part from generated text, removing any thinking/thought sections.
    """
    thinking_patterns = [
        r'<think>.*?</think>',
        r'<thinking>.*?</thinking>',
        r'\[think\].*?\[/think\]',
        r'Thinking:.*?(?=\n\n|\n[^\n]*:|$)',
        r'Let me think.*?(?=\n\n|\n[^\n]*:|$)',
    ]

    text = generated_text
    for pattern in thinking_patterns:
        import re

        text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

    text = text.strip()

    return text


def create_char_binary_vector(extracted_answer: str) -> List[float]:
    """
    Create a binary vector where 1 means character is inside [SPAN][/SPAN] tags,
    0 means outside, excluding the span tag characters themselves.
    """
    result = []
    i = 0

    while i < len(extracted_answer):
        if extracted_answer[i : i + 6] == '[SPAN]':
            i += 6
            while i < len(extracted_answer):
                if extracted_answer[i : i + 7] == '[/SPAN]':
                    i += 7
                    break
                else:
                    result.append(1.0)  # Inside span
                    i += 1
        elif extracted_answer[i : i + 7] == '[/SPAN]':
            i += 7
        else:
            result.append(0.0)  # Outside span
            i += 1

    return result


# ============================================================================
# TOKEN PREDICTION REARRANGEMENT
# ============================================================================

def rearrange_token_predictions_with_indices(
    probs: List[torch.Tensor],
    preds: List[torch.Tensor],
    offsets: List[torch.Tensor],
    answer_indices: List[List[int]],
) -> Tuple[List[List[float]], List[List[int]]]:
    """
    Rearrange token-level predictions to character-level using repeat_interleave.
    
    Used by token encoder judge which predicts on all tokens and then filters
    to answer tokens, repeating each prediction across its character span.
    
    Args:
        probs: Per-token probabilities for each sample [num_samples][num_tokens]
        preds: Per-token predictions for each sample [num_samples][num_tokens]
        offsets: Character offsets (start, end) for each token [num_samples][num_tokens, 2]
        answer_indices: Indices of answer tokens for each sample [num_samples][num_answer_tokens]
    
    Returns:
        tuple of (probs_per_sample, preds_per_sample) at character level
    """
    repeats = [offset[:, 1] - offset[:, 0] for offset in offsets]
    
    probs_list = [
        prob[indices].repeat_interleave(repeat).tolist()
        for prob, repeat, indices in zip(probs, repeats, answer_indices)
    ]
    preds_list = [
        pred[indices].repeat_interleave(repeat).tolist()
        for pred, repeat, indices in zip(preds, repeats, answer_indices)
    ]
    
    return probs_list, preds_list


def repeat_labels_with_offsets(
    labels: List[List[int]],
    repeats: List[torch.Tensor],
) -> List[List[int]]:
    """
    Repeat token-level labels to character-level using offsets.
    
    Used by token encoder judge to expand labels from token to character level.
    
    Args:
        labels: Token-level labels [num_samples][num_tokens]
        repeats: Character span lengths for each token [num_samples][num_tokens]
    
    Returns:
        Character-level labels [num_samples][num_chars]
    """
    return [
        torch.tensor(label).repeat_interleave(repeat).tolist()
        for label, repeat in zip(labels, repeats)
    ]
