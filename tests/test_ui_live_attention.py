"""Pure-helper tests for the live LookbackLens attention view — no model, no GPU, no streamlit."""

import numpy as np
import torch

from sirin.ui import live_attention as la


def test_full_attention_layers_picks_the_fourth_of_every_block():
    layer_types = (['linear_attention'] * 3 + ['full_attention']) * 8
    assert la.full_attention_layers(layer_types) == [3, 7, 11, 15, 19, 23, 27, 31]
    assert all(i % 4 == 3 for i in la.full_attention_layers(layer_types))


def test_full_attention_layers_empty_and_mixed():
    assert la.full_attention_layers([]) == []
    assert la.full_attention_layers(['full_attention', 'linear_attention', 'full_attention']) == [0, 2]


def _tiny_attn() -> torch.Tensor:
    """(H=2, S=5) attention. With context_len=3 the answer tokens are query rows 3 and 4.
    Head 0 is built for the two boundary cases; head 1 is a hand-computable mix."""
    attn = torch.zeros((2, 5, 5), dtype=torch.float32)
    attn[0, 3] = torch.tensor([1.0, 1.0, 1.0, 0.0, 0.0])  # all context, no new -> ratio 1 (low risk)
    attn[0, 4] = torch.tensor([0.0, 0.0, 0.0, 1.0, 1.0])  # no context, all new -> ratio 0 (high risk)
    attn[1, 3] = torch.tensor([0.2, 0.4, 0.6, 0.8, 0.0])  # ctx=0.4, new=0.8    -> 0.4/1.2
    attn[1, 4] = torch.tensor([0.6, 0.6, 0.6, 0.2, 0.2])  # ctx=0.6, new=0.2    -> 0.6/0.8
    return attn


def test_layer_lookback_ratio_matches_hand_computation():
    ratio = la.layer_lookback_ratio(_tiny_attn(), context_len=3, token_len=5)
    assert ratio.shape == (2, 2)  # (n_answer_tokens, H)
    expected = torch.tensor([[1.0, 0.4 / 1.2], [0.0, 0.6 / 0.8]])
    assert torch.allclose(ratio, expected, atol=1e-6)


def test_layer_lookback_ratio_boundary_semantics():
    ratio = la.layer_lookback_ratio(_tiny_attn(), 3, 5)
    assert torch.allclose(ratio[0, 0], torch.tensor(1.0), atol=1e-6)  # new≈0     -> ratio 1 (low risk)
    assert torch.allclose(ratio[1, 0], torch.tensor(0.0), atol=1e-6)  # context≈0 -> ratio 0 (high risk)


def test_lookback_layer_token_matrix_shape_and_headmean():
    attn = _tiny_attn()
    mat = la.lookback_layer_token_matrix([attn, attn, attn], 3, 5)
    assert mat.shape == (3, 2)  # (n_layers=3, n_answer_tokens=2)
    per_layer = la.layer_lookback_ratio(attn, 3, 5).mean(dim=1).numpy()
    for row in mat:
        assert np.allclose(row, per_layer)


def test_clean_token_labels_replaces_bpe_sentinels():
    assert la.clean_token_labels(['ĠBusiness', 'Admin']) == [' Business', 'Admin']
    assert la.clean_token_labels(['a▁b', 'lineĊnext']) == ['a b', 'line\nnext']
