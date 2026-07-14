"""Global styling for the SIRIN Streamlit UI.

A bright, holographic *silk* backdrop (baked gradient, recreated from the design reference — no
external assets) painted on the app's OWN background, with dark frosted-glass panels on top so text
stays readable over the vivid colour. All accent colours live in ``PALETTE`` so the visualizers can
import the same tokens (single source of truth).
"""

import html
import json
import re
from functools import lru_cache
from pathlib import Path

_TOKENS_PATH = Path(__file__).parent / 'tokens.json'


@lru_cache(maxsize=1)
def _tokens() -> dict:
    """The single design-token source (sirin/ui/tokens.json), loaded once per process.

    The workspace component imports the same file directly, so host chrome, native Streamlit
    widgets, and the component all resolve identical palette/type/font values.
    """
    return json.loads(_TOKENS_PATH.read_text(encoding='utf-8'))

# Reference-matched holographic palette (dusty-pastel, sampled from the design reference).
PALETTE: dict[str, str] = {
    # --- backdrop hues (the silk) ---
    'deep': '#563678',
    'violet': '#6c5491',
    'orchid': '#986aaa',
    'periwinkle': '#a999ca',
    'mint': '#afdedd',
    'lilac': '#cca2c7',
    'pink': '#dc8db9',
    'hot': '#b91b63',
    'sheen': '#e8ebed',
    # --- app surfaces (dark glass over the bright backdrop) ---
    'bg': '#0d0819',
    'surface': 'rgba(20, 14, 34, 0.86)',  # dense enough to stay dark over bright silk
    'surface_2': 'rgba(15, 10, 26, 0.72)',
    'border': 'rgba(255, 255, 255, 0.14)',
    'text': '#f4f0fb',
    'muted': '#c3b8dc',
    'faint': '#9086ab',
    'shadow': 'rgba(0, 0, 0, 0.50)',
    # --- semantic tokens (results; readable on dark glass) ---
    'risk': '#a52e35',  # flagged / high score
    'ok': '#086a60',  # clear / low score
    'track': 'rgba(148, 163, 184, 0.24)',
    'accent': '#b91b63',
}

# Theme-varying tokens are DERIVED from tokens.json so the host consumes the same demo palette as
# the workspace component. Each host CSS @@placeholder@@ maps onto one canonical palette key; the
# component reads those same keys (see sirin/ui/workspace/frontend/src/theme.ts).
_HOST_TOKEN_MAP: dict[str, str] = {
    'color_scheme': 'colorScheme',
    'bg': 'canvas',
    'surface': 'surface',
    'surface_2': 'surface2',
    'scrim': 'scrim',
    'border': 'line',
    'text': 'ink',
    'muted': 'muted',
    'faint': 'faint',
    'shadow': 'shadowColor',
    'hot': 'brand',
    'mint': 'mint',
    'accent': 'brand',
    'link': 'link',
    'sidebar_bg': 'sidebarBg',
    'input_bg': 'inputBg',
    'popover_bg': 'popoverBg',
    'option_hover': 'optionHover',
    'btn_bg': 'btnBg',
    'btn_hover_bg': 'btnHoverBg',
    'btn_hover_border': 'btnHoverBorder',
    'pill_bg': 'pillBg',
    'pill_selected': 'pillSelected',
    'pill_selected_border': 'pillSelectedBorder',
    'scroll_thumb': 'scrollThumb',
    'scroll_thumb2': 'scrollThumb2',
    'scroll_thumb_hover': 'scrollThumbHover',
}


def _build_themes() -> dict[str, dict[str, str]]:
    palette = _tokens()['palette']
    return {
        theme: {
            placeholder: palette[theme][token_key]
            for placeholder, token_key in _HOST_TOKEN_MAP.items()
        }
        for theme in palette
    }


THEMES: dict[str, dict[str, str]] = _build_themes()

PALETTE['warn'] = (
    '#81520c'  # amber "mid" anchor for the risk colormap; every other accent is
)
# cool pink/teal, so mid needs its own hue or it collapses toward "high".

RISK_STOPS: tuple[str, str, str] = (PALETTE['ok'], PALETTE['warn'], PALETTE['risk'])
RISK_CELL_BORDER: str = (
    'rgba(26, 18, 38, 0.4)'  # fixed dark hairline; NOT var(--sirin-border), which
)
# would go light-on-light on these pastels in dark mode.
_DARK_INK = THEMES['light']['text']
_LIGHT_INK = THEMES['dark']['text']


def lerp_hex(a: str, b: str, t: float) -> str:
    """Plain sRGB channel-wise lerp — the same space CSS linear-gradient() uses."""
    ah, bh = a.lstrip('#'), b.lstrip('#')
    out = [
        round(
            int(ah[i : i + 2], 16)
            + (int(bh[i : i + 2], 16) - int(ah[i : i + 2], 16)) * t
        )
        for i in (0, 2, 4)
    ]
    return '#{:02x}{:02x}{:02x}'.format(*out)


def risk_color(t: float, stops: tuple[str, str, str] = RISK_STOPS) -> str:
    """[0,1] -> opaque hex. Two-segment lerp over 3 stops: safe -> mid(t=0.5) -> danger."""
    t = min(1.0, max(0.0, t))
    lo, mid, hi = stops
    return lerp_hex(lo, mid, t * 2) if t <= 0.5 else lerp_hex(mid, hi, (t - 0.5) * 2)


def risk_ink(fill_hex: str) -> str:
    """AA-legible ink for a risk_color() fill, by WCAG relative luminance."""
    h = fill_hex.lstrip('#')

    def _lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    luminance = 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)
    return _DARK_INK if luminance > 0.18 else _LIGHT_INK


def risk_gradient_css(stops: tuple[str, str, str] = RISK_STOPS) -> str:
    lo, mid, hi = stops
    return f"linear-gradient(90deg, {lo} 0%, {mid} 50%, {hi} 100%)"


def colorbar_html(
    low: float = 0.0,
    high: float = 1.0,
    *,
    stops: tuple[str, str, str] = RISK_STOPS,
    label: str = '',
) -> str:
    """Inline colour-scale legend: numeric low — gradient bar — numeric high (+ optional caption)."""
    caption = (
        f'<span style="margin-left:0.5rem;opacity:0.85;">{html.escape(label)}</span>'
        if label
        else ''
    )
    return (
        '<div style="display:flex;align-items:center;gap:0.5rem;margin:0.3rem 0 0.6rem;'
        'font-size:0.72rem;color:var(--sirin-muted);font-family:var(--sirin-mono);">'
        f'<span>{low:.2f}</span>'
        f'<span style="flex:0 0 auto;width:160px;height:10px;border-radius:999px;'
        f'background:{risk_gradient_css(stops)};border:1px solid var(--sirin-border);"></span>'
        f'<span>{high:.2f}</span>{caption}</div>'
    )


# Baked holographic-silk background (chosen candidate "Aurora Silk — Balanced"), recreated
# procedurally from the reference (no stock imagery). Served as a static file via Streamlit's
# ``enableStaticServing`` (see .streamlit/config.toml) from sirin/ui/static/, referenced as
# url("app/static/<file>"), instead of a ~350KB base64 data URI re-shipped in the CSS every rerun.
# The dark theme paints a deep plum/indigo twin (silk_bg_dark.jpg, colour-graded from the light silk)
# so cards read as dark glass over a dark silk, not over the bright pink one. Both stay in assets/ for
# packaging compatibility. The active file is picked per theme in _compiled_css (@@silk@@ runtime key).
_SILK_ASSET: dict[str, str] = {'light': 'silk_bg.jpg', 'dark': 'silk_bg_dark.jpg'}

_FONT = _tokens()['fonts']['sans']
_MONO = _tokens()['fonts']['mono']

# Motion presets — a compositor-only pan+zoom "breathe" on the dedicated silk layer. Animate ONLY
# transform (animating background-position on a cover-sized layer moved ~0px visually but forced a
# full-viewport raster repaint every frame; transform/filter on stApp itself bleed onto content).
_MOTION = {
    'static': 'none',
    'subtle': 'sirin-breathe-subtle 60s ease-in-out infinite alternate',
    'lively': 'sirin-breathe-lively 30s ease-in-out infinite alternate',
}

_CSS_TEMPLATE = """<style>
/* One font family everywhere: the same Manrope / IBM Plex Mono files the workspace component ships,
   served here via Streamlit's static dir so native widgets (config.toml font/codeFont) resolve them. */
@font-face {
    font-family: "Manrope";
    src: url("app/static/fonts/Manrope-Variable.woff2") format("woff2");
    font-weight: 200 800;
    font-style: normal;
    font-display: swap;
}
@font-face {
    font-family: "IBM Plex Mono";
    src: url("app/static/fonts/IBMPlexMono-Regular.woff2") format("woff2");
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}
@font-face {
    font-family: "IBM Plex Mono";
    src: url("app/static/fonts/IBMPlexMono-SemiBold.woff2") format("woff2");
    font-weight: 600;
    font-style: normal;
    font-display: swap;
}
/* THEME CONTRACT: a theme is one entry in THEMES that provides every token referenced below.
   Selectors are theme-INDEPENDENT — they read CSS vars / theme tokens, never per-theme values — so a new
   theme = one token map and nothing else (enforced by _validate_theme_contract). The Streamlit "native
   chrome" overrides further down (inputs, number steppers, pills, chat input, footer, dropdown popover
   portal, send-button icon) are DOM-selector-dependent and may need updating on a Streamlit upgrade;
   keep them pointing at CSS vars only, never a hard-coded colour. */
:root {
    color-scheme: @@color_scheme@@;
    --sirin-bg: @@bg@@;
    --sirin-surface: @@surface@@;
    --sirin-surface-2: @@surface_2@@;
    --sirin-border: @@border@@;
    --sirin-text: @@text@@;
    --sirin-muted: @@muted@@;
    --sirin-faint: @@faint@@;
    --sirin-shadow: @@shadow@@;
    --sirin-hot: @@hot@@;
    --sirin-mint: @@mint@@;
    --sirin-accent: @@accent@@;
    --sirin-link: @@link@@;
    --sirin-font: @@font@@;
    --sirin-mono: @@mono@@;
}

html, body, [data-testid="stApp"] {
    color: var(--sirin-text);
    font-family: var(--sirin-font);
    min-height: 100%;
}
*, *::before, *::after { box-sizing: border-box; }

/* The Streamlit host owns the one full-viewport silk layer. Workspace components remain transparent.
   The silk lives on a DEDICATED fixed, oversized (~132%) pseudo-element so motion animates ONLY that
   layer's transform (compositor-only). Never animate [data-testid="stApp"] itself: transforms/filters
   there bleed onto content, and animating the image position repaints the whole viewport per frame. */
[data-testid="stApp"] {
    background-color: var(--sirin-bg);
    isolation: isolate; /* keep the negative z-index silk/scrim layers inside this element */
}
[data-testid="stApp"]::before {
    content: "";
    position: fixed;
    inset: -16%;
    z-index: -2;
    background: var(--sirin-bg) url("app/static/@@silk@@") no-repeat 50% 50% / cover;
    will-change: transform;
    pointer-events: none;
    animation: @@anim@@;
}
/* Readability scrim above the silk (from the recovered reference demo). NEVER animated. */
[data-testid="stApp"]::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    background: @@scrim@@;
    pointer-events: none;
}

/* Slow pan+zoom "breathe": translate3d + scale only, so the silk stays on the compositor. */
@keyframes sirin-breathe-subtle {
    from { transform: translate3d(-1.1%, -0.7%, 0) scale(1); }
    to   { transform: translate3d(1.1%, 0.7%, 0) scale(1.03); }
}
@keyframes sirin-breathe-lively {
    from { transform: translate3d(-2.2%, -1.5%, 0) scale(1); }
    to   { transform: translate3d(2.2%, 1.5%, 0) scale(1.06); }
}

/* Same-document motion override: the workspace component sets html[data-sirin-motion] the instant the
   user changes motion (it renders in a shadow root of THIS document), so the silk reacts immediately;
   the server-rendered value above stays canonical and reconciles on the next rerun. */
html[data-sirin-motion="subtle"] [data-testid="stApp"]::before {
    animation: sirin-breathe-subtle 60s ease-in-out infinite alternate;
}
html[data-sirin-motion="lively"] [data-testid="stApp"]::before {
    animation: sirin-breathe-lively 30s ease-in-out infinite alternate;
}
html[data-sirin-motion="static"] [data-testid="stApp"]::before {
    animation: none;
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stApp"]::before { animation: none !important; }
}

[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
.main .block-container {
    background: transparent;
}

/* Fixed bottom chat footer: a solid, theme-following bar (it otherwise keeps the native
   base="dark" background and stays dark on the light theme). */
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] {
    background: var(--sirin-bg) !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 { color: var(--sirin-text); letter-spacing: -0.01em; }
p, span, li, label, [data-testid="stMarkdownContainer"] { color: var(--sirin-text); }
[data-testid="stCaptionContainer"], small { color: var(--sirin-muted); }

/* Sidebar: flat translucent fill. Its backdrop blur was the last per-frame re-blur over the moving
   silk (measured: exactly the 60fps -> 30fps step), so the app now has ZERO blur surfaces. */
[data-testid="stSidebar"] {
    background: @@sidebar_bg@@;
    border-right: 1px solid var(--sirin-border);
}
[data-testid="stSidebar"] * { color: var(--sirin-text); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: var(--sirin-text) !important; opacity: 0.96;
}
/* Census section headings (Detector / Generator / Appearance): small-caps pink, mirroring the
   recovered demo's sidebar. Emitted via st.html(), so they read the same --sirin-* vars as the
   native widgets. The more specific class selector wins over the sidebar-wide text-colour rule. */
[data-testid="stSidebar"] .sirin-side-heading {
    margin: 0.85rem 0 0.15rem;
    font-size: 0.6875rem;
    font-weight: 650;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--sirin-hot);
}

/* Panels: chat bubbles, expanders, metrics, alerts, tables, bordered blocks. Flat translucent
   fills — the scrim supplies backdrop contrast; per-panel backdrop blur re-rendered every frame
   while the silk moved, so no panel gets one. */
[data-testid="stChatMessage"], [data-testid="stExpander"], [data-testid="stMetric"],
[data-testid="stAlert"], [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--sirin-surface);
    border: 1px solid var(--sirin-border);
    border-radius: 16px;
    box-shadow: 0 4px 16px var(--sirin-shadow);
    color: var(--sirin-text);
    max-width: 100%;
    min-width: 0;
}

/* Publication/result panels are emitted as inline HTML; keep their geometry under the same cap. */
.sirin-granularity-panel,
[data-testid="stApp"] div[style*="background:var(--sirin-surface);"][style*="border-radius"],
[data-testid="stApp"] div[style*="background:var(--sirin-surface-2);"][style*="border-radius"] {
    border-radius: 16px !important;
}
.sirin-granularity-panel,
[data-testid="stApp"] div[style*="background:var(--sirin-surface);"][style*="box-shadow"],
[data-testid="stApp"] div[style*="background:var(--sirin-surface-2);"][style*="box-shadow"] {
    box-shadow: 0 4px 16px var(--sirin-shadow) !important;
}

/* Expander summary carries a base-theme bg on light; let the glass surface show through */
[data-testid="stExpander"] summary { background: transparent !important; }

/* Inputs / textareas / selects / chat input (incl. native root wrappers + number steppers that
   otherwise keep the base-theme dark bg on the light theme) */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="textarea"],
[data-baseweb="input"], [data-baseweb="base-input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
[data-testid="stNumberInputContainer"],
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"],
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea,
[data-testid="stChatInputContainer"] {
    background: @@input_bg@@ !important;
    border-color: var(--sirin-border) !important;
    color: var(--sirin-text) !important;
    caret-color: var(--sirin-text) !important;
}
input::placeholder, textarea::placeholder { color: var(--sirin-faint) !important; }

/* BaseWeb's value and icon retain the configured base theme unless the descendants are overridden. */
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-baseweb="select"] [aria-selected],
[data-baseweb="select"] input {
    color: var(--sirin-text) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] svg {
    color: var(--sirin-muted) !important;
    fill: var(--sirin-muted) !important;
}
/* Streamlit 1.59 uses React Aria rather than BaseWeb for selectboxes. */
[data-testid="stSelectbox"] .react-aria-ComboBox > [role="group"] {
    background: @@input_bg@@ !important;
    border-color: var(--sirin-border) !important;
}
[data-testid="stSelectbox"] .react-aria-ComboBox > [role="group"] > button {
    background: @@input_bg@@ !important;
    color: var(--sirin-muted) !important;
}
[data-testid="stSelectbox"] button[aria-label="Open"] {
    background: @@input_bg@@ !important;
    color: var(--sirin-muted) !important;
}
[data-testid="stSelectbox"] button[aria-label="Open"] svg {
    color: var(--sirin-muted) !important;
    fill: var(--sirin-muted) !important;
}

/* --- Unified sidebar widgets onto the token palette: consistent radius, accent focus, no dark
   base-theme borders on the light theme (selects, text inputs, the Max tokens stepper, the
   Temperature slider, checkboxes). Every value below is a CSS var or theme token, never a hard colour. */
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] .react-aria-ComboBox > [role="group"],
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
[data-testid="stNumberInputContainer"] {
    border-radius: 10px !important;
}
/* Max tokens +/- steppers: token border + radius and an accent hover, not the base-theme dark chip. */
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {
    border-color: var(--sirin-border) !important;
    color: var(--sirin-muted) !important;
}
[data-testid="stNumberInputStepUp"]:hover, [data-testid="stNumberInputStepDown"]:hover {
    color: var(--sirin-hot) !important;
    background: @@option_hover@@ !important;
}

/* Temperature slider: unfilled track = faint token line; thumb + filled portion follow the pink
   primaryColor (Streamlit theme); the value bubble and min/max ticks read in mono. */
[data-testid="stSlider"] [role="slider"] {
    border-color: var(--sirin-hot) !important;
    box-shadow: 0 0 0 1px var(--sirin-hot) !important;
}
[data-testid="stSlider"] [data-testid="stThumbValue"],
[data-testid="stSlider"] [data-testid="stSliderThumbValue"],
[data-testid="stSliderThumbValue"] {
    color: var(--sirin-hot) !important;
    background: transparent !important;
    font-family: var(--sirin-mono) !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"],
[data-testid="stSliderTickBar"],
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"],
[data-testid="stTickBarMin"], [data-testid="stTickBarMax"] {
    color: var(--sirin-muted) !important;
    font-family: var(--sirin-mono) !important;
}

/* Checkboxes: token-lined box, accent fill when checked (base theme leaves a dark box on light). */
[data-testid="stCheckbox"] [data-baseweb="checkbox"] div[data-checked="false"],
[data-testid="stCheckbox"] label span[aria-hidden="true"] {
    border-color: var(--sirin-border) !important;
    border-radius: 6px !important;
}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] div[data-checked="true"] {
    background-color: var(--sirin-hot) !important;
    border-color: var(--sirin-hot) !important;
}

/* React Aria places the final sidebar menu just below the short viewport. Keep all three
   appearance choices inside Streamlit's clipped app container. */
@media (max-height: 720px) {
    div:has(> [role="listbox"][aria-label="Background motion"]) {
        translate: 0 -32px !important;
    }
}

/* Chat send-button icon follows the theme (native icon is base-theme light => invisible on light) */
[data-testid="stChatInputSubmitButton"] svg { fill: var(--sirin-muted) !important; }

/* Chat input focus = ONE clean ring on the rounded pill. The inner textarea's own offset
   focus outline peeked out as pink corner fragments over the opaque input wrappers (glaring on
   the light theme), so suppress it and ring the pill via :focus-within instead. */
[data-testid="stChatInput"] textarea:focus-visible { outline: none; }
[data-testid="stChatInput"]:focus-within > div {
    border-color: var(--sirin-hot) !important;
    box-shadow: 0 0 0 2px var(--sirin-hot);
}

/* Selectbox / dropdown popover (BaseWeb portal, rendered OUTSIDE stApp). Current BaseWeb nests the
   menu as popover > div > ul with no role="listbox", so target the whole popover/menu subtree. */
[data-baseweb="popover"], [data-baseweb="popover"] > div, [data-baseweb="popover"] ul,
[data-baseweb="menu"], [data-baseweb="menu"] ul, [role="listbox"] {
    background: @@popover_bg@@ !important;
    border-color: var(--sirin-border) !important;
}
[role="option"] { color: var(--sirin-text) !important; background: transparent !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] {
    background: @@option_hover@@ !important;
}

/* Links */
[data-testid="stApp"] a { color: var(--sirin-link); text-underline-offset: 2px; }

/* Buttons */
.stButton > button {
    background: @@btn_bg@@;
    border: 1px solid var(--sirin-border);
    color: var(--sirin-text);
    border-radius: 10px;
    font-weight: 600;
    transition: transform 0.12s ease, background 0.12s ease, border-color 0.12s ease;
}
.stButton > button:hover {
    background: @@btn_hover_bg@@;
    border-color: @@btn_hover_border@@;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* Suggestion pills across the legacy and current Streamlit button-group primitives. */
[data-testid="stPills"] button, [data-testid="stBaseButton-pills"], [data-testid="stPillsItem"],
[data-testid="stButtonGroup"] button[data-variant="pills"] {
    background: @@pill_bg@@ !important;
    border: 1px solid var(--sirin-border) !important;
    color: var(--sirin-text) !important;
    border-radius: 999px !important;
}
[data-testid="stPills"] button *, [data-testid="stBaseButton-pills"] *,
[data-testid="stButtonGroup"] button[data-variant="pills"] * {
    color: var(--sirin-text) !important;
}
[data-testid="stPills"] button svg, [data-testid="stBaseButton-pills"] svg,
[data-testid="stButtonGroup"] button[data-variant="pills"] svg {
    fill: var(--sirin-text) !important;
}
[data-testid="stBaseButton-pills"]:hover { border-color: @@btn_hover_border@@ !important; }
[data-testid="stBaseButton-pills"][aria-checked="true"], [data-testid="stBaseButton-pills"][aria-selected="true"] {
    background: @@pill_selected@@ !important;
    border-color: @@pill_selected_border@@ !important;
}
[data-testid="stButtonGroup"] button[data-variant="pills"][aria-checked="true"],
[data-testid="stButtonGroup"] button[data-variant="pills"][data-selected] {
    background: @@pill_selected@@ !important;
    border-color: @@pill_selected_border@@ !important;
}

/* Segmented controls share Streamlit's button-group primitive, not the pills primitive. */
[data-testid="stBaseButton-segmented_control"] {
    background: @@pill_bg@@ !important;
    border-color: var(--sirin-border) !important;
    color: var(--sirin-text) !important;
}
[data-testid="stBaseButton-segmented_control"] * {
    color: var(--sirin-text) !important;
}
[data-testid="stBaseButton-segmented_controlActive"] {
    background: @@pill_selected@@ !important;
    border-color: @@pill_selected_border@@ !important;
}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {
    background: @@pill_bg@@ !important;
    border-color: var(--sirin-border) !important;
    color: var(--sirin-text) !important;
}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] * {
    color: var(--sirin-text) !important;
}
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"],
[data-testid="stButtonGroup"] button[data-variant="segmented_control"][data-selected] {
    background: @@pill_selected@@ !important;
    border-color: @@pill_selected_border@@ !important;
}

/* Visible keyboard focus everywhere */
:where(button, [role="button"], [role="option"], a, input, textarea, summary,
       [data-baseweb="select"] > div):focus-visible {
    outline: 2px solid var(--sirin-hot);
    outline-offset: 2px;
    border-radius: 10px;
}

/* Themed scrollbars */
* { scrollbar-width: thin; scrollbar-color: @@scroll_thumb@@ transparent; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: @@scroll_thumb2@@;
    border-radius: 999px; border: 2px solid transparent; background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: @@scroll_thumb_hover@@; }

/* Result HTML contains compact inline grids. Collapse them with the Streamlit columns at tablet
   width so provenance, token, and verdict content never imposes a desktop minimum width. */
@media (max-width: 800px) {
    [data-testid="stApp"] { overflow-x: clip; }
    .main .block-container {
        width: 100%;
        max-width: 100%;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 14rem !important;
        width: auto !important;
        min-width: min(100%, 14rem) !important;
    }
    .sirin-paper-title { flex-direction: column !important; }
    .sirin-provenance {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        min-width: 0 !important;
        width: 100%;
    }
    .sirin-demo-grid, .sirin-answer-row, .sirin-memory,
    .sirin-granularity-panel [style*="grid-template-columns"] {
        grid-template-columns: minmax(0, 1fr) !important;
    }
    .sirin-paper-figure, .sirin-panel, .sirin-prov-item, .sirin-granularity-panel,
    .sirin-token-strip, .sirin-heatmap, .sirin-token-evidence {
        max-width: 100% !important;
        min-width: 0 !important;
        overflow-wrap: anywhere;
    }
    .sirin-granularity-panel { padding: 0.75rem !important; }
    .sirin-granularity-panel [style*="justify-content:space-between"] { flex-wrap: wrap; }
    .sirin-token-strip, .sirin-heatmap, .sirin-token-evidence { white-space: normal !important; }
}
</style>"""

# --- theme contract (fail fast on a mis-defined theme) ------------------------------------------
_THEME_PLACEHOLDER_RE = re.compile(r"@@([A-Za-z0-9_]+)@@")
_RUNTIME_KEYS = frozenset(
    {'font', 'mono', 'anim', 'silk'}
)  # injected per-call, not theme tokens


def _validate_theme_contract() -> None:
    """Every theme must define the SAME token set, and every @@placeholder@@ in the template must be
    provided by that set (or by the per-call runtime keys). Runs at import so a partial/typo'd theme
    fails loudly instead of shipping half-styled UI."""
    required = set(THEMES['dark'])
    for name, tokens in THEMES.items():
        if set(tokens) != required:
            missing, extra = required - set(tokens), set(tokens) - required
            raise ValueError(
                f"theme {name!r} key mismatch: missing={sorted(missing)} extra={sorted(extra)}"
            )
    unknown = (
        set(_THEME_PLACEHOLDER_RE.findall(_CSS_TEMPLATE)) - required - _RUNTIME_KEYS
    )
    if unknown:
        raise ValueError(
            f"CSS placeholders no theme/runtime provides: {sorted(unknown)}"
        )


_validate_theme_contract()


@lru_cache(maxsize=None)
def _compiled_css(theme: str, motion: str) -> str:
    """Fully substituted stylesheet for one (theme, motion) pair.

    Cached because the result is constant per process and the base template is large: the token
    substitution pass should run once, not on every Streamlit rerun.
    """
    subs = {
        **THEMES.get(theme, THEMES['dark']),
        'font': _FONT,
        'mono': _MONO,
        'anim': _MOTION.get(motion, _MOTION['subtle']),
        'silk': _SILK_ASSET.get(theme, _SILK_ASSET['light']),
    }
    css = _CSS_TEMPLATE
    for key, value in subs.items():
        css = css.replace(f"@@{key}@@", value)
    unresolved = _THEME_PLACEHOLDER_RE.findall(css)
    if unresolved:
        raise ValueError(f"unresolved theme placeholders: {sorted(set(unresolved))}")
    return css


def inject_global_styles(st, motion: str = 'subtle', theme: str = 'light') -> None:
    """Inject the global stylesheet. ``motion`` is one of 'static' | 'subtle' | 'lively';
    ``theme`` is one of 'dark' | 'light'.

    Streamlit discards the ``<style>`` element unless it is re-emitted on every rerun, so this always
    calls ``st.html``; only the (constant per theme/motion) string build is cached.
    """
    st.html(_compiled_css(theme, motion))
