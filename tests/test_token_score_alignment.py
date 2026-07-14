from types import SimpleNamespace

import numpy as np
import pytest
import torch

from sirin.detection.uncertainty.detectors import (
    SequenceUncertaintyDetector,
    TokenUncertaintyDetector,
)
from sirin.definitions import TokenLocation
from sirin.detection.utils.token import get_answer_offsets, rearrange_token_predictions
from sirin.inference.adapters.hf_adapter import _token_uncertainty_trace
from sirin.inference.token_locators import HfTokenLocator
from sirin.models.inference import TokenLocatorConfig
from sirin.ui.streamlit_app import detection_view_model
from sirin.ui.styles import risk_color
from sirin.ui.visualizers import publication_granularity_html


def test_answer_locator_includes_prompt_answer_boundary_token():
    class Tokenizer:
        bos_token_id = None
        eos_token_id = 99

        @staticmethod
        def decode(tokens, **kwargs):
            assert tokens == [10, 11]
            return '.Two'

        @staticmethod
        def __call__(text, return_offsets_mapping=False, **kwargs):
            assert text == '.Two'
            encoded = {'input_ids': [10, 11]}
            if return_offsets_mapping:
                encoded['offset_mapping'] = [(0, 2), (2, 4)]
            return encoded

    locator = HfTokenLocator(TokenLocatorConfig(locate_answer_start=True))

    locations = locator.locate([10, 11], Tokenizer(), answer_text='Two')

    assert locations[TokenLocation.ANS_START.value] == 0


def test_token_projection_rejects_feature_offset_count_mismatch():
    with pytest.raises(ValueError, match='2 features.*3 offsets'):
        rearrange_token_predictions(
            np.array([0.2, 0.8]),
            np.array([0, 1]),
            np.array([[0, 1], [1, 629], [629, 630]]),
            [0, 2],
        )


def test_token_projection_covers_the_full_answer():
    probs, preds = rearrange_token_predictions(
        np.array([0.2, 0.8, 0.4]),
        np.array([0, 1, 0]),
        np.array([[0, 1], [1, 629], [629, 630]]),
        [0, 3],
    )

    assert len(probs[0]) == len(preds[0]) == 630
    assert probs[0][-1] == pytest.approx(0.4)


def test_token_view_rejects_empty_or_misaligned_output():
    detector = SimpleNamespace(
        detection_level=SimpleNamespace(value='token'),
        _ui_family='probing',
        _ui_calibrated=False,
        _ui_display_mode='threshold-spans',
        threshold=0.5,
    )

    with pytest.raises(ValueError, match='empty scores or predictions'):
        detection_view_model(([[]], [[]], None), 'abc', detector)
    with pytest.raises(ValueError, match='3 answer characters, 2 scores'):
        detection_view_model(([[0.2, 0.8]], [[0, 1]], None), 'abc', detector)


def test_token_offsets_preserve_ui_gradient_across_spaces():
    answer = 'Based on evidence'
    probs, preds = rearrange_token_predictions(
        np.array([0.1, 0.5, 0.9]),
        np.array([0, 0, 1]),
        np.array([[0, 5], [6, 8], [9, 17]]),
        [0, 3],
    )
    detector = SimpleNamespace(
        detection_level=SimpleNamespace(value='token'),
        _ui_family='uncertainty',
        _ui_calibrated=False,
        _ui_display_mode='heatmap',
        threshold=0.5,
    )

    view = detection_view_model((probs, preds, None), answer, detector)
    rendered = publication_granularity_html(view)

    assert view['aligned'] is True
    assert 'data-score="0.000" data-index="0" data-end="5"' in rendered
    assert 'data-score="0.500" data-index="6" data-end="8"' in rendered
    assert 'data-score="1.000" data-index="9" data-end="17"' in rendered
    assert all(
        f'background:{risk_color(score)}' in rendered for score in (0.0, 0.5, 1.0)
    )


def test_answer_offsets_exclude_chat_template_framing():
    class Tokenizer:
        def __call__(self, texts, return_offsets_mapping=False, **kwargs):
            encoded = {'input_ids': [list(range(len(text))) for text in texts]}
            if return_offsets_mapping:
                encoded['offset_mapping'] = [
                    [(index, index + 1) for index in range(len(text))] for text in texts
                ]
            return encoded

    class Model:
        tokenizer = Tokenizer()
        config = SimpleNamespace(truncation=False)

        @staticmethod
        def _preprocess_input(samples):
            rendered = []
            for sample in samples:
                user = sample[0]['content']
                assistant = next(
                    (item['content'] for item in sample if item['role'] == 'assistant'),
                    None,
                )
                text = f'<user>{user}</user>'
                if assistant is not None:
                    text += f'<assistant>{assistant}</assistant>'
                rendered.append(text)
            return rendered

    offsets, _, answer_indices = get_answer_offsets(
        [
            [
                {'role': 'user', 'content': 'Evidence'},
                {'role': 'assistant', 'content': 'Answer'},
            ]
        ],
        Model(),
    )

    assert offsets == [[(index, index + 1) for index in range(len('Answer'))]]
    assert len(answer_indices[0]) == len('Answer')


def _trace_detector():
    detector = object.__new__(TokenUncertaintyDetector)
    detector.threshold = 0.5
    detector._context_splitter = None
    detector.config = SimpleNamespace(
        aggregation_method='mean',
        method_weights=None,
        num_classification_heads=2,
    )
    detector.feature_processor = SimpleNamespace(
        config=SimpleNamespace(
            uncertainty_methods=['MaximumTokenProbability', 'TokenEntropy']
        )
    )
    return detector


def test_stream_trace_keeps_exact_tokens_offsets_and_scores():
    class Tokenizer:
        pieces = {1: 'A', 2: ' B', 0: ''}

        def decode(self, ids, **kwargs):
            return ''.join(self.pieces[token_id] for token_id in ids)

    scores = (
        torch.tensor([[0.0, 2.0, -1.0]]),
        torch.tensor([[0.0, -1.0, 1.5]]),
        torch.tensor([[3.0, 0.0, 0.0]]),
    )
    trace = _token_uncertainty_trace(
        Tokenizer(),
        torch.tensor([1, 2, 0]),
        scores,
        input_sha256='input',
        temperature=0.0,
        max_tokens=8,
    )

    assert trace['text'] == 'A B'
    assert trace['token_ids'] == [1, 2]
    assert trace['pieces'] == ['A', ' B']
    assert trace['offsets'] == [[0, 1], [1, 3]]
    assert len(trace['MaximumTokenProbability']) == 2
    assert len(trace['TokenEntropy']) == 2
    assert trace['methods'] == ['MaximumTokenProbability', 'TokenEntropy']
    assert trace['entropy_scope'] == 'full-vocabulary'
    assert len(trace['trace_sha256']) == 64


def test_token_detector_scores_only_the_answer_bound_to_the_trace():
    trace = {
        'text': '1 sport',
        'pieces': ['1', ' sport'],
        'offsets': [[0, 1], [1, 7]],
        'MaximumTokenProbability': [0.8, 0.6],
        'TokenEntropy': [1.0, 0.4],
    }
    detector = _trace_detector()
    sample = [
        [
            {'role': 'user', 'content': 'How many?'},
            {'role': 'assistant', 'content': '1 sport'},
        ]
    ]

    probs, preds, _ = detector.detect(sample, generation_trace=trace)

    assert probs[0] == pytest.approx([0.9] + [0.5] * 6)
    assert preds[0] == [1] + [0] * 6
    assert detector.last_generated_text == '1 sport'

    sample[0][-1]['content'] = '2 sports'
    with pytest.raises(ValueError, match='does not match the displayed answer'):
        detector.detect(sample, generation_trace=trace)


def test_sequence_uncertainty_verdict_uses_the_same_generation_trace():
    detector = object.__new__(SequenceUncertaintyDetector)
    detector.threshold = 0.25
    detector._context_splitter = None
    detector.config = SimpleNamespace(
        aggregation_method='mean',
        method_weights=None,
        num_classification_heads=2,
    )
    detector.feature_processor = SimpleNamespace(
        config=SimpleNamespace(uncertainty_methods=['MeanTokenEntropy', 'Perplexity'])
    )
    trace = {
        'text': 'wrong count',
        'pieces': ['wrong', ' count'],
        'offsets': [[0, 5], [5, 11]],
        'MaximumTokenProbability': [0.2, 0.4],
        'TokenEntropy': [0.4, 0.6],
    }
    sample = [
        [
            {'role': 'user', 'content': 'Question'},
            {'role': 'assistant', 'content': 'wrong count'},
        ]
    ]

    probs, preds, _ = detector.detect(sample, generation_trace=trace)

    assert probs == pytest.approx([0.4])
    assert preds.tolist() == [1]
    assert detector.last_method_scores == {
        'MeanTokenEntropy': pytest.approx(0.5),
        'Perplexity': pytest.approx(0.3),
    }
