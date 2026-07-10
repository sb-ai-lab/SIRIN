"""Pure-helper tests for the attention/token explorer — synthetic joblib pkls, no real fixture."""

import json

import joblib
import numpy as np
import pandas as pd

from sirin.ui import attention_explorer as ax
from sirin.ui.styles import PALETTE, risk_color, risk_ink
from sirin.ui.visualizers import layer_token_heatmap, token_strip


def test_sample_hash_deterministic_ordered():
    assert ax.sample_hash('ctx Q?', 'an answer') == ax.sample_hash('ctx Q?', 'an answer')
    assert len(ax.sample_hash('a', 'b')) == 12
    assert ax.sample_hash('a', 'b') != ax.sample_hash('b', 'a')  # list order matters


def test_hall_label():
    assert ax._hall_label(json.dumps({'hallucination_strict': 1})) == 1
    assert ax._hall_label(json.dumps({'hallucination_strict': 0})) == 0
    assert ax._hall_label(json.dumps({'other': 1})) is None
    assert ax._hall_label(None) is None


def test_lookback_headmean_skips_context_rows():
    feats = np.array([[0, 0], [0, 0], [0, 0], [0.2, 0.4], [0.6, 0.8]], dtype=float)
    assert ax.answer_span(feats, 3).shape == (2, 2)
    assert np.allclose(ax.lookback_token_scores(feats, 3), [0.3, 0.7])  # per-token head-mean


def test_hidden_token_norms():
    feats = np.array([[0, 0], [3, 4], [6, 8]], dtype=float)
    assert np.allclose(ax.hidden_token_norms(feats, 1), [5.0, 10.0])


def test_normalize01():
    assert np.allclose(ax.normalize01(np.array([1.0, 3.0, 5.0])), [0.0, 0.5, 1.0])
    assert np.allclose(ax.normalize01(np.array([2.0, 2.0])), [0.5, 0.5])  # constant -> mid
    assert ax.normalize01(np.array([])).size == 0


def test_empty_answer_span():
    feats = np.zeros((3, 2))
    assert ax.lookback_token_scores(feats, 3).size == 0
    assert ax.hidden_token_norms(feats, 3).size == 0


def test_token_strip_invert_direction():
    # invert=True: a LOW ratio must render as HIGH risk (shown intensity 1.0), and vice-versa.
    assert 'title="1.00"' in token_strip(['a'], [0.0], invert=True)
    assert 'title="0.00"' in token_strip(['a'], [1.0], invert=True)
    assert 'title="0.30"' in token_strip(['a'], [0.3], invert=False)


def test_build_index_and_load_roundtrip(tmp_path):
    cache = tmp_path / 'cache'
    cache.mkdir()
    prompt_user, answer = 'context Q?', 'the answer'
    digest = ax.sample_hash(prompt_user, answer)
    feats = np.zeros((5, 2))
    feats[3:] = [[0.2, 0.4], [0.6, 0.8]]
    for layer in (4, 5, 6):
        joblib.dump(
            {'layer_idx': layer, 'features': feats,
             'locations': {'answer_start': 3}, 'sample_hash': digest},
            cache / f'lookback_{digest}_layer_{layer}.pkl',
        )
    df = pd.DataFrame([
        {'question': 'Q1?', 'prediction': answer, 'labels': json.dumps({'hallucination_strict': 1}),
         'prompt_user': prompt_user, 'prompt_assistant': answer, 'sample_id': 'aaaa'},
        {'question': 'Q2?', 'prediction': 'x', 'labels': json.dumps({'hallucination_strict': 0}),
         'prompt_user': 'other', 'prompt_assistant': 'x', 'sample_id': 'bbbb'},
    ])
    parquet = tmp_path / 'd.parquet'
    df.to_parquet(parquet)

    rows = ax.build_index(str(parquet), str(cache))
    assert len(rows) == 1  # only the row whose sample is cached
    assert rows[0]['hash'] == digest and rows[0]['label'] == 1
    assert ax.layers_for(str(cache), digest, 'lookback') == [4, 5, 6]
    feat = ax.load_feature(str(cache), 'lookback', digest, 4)
    assert feat['answer_start'] == 3
    assert np.allclose(ax.lookback_token_scores(feat['features'], feat['answer_start']), [0.3, 0.7])


def test_valid_span():
    assert ax._valid_span({'answer_start': 3, 'features': np.zeros((5, 2))})
    assert not ax._valid_span({'answer_start': 0, 'features': np.zeros((5, 2))})   # 0 is suspicious
    assert not ax._valid_span({'answer_start': 5, 'features': np.zeros((5, 2))})   # out of range


def test_available_hashes_robust_parsing(tmp_path):
    for name in ('lookback_abcdef123456_layer_4.pkl', 'lookback_abcdef123456_layer_5.pkl',
                 'hidden_abcdef123456_layer_20.pkl'):
        (tmp_path / name).touch()
    assert ax.available_hashes(str(tmp_path), 'lookback') == {'abcdef123456'}
    assert ax.available_hashes(str(tmp_path), 'hidden') == {'abcdef123456'}


def test_token_strip_titles_and_missing_score():
    assert 'title="ratio 0.5"' in token_strip(['a'], [0.2], titles=['ratio 0.5'])
    # a cell with no matching score renders NEUTRAL (0.50), never max-risk under invert
    out = token_strip(['a', 'b'], [1.0], invert=True)
    assert 'title="0.00"' in out and 'title="0.50"' in out


def test_token_strip_makes_whitespace_tokens_visible():
    out = token_strip([' ', '\n', '\t', ' Admin'], [0.0, 0.5, 1.0, 0.2])

    assert '>space<' in out
    assert '>\\n<' in out
    assert '>tab<' in out
    assert ' Admin' in out


def test_heads_grid_escapes_token_labels():
    out = ax._heads_grid(np.ones((2, 1)), ['<img src=x onerror=alert(1)>', '&'])

    assert '<img' not in out
    assert '&lt;img' in out
    assert '&amp;' in out


def test_risk_color_endpoints():
    assert risk_color(0.0) == PALETTE['ok']
    assert risk_color(1.0) == PALETTE['risk']


def test_risk_color_is_monotonic_ish():
    assert risk_color(0.0) != risk_color(1.0)


def test_risk_ink_returns_valid_hex():
    ink = risk_ink(risk_color(0.0))
    assert ink.startswith('#') and len(ink) == 7
    int(ink[1:], 16)  # a valid hex colour, doesn't raise


def test_layer_token_heatmap_shows_real_tokens_not_positions():
    raw = np.array([[0.2, 0.8], [0.3, 0.7]])
    shown = 1.0 - raw
    out = layer_token_heatmap([4, 5], ['Bus', 'Adm'], raw, shown)

    assert 'Bus' in out and 'Adm' in out
    assert '>0<' not in out  # not a positional-only header
    assert 'data-layer="4"' in out
    assert 'raw 0.2000' in out
    assert 'shown 0.8000' in out


def test_content_slice_wrapper():
    # the fixture's fixed wrapper: span == 7 (header + empty think) + answer_tokens + 2 (footer)
    assert ax._content_slice(25, 16) == slice(7, 23)
    assert ax._content_slice(11, 2) == slice(7, 9)
    assert ax._content_slice(10, 2) is None   # wrapper doesn't fit -> positional fallback
    assert ax._content_slice(9, 0) is None    # no answer tokens


def test_answer_cells_and_slice_positional_fallback():
    # no tokenizer name -> positional cells over the FULL span, identity slice
    cells, sl = ax._answer_cells_and_slice('the answer', '', 5)
    assert cells == ['0', '1', '2', '3', '4']
    assert sl == slice(0, 5)


def test_answer_cells_and_slice_uses_qwen_wrapper_without_tokenizer():
    cells, sl = ax._answer_cells_and_slice('Business Administration', '', 11)

    assert cells == ['Business', ' Administration']
    assert sl == slice(7, 9)


def test_marvel_demo_renders_publication_figure_with_provenance():
    class St:
        def __init__(self):
            self.rendered = []

        def html(self, body):
            self.rendered.append(body)

    st = St()

    ax.render_marvel_demo(st)

    page = '\n'.join(st.rendered)
    assert '[data-testid="stSidebar"]' in page
    assert 'Flagged: model answered &quot;One&quot;, evidence supports 2' in page
    assert 'Recorded generated output' in page
    assert 'P(contradiction | hidden states)' in page
    assert 'hidden states only; no gold answer or failure label' in page
    assert 'memory_id' in page
    assert 'sample_id' in page
    assert '681a1674' in page
    assert '99.8%' in page
    assert 'Flagged generated span' in page
