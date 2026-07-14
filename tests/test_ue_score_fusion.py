"""UE score normalization + auto fusion selection (fit on train, frozen for detect)."""

import numpy as np
import pytest
from unittest.mock import MagicMock

from sirin.detection.uncertainty.detectors import UncertaintyDetectorBase
from sirin.models.detection import UncertaintyDetectorConfig


class ConcreteUncertaintyDetector(UncertaintyDetectorBase):
    def detect(self, *args, **kwargs):
        raise NotImplementedError

    def train(self, *args, **kwargs):
        raise NotImplementedError


def _detector(config, method_names=('MethodA', 'MethodB')):
    detector = object.__new__(ConcreteUncertaintyDetector)
    detector.config = config
    detector.feature_stats = {}
    processor_config = MagicMock()
    processor_config.uncertainty_methods = list(method_names)
    detector.feature_processor = MagicMock()
    detector.feature_processor.config = processor_config
    return detector


def test_default_none_normalization_is_a_passthrough():
    detector = _detector(UncertaintyDetectorConfig())
    scores = np.array([[1.0, 100.0], [2.0, 200.0]])
    np.testing.assert_array_equal(detector._normalize_scores(scores), scores)
    # And the mean aggregation is unchanged from the pre-merge behavior.
    np.testing.assert_allclose(
        detector._aggregate_uncertainties(scores), scores.mean(axis=-1)
    )


def test_rank_normalization_maps_onto_the_train_cdf_and_imputes_nan():
    detector = _detector(UncertaintyDetectorConfig(score_normalization='rank'))
    train = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0], [4.0, 40.0]])
    detector.fit_score_normalizer(train)

    test = np.array([[2.5, np.nan]])
    normalized = detector._normalize_scores(test)
    assert normalized[0, 0] == pytest.approx(0.5)  # 2 of 4 train values <= 2.5
    # NaN imputed with the train median (25.0) -> rank 0.5, contributes neutrally.
    assert normalized[0, 1] == pytest.approx(0.5)


def test_zscore_normalization_uses_train_statistics():
    detector = _detector(UncertaintyDetectorConfig(score_normalization='zscore'))
    train = np.array([[0.0, 100.0], [2.0, 300.0]])
    detector.fit_score_normalizer(train)

    normalized = detector._normalize_scores(np.array([[1.0, 200.0]]))
    np.testing.assert_allclose(normalized, [[0.0, 0.0]])  # both at the train mean


def test_auto_selection_freezes_the_informative_estimator():
    # Column 0 separates the classes perfectly; column 1 is anti-correlated noise that
    # would drag a plain mean to chance. Auto must pick column 0 alone on train.
    detector = _detector(
        UncertaintyDetectorConfig(aggregation_method='auto', score_normalization='rank')
    )
    rng = np.random.RandomState(0)
    y = np.array([0, 1] * 30)
    signal = y + rng.normal(0, 0.05, size=60)
    noise = -y + rng.normal(0, 0.05, size=60)
    train = np.column_stack([signal, noise])

    detector.fit_score_normalizer(train)
    detector.fit_score_selection(train, y)

    assert detector.feature_stats['selected_subset'] == [0]
    assert detector.feature_stats['selected_aggregation'] == 'mean'
    # detect-time aggregation uses the frozen subset: high signal -> high score.
    hi = detector._aggregate_uncertainties(np.array([[1.0, 1.0]]))
    lo = detector._aggregate_uncertainties(np.array([[0.0, 1.0]]))
    assert hi[0] > lo[0]


def test_auto_without_a_fitted_selection_falls_back_to_mean():
    detector = _detector(UncertaintyDetectorConfig(aggregation_method='auto'))
    scores = np.array([[1.0, 3.0]])
    np.testing.assert_allclose(detector._aggregate_uncertainties(scores), [2.0])


def test_focus_estimator_requires_method_kwargs():
    # Focus has no constructor defaults (IDF corpus, spaCy model): listing it without
    # method_kwargs must fail loudly at construction, not silently misconfigure.
    from sirin.detection.processors.uncertainty import (
        SequenceUncertaintyFeatureProcessor,
    )

    processor = object.__new__(SequenceUncertaintyFeatureProcessor)
    processor.config = MagicMock()
    processor.config.uncertainty_methods = ['Focus']
    processor.config.method_kwargs = {}

    with pytest.raises(TypeError):
        processor._initialize_uncertainty_methods()
