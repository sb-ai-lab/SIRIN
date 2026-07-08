"""Tests for split_context_train wiring."""

from unittest.mock import MagicMock, patch

import datasets

from sirin.detection.base import PipelineBase
from sirin.definitions import INPUT_COL, TARGET_COL
from sirin.models.detection import PipelineBaseConfig, ProbingDetectorConfig


class MinimalPipeline(PipelineBase):
    target_col = TARGET_COL

    def train(self, *args, **kwargs):
        pass

    def eval(self, *args, **kwargs):
        pass

    def __init__(self, config, detector):
        self.config = config
        self.detector = detector
        self._generator_adapter = None
        self.task_type = None
        self.experiment_logger = None


def _stage_names_for(config):
    detector = MagicMock()
    detector.config = ProbingDetectorConfig()
    detector._context_splitter = None
    detector.num_cpus = 1
    pipeline = MinimalPipeline(config, detector)

    dataset = datasets.Dataset.from_dict({
        INPUT_COL: [[{'role': 'user', 'content': 'q'}, {'role': 'assistant', 'content': 'a'}]],
        TARGET_COL: [0],
    })

    captured_stages = []

    def record(stage):
        def _processor(ds):
            captured_stages.append(stage)
            return ds
        return _processor

    with (
        patch.object(pipeline, '_generate_answers', side_effect=record('generation')),
        patch.object(pipeline, '_clean_generation_outputs', side_effect=record('cleaning')),
        patch.object(pipeline, '_compute_lm_metrics', side_effect=record('metrics')),
        patch.object(pipeline, '_split_context', side_effect=record('splitting')),
    ):
        pipeline._load_dataset(dataset, split='train')

    return captured_stages


def test_default_stages_exclude_splitting():
    captured_stages = _stage_names_for(PipelineBaseConfig(split_context_train=False))
    assert captured_stages == ['generation', 'cleaning', 'metrics']


def test_split_context_train_adds_splitting_stage():
    captured_stages = _stage_names_for(PipelineBaseConfig(split_context_train=True))
    assert captured_stages == ['generation', 'cleaning', 'metrics', 'splitting']
