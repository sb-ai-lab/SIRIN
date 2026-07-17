"""Tests for weighted uncertainty aggregation."""

import numpy as np
from unittest.mock import MagicMock

from sirin.detection.uncertainty.detectors import UncertaintyDetectorBase
from sirin.models.detection import UncertaintyDetectorConfig


class ConcreteUncertaintyDetector(UncertaintyDetectorBase):
    def detect(self, *args, **kwargs):
        raise NotImplementedError

    def train(self, *args, **kwargs):
        raise NotImplementedError


def test_weighted_aggregation_matches_hand_computed():
    config = UncertaintyDetectorConfig(
        aggregation_method='weighted',
        method_weights={'MethodA': 0.75, 'MethodB': 0.25},
    )
    detector = object.__new__(ConcreteUncertaintyDetector)
    detector.config = config
    processor_config = MagicMock()
    processor_config.uncertainty_methods = ['MethodA', 'MethodB']
    detector.feature_processor = MagicMock()
    detector.feature_processor.config = processor_config

    uncertainties = np.array([[1.0, 3.0], [5.0, 7.0]])
    result = ConcreteUncertaintyDetector._weighted_aggregation(detector, uncertainties)
    expected = np.average(uncertainties, axis=-1, weights=[0.75, 0.25])
    np.testing.assert_allclose(result, expected)
