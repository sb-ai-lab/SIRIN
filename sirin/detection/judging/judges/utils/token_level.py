from dataclasses import dataclass
from typing import List, Literal, Tuple

import numpy as np
import torch
from loguru import logger as lg


SPAN_OPEN = '[SPAN]'
SPAN_CLOSE = '[/SPAN]'
SpanAlignment = Literal['strict', 'whitespace_only']


@dataclass(frozen=True)
class SpanAlignmentResult:
    """A validated span annotation projected onto the original response."""

    char_scores: List[float]
    status: Literal['exact', 'whitespace_recovered']
    repaired_whitespace: int = 0


class SpanAlignmentError(ValueError):
    """A judge output cannot be aligned without changing lexical content."""

    def __init__(self, reason: Literal['malformed_tags', 'lexical_rewrite'], message: str):
        super().__init__(message)
        self.reason = reason


def _parse_tagged_text(text: str) -> Tuple[str, List[float], List[int | None]]:
    plain: List[str] = []
    scores: List[float] = []
    span_ids: List[int | None] = []
    inside = False
    current_span = 0
    index = 0
    while index < len(text):
        if text.startswith(SPAN_OPEN, index):
            if inside:
                raise SpanAlignmentError('malformed_tags', 'Nested [SPAN] markers are invalid.')
            inside = True
            current_span += 1
            index += len(SPAN_OPEN)
            continue
        if text.startswith(SPAN_CLOSE, index):
            if not inside:
                raise SpanAlignmentError('malformed_tags', 'Unexpected [/SPAN] marker.')
            inside = False
            index += len(SPAN_CLOSE)
            continue
        plain.append(text[index])
        scores.append(float(inside))
        span_ids.append(current_span if inside else None)
        index += 1
    if inside:
        raise SpanAlignmentError('malformed_tags', 'Unclosed [SPAN] marker.')
    return ''.join(plain), scores, span_ids


def _edit_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for row, left_char in enumerate(left, 1):
        current = [row]
        for column, right_char in enumerate(right, 1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_char != right_char),
            ))
        previous = current
    return previous[-1]


def align_span_annotation(
    generated_text: str,
    reference: str,
    mode: SpanAlignment = 'strict',
) -> SpanAlignmentResult:
    """Validate a tagged echo and project it onto the original response.

    ``whitespace_only`` permits only Unicode whitespace differences. Missing
    reference whitespace is inside a span only when both neighbouring lexical
    characters are inside it; boundary and ambiguous whitespace stays outside.
    """
    if mode not in {'strict', 'whitespace_only'}:
        raise ValueError(f'Unsupported span alignment mode: {mode!r}.')
    plain, generated_scores, generated_span_ids = _parse_tagged_text(generated_text)
    if plain == reference:
        return SpanAlignmentResult(generated_scores, 'exact')
    if mode == 'strict':
        raise SpanAlignmentError('lexical_rewrite', 'Judge output is not an exact echo.')

    generated_nonspace = [
        (char, generated_scores[i], generated_span_ids[i])
        for i, char in enumerate(plain) if not char.isspace()
    ]
    reference_nonspace = [char for char in reference if not char.isspace()]
    if [char for char, _, _ in generated_nonspace] != reference_nonspace:
        raise SpanAlignmentError(
            'lexical_rewrite',
            'Judge output changed non-whitespace text; refusing approximate alignment.',
        )

    nonspace_scores = [score for _, score, _ in generated_nonspace]
    nonspace_span_ids = [span_id for _, _, span_id in generated_nonspace]
    projected: List[float] = []
    nonspace_index = 0
    repaired = _edit_distance(
        ''.join(char for char in plain if char.isspace()),
        ''.join(char for char in reference if char.isspace()),
    )
    for char in reference:
        if not char.isspace():
            projected.append(nonspace_scores[nonspace_index])
            nonspace_index += 1
            continue
        previous_span = nonspace_span_ids[nonspace_index - 1] if nonspace_index > 0 else None
        next_span = (
            nonspace_span_ids[nonspace_index]
            if nonspace_index < len(nonspace_span_ids)
            else None
        )
        projected.append(float(previous_span is not None and previous_span == next_span))

    if len(projected) != len(reference):
        raise AssertionError('Span alignment must preserve the reference length.')
    return SpanAlignmentResult(projected, 'whitespace_recovered', repaired)


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
    generated_texts: List[str], reference: str | None = None,
    alignment: SpanAlignment = 'strict',
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
        extracted_answer = extract_answer_from_generation(
            gen_text, strip=reference is None
        )

        char_vector = (
            align_span_annotation(extracted_answer, reference, alignment).char_scores
            if reference is not None
            else create_char_binary_vector(extracted_answer)
        )
        all_char_vectors.append(char_vector)

    if reference is not None:
        max_len = len(reference)
        lead = 0
    elif all_char_vectors:
        max_len = len(all_char_vectors[0])
        lead = 0
    else:
        return [0.0] * len(generated_texts[0]) if generated_texts else []

    padded_vectors = []
    for vec in all_char_vectors:
        padded_vec = [0.0] * max_len
        for j, value in enumerate(vec):
            pos = lead + j
            if 0 <= pos < max_len:
                padded_vec[pos] = value
        padded_vectors.append(padded_vec)

    mean_vector = []
    for i in range(max_len):
        pos_probs = [vec[i] for vec in padded_vectors if i < len(vec)]
        if pos_probs:
            mean_vector.append(sum(pos_probs) / len(pos_probs))
        else:
            mean_vector.append(0.0)

    return mean_vector


def extract_answer_from_generation(generated_text: str, *, strip: bool = True) -> str:
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

    if strip:
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
    response_lengths: List[int] | None = None,
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
    if response_lengths is None:
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

    probs_list = []
    preds_list = []
    for prob, pred, sample_offsets, indices, response_length in zip(
        probs, preds, offsets, answer_indices, response_lengths
    ):
        char_probs = [0.0] * response_length
        char_preds = [0] * response_length
        for token_index, (start, end) in zip(indices, sample_offsets.tolist()):
            start = max(0, min(int(start), response_length))
            end = max(start, min(int(end), response_length))
            char_probs[start:end] = [float(prob[token_index])] * (end - start)
            char_preds[start:end] = [int(pred[token_index])] * (end - start)
        probs_list.append(char_probs)
        preds_list.append(char_preds)
    
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
