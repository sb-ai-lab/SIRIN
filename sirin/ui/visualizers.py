from __future__ import annotations

import math
import html
from typing import Any

from sirin.ui.styles import PALETTE

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
            f'<strong style="font-size:1.4rem;{_MONO}">{prob * 100:.1f}%</strong>{_badge(pred)}'
            '</div>'
            '<div style="position:relative;padding-top:0.55rem;">'
            '<div style="height:16px;border-radius:999px;'
            f'background:{PALETTE["track"]};overflow:hidden;">'
            '<div style="height:100%;border-radius:999px;background:'
            f'{fill};width:{prob * 100:.2f}%;"></div></div>'
            '<div title="threshold" style="position:absolute;top:0;'
            f"left:{threshold_pct:.2f}%;transform:translateX(-50%);"
            'display:flex;flex-direction:column;align-items:center;pointer-events:none;">'
            f'<span style="color:{PALETTE["sheen"]};font-size:0.6rem;line-height:1;">&#9662;</span>'
            f'<span style="width:2px;height:16px;background:{PALETTE["sheen"]};'
            'box-shadow:0 0 0 1px rgba(13,8,25,0.55);"></span></div></div>'
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
            f'background:{PALETTE["surface_2"]};border:1px solid {PALETTE["border"]};">'
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


def _render_token(st: Any, view: dict[str, Any]) -> None:
    if score_heatmap is None:
        st.info("Token heatmap is unavailable because UI helpers could not be imported.")
        return
    answer = str(view.get('answer') or '')
    heatmap = score_heatmap(answer, _scores(view.get('norm_scores')))
    swatch = 'display:inline-block;width:0.95rem;height:0.95rem;border-radius:4px;vertical-align:-0.15rem;'
    _html(
        st,
        (
            '<div style="margin-bottom:0.5rem;font-size:0.82rem;color:var(--sirin-muted);">'
            f'<span style="{swatch}background:{_tint(PALETTE["risk"], 0.14)};'
            f'border:1px solid {_tint(PALETTE["risk"], 0.3)};"></span>'
            ' low&nbsp;&nbsp;'
            f'<span style="{swatch}background:{_tint(PALETTE["risk"], 0.85)};"></span>'
            ' high&nbsp;&nbsp;<span style="opacity:0.8;">= more likely hallucinated</span></div>'
            f"{heatmap}"
        ),
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
            f'<div style="background:{PALETTE["surface_2"]};border:1px solid {PALETTE["border"]};'
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
            f'<span style="font-size:0.68rem;border:1px solid {PALETTE["border"]};'
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
