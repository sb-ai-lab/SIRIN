"""Tests moved from sirin/ui/styles.py demo block."""

from sirin.ui.styles import inject_global_styles


def test_inject_global_styles_substitutes_placeholders():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, motion='subtle')
    captured = stub.calls[0]
    assert isinstance(captured, str) and captured.strip()
    assert '@keyframes sirin-breathe-subtle' in captured
    assert 'url("app/static/silk_bg.jpg")' in captured  # silk served as a static file, not base64
    assert 'stApp' in captured
    assert '@@' not in captured

    stub_static = Stub()
    inject_global_styles(stub_static, motion='static')
    assert 'animation: none' in stub_static.calls[0]


def test_inject_global_styles_light_theme():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, theme='light')
    captured = stub.calls[0]
    assert '@@' not in captured
    assert 'color-scheme: light' in captured

    stub_dark = Stub()
    inject_global_styles(stub_dark, theme='dark')
    assert 'color-scheme: dark' in stub_dark.calls[0]


def test_original_palette_and_motion_defaults_are_preserved():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub)
    captured = stub.calls[0]

    from sirin.ui.styles import _tokens

    tokens = _tokens()
    light = tokens['palette']['light']

    assert 'color-scheme: light' in captured
    assert (
        'animation: sirin-breathe-subtle 45s ease-in-out -22.5s infinite alternate'
        in captured
    )
    assert 'fonts.googleapis.com' not in captured
    assert f"--sirin-font: {tokens['fonts']['sans']}" in captured
    assert f"--sirin-mono: {tokens['fonts']['mono']}" in captured
    assert f"--sirin-hot: {light['brand']}" in captured  # accent, sourced from tokens.json
    assert '#b91b63' not in captured  # the old crimson accent is gone
    assert light['sidebarBg'] in captured
    assert light['optionHover'] in captured


def test_styles_cover_current_streamlit_controls_and_mobile_results():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub)
    captured = stub.calls[0]

    assert '[data-testid="stSelectbox"] [data-baseweb="select"] *' in captured
    assert '.react-aria-ComboBox > [role="group"]' in captured
    assert '[data-testid="stSelectbox"] button[aria-label="Open"]' in captured
    assert '[data-testid="stNumberInputContainer"]' in captured
    assert '[role="listbox"][aria-label="Background motion"]' in captured
    assert 'translate: 0 calc(-100% - 46px)' in captured
    assert '[role="listbox"][aria-label="Theme"]' in captured
    assert '[data-testid="stPills"] button *' in captured
    assert '[data-testid="stButtonGroup"] button[data-variant="pills"] *' in captured
    assert (
        '[data-testid="stButtonGroup"] button[data-variant="segmented_control"] *'
        in captured
    )
    assert '[data-testid="stBaseButton-segmented_control"]' in captured
    assert '[data-testid="stBaseButton-segmented_controlActive"]' in captured
    assert 'button[data-variant="segmented_control"][data-selected]' in captured
    assert '[role="listbox"]' in captured
    assert '@media (max-width: 800px)' in captured
    assert '.sirin-provenance' in captured
    assert '.sirin-granularity-panel [style*="grid-template-columns"]' in captured
    assert 'border-radius: 16px !important' in captured
    assert '0 20px 50px' not in captured
    assert '@media (prefers-reduced-motion: reduce)' in captured
    assert ':focus-visible' in captured


def test_silk_motion_is_compositor_only_with_static_scrim():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, motion='lively', theme='light')
    captured = stub.calls[0]

    # Silk on a dedicated fixed oversized layer, animated by transform only.
    assert '[data-testid="stApp"]::before' in captured
    assert 'inset: -16%' in captured
    assert 'will-change: transform' in captured
    assert 'translate3d' in captured and 'scale(1.09)' in captured
    assert 'background-position' not in captured  # never animated (or even set longhand) again

    # Readability scrim: present, above the silk, and never animated.
    from sirin.ui.styles import _tokens

    assert _tokens()['palette']['light']['scrim'] in captured
    scrim_block = captured.split('[data-testid="stApp"]::after', 1)[1].split('}')[0]
    assert 'animation' not in scrim_block

    # Component-side synchronous switching hooks: host CSS keyed off html[data-sirin-motion].
    for mode in ('static', 'subtle', 'lively'):
        assert f'html[data-sirin-motion="{mode}"] [data-testid="stApp"]::before' in captured
    assert '@media (prefers-reduced-motion: reduce)' in captured


def test_backdrop_filter_fanout_is_eliminated():
    # ZERO blur surfaces: each backdrop blur re-renders every frame over the moving silk (the last
    # one, the sidebar, alone cost 60fps -> 30fps). Panels are flat translucent fills over the scrim.
    assert 'backdrop-filter' not in _host_css('light')
    assert 'backdrop-filter' not in _component_build_css()


def test_component_build_syncs_host_motion_dataset():
    assert 'sirinMotion' in _component_build_text()


def test_component_header_is_compact_not_a_hero_card():
    css = _component_build_css()
    js = _component_build_text()
    # The giant hero card and the in-header appearance cluster are gone.
    assert '.hero-copy' not in css
    assert '.appearance' not in css
    assert 'motion-toggle' not in css
    assert 'Pause motion' not in js and 'Resume motion' not in js
    assert 'Paused' not in js  # the motion alias is dead everywhere
    # Replaced by a flat, compact page header driven by the shared pageTitle type role.
    assert '.page-head' in css
    assert '--text-pageTitle-size' in css


def test_component_runs_grid_is_container_relative_not_viewport():
    css = _component_build_css()
    # 100vw ignored the open sidebar and overflowed horizontally; runs widens via its own container.
    assert '100vw' not in css
    assert '.runs-workspace' in css


def test_component_selects_strip_os_chrome_with_token_chevron():
    css = _component_build_css()
    # The Task / Answer source / outcome-filter selects keep the native element but lose OS chrome
    # (appearance:none) and gain a token chevron rendered in a wrapper span.
    assert 'appearance:none' in css
    assert '.select-wrap' in css
    assert '.select-chevron' in css
    # type=search sheds its OS clear/decoration widgets so it matches the other token fields.
    assert 'webkit-search-cancel-button' in css


def test_component_prompt_disclosure_is_a_summary_row_not_a_disabled_input():
    css = _component_build_css()
    # A rotating chevron + label + mono char count, in the card language — not a flat greyed field.
    assert '.disclosure-chevron' in css
    assert '.disclosure-count' in css
    assert '.prompt-disclosure[open] .disclosure-chevron' in css


def test_host_sidebar_uses_census_section_heading():
    host = _host_css('light')
    assert '.sirin-side-heading' in host
    assert 'text-transform: uppercase' in host


def test_host_unifies_sidebar_slider_stepper_and_checkbox_onto_tokens():
    host = _host_css('light')
    # Temperature slider: accent-ringed thumb, value + ticks in the mono font.
    assert '[data-testid="stSlider"] [role="slider"]' in host
    assert 'stSliderThumbValue' in host
    assert 'stTickBar' in host
    # Max tokens +/- steppers get an accent hover, not a base-theme dark chip.
    assert '[data-testid="stNumberInputStepUp"]:hover' in host
    # Checkboxes fill with the accent when checked.
    assert '[data-testid="stCheckbox"]' in host
    assert 'div[data-checked="true"]' in host
    # Driven purely by tokens — the accent is the pink brand var, never a hard colour.
    assert 'var(--sirin-hot)' in host
    assert 'var(--sirin-mono)' in host


def test_inject_global_styles_keeps_input_caret_visible():
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, theme='light')

    assert 'caret-color: var(--sirin-text)' in stub.calls[0]


def test_theme_contract_holds():
    from sirin.ui import styles

    keysets = [frozenset(t) for t in styles.THEMES.values()]
    assert keysets and all(
        k == keysets[0] for k in keysets
    )  # every theme defines the same tokens
    placeholders = set(styles._THEME_PLACEHOLDER_RE.findall(styles._CSS_TEMPLATE))
    assert placeholders <= (
        keysets[0] | styles._RUNTIME_KEYS
    )  # no orphan @@placeholder@@
    styles._validate_theme_contract()  # real themes pass


def test_theme_contract_rejects_partial_theme(monkeypatch):
    import pytest

    from sirin.ui import styles

    monkeypatch.setitem(
        styles.THEMES, 'bad', {'bg': '#000'}
    )  # missing every other token
    with pytest.raises(ValueError):
        styles._validate_theme_contract()


# --- single design-token source: host + component consume the same tokens.json --------------------
import json  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TOKENS_PATH = _REPO_ROOT / 'sirin' / 'ui' / 'tokens.json'
_FRONTEND_BUILD = _REPO_ROOT / 'sirin' / 'ui' / 'workspace' / 'frontend' / 'build'


def _load_tokens() -> dict:
    return json.loads(_TOKENS_PATH.read_text(encoding='utf-8'))


def _host_css(theme: str) -> str:
    class Stub:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def html(self, s) -> None:
            self.calls.append(s)

    stub = Stub()
    inject_global_styles(stub, theme=theme)
    return stub.calls[0]


def _component_build_css() -> str:
    css = sorted(_FRONTEND_BUILD.glob('style-*.css'))
    assert css, 'frontend build CSS missing; run `npm run build` in the frontend dir'
    return css[0].read_text(encoding='utf-8')


def _component_build_text() -> str:
    js = sorted(_FRONTEND_BUILD.glob('index-*.js'))
    assert js, 'frontend build JS missing; run `npm run build` in the frontend dir'
    return _component_build_css() + '\n' + js[0].read_text(
        encoding='utf-8', errors='replace'
    )


def _token_hexes(tokens: dict) -> set[str]:
    return {h.lower() for h in re.findall(r'#[0-9a-fA-F]{6}', json.dumps(tokens))}


def _six_digit_hexes(text: str) -> set[str]:
    # Vite minifies structural rgba() shadows/scrims into 8-digit alpha hexes (e.g. #3325350f); the
    # negative lookahead keeps only true 6-digit colour values, which is what tokens.json governs.
    return {
        m.group(0).lower()
        for m in re.finditer(r'#[0-9a-fA-F]{6}(?![0-9a-fA-F])', text)
    }


def test_tokens_json_defines_light_and_dark_with_identical_keys():
    palette = _load_tokens()['palette']
    assert set(palette) == {'light', 'dark'}
    assert set(palette['light']) == set(palette['dark'])


def test_host_and_component_consume_identical_palette_values():
    tokens = _load_tokens()
    light = tokens['palette']['light']
    host = _host_css('light')
    component = _component_build_text()

    # The demo core palette (the subset both surfaces consume) must appear verbatim in BOTH.
    for key in ('ink', 'muted', 'faint', 'brand', 'canvas', 'safe', 'line'):
        value = light[key]
        assert value in host, f'{key}={value} missing from host CSS'
        assert value in component, f'{key}={value} missing from component build'

    # One font family everywhere.
    family = tokens['fonts']['sans'].split(',')[0].strip()
    assert family == 'Manrope'
    assert family in host and family in component


def test_component_build_drops_crimson_and_ad_hoc_inks():
    colours = _six_digit_hexes(_component_build_text())
    for gone in ('#b91b63', '#d91a72', '#46394a', '#332535', '#5b4b5e', '#e88c3a', '#e78b3d'):
        assert gone not in colours, f'ad-hoc/crimson ink {gone} still a colour in the build'


def test_emitted_component_css_hexes_all_originate_in_tokens():
    tokens = _load_tokens()
    stray = _six_digit_hexes(_component_build_css()) - _token_hexes(tokens)
    assert not stray, f'component CSS carries hexes absent from tokens.json: {sorted(stray)}'


def test_component_css_font_weights_are_restricted():
    css = _component_build_css()
    weights = {int(w) for w in re.findall(r'font-weight:\s*([0-9]{3})', css)}
    # 200 is only the lower bound of the Manrope variable @font-face range.
    assert weights <= {200, 400, 450, 600, 650}, f'stray weights in component CSS: {weights}'


def test_component_build_emits_hashed_woff2_files_not_base64():
    css = _component_build_css()
    assert 'data:font' not in css
    assert 'format("woff2")' in css
    fonts = list(_FRONTEND_BUILD.glob('Manrope-Variable-*.woff2'))
    assert fonts, 'Manrope woff2 was not emitted as a hashed file'
    assert fonts[0].read_bytes()[:4] == b'wOF2'


def test_live_owl_emits_a_looping_transparent_webp_file_not_base64():
    # The header owl animates on Lively while a run is in flight. It must stay a hashed FILE: dropping
    # the ?url&no-inline suffix re-inlines ~350KB of base64 into the bundle, the same regression the
    # font imports carry that suffix to prevent. Transparency is what lets one owl serve both themes.
    owls = list(_FRONTEND_BUILD.glob('owl_live-*.webp'))
    assert owls, 'owl_live webp was not emitted as a hashed file; run scripts/dev/make_owl_live.py + npm run build'
    data = owls[0].read_bytes()
    assert 'data:image/webp' not in _component_build_text()
    assert data[:4] == b'RIFF' and data[8:12] == b'WEBP'
    assert b'ANIM' in data[:64], 'owl_live is not animated'
    assert data[data.index(b'VP8X') + 8] & 0x10, 'owl_live has no alpha channel; it would box on one theme'
    assert len(data) <= 400 * 1024, 'owl_live exceeds its 400KB budget'


# --- S11: dark environment (theme-conditional silk background, tuned dark scrim, dark asset) --------
_STATIC_DIR = _REPO_ROOT / 'sirin' / 'ui' / 'static'
_ASSETS_DIR = _REPO_ROOT / 'sirin' / 'ui' / 'assets'


def test_host_background_is_theme_conditional_silk():
    # Light paints the bright silk; dark paints its deep plum/indigo twin — never the bright one.
    light, dark = _host_css('light'), _host_css('dark')
    assert 'url("app/static/silk_bg.jpg")' in light
    assert 'url("app/static/silk_bg_dark.jpg")' not in light
    assert 'url("app/static/silk_bg_dark.jpg")' in dark
    assert 'url("app/static/silk_bg.jpg")' not in dark


def test_dark_silk_asset_ships_in_static_and_assets():
    # The dark host CSS references app/static/silk_bg_dark.jpg, so the file must be served + packaged.
    for path in (_STATIC_DIR / 'silk_bg_dark.jpg', _ASSETS_DIR / 'silk_bg_dark.jpg'):
        assert path.exists(), f'missing dark silk asset: {path}'
        assert path.read_bytes()[:3] == b'\xff\xd8\xff', f'{path} is not a JPEG'
        assert path.stat().st_size <= 300 * 1024, f'{path} exceeds the 300KB budget'


def test_dark_scrim_is_tuned_for_the_dark_silk():
    # Over the already-dark silk the scrim is a light near-black radial wash (silk texture shows
    # through), not the heavy 0.72-alpha darkener that was calibrated for the bright light silk.
    dark_scrim = _load_tokens()['palette']['dark']['scrim']
    assert dark_scrim in _host_css('dark')
    assert dark_scrim.startswith('radial-gradient')
    assert '0.72' not in dark_scrim  # the bright-silk darkener is gone
