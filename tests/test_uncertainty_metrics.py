"""Tests for uncertainty detector classification-metrics config wiring."""

from types import SimpleNamespace

from sirin.definitions import BASIC_METRICS, ClassificationMetric
from sirin.detection.uncertainty.detectors import UncertaintyDetectorBase


def test_defaults_to_basic_metrics_when_unset():
    fake = SimpleNamespace(config=SimpleNamespace(classification_metrics=None))
    assert (
        UncertaintyDetectorBase._get_classification_metrics_config(fake) == BASIC_METRICS
    )


def test_honors_configured_classification_metrics():
    custom = [ClassificationMetric.ROC_AUC]
    fake = SimpleNamespace(config=SimpleNamespace(classification_metrics=custom))
    assert UncertaintyDetectorBase._get_classification_metrics_config(fake) == custom


def test_explicit_empty_list_is_preserved():
    # metrics=[] means "compute nothing" — must not fall back to defaults
    fake = SimpleNamespace(config=SimpleNamespace(classification_metrics=[]))
    assert UncertaintyDetectorBase._get_classification_metrics_config(fake) == []
