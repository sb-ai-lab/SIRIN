"""Regression for the API token judge: each character is scored by span-tag agreement across the
DISTINCT sampled generations. The bug fed num_beams copies of the first generation (fake consensus,
every char forced to a hard 0/1), and the view min-maxed the near-binary array to a misleading grey.
"""
from sirin.detection.judging.judges.utils import calculate_character_probabilities
from sirin.ui.presets import PRESETS


def test_consensus_is_graded_across_distinct_generations():
    # answer "abcd": gen1 flags "bc", gen2 flags "c", gen3 flags nothing -> a:0, b:1/3, c:2/3, d:0
    gens = ['a[SPAN]bc[/SPAN]d', 'ab[SPAN]c[/SPAN]d', 'abcd']
    assert calculate_character_probabilities(gens) == [0.0, 1 / 3, 2 / 3, 0.0]


def test_all_clear_scores_zero_not_mid():
    # nothing flagged anywhere -> all 0.0; with calibrated=True the heatmap reads all-clear rather
    # than a misleading uniform mid from min-maxing a flat array.
    assert calculate_character_probabilities(['abcd', 'abcd', 'abcd']) == [0.0, 0.0, 0.0, 0.0]


def test_api_token_judge_is_calibrated_absolute():
    # char scores are a fraction in [0, 1] -> shown absolute, not min-max-stretched.
    assert PRESETS['Judge — API Token (zero-shot)'].calibrated is True
