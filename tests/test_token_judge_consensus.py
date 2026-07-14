"""Regression for the API token judge: each character is scored by span-tag agreement across the
DISTINCT sampled generations, aligned to the reference answer. Only generations that echo the
answer verbatim vote; paraphrases are dropped; zero valid generations raise (never a silent
all-clear). The old bug fed num_beams copies of the first generation (fake consensus, every char
forced to a hard 0/1) and never validated the echo.
"""
import pytest

from sirin.detection.judging import JudgeAnnotationError, TokenOpenAIJudge
from sirin.detection.judging.judges.utils import calculate_character_probabilities
from sirin.models.detection import OpenAIJudgeConfig
from sirin.ui.presets import PRESETS


def test_consensus_is_graded_across_distinct_generations():
    # answer "abcd": gen1 flags "bc", gen2 flags "c", gen3 flags nothing -> a:0, b:1/3, c:2/3, d:0
    gens = ['a[SPAN]bc[/SPAN]d', 'ab[SPAN]c[/SPAN]d', 'abcd']
    assert calculate_character_probabilities(gens) == [0.0, 1 / 3, 2 / 3, 0.0]


def test_all_clear_scores_zero_not_mid():
    # nothing flagged anywhere -> all 0.0; with calibrated=True the heatmap reads all-clear rather
    # than a misleading uniform mid from min-maxing a flat array.
    assert calculate_character_probabilities(['abcd', 'abcd', 'abcd']) == [0.0, 0.0, 0.0, 0.0]


def test_reference_aligns_scores_to_answer_length():
    # scores are over the REFERENCE's characters, not the first generation's tag-stripped length.
    gens = ['a[SPAN]bc[/SPAN]d', 'abcd']
    assert calculate_character_probabilities(gens, reference='abcd') == [0.0, 0.5, 0.5, 0.0]


def test_api_token_judge_is_calibrated_absolute():
    # char scores are a fraction in [0, 1] -> shown absolute, not min-max-stretched.
    assert PRESETS['Judge — API Span (zero-shot)'].calibrated is True


# --- judge.detect() reference-aligned consensus (fake adapter, no network) -----------------


class _FakeAdapter:
    """Mimics OpenAIModelAdapter.sample: n==1 -> list[str]; n>1 -> list[list[str]]."""

    def __init__(self, per_sample_gens):
        self.per_sample_gens = per_sample_gens
        self.calls = []

    def sample(self, inputs, max_tokens=None, temperature=None, top_p=None, n=1):
        self.calls.append({'inputs': inputs, 'max_tokens': max_tokens, 'n': n})
        if n == 1:
            return [gens[0] for gens in self.per_sample_gens]
        return self.per_sample_gens


def _make_judge(per_sample_gens, n):
    judge = object.__new__(TokenOpenAIJudge)  # bypass model-loading __init__
    judge.config = OpenAIJudgeConfig(num_beams=n, temperature=0.7)
    judge.model_adapter = _FakeAdapter(per_sample_gens)
    judge.threshold = 0.5
    judge._context_splitter = None
    judge.last_generations = judge.last_spans = judge.last_consensus = None
    return judge


def _sample(answer, question='q'):
    return [
        {'role': 'user', 'content': question},
        {'role': 'assistant', 'content': answer},
    ]


def test_detect_grades_kn_over_reference():
    gens = ['a[SPAN]bc[/SPAN]d', 'ab[SPAN]c[/SPAN]d', 'abcd']
    judge = _make_judge([gens], n=3)

    probs, _, _ = judge.detect([_sample('abcd')])

    # judge wraps scores in torch.tensor -> float32; approx tolerates the rounding of 1/3, 2/3.
    assert probs[0] == pytest.approx([0.0, 1 / 3, 2 / 3, 0.0])
    assert judge.last_consensus == [{'requested': 3, 'valid': 3, 'temperature': 0.7}]
    assert judge.last_generations == gens  # sample 0's generations for the UI


def test_shorter_longer_and_paraphrased_echoes_are_dropped():
    gens = [
        'a[SPAN]bc[/SPAN]d',    # valid echo, flags bc
        'ab[SPAN]c[/SPAN]',     # echo "abc" (shorter) -> dropped
        'a[SPAN]bc[/SPAN]de',   # echo "abcde" (longer) -> dropped
        'a totally different answer',  # paraphrase -> dropped
    ]
    judge = _make_judge([gens], n=4)

    probs, _, _ = judge.detect([_sample('abcd')])

    assert probs[0] == [0.0, 1.0, 1.0, 0.0]  # only the one valid echo votes
    assert judge.last_consensus[0] == {'requested': 4, 'valid': 1, 'temperature': 0.7}


def test_all_invalid_raises_annotation_error_never_all_clear():
    judge = _make_judge([['wxyz', 'a paraphrase', 'ab']], n=3)

    with pytest.raises(JudgeAnnotationError):
        judge.detect([_sample('abcd')])


def test_think_wrapper_is_stripped_before_echo_check():
    gens = ['<think>let me check the passage</think>a[SPAN]bc[/SPAN]d', 'abcd']
    judge = _make_judge([gens], n=2)

    probs, _, _ = judge.detect([_sample('abcd')])

    assert probs[0] == [0.0, 0.5, 0.5, 0.0]
    assert judge.last_consensus[0]['valid'] == 2


def test_multi_sample_batch_isolation():
    gens0 = ['a[SPAN]bc[/SPAN]d', 'abcd']            # sample 0: bc flagged 1/2 -> 0.5
    gens1 = ['[SPAN]x[/SPAN]y', 'x[SPAN]y[/SPAN]']   # sample 1: x 1/2, y 1/2 -> 0.5, 0.5
    judge = _make_judge([gens0, gens1], n=2)

    probs, _, _ = judge.detect([_sample('abcd', 'q0'), _sample('xy', 'q1')])

    assert probs[0] == [0.0, 0.5, 0.5, 0.0]
    assert probs[1] == [0.5, 0.5]
    assert judge.last_consensus == [
        {'requested': 2, 'valid': 2, 'temperature': 0.7},
        {'requested': 2, 'valid': 2, 'temperature': 0.7},
    ]


def test_detect_forwards_max_new_tokens_and_n():
    judge = _make_judge([['abcd', 'abcd']], n=2)
    judge.config.max_new_tokens = 777

    judge.detect([_sample('abcd')])

    assert judge.model_adapter.calls[0]['max_tokens'] == 777
    assert judge.model_adapter.calls[0]['n'] == 2


def test_detect_single_generation_path():
    judge = _make_judge([['a[SPAN]bc[/SPAN]d']], n=1)

    probs, _, _ = judge.detect([_sample('abcd')])

    assert probs[0] == [0.0, 1.0, 1.0, 0.0]
    assert judge.last_consensus[0] == {'requested': 1, 'valid': 1, 'temperature': 0.7}
