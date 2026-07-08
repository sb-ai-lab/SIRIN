"""Tests for TabPFN checkpoint compatibility helpers."""

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
