"""Tests for PipelineBase._generate_answers."""

import inspect
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock, patch

import datasets
import pytest

from sirin.definitions import INPUT_COL, TARGET_COL
from sirin.detection.base import PipelineBase
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.models.detection import PipelineBaseConfig, ProbingDetectorConfig, SamplingConfig


class FakeGeneratorAdapter(ModelAdapterBase):
    def __init__(self):
        self.device = 'cpu'
        self._is_loaded = False
        self._model_name = 'fake'
        self.sample_kwargs_log = []

    def load(self):
        self._is_loaded = True

    def unload(self):
        self._is_loaded = False

    def sample(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        self.sample_kwargs_log.append({
            'input_count': len(inputs),
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'extra': kwargs,
        })
        return [f"generated-{i}" for i in range(len(inputs))]


class MinimalPipeline(PipelineBase):
    target_col = TARGET_COL

    def train(self, *args, **kwargs):
        pass

    def eval(self, *args, **kwargs):
        pass

    def __init__(self, config, detector, generator_adapter=None):
        self.config = config
        self.detector = detector
        self._generator_adapter = generator_adapter
        self.task_type = None
        self.experiment_logger = None


def test_fake_adapter_signature_matches_base():
    assert inspect.signature(FakeGeneratorAdapter.sample) == inspect.signature(ModelAdapterBase.sample)


def test_generate_answers_appends_assistant_messages():
    config = PipelineBaseConfig(
        sampling=SamplingConfig(max_length=64, do_sample=True, num_beams=4),
    )
    detector = MagicMock()
    detector.config = ProbingDetectorConfig(batch_size=2)
    detector.num_cpus = 1
    pipeline = MinimalPipeline(config, detector, FakeGeneratorAdapter())

    dataset = datasets.Dataset.from_dict({
        INPUT_COL: [
            [{'role': 'user', 'content': 'Q1'}],
            [{'role': 'user', 'content': 'Q2'}, {'role': 'assistant', 'content': 'A2'}],
        ],
        TARGET_COL: [0, 1],
    })

    with patch('sirin.detection.base.ModelManager.load_model', return_value=pipeline._generator_adapter) as load_model:
        result = pipeline._generate_answers(dataset)

    load_model.assert_called_once_with(pipeline._generator_adapter)
    assert result[INPUT_COL][0][-1]['role'] == 'assistant'
    assert result[INPUT_COL][0][-1]['content'] == 'generated-0'
    assert 'do_sample' not in pipeline._generator_adapter.sample_kwargs_log[0]['extra']
    assert 'num_beams' not in pipeline._generator_adapter.sample_kwargs_log[0]['extra']
    assert pipeline._generator_adapter.sample_kwargs_log[0]['max_tokens'] == 64


def test_generate_answers_passes_sampling_kwargs():
    config = PipelineBaseConfig(
        sampling=SamplingConfig(
            max_length=64,
            kwargs={'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}},
        ),
    )
    detector = MagicMock()
    detector.config = ProbingDetectorConfig(batch_size=1)
    detector.num_cpus = 1
    pipeline = MinimalPipeline(config, detector, FakeGeneratorAdapter())

    dataset = datasets.Dataset.from_dict({
        INPUT_COL: [[{'role': 'user', 'content': 'Q1'}]],
        TARGET_COL: [0],
    })

    with patch('sirin.detection.base.ModelManager.load_model', return_value=pipeline._generator_adapter) as load_model:
        pipeline._generate_answers(dataset)

    load_model.assert_called_once_with(pipeline._generator_adapter)
    assert pipeline._generator_adapter.sample_kwargs_log[0]['extra'] == {
        'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}
    }


def test_generate_answers_batches_missing_samples():
    config = PipelineBaseConfig(sampling=SamplingConfig(max_length=64))
    detector = MagicMock()
    detector.config = ProbingDetectorConfig(batch_size=2)
    detector.num_cpus = 1
    pipeline = MinimalPipeline(config, detector, FakeGeneratorAdapter())

    dataset = datasets.Dataset.from_dict({
        INPUT_COL: [[{'role': 'user', 'content': f'Q{i}'}] for i in range(5)],
        TARGET_COL: [0, 1, 0, 1, 0],
    })

    with patch('sirin.detection.base.ModelManager.load_model', return_value=pipeline._generator_adapter):
        pipeline._generate_answers(dataset)

    assert [call['input_count'] for call in pipeline._generator_adapter.sample_kwargs_log] == [2, 2, 1]


@pytest.mark.integration
def test_generate_answers_real_endpoint():
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
    config = PipelineBaseConfig(
        sampling=SamplingConfig(
            max_length=32,
            temperature=0.0,
            kwargs={'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}},
        )
    )
    detector = MagicMock()
    detector.config = ProbingDetectorConfig(batch_size=1)
    detector.num_cpus = 1
    pipeline = MinimalPipeline(config, detector, adapter)

    dataset = datasets.Dataset.from_dict({
        INPUT_COL: [[{'role': 'user', 'content': 'Say hi in one word.'}]],
        TARGET_COL: [0],
    })

    result = pipeline._generate_answers(dataset)

    assert result[INPUT_COL][0][-1]['role'] == 'assistant'
    assert len(result[INPUT_COL][0][-1]['content'].strip()) > 0
