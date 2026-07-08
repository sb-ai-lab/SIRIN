"""Attention / token explorer — per-token signals read from the offline feature cache.

The live demo can't produce per-token attention (presets run sdpa; LookbackLens pools the token
axis away), so this view reads the cached ``lookback_*.pkl`` / ``hidden_*.pkl`` a feature-cache run
left on disk and renders, per token of the generated answer:

* **LookbackLens attention** — the attention-to-context ratio per layer (head-mean). Low ratio =>
  the model looked away from its context => more likely hallucinated (rendered as high risk).
* **Hidden-state (proxy)** — per-token hidden-state L2 norm. A magnitude proxy, NOT a calibrated
  hallucination score (a real per-token probe would need per-token labels the cache doesn't carry).

Pure helpers (hashing, slicing, head-mean, normalize) are ``st``-free so they can be unit-tested
against a tiny synthetic pkl — see tests/test_ui_attention.py.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from sirin.ui.visualizers import _badge, _html, _tint, token_strip

# Fixture defaults (LongMemEval / Qwen3.5-35B-A3B). Data is NOT committed — these are just the
# out-of-the-box paths for local runs; override them in the sidebar for any other cache dir.
_FIXTURE_ROOT = (
    '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/pure_simplemem_qwen35_35b_a3b/'
    '20260703_120500_qwen35_35b_a3b_s_full_combined_500'
)
DEFAULT_PARQUET = f'{_FIXTURE_ROOT}/sirin_datasets/dataset/trustmem_dataset.parquet'
DEFAULT_CACHE_DIR = (
    f'{_FIXTURE_ROOT}/sirin_datasets/parallel/hall_full/feature_cache/feature_cache/'
    'Qwen/Qwen3.5-35B-A3B'
)

_HALLUCINATED = '#ff6b9a'  # matches PALETTE['risk']; token_strip's default hue anyway.


# --- pure helpers (testable) -------------------------------------------------

def sample_hash(prompt_user: str, prompt_assistant: str) -> str:
    """md5[:12] of the chat sample, matching LayerFeatureCacheSaver.get_sample_hash (saver.py).
    Reimplemented here so the UI never has to import the (torch-heavy) processors package."""
    sample = [
        {'role': 'user', 'content': prompt_user},
        {'role': 'assistant', 'content': prompt_assistant},
    ]
    return hashlib.md5(json.dumps(sample, sort_keys=True).encode()).hexdigest()[:12]


def _hall_label(labels_json: Any) -> int | None:
    try:
        return int(json.loads(labels_json)['hallucination_strict'])
    except (TypeError, ValueError, KeyError):
        return None


def available_hashes(cache_dir: str, feature_type: str = 'lookback') -> set[str]:
    prefix = f'{feature_type}_'
    return {
        p.name.split('_layer_')[0].removeprefix(prefix)  # robust: hash is between prefix and _layer_
        for p in Path(cache_dir).glob(f'{feature_type}_*_layer_*.pkl')
    }


def layers_for(cache_dir: str, sample: str, feature_type: str = 'lookback') -> list[int]:
    """Layer indices present on disk for one sample (avoids needing .lookback_layers.json)."""
    layers = sorted(
        int(p.stem.rsplit('_layer_', 1)[1])
        for p in Path(cache_dir).glob(f'{feature_type}_{sample}_layer_*.pkl')
    )
    return layers


def load_feature(cache_dir: str, feature_type: str, sample: str, layer: int) -> dict[str, Any]:
    """Load one cached layer pkl (joblib, NOT pickle) -> {features, answer_start, layer_idx}."""
    obj = joblib.load(Path(cache_dir) / f'{feature_type}_{sample}_layer_{layer}.pkl')
    locations = obj.get('locations') or {}
    return {
        'features': np.asarray(obj['features'], dtype=float),
        'answer_start': int(locations.get('answer_start', 0)),
        'layer_idx': obj.get('layer_idx', layer),
    }


def answer_span(features: np.ndarray, answer_start: int) -> np.ndarray:
    """Rows from answer_start on (context rows are zero-filled for lookback)."""
    return np.asarray(features, dtype=float)[int(answer_start):]


def lookback_token_scores(features: np.ndarray, answer_start: int) -> np.ndarray:
    """Head-mean attention-to-context ratio, one value per answer token."""
    ans = answer_span(features, answer_start)
    return ans.mean(axis=1) if ans.size else np.array([])


def hidden_token_norms(features: np.ndarray, answer_start: int) -> np.ndarray:
    ans = answer_span(features, answer_start)
    return np.linalg.norm(ans, axis=1) if ans.size else np.array([])


def normalize01(arr: np.ndarray) -> np.ndarray:
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return a
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-9:
        return np.full_like(a, 0.5)
    return (a - lo) / (hi - lo)


def _valid_span(feat: dict[str, Any]) -> bool:
    """A usable generated-token span: answer_start strictly inside the sequence (0 is suspicious —
    these samples always have context — and out-of-range means missing/bad metadata)."""
    return 0 < feat['answer_start'] < len(feat['features'])


def build_index(parquet_path: str, cache_dir: str) -> list[dict[str, Any]]:
    """Dataset rows that have a matching lookback cache, newest-schema columns only."""
    df = pd.read_parquet(
        parquet_path,
        columns=['question', 'prediction', 'labels', 'prompt_user', 'prompt_assistant', 'sample_id'],
    )
    have = available_hashes(cache_dir, 'lookback')
    rows = []
    for r in df.to_dict('records'):
        digest = sample_hash(r['prompt_user'], r['prompt_assistant'])
        if digest not in have:
            continue
        rows.append({
            'hash': digest,
            'question': str(r['question']),
            'prediction': str(r['prediction']),
            'label': _hall_label(r['labels']),
            'sample_id': str(r['sample_id']),
        })
    return rows


# --- token labels (best-effort; positional by default) -----------------------

def _token_cells(prediction: str, n_tokens: int, tokenizer_name: str = '') -> list[str]:
    if tokenizer_name:
        pieces = _try_tokenize(tokenizer_name, prediction, n_tokens)
        if pieces is not None:
            return pieces
    return [str(i) for i in range(n_tokens)]  # ponytail: positional cells; answer text shown below


def _try_tokenize(name: str, text: str, n_tokens: int) -> list[str] | None:
    # Opt-in only: the 35B tokenizer often isn't local and qwen3_5 needs transformers>=5
    # (conflicts with this env), so this usually can't run — hence the safe positional default.
    try:
        tok = _load_tokenizer(name)
        ids = tok(text, add_special_tokens=False)['input_ids']
        pieces = tok.convert_ids_to_tokens(ids)
    except Exception:  # noqa: BLE001 - any load/tokenize failure => fall back to positional
        return None
    if len(pieces) != n_tokens:  # only trust an exact match to the cached answer-token count
        return None
    return [p.replace('Ġ', ' ').replace('▁', ' ') for p in pieces]


def _load_tokenizer(name: str):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(name)


# --- rendering ---------------------------------------------------------------

def _heads_grid(ans: np.ndarray, cells: list[str]) -> str:
    """Compact tokens x heads matrix (heads as rows), tinted by inverted, matrix-normalized ratio."""
    norm = normalize01(ans)  # over the whole (tokens, heads) matrix
    n_tokens, n_heads = ans.shape
    header = ''.join(
        f'<td style="font-size:0.58rem;color:var(--sirin-faint);padding:1px 3px;text-align:center;">{c}</td>'
        for c in cells
    )
    rows = [f'<tr><td style="font-size:0.58rem;color:var(--sirin-faint);">h\\t</td>{header}</tr>']
    for h in range(n_heads):
        tds = ''.join(
            f'<td title="{ans[t, h]:.3f}" style="background:{_tint(_HALLUCINATED, 0.08 + (1.0 - norm[t, h]) * 0.8)};'
            'width:1.05rem;height:1.05rem;"></td>'
            for t in range(n_tokens)
        )
        rows.append(
            f'<tr><td style="font-size:0.58rem;color:var(--sirin-faint);padding:1px 4px;">H{h}</td>{tds}</tr>'
        )
    return '<table style="border-collapse:collapse;">' + ''.join(rows) + '</table>'


def _legend(st: Any) -> None:
    swatch = 'display:inline-block;width:0.9rem;height:0.9rem;border-radius:4px;vertical-align:-0.12rem;'
    _html(
        st,
        '<div style="font-size:0.8rem;color:var(--sirin-muted);margin:0.2rem 0 0.4rem;">'
        f'<span style="{swatch}background:{_tint(_HALLUCINATED, 0.12)};'
        f'border:1px solid {_tint(_HALLUCINATED, 0.3)};"></span> low risk&nbsp;&nbsp;'
        f'<span style="{swatch}background:{_tint(_HALLUCINATED, 0.85)};"></span> high risk'
        '&nbsp;&nbsp;<span style="opacity:0.8;">(hover a cell for its value)</span></div>',
    )


def _render_lookback(st: Any, cache_dir: str, row: dict[str, Any], tokenizer_name: str) -> None:
    layers = layers_for(cache_dir, row['hash'], 'lookback')
    if not layers:
        st.info('No lookback cache for this sample.')
        return
    per_layer = {L: load_feature(cache_dir, 'lookback', row['hash'], L) for L in layers}
    first = per_layer[layers[0]]
    if not _valid_span(first):
        st.info('No valid answer span (answer_start missing or out of range).')
        return
    n_tokens = len(answer_span(first['features'], first['answer_start']))
    cells = _token_cells(row['prediction'], n_tokens, tokenizer_name)

    st.caption(
        'Attention-to-context ratio per answer token (head-averaged), **coloured relative to this '
        'answer/layer** — low ratio → high risk. Hover a cell for its raw ratio.'
    )
    _legend(st)
    for L in layers:
        feat = per_layer[L]
        raw = lookback_token_scores(feat['features'], feat['answer_start'])
        titles = [f'ratio {v:.4f}' for v in raw]
        st.markdown(
            f'**Layer {L}** · raw {float(raw.min()):.4f}–{float(raw.max()):.4f} '
            f'(mean {float(raw.mean()):.4f})'
        )
        _html(st, token_strip(cells, list(normalize01(raw)), invert=True, titles=titles))

    with st.expander(f'Per-head heatmap (layer {layers[len(layers) // 2]})'):
        mid = per_layer[layers[len(layers) // 2]]
        _html(st, _heads_grid(answer_span(mid['features'], mid['answer_start']), cells))


def _render_hidden(st: Any, cache_dir: str, row: dict[str, Any], tokenizer_name: str) -> None:
    layers = layers_for(cache_dir, row['hash'], 'hidden')
    if not layers:
        st.info('No hidden-state cache for this sample.')
        return
    layer = st.selectbox('Hidden layer', layers, key='explorer_hidden_layer')
    feat = load_feature(cache_dir, 'hidden', row['hash'], layer)
    if not _valid_span(feat):
        st.info('No valid answer span (answer_start missing or out of range).')
        return
    norms = hidden_token_norms(feat['features'], feat['answer_start'])
    cells = _token_cells(row['prediction'], len(norms), tokenizer_name)
    titles = [f'norm {float(v):.1f}' for v in norms]
    st.caption(
        ':warning: **Proxy** — per-token hidden-state L2 norm (activation magnitude), NOT a '
        'calibrated hallucination score. Coloured relative to this answer.'
    )
    _legend(st)
    _html(st, token_strip(cells, list(normalize01(norms)), titles=titles))


def render(st: Any) -> None:
    """Sidebar data controls + main-area per-token visualizers. Called from main() in Explorer view."""
    with st.sidebar:
        st.header(':material/dataset: Explorer data')
        cache_dir = st.text_input('Feature cache dir', value=DEFAULT_CACHE_DIR)
        parquet_path = st.text_input('Dataset parquet', value=DEFAULT_PARQUET)
        tokenizer_name = st.text_input(
            'Tokenizer (optional)', value='',
            help='HF name/path to label cells with real tokens; blank = positional indices.',
        )

    st.subheader('Attention explorer')
    st.caption('Per-token signals read from the offline feature cache (LookbackLens attention + hidden proxy).')

    try:
        rows = _index_cached(parquet_path, cache_dir)
    except Exception as error:  # noqa: BLE001 - bad path / unreadable parquet -> friendly message
        st.error(f'Could not load dataset/cache: {error}')
        return
    if not rows:
        st.warning('No cached samples found for this dataset + cache dir. Check the paths.')
        return

    st.caption(f'{len(rows)} cached samples.')
    index = st.selectbox(
        'Sample',
        range(len(rows)),
        format_func=lambda i: (
            f"{'⚠ ' if rows[i]['label'] == 1 else ''}{rows[i]['question'][:70]}"
        ),
    )
    row = rows[index]

    label = row['label']
    ground_truth = _badge(label) if label is not None else '<span>label n/a</span>'
    _html(
        st,
        '<div style="display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;margin:0.3rem 0 0.5rem;">'
        '<span style="font-size:0.75rem;color:var(--sirin-muted);text-transform:uppercase;'
        'letter-spacing:0.06em;">ground truth</span>'
        f'{ground_truth}</div>',
    )
    with st.expander('Answer text', expanded=True):
        st.markdown(row['prediction'])

    tab_lb, tab_hidden = st.tabs(['LookbackLens attention', 'Hidden-state (proxy)'])
    with tab_lb:
        _render_lookback(st, cache_dir, row, tokenizer_name)
    with tab_hidden:
        _render_hidden(st, cache_dir, row, tokenizer_name)


def _cache_data(func):
    try:
        import streamlit as st

        return st.cache_data(show_spinner='Indexing cached samples...')(func)
    except Exception:  # noqa: BLE001 - streamlit absent (tests) -> run uncached
        return func


_index_cached = _cache_data(build_index)
