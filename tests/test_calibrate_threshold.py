"""Tests for calibrate_threshold."""

import numpy as np

from sirin.detection.utils.basic import calibrate_threshold


def test_calibrate_threshold_fixed():
    probs = np.array([0.1, 0.5, 0.9])
    labels = np.array([0, 0, 1])
    threshold = calibrate_threshold(probs, labels, method='fixed', fixed_threshold=0.5)
    assert threshold == 0.5
