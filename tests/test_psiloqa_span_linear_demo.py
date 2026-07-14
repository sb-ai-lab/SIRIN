import hashlib
import json

import joblib
import numpy as np
import torch
from datasets import load_from_disk

from demo.train_psiloqa_span_linear import (
    character_scores,
    CHECKPOINT_DIR,
    DATASET_PATH,
    f1_optimal_threshold,
    MODEL_REVISION,
    prompt_disjoint_indices,
    span_labels,
    token_labels,
)


def test_span_and_token_labels_use_half_open_offsets():
    assert span_labels(8, [[2, 5]]).tolist() == [0, 0, 1, 1, 1, 0, 0, 0]
    assert token_labels([(0, 2), (2, 4), (4, 7)], [[2, 5]]).tolist() == [0, 1, 1]


def test_character_scores_require_exact_full_answer_coverage():
    scores = character_scores("hello", [(0, 2), (2, 5)], [0.1, 0.9])
    np.testing.assert_allclose(scores, [0.1, 0.1, 0.9, 0.9, 0.9])

    with np.testing.assert_raises_regex(ValueError, "uncovered characters"):
        character_scores("hello", [(0, 2), (3, 5)], [0.1, 0.9])


def test_f1_threshold_is_selected_from_continuous_validation_scores():
    labels = np.array([0, 0, 1, 1], dtype=np.uint8)
    scores = np.array([0.1, 0.2, 0.8, 0.9])
    threshold = f1_optimal_threshold(labels, scores)
    assert 0.2 < threshold <= 0.8
    assert ((scores >= threshold) == labels).all()


def test_real_demo_split_is_exact_and_prompt_disjoint():
    dataset = load_from_disk(str(DATASET_PATH))
    train, validation, test = prompt_disjoint_indices(dataset)
    assert (len(train), len(validation), len(test)) == (2676, 298, 1098)


def test_live_checkpoint_payload_is_complete_and_self_consistent():
    manifest = json.loads((CHECKPOINT_DIR / "manifest.json").read_text())
    assert manifest["model_revision"] == MODEL_REVISION
    assert manifest["use_chat_template"] is False
    assert manifest["threshold_method"] == "validation_f1_optimal"

    expected = {}
    for line in (CHECKPOINT_DIR / "SHA256SUMS").read_text().splitlines():
        digest, filename = line.split("  ", 1)
        expected[filename] = digest
    assert set(expected) == {
        "compressor_config.joblib",
        "compressor_scaler_0.joblib",
        "config.joblib",
        "manifest.json",
        "metrics.json",
        "model.pt",
        "provenance.json",
    }
    for filename, digest in expected.items():
        assert hashlib.sha256((CHECKPOINT_DIR / filename).read_bytes()).hexdigest() == digest

    state = torch.load(CHECKPOINT_DIR / "model.pt", map_location="cpu", weights_only=False)
    assert state["model_state_dict"]["weight"].shape == (1, 2560)
    assert state["model_state_dict"]["bias"].shape == (1,)
    config = joblib.load(CHECKPOINT_DIR / "config.joblib")
    assert config["threshold"] == manifest["threshold"]
    assert config["embedding_dim"] == [2560]
