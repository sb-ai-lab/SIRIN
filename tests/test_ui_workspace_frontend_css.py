"""Guard the built workspace-component CSS for the graded-span (S7) contract.

The span gradation and risk footer are rendered by the compiled component, so the assertions read the
built stylesheet (sirin/ui/workspace/frontend/build/style-*.css) rather than the React source.
"""

from pathlib import Path

import pytest

import sirin.ui.workspace as workspace


def _built_css() -> str:
    build_dir = Path(workspace.__file__).parent / 'frontend' / 'build'
    sheets = sorted(build_dir.glob('style-*.css'))
    if not sheets:
        pytest.skip('workspace frontend is not built (run npm run build)')
    return '\n'.join(sheet.read_text(encoding='utf-8') for sheet in sheets)


def test_graded_span_and_footer_classes_present():
    css = _built_css()
    for token in (
        '.evidence.graded',
        '.evidence-badge',
        '.evidence.below',
        '.span-footer',
        '.span-verdict-dot',
        '.span-legend-bar',
    ):
        assert token in css, f'missing {token} in built component CSS'


def test_footer_bar_lerps_between_span_ramp_endpoints():
    css = _built_css()
    assert '--span-line-low' in css and '--span-line-high' in css
    # The graded badge inherits the per-span underline colour via the inline --seg-line custom property.
    assert '--seg-line' in css


def test_forced_colors_keeps_suspect_text_fallback():
    css = _built_css()
    assert '.evidence.graded:after' in css or '.evidence.graded::after' in css
    assert '[suspect]' in css


def test_old_binary_evidence_classes_are_gone():
    css = _built_css()
    assert '.evidence.scored' not in css
    assert '.evidence.suspect' not in css


def test_reveal_choreography_classes_and_keyframes_present():
    css = _built_css()
    for token in (
        '.result-card.is-reveal',
        '.is-peak',
        '--reveal-total',
        '--seg-wash',
        '@keyframes seg-wash',
        '@keyframes seg-line',
        '@keyframes seg-fade',
        '@keyframes seg-pulse',
    ):
        assert token in css, f'missing {token} in built reveal CSS'


def test_reveal_wash_sweeps_background_size_and_staggers_per_span():
    css = _built_css()
    # The graded span starts collapsed (0% wash) and animates the wash/underline keyframes...
    assert 'background-size:0% 100%' in css
    assert 'seg-wash' in css and 'seg-line' in css
    # ...staggered off the inline --d custom property (240 + i*180ms), and the footer waits for --reveal-total.
    assert 'var(--d' in css
    assert 'animation-delay:var(--reveal-total' in css


def test_subtle_scales_reveal_and_lively_adds_single_peak_pulse():
    css = _built_css()
    # Subtle keeps the stagger but runs at 0.7x duration via --rv.
    assert '[data-motion=subtle] .result-card.is-reveal{--rv: .7}' in css
    # Lively adds one soft pulse, scoped to the highest-risk (peak) span only.
    assert '@keyframes seg-pulse' in css
    assert '[data-motion=lively] .result-card.is-reveal .evidence.graded.is-peak' in css


def test_reveal_collapses_to_end_state_under_static_and_reduced_motion():
    css = _built_css()
    # Static defence-in-depth: settle the wash/underline instantly (belt-and-braces to the component
    # also withholding .is-reveal in Static).
    assert '[data-motion=static] .result-card.is-reveal .evidence.graded{background-size:100% 100%' in css
    # Reduced motion forces the finished state and removes the pulse ring entirely.
    assert 'background-size:100% 100%!important' in css
    assert 'is-peak:before{display:none!important' in css


def test_busy_orbit_spinner_replaced_by_skeleton_status():
    css = _built_css()
    # The orbit spinner and its keyframe are gone; the busy card is now a status + shimmer skeleton.
    assert 'orbit' not in css
    assert '.activity-status' in css
    assert 'shimmer' in css
