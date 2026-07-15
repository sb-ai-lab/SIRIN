"""Turn OpenAI-style top-k logprobs into a calibrated positive-class probability."""

import math
from typing import Optional, Sequence, Tuple

# One generated position: its top-k alternatives as (token, logprob).
PositionLogprobs = Sequence[Tuple[str, float]]
# One generation: every position, in order.
TokenLogprobs = Sequence[PositionLogprobs]


def _first_class_position(
    sequence_logprobs: TokenLogprobs, positive: str, negative: str
) -> Optional[PositionLogprobs]:
    """The first generated position whose alternatives mention a class token.

    Scanning rather than assuming position 0: a model may open with whitespace or a
    newline before committing to the digit, and reasoning models can emit a preamble.
    """
    for alternatives in sequence_logprobs:
        tokens = {token.strip() for token, _ in alternatives}
        if positive in tokens or negative in tokens:
            return alternatives
    return None


def probability_of_positive_class(
    sequence_logprobs: Optional[TokenLogprobs],
    positive: str = '1',
    negative: str = '0',
) -> Optional[float]:
    """P(positive class) from the top-k alternatives at the classification position.

    Returns ``None`` when neither class token appears anywhere in the top-k, which means
    the model answered off-format and no probability can be read; callers should fall back
    to the parsed text prediction rather than invent a score. A ``None``/empty payload
    (e.g. from a provider that rejected the logprobs request) is the same case.

    Three cases, in order of how much they assume:

    * Both class tokens present -- renormalize over the pair. Standard practice for a
      constrained binary answer, and exact when the two tokens carry all the mass.
    * Only the positive token present -- ``exp(logprob)`` is already its marginal
      probability, so use it directly.
    * Only the negative token present -- report ``1 - exp(logprob)``. This is an UPPER
      bound on P(positive), not an equality: the residual mass is shared with every other
      token outside the top-k. It is monotone in the model's confidence, which is what
      threshold-free metrics (AUROC, AP) actually consume, and it only triggers when the
      model was so certain that the opposite class fell out of the top-k entirely.
    """
    if not sequence_logprobs:
        return None
    alternatives = _first_class_position(sequence_logprobs, positive, negative)
    if alternatives is None:
        return None

    # Alternatives arrive in descending-probability order; keep the first (highest) hit
    # for a token, since a tokenizer can surface the same string more than once.
    best: dict = {}
    for token, logprob in alternatives:
        best.setdefault(token.strip(), logprob)

    lp_pos, lp_neg = best.get(positive), best.get(negative)

    if lp_pos is not None and lp_neg is not None:
        p_pos, p_neg = math.exp(lp_pos), math.exp(lp_neg)
        total = p_pos + p_neg
        return p_pos / total if total > 0 else 0.5
    if lp_pos is not None:
        return math.exp(lp_pos)
    if lp_neg is not None:
        return 1.0 - math.exp(lp_neg)
    return None  # unreachable: _first_class_position matched on one of the two


def parse_binary_prediction(text: Optional[str], positive: str = '1') -> int:
    """Read the class digit out of a judge's raw text answer.

    Scans for the first ``0``/``1`` character instead of requiring ``text.isdigit()``:
    the old check failed on any decoration at all -- a trailing period, a leading space,
    a markdown wrapper -- and silently returned the negative class for every such sample.
    """
    if not text:
        return 0
    for char in text.strip():
        if char in ('0', '1'):
            return int(char == positive)
    return 0
