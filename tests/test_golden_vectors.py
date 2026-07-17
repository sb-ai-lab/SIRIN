"""Golden fixture sanity checks."""

import importlib.util
import json
import os
from pathlib import Path

import pytest


BASELINE_PATH = Path(__file__).parent / 'fixtures' / 'golden' / 'baseline.json'


def _load_baseline():
    return json.loads(BASELINE_PATH.read_text())


def _load_capture_module():
    path = Path(__file__).parent / 'fixtures' / 'capture_golden.py'
    spec = importlib.util.spec_from_file_location('capture_golden', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_golden_vectors_match_baseline():
    baseline = _load_baseline()
    assert baseline['answerability_probs'] == pytest.approx([
        0.5556640625,
        0.5556640625,
    ])
    assert baseline['uncertainty_scores'] == pytest.approx({
        'MeanTokenEntropy': 10.82451057434082,
    })


@pytest.mark.integration
def test_current_answerability_matches_golden_vectors():
    if not os.getenv('SIRIN_ANSWERABILITY_CKPT'):
        pytest.skip("Set SIRIN_ANSWERABILITY_CKPT to run answerability golden vectors")

    baseline = _load_baseline()
    actual = _load_capture_module().capture_answerability_probs()
    assert actual == pytest.approx(baseline['answerability_probs'])


@pytest.mark.integration
def test_current_uncertainty_matches_golden_vectors():
    baseline = _load_baseline()
    actual = _load_capture_module().capture_uncertainty_scores()
    if actual is None:
        pytest.skip("CUDA unavailable for uncertainty golden vectors")

    assert actual == pytest.approx(baseline['uncertainty_scores'])
