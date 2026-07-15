import math

import pytest

from sirin.detection.judging.judges.utils.logprobs import (
    parse_binary_prediction,
    probability_of_positive_class,
)

LN = math.log


def test_both_class_tokens_present_renormalizes_over_the_pair():
    # P("1")=0.8, P("0")=0.2 before renormalization (they already sum to 1)
    seq = [[('1', LN(0.8)), ('0', LN(0.2))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.8)


def test_renormalization_when_class_tokens_do_not_carry_all_mass():
    # P("1")=0.3, P("0")=0.1, rest elsewhere -> renormalized 0.3/0.4 = 0.75
    seq = [[('1', LN(0.3)), ('0', LN(0.1))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.75)


def test_confident_zero_and_confident_one_get_opposite_scores():
    """The bug this module exists to fix: -logprob gave both the SAME score."""
    confident_one = [[('1', LN(0.99)), ('0', LN(0.01))]]
    confident_zero = [[('0', LN(0.99)), ('1', LN(0.01))]]
    p_one = probability_of_positive_class(confident_one)
    p_zero = probability_of_positive_class(confident_zero)
    assert p_one == pytest.approx(0.99)
    assert p_zero == pytest.approx(0.01)
    assert p_one > 0.5 > p_zero  # they must land on opposite sides


def test_only_positive_token_present_uses_its_marginal():
    seq = [[('1', LN(0.7)), ('banana', LN(0.2))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.7)


def test_only_negative_token_present_uses_one_minus_marginal():
    seq = [[('0', LN(0.9)), ('banana', LN(0.05))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.1)


def test_scans_past_leading_whitespace_to_the_class_position():
    seq = [[('\n', LN(0.99))], [('1', LN(0.8)), ('0', LN(0.2))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.8)


def test_returns_none_when_no_class_token_anywhere():
    seq = [[('I', LN(0.5)), ('cannot', LN(0.4))]]
    assert probability_of_positive_class(seq) is None


def test_returns_none_for_empty_or_missing_payload():
    # A provider that rejected the logprobs request yields None/[] per sample; the
    # BadRequestError retry path in the sequence judge feeds exactly that.
    assert probability_of_positive_class(None) is None
    assert probability_of_positive_class([]) is None


def test_tokens_are_stripped_before_matching():
    seq = [[(' 1', LN(0.8)), (' 0', LN(0.2))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.8)


def test_duplicate_token_keeps_highest_probability_entry():
    # alternatives arrive descending; the first "1" is the real one
    seq = [[('1', LN(0.6)), ('1', LN(0.01)), ('0', LN(0.4))]]
    assert probability_of_positive_class(seq) == pytest.approx(0.6)


@pytest.mark.parametrize(
    'text,expected',
    [('1', 1), ('0', 0), (' 1 ', 1), ('1.', 1), ('**0**', 0), ('', 0), (None, 0),
     ('I cannot answer', 0), ('Answer: 1', 1)],
)
def test_parse_binary_prediction_tolerates_decoration(text, expected):
    assert parse_binary_prediction(text) == expected


def test_probability_is_monotone_in_confidence():
    """AUROC only consumes ordering, so the score must rank confidence correctly."""
    scores = [
        probability_of_positive_class([[('1', LN(p)), ('0', LN(1 - p))]])
        for p in (0.51, 0.7, 0.9, 0.99)
    ]
    assert scores == sorted(scores)
