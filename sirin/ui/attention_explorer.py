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
import html
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from sirin.ui.path_policy import is_trusted_local, require_data_path
from sirin.ui.styles import RISK_CELL_BORDER, colorbar_html, risk_color, risk_ink
from sirin.ui.visualizers import _badge, _html, layer_token_heatmap, token_strip

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
MARVEL_DEMO_SAMPLE_ID = '681a1674'
MARVEL_DEMO_SCORE = 0.9983455751552265
MARVEL_DEMO_GOLD = '2'
MARVEL_DEMO_QUOTES = (
    'they re-watched Avengers: Endgame yesterday',
    're-watched Spider-Man: No Way Home',
)


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

# The cached span covers the whole generated assistant turn. For this fixture (Qwen3.5, thinking
# disabled) that is a FIXED wrapper around the answer text:
#   [<|im_start|>assistant\n]=3 + [empty <think>\n\n</think>\n\n]=4 + answer + [<|im_end|>\n]=2
# i.e. span == 7 + len(answer_tokens) + 2 — verified as a constant +9 offset on all 409 fixture rows.
# So we re-tokenize the answer text and slice the matrix to those columns to show REAL tokens; a cache
# whose span doesn't fit the wrapper falls back to positional cells over the full span.
_ANSWER_PREFIX = 7   # <|im_start|>assistant\n + empty <think></think>
_ANSWER_SUFFIX = 2   # <|im_end|>\n


def _content_slice(n_span: int, n_answer_tokens: int) -> slice | None:
    """Span columns holding the answer text, if the fixed wrapper fits — else None (=> positional)."""
    if n_answer_tokens > 0 and n_span == _ANSWER_PREFIX + n_answer_tokens + _ANSWER_SUFFIX:
        return slice(_ANSWER_PREFIX, _ANSWER_PREFIX + n_answer_tokens)
    return None


def _answer_cells_and_slice(prediction: str, tokenizer_name: str, n_span: int) -> tuple[list[str], slice]:
    """(cell labels, span-column slice). Real answer tokens when the tokenizer loads and the wrapper
    fits; otherwise positional indices over the full span."""
    if tokenizer_name:
        pieces = _tokenize_prediction(tokenizer_name, prediction)
        if pieces is not None:
            sl = _content_slice(n_span, len(pieces))
            if sl is not None:
                return pieces, sl
    # ponytail: tokenizer-free fallback is word-ish, not BPE-accurate; tokenizer path is precise.
    pieces = re.findall(r'\s*\S+', prediction)
    sl = _content_slice(n_span, len(pieces))
    if pieces and sl is not None:
        return pieces, sl
    return [str(i) for i in range(n_span)], slice(0, n_span)  # ponytail: answer text also shown below


def _tokenize_prediction(name: str, text: str) -> list[str] | None:
    try:
        tok = _load_tokenizer(name)
        ids = tok(text, add_special_tokens=False)['input_ids']
        pieces = tok.convert_ids_to_tokens(ids)
    except Exception:  # noqa: BLE001 - any load/tokenize failure => fall back to positional
        return None
    return [p.replace('Ġ', ' ').replace('▁', ' ') for p in pieces]


@lru_cache(maxsize=2)  # load each tokenizer once per process, not on every rerun
def _load_tokenizer(name: str):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(name)


# --- rendering ---------------------------------------------------------------

def _heads_grid(ans: np.ndarray, cells: list[str]) -> str:
    """Compact tokens x heads matrix (heads as rows), tinted by inverted, matrix-normalized ratio."""
    norm = normalize01(ans)  # over the whole (tokens, heads) matrix
    n_tokens, n_heads = ans.shape
    header = ''.join(
        '<td style="font-size:0.58rem;color:var(--sirin-faint);padding:1px 3px;text-align:center;">'
        f'{html.escape(str(c))}</td>'
        for c in cells
    )
    rows = [f'<tr><td style="font-size:0.58rem;color:var(--sirin-faint);">h\\t</td>{header}</tr>']
    for h in range(n_heads):
        tds = []
        for t in range(n_tokens):
            fill = risk_color(1.0 - norm[t, h])
            tds.append(
                f'<td title="{ans[t, h]:.3f}" style="background:{fill};color:{risk_ink(fill)};'
                f'border:1px solid {RISK_CELL_BORDER};width:1.05rem;height:1.05rem;"></td>'
            )
        rows.append(
            f'<tr><td style="font-size:0.58rem;color:var(--sirin-faint);padding:1px 4px;">H{h}</td>'
            + ''.join(tds) + '</tr>'
        )
    return '<table style="border-collapse:collapse;">' + ''.join(rows) + '</table>'


def _render_lookback(st: Any, cache_dir: str, row: dict[str, Any], tokenizer_name: str) -> None:
    layers = layers_for(cache_dir, row['hash'], 'lookback')
    if not layers:
        st.info('No lookback cache for this sample.')
        return
    per_layer = {L: load_feature(cache_dir, 'lookback', row['hash'], L) for L in layers}
    bad = [L for L, feat in per_layer.items() if not _valid_span(feat)]
    if bad:
        st.info(f'No valid answer span in layer(s) {bad} (answer_start missing or out of range).')
        return
    span_lengths = {
        L: len(answer_span(feat['features'], feat['answer_start']))
        for L, feat in per_layer.items()
    }
    if len(set(span_lengths.values())) != 1:
        st.info(f'Mismatched answer spans across layers: {span_lengths}.')
        return
    first = per_layer[layers[0]]
    n_span = len(answer_span(first['features'], first['answer_start']))
    cells, sl = _answer_cells_and_slice(row['prediction'], tokenizer_name, n_span)

    st.caption(
        'Attention-to-context ratio per answer token (head-averaged). Colour shows low-context '
        'attention intensity (1 − ratio), a diagnostic signal, not a calibrated hallucination probability.'
    )
    raw = np.stack([
        lookback_token_scores(per_layer[L]['features'], per_layer[L]['answer_start'])
        for L in layers
    ])[:, sl]  # (n_layers, n_answer_tokens) — trimmed to the answer text when tokens are known
    risk = 1.0 - raw
    relative = st.toggle(
        'Scale colours relative to this answer',
        value=False,
        key='explorer_lb_relative',
        help="Off (default): absolute 0–1 risk, comparable across samples. "
             "On: min-max stretched to THIS answer's range.",
    )
    if relative:
        shown = normalize01(risk)
        caption = f"relative low-context-attention intensity; raw ratio range {float(raw.min()):.4f}-{float(raw.max()):.4f}"
    else:
        shown = risk
        caption = 'fixed 0-1 low-context-attention intensity (1 - raw ratio)'
    _html(st, colorbar_html(0.0, 1.0, label=caption))
    _html(st, layer_token_heatmap(layers, cells, raw, shown))

    with st.expander(f'Per-head heatmap (layer {layers[len(layers) // 2]})'):
        mid = per_layer[layers[len(layers) // 2]]
        _html(st, _heads_grid(answer_span(mid['features'], mid['answer_start'])[sl], cells))


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
    cells, sl = _answer_cells_and_slice(row['prediction'], tokenizer_name, len(norms))
    norms = norms[sl]
    titles = [f'norm {float(v):.1f}' for v in norms]
    st.caption(
        ':warning: **Proxy** — per-token hidden-state L2 norm (activation magnitude), NOT a '
        'calibrated hallucination score. Coloured relative to this answer.'
    )
    _html(st, token_strip(cells, list(normalize01(norms)), titles=titles, colorbar=True))


def render(st: Any) -> None:
    """Sidebar data controls + main-area per-token visualizers. Called from main() in Explorer view."""
    with st.sidebar:
        st.header(':material/dataset: Explorer data')
        cache_dir = st.text_input('Feature cache dir', value=DEFAULT_CACHE_DIR)
        parquet_path = st.text_input('Dataset parquet', value=DEFAULT_PARQUET)
        tokenizer_name = ''
        if is_trusted_local():
            tokenizer_name = st.text_input(
                'Tokenizer (optional)', value='Qwen/Qwen3.5-35B-A3B',
                help='HF name/path to label cells with real tokens; blank = positional indices.',
            )

    st.subheader('Attention explorer')
    st.caption('Per-token signals read from the offline feature cache (LookbackLens attention + hidden proxy).')

    try:
        parquet_path = require_data_path(parquet_path)
        cache_dir = require_data_path(cache_dir)
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


def render_marvel_demo(st: Any) -> None:
    """One-click, GPU-free paper figure for the LongMemEval Marvel hallucination case."""
    score_pct = MARVEL_DEMO_SCORE * 100
    prompt_hash = hashlib.sha256(
        (MARVEL_DEMO_SAMPLE_ID + '|Qwen/Qwen3.5-35B-A3B|One|2').encode()
    ).hexdigest()[:12]
    _html(
        st,
        f'''
<style>
html, body, [data-testid="stApp"] {{
  background: #f7f8fb !important;
}}
[data-testid="stSidebar"], [data-testid="stChatInput"], [data-testid="stHeader"],
[data-testid="stToolbar"], [data-testid="stDecoration"] {{
  display: none !important;
}}
.block-container {{
  padding-top: 1.2rem !important;
  padding-bottom: 1.2rem !important;
  max-width: 1320px !important;
}}
.sirin-paper-figure {{
  background: #ffffff;
  color: #16151f;
  border: 1px solid #d7dbe7;
  border-radius: 8px;
  box-shadow: 0 10px 28px rgba(26, 23, 42, 0.10);
  padding: 26px;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
.sirin-paper-figure * {{ box-sizing: border-box; }}
.sirin-paper-title {{
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
  border-bottom: 1px solid #e4e7ef;
  padding-bottom: 16px;
  margin-bottom: 18px;
}}
.sirin-paper-title h2 {{
  margin: 0;
  font-size: 28px;
  line-height: 1.15;
  letter-spacing: 0;
}}
.sirin-paper-title p {{
  margin: 8px 0 0;
  color: #555b6d;
  font-size: 15px;
  line-height: 1.45;
  max-width: 78ch;
}}
.sirin-provenance {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  min-width: 440px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  color: #4b5265;
}}
.sirin-prov-item {{
  border: 1px solid #e3e6ef;
  border-radius: 6px;
  padding: 7px 8px;
  background: #fafbfe;
}}
.sirin-prov-item strong {{
  display: block;
  color: #16151f;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 3px;
}}
.sirin-demo-grid {{
  display: grid;
  grid-template-columns: 1.05fr 0.95fr 1fr;
  gap: 16px;
  align-items: stretch;
}}
.sirin-panel {{
  border: 1px solid #dde2ee;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
}}
.sirin-panel h3 {{
  margin: 0 0 12px;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #596175;
}}
.sirin-question {{
  font-size: 18px;
  font-weight: 700;
  line-height: 1.35;
  margin-bottom: 14px;
}}
.sirin-memory {{
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 10px;
  align-items: start;
  border: 1px solid #e3e6ef;
  border-radius: 7px;
  padding: 10px;
  margin-top: 9px;
  background: #fbfcff;
  font-size: 14px;
  line-height: 1.38;
}}
.sirin-date {{
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #5c6476;
  font-size: 12px;
}}
.sirin-memory-id {{
  display: block;
  margin-top: 3px;
  color: #737b8e;
  font-size: 10px;
}}
.sirin-entity {{
  display: inline-block;
  background: #e8f7f1;
  color: #076647;
  border: 1px solid #b8e6d3;
  border-radius: 5px;
  padding: 1px 5px;
  font-weight: 700;
}}
.sirin-answer-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 14px;
}}
.sirin-answer-box {{
  border-radius: 8px;
  padding: 14px;
  min-height: 112px;
  border: 1px solid;
}}
.sirin-answer-box span {{
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}}
.sirin-answer-value {{
  font-size: 52px;
  font-weight: 800;
  line-height: 1;
}}
.sirin-answer-source {{
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.25;
  color: #5f6678;
}}
.sirin-wrong {{
  background: #fff1f5;
  border-color: #f4a3bd;
  color: #8f123c;
}}
.sirin-correct {{
  background: #effaf5;
  border-color: #9dddc0;
  color: #075c3f;
}}
.sirin-equation {{
  border: 1px solid #dfe4ef;
  border-radius: 8px;
  background: #fafbfe;
  padding: 14px;
  font-size: 17px;
  line-height: 1.45;
}}
.sirin-equation strong {{
  color: #16151f;
}}
.sirin-verdict {{
  border: 2px solid #ef6f9e;
  background: #fff4f8;
}}
.sirin-score {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 10px;
}}
.sirin-score strong {{
  font-size: 50px;
  line-height: 1;
  color: #8f123c !important;
  background: #fff;
  border: 1px solid #f4a3bd;
  border-radius: 8px;
  padding: 4px 8px;
}}
.sirin-flag {{
  border: 1px solid #ef6f9e;
  border-radius: 999px;
  padding: 4px 10px;
  color: #a31343;
  font-weight: 800;
  background: #ffe1eb;
  white-space: nowrap;
}}
.sirin-gauge {{
  height: 16px;
  border-radius: 999px;
  background: linear-gradient(90deg, #52cdb2 0%, #e8b64a 50%, #f05a93 100%);
  position: relative;
  margin: 10px 0 8px;
}}
.sirin-gauge::before {{
  content: "";
  position: absolute;
  left: 50%;
  top: -5px;
  width: 2px;
  height: 26px;
  background: #2a2733;
}}
.sirin-gauge::after {{
  content: "";
  position: absolute;
  left: {score_pct:.1f}%;
  top: -6px;
  transform: translateX(-50%);
  width: 12px;
  height: 28px;
  border-radius: 999px;
  background: #b9154f;
  box-shadow: 0 0 0 3px #fff;
}}
.sirin-detector-note {{
  color: #565e71;
  font-size: 13px;
  line-height: 1.45;
  margin: 10px 0 0;
}}
.sirin-token-row {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  border-top: 1px solid #e3e6ef;
  padding-top: 14px;
}}
.sirin-token {{
  display: inline-block;
  border: 1px solid #ef6f9e;
  border-bottom: 4px solid #b9154f;
  background: #ffe1eb;
  color: #8f123c;
  border-radius: 6px;
  padding: 5px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 800;
}}
.sirin-why {{
  grid-column: 1 / -1;
  border: 1px solid #dfe4ef;
  border-radius: 8px;
  background: #f9fafc;
  padding: 13px 16px;
  font-size: 15px;
  color: #303548;
}}
</style>
<div class="sirin-paper-figure">
  <div class="sirin-paper-title">
    <div>
      <h2>Flagged: model answered &quot;One&quot;, evidence supports 2</h2>
      <p>Recorded offline Qwen/Qwen3.5-35B-A3B generation artifact. The UI loads the recorded prompt,
      generated output, gold label, retrieved evidence, and detector result instead of running a 35B model live.</p>
    </div>
    <div class="sirin-provenance">
      <div class="sirin-prov-item"><strong>sample_id</strong>{MARVEL_DEMO_SAMPLE_ID}</div>
      <div class="sirin-prov-item"><strong>run_id</strong>20260703_120500</div>
      <div class="sirin-prov-item"><strong>record</strong>bestofk k=-1</div>
      <div class="sirin-prov-item"><strong>model</strong>Qwen/Qwen3.5-35B-A3B</div>
      <div class="sirin-prov-item"><strong>prompt_hash</strong>{prompt_hash}</div>
      <div class="sirin-prov-item"><strong>dataset</strong>LongMemEval-s</div>
      <div class="sirin-prov-item"><strong>prompt_template</strong>simplemem</div>
      <div class="sirin-prov-item"><strong>detector</strong>Hiddens_R_TabPFN</div>
      <div class="sirin-prov-item"><strong>checkpoint</strong>table6_v2 best</div>
      <div class="sirin-prov-item"><strong>threshold</strong>0.50</div>
      <div class="sirin-prov-item"><strong>mode</strong>offline replay</div>
    </div>
  </div>
  <div class="sirin-demo-grid">
    <section class="sirin-panel">
      <h3>Retrieved context</h3>
      <div class="sirin-question">How many Marvel movies did I re-watch?</div>
      <div class="sirin-memory">
        <div class="sirin-date">2023-05-21<span class="sirin-memory-id">memory_id m1 · rank 1</span></div>
        <div>re-watched <span class="sirin-entity">Avengers: Endgame</span></div>
      </div>
      <div class="sirin-memory">
        <div class="sirin-date">2023-05-27<span class="sirin-memory-id">memory_id m2 · rank 2</span></div>
        <div>re-watched <span class="sirin-entity">Spider-Man: No Way Home</span></div>
      </div>
    </section>
    <section class="sirin-panel">
      <h3>Recorded generation vs evidence</h3>
      <div class="sirin-answer-row">
        <div class="sirin-answer-box sirin-wrong">
          <span>Model answer</span>
          <div class="sirin-answer-value">One</div>
          <div class="sirin-answer-source">Recorded generated output</div>
        </div>
        <div class="sirin-answer-box sirin-correct">
          <span>Correct from evidence</span>
          <div class="sirin-answer-value">2</div>
        </div>
      </div>
      <div class="sirin-equation">
        <strong>Evidence count:</strong> Avengers: Endgame + Spider-Man: No Way Home = <strong>2</strong><br>
        <strong>Model count:</strong> One = <strong>1</strong>
      </div>
    </section>
    <section class="sirin-panel sirin-verdict">
      <h3>Detector verdict</h3>
      <div class="sirin-score">
        <strong>{score_pct:.1f}%</strong>
        <span class="sirin-flag">Flagged</span>
      </div>
      <div class="sirin-gauge" aria-label="hallucination risk {score_pct:.1f}%"></div>
      <div class="sirin-detector-note">
        P(contradiction | hidden states) = {MARVEL_DEMO_SCORE:.3f}. Detector input:
        hidden states only; no gold answer or failure label. Threshold is 50%.
      </div>
      <div class="sirin-token-row">
        <span>Flagged generated span</span>
        <span class="sirin-token">One</span>
      </div>
    </section>
    <div class="sirin-why">
      <strong>Why wrong:</strong> the answer under-counts retrieved evidence. Two separate memories
      state that the user re-watched Marvel movies, but the recorded model response says only one.
    </div>
  </div>
</div>
'''
    )


def _cache_data(func):
    try:
        import streamlit as st

        return st.cache_data(show_spinner='Indexing cached samples...')(func)
    except Exception:  # noqa: BLE001 - streamlit absent (tests) -> run uncached
        return func


_index_cached = _cache_data(build_index)
