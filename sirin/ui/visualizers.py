from __future__ import annotations

import math
import html
import re
from typing import Any

import numpy as np

from sirin.ui.styles import PALETTE, RISK_CELL_BORDER, colorbar_html, risk_color, risk_ink

try:
    from sirin.ui.streamlit_app import score_heatmap
except ImportError:
    from loguru import logger as lg
    lg.warning("score_heatmap unavailable — heatmap visualizations disabled")
    score_heatmap = None

# Shared numeric style — mono + tabular so scores line up.
_MONO = 'font-family:var(--sirin-mono);font-variant-numeric:tabular-nums;'


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _clamp01(value: float | None) -> float:
    return min(1.0, max(0.0, value if value is not None else 0.0))


def _pred_bool(pred: Any) -> bool | None:
    if isinstance(pred, bool):
        return pred
    if pred in (0, 0.0, '0', 'false', 'False'):
        return False
    if pred in (1, 1.0, '1', 'true', 'True'):
        return True
    return None


def _tint(hex_color: str, alpha: float) -> str:
    """rgba() string from a '#rrggbb' palette colour."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _badge(pred: Any) -> str:
    """Tinted glass pill + glyph, so status survives without colour and keeps AA contrast."""
    is_flagged = _pred_bool(pred)
    if is_flagged is None:
        label, glyph, color = f"Pred {pred}", '•', PALETTE['faint']
    elif is_flagged:
        label, glyph, color = "Flagged", '⚠', PALETTE['risk']
    else:
        label, glyph, color = "Clear", '✓', PALETTE['ok']
    return (
        '<span style="display:inline-flex;align-items:center;gap:0.34rem;'
        'padding:0.2rem 0.62rem;border-radius:999px;'
        f"background:{_tint(color, 0.16)};border:1px solid {_tint(color, 0.5)};"
        f'color:{color};font-size:0.8rem;font-weight:700;letter-spacing:0.01em;">'
        f'<span aria-hidden="true">{glyph}</span>{html.escape(label)}</span>'
    )


def _html(st: Any, body: str) -> None:
    if hasattr(st, 'html'):
        st.html(body)
    else:
        st.markdown(body, unsafe_allow_html=True)


def _sequence_mode(view: dict[str, Any]) -> str:
    # detection_view_model always sets display_mode; bare views fall back to a gauge.
    return str(view.get('display_mode') or 'gauge')


def _render_gauge(st: Any, view: dict[str, Any]) -> None:
    pred = view.get('prediction')
    threshold = _num(view.get('threshold'), 0.5)
    prob = _clamp01(_num(view.get('probability'), 0.0))
    threshold_pct = _clamp01(threshold) * 100
    fill = f"linear-gradient(90deg,{PALETTE['ok']},{PALETTE['hot']})"
    _html(
        st,
        (
            '<div style="padding:0.75rem 0;">'
            '<div style="display:flex;justify-content:space-between;'
            'align-items:center;gap:0.75rem;margin-bottom:0.5rem;">'
            '<strong style="font-size:1.4rem;color:#8f123c;background:#fff1f5;'
            'border:1px solid #f4a3bd;border-radius:0.55rem;padding:0.16rem 0.45rem;'
            f'{_MONO}">{prob * 100:.1f}%</strong>{_badge(pred)}'
            '</div>'
            '<div style="position:relative;padding-top:0.55rem;">'
            '<div style="height:16px;border-radius:999px;'
            f'background:{PALETTE["track"]};overflow:hidden;">'
            '<div style="height:100%;border-radius:999px;background:'
            f'{fill};width:{prob * 100:.2f}%;"></div></div>'
            '<div title="threshold" style="position:absolute;top:0;'
            f"left:{threshold_pct:.2f}%;transform:translateX(-50%);"
            'display:flex;flex-direction:column;align-items:center;pointer-events:none;">'
            '<span style="color:var(--sirin-text);opacity:0.85;font-size:0.6rem;line-height:1;">&#9662;</span>'
            '<span style="width:2px;height:16px;background:var(--sirin-text);opacity:0.85;'
            'box-shadow:0 0 0 1px var(--sirin-shadow);"></span></div></div>'
            '<div style="margin-top:0.4rem;font-size:0.8rem;'
            f'color:var(--sirin-muted);{_MONO}">threshold {threshold_pct:.1f}%</div></div>'
        ),
    )


def _render_raw(st: Any, view: dict[str, Any]) -> None:
    threshold = _num(view.get('threshold'))
    raw = _num(view.get('raw_prob'), 0.0)
    threshold_text = f"{threshold:.4g}" if threshold is not None else "not set"
    _html(
        st,
        (
            '<div style="display:flex;align-items:center;gap:0.75rem;'
            'flex-wrap:wrap;padding:0.75rem 0;">'
            '<span style="display:inline-flex;gap:0.45rem;align-items:baseline;'
            'padding:0.42rem 0.7rem;border-radius:0.6rem;'
            'background:var(--sirin-surface-2);border:1px solid var(--sirin-border);">'
            '<strong>Raw score</strong>'
            f'<span style="{_MONO}">{raw:.4g}</span>'
            f'<span style="color:var(--sirin-muted);{_MONO}">threshold {html.escape(threshold_text)}</span>'
            '</span>'
            '<span style="font-size:0.84rem;color:var(--sirin-muted);">'
            'higher = more uncertain</span></div>'
        ),
    )


def _render_multiclass(st: Any, view: dict[str, Any]) -> None:
    probs = view.get('class_probs')
    probs = probs.tolist() if hasattr(probs, 'tolist') else probs
    probs = probs if isinstance(probs, list) else []
    active = _num(view.get('class_index'))
    index = int(active) if active is not None else -1
    rows = []
    for idx, prob in enumerate(probs):
        value = _clamp01(_num(prob, 0.0))
        active = idx == index
        bar = PALETTE['hot'] if active else PALETTE['periwinkle']
        rows.append(
            '<div style="display:grid;grid-template-columns:minmax(4.5rem,7rem) 1fr '
            '4.2rem;gap:0.65rem;align-items:center;margin:0.42rem 0;">'
            f'<strong style="opacity:{1 if active else 0.72};">Class {idx}</strong>'
            f'<div style="height:12px;border-radius:999px;background:{PALETTE["track"]};'
            'overflow:hidden;">'
            '<div style="height:100%;border-radius:999px;background:'
            f'{bar};width:{value * 100:.2f}%;"></div>'
            '</div>'
            f'<span style="text-align:right;{_MONO}">{value * 100:.1f}%</span>'
            '</div>'
        )
    _html(st, '<div style="padding:0.65rem 0;">' + ''.join(rows) + '</div>')


def _render_verdict(st: Any, view: dict[str, Any]) -> None:
    raw = _num(view.get('raw_prob'))
    pred = view.get('prediction')
    confidence = 'n/a' if raw is None else f"{raw:.3g}"
    _html(
        st,
        (
            '<div style="padding:0.85rem 0;display:flex;align-items:center;'
            'gap:0.8rem;flex-wrap:wrap;">'
            f'<span style="font-size:1.05rem;">{_badge(pred)}</span>'
            f'<span style="font-size:0.86rem;color:var(--sirin-muted);{_MONO}">'
            f"confidence {confidence}</span>"
            '</div>'
        ),
    )


def _render_sequence(st: Any, view: dict[str, Any]) -> None:
    mode = _sequence_mode(view)
    if mode == 'multiclass':
        _render_multiclass(st, view)
    elif mode == 'verdict':
        _render_verdict(st, view)
    elif mode == 'raw':
        _render_raw(st, view)
    else:
        _render_gauge(st, view)


def _scores(value: Any) -> list[float]:
    if value is None:
        return []
    if hasattr(value, 'tolist'):
        value = value.tolist()
    if not isinstance(value, list):
        return []
    scores = []
    for item in value:
        number = _num(item, 0.0)
        scores.append(_clamp01(number))
    return scores


def _cell_label(cell: str) -> str:
    if cell == ' ':
        return 'space'
    if cell == '\n':
        return '\\n'
    if cell == '\t':
        return 'tab'
    if cell and not cell.strip():
        return f'{len(cell)} spaces'
    return html.escape(cell) if cell else '&nbsp;'


def token_strip(
    cells: list[str],
    scores: list[float],
    *,
    invert: bool = False,
    color: str | None = None,
    titles: list[str] | None = None,
    colorbar: bool = False,
) -> str:
    """One row of per-token cells tinted by score in [0, 1] — the shared primitive behind the
    per-token visualizers. ``invert`` colours LOW scores hot (e.g. a lookback ratio: little
    attention to context => higher hallucination risk). ``color`` overrides the risk-colormap's
    hot end. ``titles`` gives per-cell hover text (e.g. the RAW value), else the shown intensity
    is used. A cell with no matching score renders NEUTRAL (not hot), so a length mismatch never
    masquerades as risk. ``colorbar`` prefixes an inline 0-1 legend."""
    from sirin.ui.styles import RISK_STOPS, lerp_hex

    stops = RISK_STOPS if color is None else (PALETTE['ok'], lerp_hex(PALETTE['ok'], color, 0.5), color)
    out = []
    for index, cell in enumerate(cells):
        if index < len(scores):
            score = _clamp01(scores[index])
            shown = 1.0 - score if invert else score
        else:
            shown = 0.5  # missing score => neutral, never max-risk
        title = titles[index] if titles and index < len(titles) else f"{shown:.2f}"
        text = _cell_label(cell)
        fill = risk_color(shown, stops)
        out.append(
            f'<span title="{html.escape(title)}" style="display:inline-block;margin:0.09rem;'
            f'padding:0.1rem 0.3rem;border-radius:0.35rem;{_MONO}font-size:0.86rem;'
            f'color:{risk_ink(fill)};background:{fill};border:1px solid {RISK_CELL_BORDER};">{text}</span>'
        )
    body = '<div class="sirin-token-strip" style="line-height:2.2;">' + ''.join(out) + '</div>'
    return (colorbar_html(0.0, 1.0) + body) if colorbar else body


def _segments(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r'\s+|\S+', text)]


def _score_values(value: Any) -> list[float | None]:
    if value is None:
        return []
    if hasattr(value, 'tolist'):
        value = value.tolist()
    if not isinstance(value, list):
        return []
    return [_num(item) for item in value]


def _segment_values(
    text: str,
    segments: list[tuple[int, int, str]],
    values: list[float | None],
) -> list[float | None]:
    if len(values) == len(text):
        return [
            max((v for v in values[start:end] if v is not None), default=None)
            for start, end, _ in segments
        ]
    if len(values) == len(segments):
        return list(values)

    non_ws = [i for i, (_, _, piece) in enumerate(segments) if not piece.isspace()]
    if len(values) <= len(non_ws):
        out: list[float | None] = [None] * len(segments)
        for slot, value in zip(non_ws, values):
            out[slot] = value
        return out
    return [values[i] if i < len(values) else None for i in range(len(segments))]


def _sentence_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    for match in re.finditer(r'[^.!?\n]+[.!?]*', text):
        piece = match.group(0)
        if piece.strip():
            spans.append((match.start(), match.end(), piece.strip()))
    return spans or ([(0, len(text), text.strip())] if text.strip() else [])


def _format_score(value: float | None, calibrated: bool) -> str:
    if value is None:
        return 'score n/a'
    return f'{value * 100:.1f}%' if calibrated and 0.0 <= value <= 1.0 else f'score {value:.4g}'


def _review_badge(pred: Any) -> str:
    flagged = _pred_bool(pred)
    if flagged is None:
        label, color = 'No verdict', PALETTE['faint']
    elif flagged:
        label, color = 'Flagged for review', PALETTE['risk']
    else:
        label, color = 'Not flagged', PALETTE['ok']
    return (
        '<span style="display:inline-flex;align-items:center;border-radius:999px;'
        'padding:0.16rem 0.52rem;font-size:0.74rem;font-weight:700;'
        f'background:{_tint(color, 0.15)};border:1px solid {_tint(color, 0.45)};'
        f'color:{color};">{html.escape(label)}</span>'
    )


def _is_sequence_broadcast(view: dict[str, Any]) -> bool:
    return str(view.get('display_mode') or '') == 'sequence-broadcast'


def _sequence_broadcast_html(
    answer: str,
    score: float | None,
    shown_score: float | None,
    calibrated: bool,
    scale_label: str,
    signal_note: str,
) -> str:
    shown = _clamp01(shown_score if shown_score is not None else score)
    fill = risk_color(shown)
    tint = _tint(fill, 0.24)
    score_text = _format_score(score, calibrated)
    token_cells = []
    for start, end, piece in _segments(answer):
        escaped = html.escape(piece)
        if piece.isspace():
            token_cells.append(escaped)
            continue
        token_cells.append(
            '<span data-granularity="token"'
            f' data-score="{shown:.3f}" data-index="{start}" data-end="{end}"'
            f' title="{html.escape(score_text + " · " + scale_label)}"'
            ' style="display:inline;margin:0 0.02rem;padding:0.03rem 0.18rem;'
            f'border-radius:0.24rem;background:{tint};color:var(--sirin-text);'
            f'box-shadow:inset 0 -0.18rem 0 {_tint(fill, 0.72)};'
            f'border:1px solid {_tint(fill, 0.38)};">{escaped}</span>'
        )
    sentence_rows = []
    for _, _, sentence in _sentence_spans(answer):
        sentence_rows.append(
            '<div style="border:1px solid var(--sirin-border);border-radius:0.55rem;'
            f'border-left:4px solid {fill};padding:0.55rem 0.65rem;background:var(--sirin-surface-2);">'
            '<div style="display:flex;align-items:center;justify-content:space-between;gap:0.7rem;">'
            f'<span style="line-height:1.42;color:var(--sirin-text);">{html.escape(sentence)}</span>'
            f'<strong style="{_MONO}white-space:nowrap;color:{risk_ink(fill)};background:{fill};'
            f'border:1px solid {RISK_CELL_BORDER};border-radius:999px;'
            f'padding:0.12rem 0.45rem;">{html.escape(score_text)}</strong></div></div>'
        )
    return (
        '<div class="sirin-granularity-panel" style="border:1px solid var(--sirin-border);'
        'border-radius:10px;padding:0.9rem 1rem;background:var(--sirin-surface-2);'
        'box-shadow:0 12px 30px var(--sirin-shadow);">'
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;'
        'gap:0.9rem;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<div><div style="font-size:0.82rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:800;color:var(--sirin-hot);">Output · Sequence Attribution</div>'
        '<div style="font-size:0.86rem;color:var(--sirin-muted);margin-top:0.2rem;">'
        f'{html.escape(signal_note)}</div></div>'
        f'<span style="border:1px solid var(--sirin-border);border-radius:999px;'
        'padding:0.16rem 0.55rem;font-size:0.74rem;color:var(--sirin-muted);'
        f'text-transform:uppercase;letter-spacing:0.06em;">{html.escape(scale_label)}</span></div>'
        '<div style="display:grid;grid-template-columns:minmax(9rem,12rem) 1fr;'
        'gap:0.8rem;align-items:center;margin-bottom:0.75rem;">'
        f'<strong style="{_MONO}font-size:1.35rem;color:{risk_ink(fill)};background:{fill};'
        f'border:1px solid {RISK_CELL_BORDER};border-radius:0.55rem;padding:0.22rem 0.55rem;'
        f'text-align:center;">{html.escape(score_text)}</strong>'
        f'<div style="height:12px;border-radius:999px;background:{PALETTE["track"]};overflow:hidden;">'
        f'<div style="height:100%;width:{shown * 100:.2f}%;background:{fill};"></div></div>'
        '</div>'
        '<section>'
        '<div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:700;color:var(--sirin-muted);">Highlighted answer tokens</div>'
        '<div style="margin-top:0.35rem;border:1px solid var(--sirin-border);'
        'border-radius:0.65rem;background:var(--sirin-surface);padding:0.75rem 0.85rem;'
        'line-height:1.85;color:var(--sirin-text);font-size:0.94rem;white-space:pre-wrap;">'
        + ''.join(token_cells)
        + '</div></section>'
        '<section style="margin-top:0.8rem;">'
        '<div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:700;color:var(--sirin-muted);">Sentence coverage</div>'
        '<div style="display:grid;gap:0.45rem;margin-top:0.35rem;">'
        + ''.join(sentence_rows)
        + '</div></section></div>'
    )


def publication_granularity_html(view: dict[str, Any]) -> str:
    """Publication-style output panel: token spans, derived sentence summary, optional claim rows."""
    answer = str(view.get('answer') or '')
    segments = _segments(answer)
    shown_values = _segment_values(answer, segments, _score_values(view.get('norm_scores')))
    raw_values = _segment_values(answer, segments, _score_values(view.get('scores')))
    preds = _segment_values(answer, segments, _score_values(view.get('predictions')))
    calibrated = bool(view.get('calibrated', True))
    scale_label = str(view.get('scale_label') or (
        'calibrated detector score' if calibrated else 'relative detector signal'
    ))
    signal_note = str(
        view.get('signal_note')
        or 'Each highlighted span shows detector signal assigned to generated text. '
           'Color is not evidence by itself.'
    )
    if _is_sequence_broadcast(view):
        scores = _score_values(view.get('scores'))
        shown_scores = _score_values(view.get('norm_scores'))
        return _sequence_broadcast_html(
            answer,
            scores[0] if scores else None,
            shown_scores[0] if shown_scores else None,
            calibrated,
            scale_label,
            signal_note,
        )
    legend = (
        'lower detector signal -> higher detector signal'
        if calibrated
        else 'lower relative signal -> higher relative signal'
    )

    token_cells = []
    for index, (start, end, piece) in enumerate(segments):
        escaped_piece = html.escape(piece)
        if piece.isspace():
            token_cells.append(escaped_piece)
            continue
        shown = shown_values[index] if index < len(shown_values) else None
        raw = raw_values[index] if index < len(raw_values) else None
        pred = preds[index] if index < len(preds) else None
        pred_attr = f' data-pred="{int(pred)}"' if pred in (0, 0.0, 1, 1.0) else ''
        if shown is None:
            title = f'span "{piece}" · no detector score'
            token_cells.append(
                '<span data-granularity="token" data-score="missing" data-missing="true"'
                f' data-index="{start}" data-end="{end}" title="{html.escape(title)}"'
                ' style="display:inline-block;margin:0.08rem 0.02rem;padding:0.08rem 0.24rem;'
                'border-radius:0.3rem;background:rgba(148,163,184,0.14);'
                'border-bottom:3px dashed var(--sirin-faint);">'
                f'{escaped_piece}</span>'
            )
            continue
        shown = _clamp01(shown)
        raw_text = _format_score(raw, calibrated)
        title = (
            f'span "{piece}" · {raw_text} · {scale_label}'
            if calibrated
            else f'span "{piece}" · raw {raw if raw is not None else "n/a"} · '
                 f'color value {shown:.3f} · not a probability'
        )
        fill = risk_color(shown)
        token_cells.append(
            '<span data-granularity="token"'
            f' data-score="{shown:.3f}" data-index="{start}" data-end="{end}"{pred_attr}'
            f' title="{html.escape(title)}"'
            ' style="display:inline-block;margin:0.08rem 0.02rem;padding:0.08rem 0.24rem;'
            f'border-radius:0.3rem;background:{fill};color:{risk_ink(fill)};'
            f'border:1px solid {RISK_CELL_BORDER};">'
            f'{escaped_piece}</span>'
        )

    sentence_rows = []
    for start, end, sentence in _sentence_spans(answer):
        candidates = [
            shown_values[index]
            for index, (seg_start, seg_end, piece) in enumerate(segments)
            if not piece.isspace()
            and seg_start < end
            and start < seg_end
            and index < len(shown_values)
            and shown_values[index] is not None
        ]
        score = max(candidates, default=None)
        width = _clamp01(score) * 100 if score is not None else 0
        score_attr = f'{score:.3f}' if score is not None else 'missing'
        fill = risk_color(_clamp01(score)) if score is not None else 'rgba(148,163,184,0.18)'
        sentence_rows.append(
            '<div data-granularity="sentence"'
            f' data-score="{score_attr}"'
            ' style="border:1px solid var(--sirin-border);border-radius:0.55rem;'
            'padding:0.55rem 0.65rem;margin-top:0.45rem;background:var(--sirin-surface-2);">'
            '<div style="display:flex;align-items:center;gap:0.65rem;justify-content:space-between;">'
            f'<span style="line-height:1.4;">{html.escape(sentence)}</span>'
            f'<strong style="{_MONO}white-space:nowrap;">{html.escape(_format_score(score, calibrated))}</strong>'
            '</div>'
            f'<div style="height:6px;border-radius:999px;background:{PALETTE["track"]};'
            'overflow:hidden;margin-top:0.45rem;">'
            f'<div style="height:100%;width:{width:.2f}%;background:{fill};"></div></div>'
            '</div>'
        )

    claim_rows = []
    for claim in list(view.get('claims') or []):
        fact = str(claim.get('fact') or '')
        score = _num(claim.get('prob'))
        shown = _clamp01(score)
        fill = risk_color(shown)
        claim_rows.append(
            '<div data-granularity="claim"'
            f' data-score="{shown:.3f}"'
            ' style="display:grid;grid-template-columns:1fr auto auto;gap:0.7rem;'
            'align-items:center;border:1px solid var(--sirin-border);border-radius:0.55rem;'
            'padding:0.55rem 0.65rem;margin-top:0.45rem;background:var(--sirin-surface-2);">'
            f'<span style="line-height:1.4;">{html.escape(fact)}</span>'
            f'<strong style="{_MONO}color:{risk_ink(fill)};background:{fill};'
            f'border:1px solid {RISK_CELL_BORDER};border-radius:999px;padding:0.12rem 0.45rem;">'
            f'{html.escape(_format_score(score, calibrated))}</strong>'
            f'{_review_badge(claim.get("pred"))}</div>'
        )

    claim_lane = (
        '<section style="margin-top:0.8rem;">'
        '<div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:700;color:var(--sirin-muted);">Claim-level output</div>'
        '<div style="font-size:0.82rem;color:var(--sirin-muted);margin-top:0.15rem;">'
        'Shown only when the detector provides claim rows.</div>'
        + ''.join(claim_rows)
        + '</section>'
        if claim_rows else ''
    )

    return (
        '<div class="sirin-granularity-panel" style="border:1px solid var(--sirin-border);'
        'border-radius:12px;padding:0.9rem 1rem;background:var(--sirin-surface-2);'
        'box-shadow:0 12px 30px var(--sirin-shadow);">'
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;'
        'gap:0.9rem;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<div><div style="font-size:0.82rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:800;color:var(--sirin-hot);">Output · Granularity</div>'
        '<div style="font-size:0.86rem;color:var(--sirin-muted);margin-top:0.2rem;">'
        f'{html.escape(signal_note)}</div></div>'
        f'<span style="border:1px solid var(--sirin-border);border-radius:999px;'
        'padding:0.16rem 0.55rem;font-size:0.74rem;color:var(--sirin-muted);'
        f'text-transform:uppercase;letter-spacing:0.06em;">{html.escape(scale_label)}</span></div>'
        f'{colorbar_html(0.0, 1.0, label=legend)}'
        '<section>'
        '<div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:700;color:var(--sirin-muted);">Token-level signal</div>'
        '<div style="line-height:2.25;white-space:pre-wrap;margin-top:0.35rem;">'
        + ''.join(token_cells)
        + '</div></section>'
        '<section style="margin-top:0.8rem;">'
        '<div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;'
        'font-weight:700;color:var(--sirin-muted);">Sentence-level summary</div>'
        '<div style="font-size:0.82rem;color:var(--sirin-muted);margin-top:0.15rem;">'
        'Derived as max token signal in each sentence.</div>'
        + ''.join(sentence_rows)
        + '</section>'
        + claim_lane
        + '</div>'
    )


def layer_token_heatmap(layers: list[int], cells: list[str], raw: np.ndarray, shown: np.ndarray) -> str:
    """Rows = layers, cols = REAL answer tokens. Opaque risk-colormap cells; hover = raw value.
    `raw` and `shown` are (n_layers, n_tokens); `shown` is already risk-oriented in [0,1]."""
    header_cells = ''.join(
        f'<th style="padding:0.3rem 0.5rem;text-align:center;font-weight:600;color:var(--sirin-muted);'
        f'font-size:0.74rem;white-space:pre;max-width:5rem;overflow:hidden;text-overflow:ellipsis;'
        f'border-bottom:1px solid var(--sirin-border);" title="{html.escape(c)}">'
        f'{html.escape(c) if c.strip() else "&nbsp;"}</th>'
        for c in cells
    )
    rows = [
        '<tr><th style="position:sticky;left:0;background:var(--sirin-surface-2);'
        'border-bottom:1px solid var(--sirin-border);border-right:1px solid var(--sirin-border);'
        f'padding:0.3rem 0.6rem;text-align:right;color:var(--sirin-muted);">layer</th>{header_cells}</tr>'
    ]
    for r, layer in enumerate(layers):
        tds = []
        for c in range(len(cells)):
            t = float(shown[r, c])
            raw_value = float(raw[r, c])
            fill = risk_color(t)
            title = (
                f'layer {layer} | token {c} | {cells[c]} | '
                f'raw {raw_value:.4f} | shown {t:.4f}'
            )
            tds.append(
                f'<td data-layer="{layer}" data-token-index="{c}" data-raw="{raw_value:.4f}" '
                f'data-shown="{t:.4f}" title="{html.escape(title)}" '
                f'style="background:{fill};color:{risk_ink(fill)};'
                f'border:1px solid {RISK_CELL_BORDER};padding:0.28rem 0.4rem;text-align:center;'
                f'min-width:2.3rem;font-size:0.78rem;">{raw_value:.2f}</td>'
            )
        rows.append(
            '<tr><th style="position:sticky;left:0;background:var(--sirin-surface-2);'
            'border-right:1px solid var(--sirin-border);padding:0.28rem 0.6rem;text-align:right;'
            f'font-weight:600;color:var(--sirin-text);white-space:nowrap;">L{layer}</th>'
            + ''.join(tds) + '</tr>'
        )
    table = ('<table style="border-collapse:collapse;width:max-content;font-family:var(--sirin-mono);">'
             + ''.join(rows) + '</table>')
    return f'<div style="overflow:auto;max-height:70vh;border-radius:12px;">{table}</div>'


def _render_token(st: Any, view: dict[str, Any]) -> None:
    answer = str(view.get('answer') or '')
    _html(st, publication_granularity_html(view))
    if score_heatmap is None:
        st.info("Exact span boundary debug is unavailable because UI helpers could not be imported.")
    else:
        with st.expander('Exact span boundary debug', expanded=False):
            heatmap = score_heatmap(
                answer,
                _scores(view.get('norm_scores')),
                predictions=list(view.get('predictions') or []),
            )
            _html(
                st,
                '<div style="font-size:0.82rem;color:var(--sirin-muted);margin-bottom:0.4rem;">'
                'Exact span boundary debug</div>'
                + colorbar_html(0.0, 1.0, label='lower detector signal → higher detector signal')
                + heatmap,
            )
    if view.get('tagged_generation'):
        with st.expander("Judge's annotated answer (raw)"):
            st.write(str(view.get('tagged_generation')))


def _prob_text(value: Any) -> str:
    number = _num(value)
    if number is None:
        return 'n/a'
    if 0.0 <= number <= 1.0:
        return f"{number * 100:.1f}%"
    return f"{number:.4g}"


def _render_claim(st: Any, view: dict[str, Any]) -> None:
    claims = list(view.get('claims') or [])
    calibrated = view.get('calibrated', True)
    overall_prob = view.get(
        'overall_prob',
        claims[0].get('overall_prob') if claims and isinstance(claims[0], dict) else None,
    )
    overall_pred = view.get(
        'overall_pred',
        claims[0].get('overall_pred') if claims and isinstance(claims[0], dict) else None,
    )
    cards = []
    for claim in claims:
        fact = html.escape(str(claim.get('fact', '')))
        fact = fact or '<em>No fact text</em>'
        claim_prob = _num(claim.get('prob'))
        prob = html.escape(
            _prob_text(claim.get('prob'))
            if calibrated
            else f"score {claim_prob:.4g}" if claim_prob is not None else "score n/a"
        )
        pred = claim.get('pred')
        cards.append(
            '<div style="background:var(--sirin-surface-2);border:1px solid var(--sirin-border);'
            'border-radius:12px;padding:0.7rem 0.85rem;margin:0.5rem 0;">'
            '<div style="margin-bottom:0.4rem;line-height:1.5;">'
            f"{fact}</div>"
            '<div style="display:flex;gap:0.55rem;align-items:center;'
            'font-size:0.9rem;">'
            f'<strong style="{_MONO}">{prob}</strong>'
            f"{_badge(pred)}</div></div>"
        )
    _html(
        st,
        (
            '<div style="padding:0.35rem 0 0.15rem;">'
            '<div style="display:flex;align-items:center;gap:0.7rem;'
            'flex-wrap:wrap;margin-bottom:0.3rem;">'
            f'<strong style="{_MONO}">Overall '
            + (
                html.escape(_prob_text(overall_prob))
                if calibrated
                else html.escape(
                    f"score {_num(overall_prob):.4g}"
                    if _num(overall_prob) is not None
                    else "score n/a"
                )
            )
            + '</strong>'
            f"{_badge(overall_pred)}</div>"
            + ''.join(cards)
            + '</div>'
        ),
    )


def _render_reasoning(st: Any, reasoning: Any) -> None:
    if not reasoning:
        return
    with st.expander("Reasoning"):
        st.write(reasoning)


def render_result(st: Any, view: dict[str, Any]) -> None:
    level = view.get('level')
    family = html.escape(str(view.get('family', 'unknown') or 'unknown'))
    level_label = html.escape(str(level or 'unknown'))
    calibration = 'calibrated' if view.get('calibrated', True) else 'raw'
    _html(
        st,
        (
            '<div style="display:flex;gap:0.45rem;align-items:center;'
            'flex-wrap:wrap;margin:0.15rem 0 0.5rem;">'
            f'<span style="font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;'
            f'color:var(--sirin-hot);font-weight:600;">{family}</span>'
            '<span style="font-size:0.75rem;color:var(--sirin-faint);">/</span>'
            f'<span style="font-size:0.72rem;letter-spacing:0.08em;text-transform:uppercase;'
            f'color:var(--sirin-muted);">{level_label}</span>'
            '<span style="font-size:0.68rem;border:1px solid var(--sirin-border);'
            'border-radius:999px;padding:0.08rem 0.45rem;color:var(--sirin-muted);'
            'text-transform:uppercase;letter-spacing:0.06em;">'
            f"{calibration}</span></div>"
        ),
    )
    if level == 'sequence':
        _render_sequence(st, view)
    elif level == 'token':
        _render_token(st, view)
    elif level == 'claim':
        _render_claim(st, view)
    else:
        st.info("No visualization available for this result.")

    _render_reasoning(st, view.get('reasoning'))


def _render_method_scores(st: Any, method_scores: dict[str, float]) -> None:
    items = [(str(k), _num(v)) for k, v in (method_scores or {}).items()]
    values = [v for _, v in items if v is not None]
    if not values:
        st.info("No per-method scores available.")
        return
    low, high = min(values), max(values)
    rows = []
    for name, value in items:
        width = 0.0 if value is None else 100.0
        if value is not None and high > low:
            width = (value - low) / (high - low) * 100
        # bars are min-max scaled across methods; equal scores all get full bars.
        rows.append(
            '<div style="display:grid;grid-template-columns:minmax(7rem,12rem) 1fr '
            '5.5rem;gap:0.65rem;align-items:center;margin:0.4rem 0;">'
            f"<span>{html.escape(name)}</span>"
            f'<div style="height:11px;border-radius:999px;background:{PALETTE["track"]};'
            'overflow:hidden;">'
            f'<div style="height:100%;border-radius:999px;background:{PALETTE["mint"]};'
            f'width:{width:.2f}%;"></div></div>'
            f'<strong style="text-align:right;{_MONO}">{value:.4g}</strong>'
            '</div>'
            if value is not None
            else (
                '<div style="display:grid;grid-template-columns:minmax(7rem,12rem) 1fr '
                '5.5rem;gap:0.65rem;align-items:center;margin:0.4rem 0;">'
                f"<span>{html.escape(name)}</span><div></div>"
                f'<strong style="text-align:right;{_MONO}">n/a</strong></div>'
            )
        )
    _html(st, '<div style="padding:0.4rem 0;">' + ''.join(rows) + '</div>')


def render_debug(st: Any, detector: Any) -> None:
    processor = getattr(detector, 'feature_processor', None)
    debug = getattr(processor, 'last_debug', None)
    if not debug:
        st.info("No debug artifacts captured for the last detection run.")
        return

    from sirin.ui.streamlit_app import debug_summary

    st.json(debug_summary(debug))
    if debug.get('children'):
        st.write("Ensemble processors")
        st.dataframe([debug_summary(child) for child in debug['children'] if child])
