"""Global styling for the SIRIN Streamlit UI.

A bright, holographic *silk* backdrop (baked gradient, recreated from the design reference — no
external assets) painted on the app's OWN background, with dark frosted-glass panels on top so text
stays readable over the vivid colour. All accent colours live in ``PALETTE`` so the visualizers can
import the same tokens (single source of truth).
"""

import base64
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
:root {
    color-scheme: dark;
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
        radial-gradient(125% 90% at 50% 34%, rgba(13, 8, 25, 0.52), rgba(13, 8, 25, 0.24) 78%),
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
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"], .main .block-container {
    background: transparent;
}

/* Typography */
h1, h2, h3, h4, h5, h6 { color: var(--sirin-text); letter-spacing: -0.01em; }
p, span, li, label, [data-testid="stMarkdownContainer"] { color: var(--sirin-text); }
[data-testid="stCaptionContainer"], small { color: var(--sirin-muted); }

/* Dark-glass sidebar */
[data-testid="stSidebar"] {
    background: rgba(11, 8, 22, 0.86);
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

/* Inputs / textareas / selects / chat input */
input, textarea, [data-baseweb="select"] > div,
[data-testid="stChatInput"] textarea, [data-testid="stChatInputContainer"] {
    background: rgba(12, 8, 24, 0.80) !important;
    border-color: var(--sirin-border) !important;
    color: var(--sirin-text) !important;
}
input::placeholder, textarea::placeholder { color: var(--sirin-faint) !important; }

/* Selectbox / dropdown popover (BaseWeb portal) — was unstyled light chrome on the dark theme */
[data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] ul, ul[role="listbox"] {
    background: rgba(15, 10, 26, 0.97) !important;
    border: 1px solid var(--sirin-border) !important;
    backdrop-filter: blur(16px) saturate(130%);
}
[role="option"] { color: var(--sirin-text) !important; background: transparent !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] {
    background: rgba(229, 98, 168, 0.20) !important;
}

/* Links */
[data-testid="stApp"] a { color: var(--sirin-mint); text-underline-offset: 2px; }

/* Buttons */
.stButton > button {
    background: rgba(124, 84, 145, 0.28);
    border: 1px solid var(--sirin-border);
    color: var(--sirin-text);
    border-radius: 12px;
    font-weight: 600;
    transition: transform 0.12s ease, background 0.12s ease, border-color 0.12s ease;
}
.stButton > button:hover {
    background: rgba(229, 98, 168, 0.32);
    border-color: rgba(229, 98, 168, 0.55);
    transform: translateY(-1px);
}

/* Suggestion pills (empty-state CTA) */
[data-testid="stPills"] button, [data-testid="stPillsItem"] {
    background: rgba(20, 14, 34, 0.66) !important;
    border: 1px solid var(--sirin-border) !important;
    color: var(--sirin-text) !important;
    border-radius: 999px !important;
}
[data-testid="stPills"] button:hover { border-color: rgba(229, 98, 168, 0.55) !important; }
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stPills"] button[aria-selected="true"] {
    background: linear-gradient(135deg, rgba(229, 98, 168, 0.34), rgba(175, 222, 221, 0.24)) !important;
    border-color: rgba(229, 98, 168, 0.6) !important;
}

/* Visible keyboard focus everywhere */
:where(button, [role="button"], [role="option"], a, input, textarea, summary,
       [data-baseweb="select"] > div, [data-testid="stChatInput"] textarea):focus-visible {
    outline: 2px solid var(--sirin-hot);
    outline-offset: 2px;
    border-radius: 8px;
}

/* Themed scrollbars */
* { scrollbar-width: thin; scrollbar-color: rgba(229, 98, 168, 0.5) transparent; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(229, 98, 168, 0.42);
    border-radius: 999px; border: 2px solid transparent; background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: rgba(229, 98, 168, 0.66); }
</style>"""


def glass_css(key: str) -> str:
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


def inject_global_styles(st, motion: str = 'subtle') -> None:
    """Inject the global stylesheet. ``motion`` is one of 'static' | 'subtle' | 'lively'."""
    subs = {
        'bg': PALETTE['bg'], 'surface': PALETTE['surface'], 'surface_2': PALETTE['surface_2'],
        'border': PALETTE['border'], 'text': PALETTE['text'], 'muted': PALETTE['muted'],
        'faint': PALETTE['faint'], 'shadow': PALETTE['shadow'], 'hot': PALETTE['hot'],
        'mint': PALETTE['mint'], 'accent': PALETTE['accent'],
        'font': _FONT, 'mono': _MONO,
        'anim': _MOTION.get(motion, _MOTION['subtle']),
        'b64': _SILK_JPEG_B64,
    }
    css = _CSS_TEMPLATE
    for key, value in subs.items():
        css = css.replace(f"@@{key}@@", value)
    st.html(css)
