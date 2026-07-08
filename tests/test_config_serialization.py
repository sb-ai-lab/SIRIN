"""Tests for config serialization and legacy checkpoint loading."""

import joblib

from sirin.models.detection import CompressionConfig, ProbingDetectorConfig
from sirin.utils.config_serialization import deserialize_probing_detector_config


def test_legacy_keys_dropped(tmp_path):
    fixture_path = tmp_path / 'config.joblib'
    joblib.dump(
        {
            'model_name': 'default_detector',
            'threshold': 0.5,
            'compression': {
                **CompressionConfig().__dict__,
                'n_components': 64,
                'auto_compress_threshold': 128,
            },
        },
        fixture_path,
    )

    config_dict = joblib.load(fixture_path)
    config, threshold = deserialize_probing_detector_config(config_dict.copy())
    assert isinstance(config, ProbingDetectorConfig)
    assert threshold == 0.5
