"""Tests for SEPTargetApproximator."""

import numpy as np
import pytest
from unittest.mock import MagicMock

from sirin.detection.approximators.sep import SEPTargetApproximator
from sirin.inference.adapters.base import ModelAdapterBase


class FakeLogprobAdapter(ModelAdapterBase):
    def __init__(self):
        self.device = 'cpu'
        self._is_loaded = False
        self._model_name = 'fake'

    def load(self):
        self._is_loaded = True

    def unload(self):
        self._is_loaded = False

    def sample(self, inputs, return_logprobs=False, num_return_sequences=1, **kwargs):
        texts = [f"answer-{i}" for i in range(len(inputs))]
        logprobs = [[[-0.1], [-0.2]] for _ in inputs]
        return texts, logprobs


def test_sep_does_not_reject_hf_adapter_with_logprob_signature():
    from sirin.inference.adapters import HfModelAdapter
    from sirin.models.inference import HFConfig

    adapter = HfModelAdapter(HFConfig(model_path='sshleifer/tiny-gpt2', device='cpu'))
    sep = SEPTargetApproximator.__new__(SEPTargetApproximator)
    sep.extractor = adapter
    sep._ensure_logprob_support()


def test_sep_normalizes_openai_flat_outputs():
    sep = SEPTargetApproximator.__new__(SEPTargetApproximator)
    sep.num_return_sequences = 2

    texts, logprobs = sep._normalize_sample_outputs(
        ['a', 'b'],
        [[[-0.1], [-0.2]], [[-0.3]]],
        sample_count=2,
    )
    assert texts == [['a'], ['b']]
    assert logprobs == [[-0.30000000000000004], [-0.3]]


def test_sep_normalizes_flat_multi_return_outputs():
    sep = SEPTargetApproximator.__new__(SEPTargetApproximator)
    sep.num_return_sequences = 2

    texts, logprobs = sep._normalize_sample_outputs(
        ['a', 'b', 'c', 'd'],
        [[[-0.1]], [[-0.2]], [[-0.3]], [[-0.4]]],
        sample_count=2,
    )
    assert texts == [['a', 'b'], ['c', 'd']]
    assert logprobs == [[-0.1, -0.2], [-0.3, -0.4]]


def test_sep_normalizes_vllm_nested_outputs():
    sep = SEPTargetApproximator.__new__(SEPTargetApproximator)
    sep.num_return_sequences = 2

    texts, logprobs = sep._normalize_sample_outputs(
        [['a', 'b']],
        [[[[-0.1], [-0.2]], [[-0.3]]]],
        sample_count=1,
    )
    assert texts == [['a', 'b']]
    assert logprobs == [[-0.30000000000000004, -0.3]]


def test_sep_fake_adapter_finite_entropy(monkeypatch):
    adapter = FakeLogprobAdapter()
    sep = SEPTargetApproximator.__new__(SEPTargetApproximator)
    sep.extractor = adapter
    sep.num_return_sequences = 2
    sep.stats = {}
    sep.nli_model = MagicMock()

    class FakeSemanticMatrixCalculator:
        def __init__(self, nli_model):
            pass

        def __call__(self, stats, samples):
            return {'semantic_matrix_entail': np.zeros((len(samples), 1, 1))}

    class FakeSemanticClassesCalculator:
        def __call__(self, stats):
            return {
                'semantic_classes_entail': {
                    'class_to_sample': [[[0]] for _ in stats['sample_texts']],
                    'sample_to_class': [[0] for _ in stats['sample_texts']],
                }
            }

    class FakeSemanticEntropy:
        def __call__(self, stats):
            return np.array([0.1, 0.9])

    monkeypatch.setattr(
        'lm_polygraph.stat_calculators.SemanticMatrixCalculator',
        FakeSemanticMatrixCalculator,
    )
    monkeypatch.setattr(
        'lm_polygraph.stat_calculators.SemanticClassesCalculator',
        FakeSemanticClassesCalculator,
    )
    monkeypatch.setattr('lm_polygraph.estimators.SemanticEntropy', FakeSemanticEntropy)

    labels = sep(
        [
            [{'role': 'user', 'content': 'q1'}],
            [{'role': 'user', 'content': 'q2'}],
        ]
    )
    assert len(labels) == 2
    assert all(label in {0, 1} for label in labels)
    assert sep.stats['sample_texts'] == [['answer-0'], ['answer-1']]
    assert sep.stats['sample_log_probs'] == [[-0.30000000000000004], [-0.30000000000000004]]


def test_sep_reshape_logprobs():
    logits = [[[[-0.1], [-0.2]]]]
    result = SEPTargetApproximator._reshape_logprobs(logits)
    assert len(result) == 1
    assert isinstance(result[0][0], float)


@pytest.mark.integration
def test_sep_real_endpoint():
    import urllib.request

    try:
        urllib.request.urlopen('http://localhost:30035/v1/models', timeout=5)
    except Exception:
        pytest.skip("localhost:30035 endpoint unavailable")

    from sirin.inference.adapters import OpenAIModelAdapter
    from sirin.models.inference import OpenAIConfig

    adapter = OpenAIModelAdapter(
        OpenAIConfig(
            model_path='Qwen/Qwen3.5-35B-A3B',
            base_url='http://localhost:30035/v1',
            api_key='EMPTY',
        )
    )
    sep = SEPTargetApproximator(
        adapter,
        num_return_sequences=2,
        sampling_kwargs={'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}},
    )
    labels = sep(
        [
            [{'role': 'user', 'content': 'What is 2+2? Answer briefly.'}],
            [{'role': 'user', 'content': 'Name one color.'}],
        ]
    )
    assert len(labels) == 2
    assert all(label in {0, 1} for label in labels)
