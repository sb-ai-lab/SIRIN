"""Verbalized-confidence judge parsing + tuple logprob extraction.

Ported from the collaborator's tree minus one test (`test_threshold_at_an_attained_score_
still_fires`) that imports their repo-root `experiment_api.py`, which is not part of the
`sirin` package.
"""
import types

import pytest

from sirin.detection.judging.judges.sequence.openai import parse_label_and_confidence
from sirin.inference.adapters.openai_adapter import _extract_sequence_logprobs


def _top(token, logprob):
    return types.SimpleNamespace(token=token, logprob=logprob)


def _pos(token, logprob, tops=None):
    return types.SimpleNamespace(token=token, logprob=logprob, top_logprobs=tops)


def test_extract_sequence_logprobs_keeps_the_token_string():
    """The whole point: a bare float cannot say WHICH class it belongs to."""
    payload = [_pos('0', -0.06, [_top('0', -0.06), _top('1', -2.81)])]
    assert _extract_sequence_logprobs(payload) == [[('0', -0.06), ('1', -2.81)]]


def test_extract_sequence_logprobs_falls_back_to_the_chosen_token():
    """When the provider omits top_logprobs, the sampled token is still recoverable."""
    payload = [_pos('1', -0.5, None)]
    assert _extract_sequence_logprobs(payload) == [[('1', -0.5)]]


def test_extract_sequence_logprobs_preserves_position_order():
    payload = [_pos('a', -0.1, [_top('a', -0.1)]), _pos('b', -0.2, [_top('b', -0.2)])]
    assert _extract_sequence_logprobs(payload) == [[('a', -0.1)], [('b', -0.2)]]


@pytest.mark.parametrize(
    'text,pred,prob',
    [
        ('1 87', 1, 0.87),
        ('0 90', 0, 0.10),   # 90% sure GROUNDED -> P(hallucinated) = 0.10
        ('1 100', 1, 1.00),
        ('0 50', 0, 0.50),   # maximal uncertainty lands at the threshold
        ('**1** (95%)', 1, 0.95),
        ('1 150', 1, 1.00),  # confidence clamped into [0, 100]
    ],
)
def test_parse_label_and_confidence(text, pred, prob):
    got_pred, got_prob = parse_label_and_confidence(text)
    assert got_pred == pred
    assert got_prob == pytest.approx(prob)


@pytest.mark.parametrize('text', ['garbage', '', None, 'I cannot answer'])
def test_parse_label_and_confidence_degrades_to_hard_prediction(text):
    pred, prob = parse_label_and_confidence(text)
    assert pred == 0
    assert prob == 0.0  # no invented score


def test_bare_label_without_confidence_degrades_to_hard_prediction():
    assert parse_label_and_confidence('1') == (1, 1.0)
    assert parse_label_and_confidence('0') == (0, 0.0)


def test_glued_digits_are_read_as_label_then_confidence():
    """"10" is ambiguous; we resolve it as label=1, confidence=0, not label=10.

    Documented rather than silently surprising: a model that ignores the space in the
    requested "<label> <confidence>" format yields a confident-looking label with a
    zero confidence, which correctly scores as maximally uncertain-against-itself.
    """
    assert parse_label_and_confidence('10') == (1, 0.0)
