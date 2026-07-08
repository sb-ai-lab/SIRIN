"""Tests for TabPFN checkpoint compatibility helpers."""

import sys

import numpy as np
import pytest

import sirin.detection.probing.detectors.utils.tabpfn_compat  # noqa: F401  (registers stubs)
from sirin.detection.probing.detectors.utils.tabpfn_compat import (
    _filter_tabpfn_init_params,
)


def test_filter_tabpfn_init_params_drops_legacy_keys():
    class Estimator:
        def __init__(self, keep=None):
            pass

    assert _filter_tabpfn_init_params(
        Estimator,
        {'keep': 1, 'eval_metric': 'auc'},
    ) == {'keep': 1}


def test_squashing_scaler_stub_fails_loudly_instead_of_clipping():
    mod = sys.modules.get('tabpfn.preprocessing.steps.squashing_scaler_transformer')
    if mod is None or hasattr(mod, '__file__'):
        pytest.skip('real tabpfn SquashingScaler present; clip-only stub not active')
    scaler = mod.SquashingScaler()
    with pytest.raises(RuntimeError):
        scaler.transform(np.zeros((2, 2), dtype=float))
