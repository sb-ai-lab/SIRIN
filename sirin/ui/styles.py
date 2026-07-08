"""Global styling for the SIRIN Streamlit UI.

A bright, holographic *silk* backdrop (baked gradient, recreated from the design reference — no
external assets) painted on the app's OWN background, with dark frosted-glass panels on top so text
stays readable over the vivid colour. All accent colours live in ``PALETTE`` so the visualizers can
import the same tokens (single source of truth).
"""

import base64
import re
from pathlib import Path

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
    'hot': '#e562a8',
    'sheen': '#e8ebed',
    # --- app surfaces (dark glass over the bright backdrop) ---
    'bg': '#0d0819',
    'surface': 'rgba(20, 14, 34, 0.86)',        # dense enough to stay dark over bright silk
    'surface_2': 'rgba(15, 10, 26, 0.72)',
    'border': 'rgba(255, 255, 255, 0.14)',
    'text': '#f4f0fb',
    'muted': '#c3b8dc',
    'faint': '#9086ab',
    'shadow': 'rgba(0, 0, 0, 0.50)',
    # --- semantic tokens (results; readable on dark glass) ---
    'risk': '#ff6b9a',        # flagged / high score
    'ok': '#4fd6b8',          # clear / low score
    'track': 'rgba(148, 163, 184, 0.24)',
    'accent': '#e562a8',
}

# Theme-varying tokens (dark == today's literals, byte-for-byte; light == frosted-light variant).
# hot/mint/accent are identical in both themes, so they stay sourced from PALETTE instead.
THEMES: dict[str, dict[str, str]] = {
    'dark': {
        'color_scheme': 'dark',
        'bg': PALETTE['bg'], 'surface': PALETTE['surface'], 'surface_2': PALETTE['surface_2'],
        'border': PALETTE['border'], 'text': PALETTE['text'], 'muted': PALETTE['muted'],
        'faint': PALETTE['faint'], 'shadow': PALETTE['shadow'], 'link': '#afdedd',
        'scrim1': 'rgba(13, 8, 25, 0.52)', 'scrim2': 'rgba(13, 8, 25, 0.24)',
        'sidebar_bg': 'rgba(11, 8, 22, 0.86)', 'input_bg': 'rgba(12, 8, 24, 0.80)',
        'popover_bg': 'rgba(15, 10, 26, 0.97)', 'option_hover': 'rgba(229, 98, 168, 0.20)',
        'btn_bg': 'rgba(124, 84, 145, 0.28)', 'btn_hover_bg': 'rgba(229, 98, 168, 0.32)',
        'btn_hover_border': 'rgba(229, 98, 168, 0.55)', 'pill_bg': 'rgba(20, 14, 34, 0.66)',
        'pill_selected': 'linear-gradient(135deg, rgba(229, 98, 168, 0.34), rgba(175, 222, 221, 0.24))',
        'pill_selected_border': 'rgba(229, 98, 168, 0.6)',
        'scroll_thumb': 'rgba(229, 98, 168, 0.5)', 'scroll_thumb2': 'rgba(229, 98, 168, 0.42)',
        'scroll_thumb_hover': 'rgba(229, 98, 168, 0.66)',
        'hot': PALETTE['hot'], 'mint': PALETTE['mint'], 'accent': PALETTE['accent'],
    },
    'light': {
        'color_scheme': 'light',
        'bg': '#eae6f2', 'surface': 'rgba(255, 255, 255, 0.72)', 'surface_2': 'rgba(255, 255, 255, 0.58)',
        'border': 'rgba(30, 18, 45, 0.16)', 'text': '#1a1226', 'muted': '#5a4d70',
        'faint': '#8a7fa0', 'shadow': 'rgba(80, 60, 110, 0.18)', 'link': '#0d8f7d',
        'scrim1': 'rgba(248, 246, 252, 0.66)', 'scrim2': 'rgba(248, 246, 252, 0.40)',
        'sidebar_bg': 'rgba(255, 255, 255, 0.80)', 'input_bg': 'rgba(255, 255, 255, 0.86)',
        'popover_bg': 'rgba(252, 250, 255, 0.98)', 'option_hover': 'rgba(229, 98, 168, 0.16)',
        'btn_bg': 'rgba(152, 106, 170, 0.16)', 'btn_hover_bg': 'rgba(229, 98, 168, 0.20)',
        'btn_hover_border': 'rgba(229, 98, 168, 0.50)', 'pill_bg': 'rgba(255, 255, 255, 0.70)',
        'pill_selected': 'linear-gradient(135deg, rgba(229, 98, 168, 0.22), rgba(79, 214, 184, 0.18))',
        'pill_selected_border': 'rgba(229, 98, 168, 0.55)',
        'scroll_thumb': 'rgba(152, 106, 170, 0.50)', 'scroll_thumb2': 'rgba(152, 106, 170, 0.42)',
        'scroll_thumb_hover': 'rgba(152, 106, 170, 0.66)',
        'hot': PALETTE['hot'], 'mint': PALETTE['mint'], 'accent': PALETTE['accent'],
    },
}

# Baked holographic-silk background, JPEG bytes (chosen candidate "Aurora Silk — Balanced").
# Recreated procedurally from the reference (no stock imagery).
_SILK_JPEG_PATH = Path(__file__).parent / 'assets' / 'silk_bg.jpg'
_SILK_JPEG_B64 = base64.b64encode(_SILK_JPEG_PATH.read_bytes()).decode()

_FONT = "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
_MONO = "'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

# Motion presets — animate ONLY background-position/size (transform/filter on stApp bleed onto content).
_MOTION = {
    'static': 'none',
    'subtle': 'sirin-drift-subtle 60s ease-in-out infinite',
    'lively': 'sirin-drift-lively 30s ease-in-out infinite',
}

_CSS_TEMPLATE = """<style>
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

/* Holographic silk on the app's OWN background (always behind content). A soft, uneven scrim keeps
   on-backdrop text readable while the bright silk still shows through the page margins. Motion is
   background-position/size drift only. */
[data-testid="stApp"] {
    background-color: var(--sirin-bg);
    background-image:
        radial-gradient(125% 90% at 50% 34%, @@scrim1@@, @@scrim2@@ 78%),
        url("data:image/jpeg;base64,@@b64@@");
    background-repeat: no-repeat;
    background-position: center, 50% 50%;
    background-size: cover, 132% 132%;
    background-attachment: fixed, fixed;
    animation: @@anim@@;
}

@keyframes sirin-drift-subtle {
    0%, 100% { background-position: center, 44% 47%; background-size: cover, 132% 132%; }
    50%      { background-position: center, 56% 53%; background-size: cover, 140% 140%; }
}
@keyframes sirin-drift-lively {
    0%, 100% { background-position: center, 38% 43%; background-size: cover, 132% 132%; }
    50%      { background-position: center, 63% 57%; background-size: cover, 152% 152%; }
}
@media (prefers-reduced-motion: reduce) {
    [data-testid="stApp"] { animation: none !important; }
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

/* Dark-glass sidebar */
[data-testid="stSidebar"] {
    background: @@sidebar_bg@@;
    border-right: 1px solid var(--sirin-border);
    backdrop-filter: blur(20px) saturate(135%);
    -webkit-backdrop-filter: blur(20px) saturate(135%);
}
[data-testid="stSidebar"] * { color: var(--sirin-text); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: var(--sirin-text) !important; opacity: 0.96;
}

/* Glass panels: chat bubbles, expanders, metrics, alerts, tables, bordered blocks */
[data-testid="stChatMessage"], [data-testid="stExpander"], [data-testid="stMetric"],
[data-testid="stAlert"], [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--sirin-surface);
    border: 1px solid var(--sirin-border);
    border-radius: 16px;
    box-shadow: 0 20px 50px var(--sirin-shadow);
    backdrop-filter: blur(18px) saturate(135%);
    -webkit-backdrop-filter: blur(18px) saturate(135%);
    color: var(--sirin-text);
}

/* Expander summary carries a base-theme bg on light; let the glass surface show through */
[data-testid="stExpander"] summary { background: transparent !important; }

/* Inputs / textareas / selects / chat input (incl. native root wrappers + number steppers that
   otherwise keep the base-theme dark bg on the light theme) */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="textarea"],
[data-baseweb="input"], [data-baseweb="base-input"],
[data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"],
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"],
[data-testid="stChatInput"], [data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea,
[data-testid="stChatInputContainer"] {
    background: @@input_bg@@ !important;
    border-color: var(--sirin-border) !important;
    color: var(--sirin-text) !important;
}
input::placeholder, textarea::placeholder { color: var(--sirin-faint) !important; }

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
[data-baseweb="menu"], [data-baseweb="menu"] ul {
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
    border-radius: 12px;
    font-weight: 600;
    transition: transform 0.12s ease, background 0.12s ease, border-color 0.12s ease;
}
.stButton > button:hover {
    background: @@btn_hover_bg@@;
    border-color: @@btn_hover_border@@;
    transform: translateY(-1px);
}

/* Suggestion pills (empty-state CTA) — stBaseButton-pills is the actual per-pill button testid */
[data-testid="stPills"] button, [data-testid="stBaseButton-pills"], [data-testid="stPillsItem"] {
    background: @@pill_bg@@ !important;
    border: 1px solid var(--sirin-border) !important;
    color: var(--sirin-text) !important;
    border-radius: 999px !important;
}
[data-testid="stBaseButton-pills"]:hover { border-color: @@btn_hover_border@@ !important; }
[data-testid="stBaseButton-pills"][aria-checked="true"], [data-testid="stBaseButton-pills"][aria-selected="true"] {
    background: @@pill_selected@@ !important;
    border-color: @@pill_selected_border@@ !important;
}

/* Visible keyboard focus everywhere */
:where(button, [role="button"], [role="option"], a, input, textarea, summary,
       [data-baseweb="select"] > div):focus-visible {
    outline: 2px solid var(--sirin-hot);
    outline-offset: 2px;
    border-radius: 8px;
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
</style>"""

# --- theme contract (fail fast on a mis-defined theme) ------------------------------------------
_THEME_PLACEHOLDER_RE = re.compile(r"@@([A-Za-z0-9_]+)@@")
_RUNTIME_KEYS = frozenset({'font', 'mono', 'anim', 'b64'})  # injected per-call, not theme tokens


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
    unknown = set(_THEME_PLACEHOLDER_RE.findall(_CSS_TEMPLATE)) - required - _RUNTIME_KEYS
    if unknown:
        raise ValueError(f"CSS placeholders no theme/runtime provides: {sorted(unknown)}")


_validate_theme_contract()


def glass_css(key: str) -> str:
    # ponytail: dead code, dark-only (reads PALETTE directly); wire through THEMES if it goes live.
    # keys are caller-owned Streamlit keys; sanitize here if they ever come from users.
    return f""".st-key-{key} {{
    background: {PALETTE['surface']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    box-shadow: 0 20px 50px {PALETTE['shadow']};
    backdrop-filter: blur(18px) saturate(135%);
    -webkit-backdrop-filter: blur(18px) saturate(135%);
    color: {PALETTE['text']};
}}"""


def inject_global_styles(st, motion: str = 'subtle', theme: str = 'dark') -> None:
    """Inject the global stylesheet. ``motion`` is one of 'static' | 'subtle' | 'lively';
    ``theme`` is one of 'dark' | 'light'."""
    subs = {
        **THEMES.get(theme, THEMES['dark']),
        'font': _FONT, 'mono': _MONO,
        'anim': _MOTION.get(motion, _MOTION['subtle']),
        'b64': _SILK_JPEG_B64,
    }
    css = _CSS_TEMPLATE
    for key, value in subs.items():
        css = css.replace(f"@@{key}@@", value)
    unresolved = _THEME_PLACEHOLDER_RE.findall(css)
    if unresolved:
        raise ValueError(f"unresolved theme placeholders: {sorted(set(unresolved))}")
    st.html(css)
