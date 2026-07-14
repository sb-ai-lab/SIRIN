"""Hosted profile (SIRIN_UI_HOSTED=1): API-judge-only presets, OpenRouter-first backends, CPU."""

import pytest

from sirin.ui import presets
from sirin.ui import streamlit_app as ui
from test_streamlit_ui import _SidebarHarness

CENSUS_PRESET = 'Probing — Token Linear · PsiloQA/Qwen3-4B'
QWEN35_PRESET = 'Probing — Token Linear · PsiloQA/Qwen3.5-4B'


@pytest.fixture
def hosted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setenv('SIRIN_UI_HOSTED', '1')


@pytest.fixture
def not_hosted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.delenv('SIRIN_UI_HOSTED', raising=False)


def test_hosted_visible_presets_are_api_judges_only(hosted):
    visible = presets.visible_presets()

    assert visible
    assert all(p.family == 'judge' for p in visible)


def test_visible_presets_equal_list_presets_when_not_hosted(not_hosted):
    assert presets.visible_presets() == presets.list_presets()


def test_hosted_sidebar_defaults_to_judge_span_and_api_backends(hosted):
    harness = _SidebarHarness()

    cfg = ui._sidebar(harness)

    assert cfg['preset_name'] == presets.JUDGE_SPAN_PRESET
    preset_options = dict(harness.selectbox_calls)['Preset']
    assert preset_options[0] == presets.JUDGE_SPAN_PRESET
    assert preset_options.count(presets.JUDGE_SPAN_PRESET) == 1
    backend_options = dict(harness.selectbox_calls)['Backend']
    assert backend_options == ['OpenRouter', 'OpenAI', 'Anthropic']
    assert cfg['backend'] == 'OpenRouter'
    assert cfg['device'] == 'cpu'


def test_hosted_seed_runs_hero_is_qwen35_probe_without_census(hosted):
    from sirin.ui.workspace.seed import build_seed_runs

    runs = build_seed_runs()

    assert runs[-1].setup_snapshot.detector_preset == QWEN35_PRESET
    assert all(r.setup_snapshot.detector_preset != CENSUS_PRESET for r in runs)
    assert any(r.setup_snapshot.detector_family == 'judge' for r in runs)


def test_non_hosted_seed_runs_keep_the_census_hero(not_hosted):
    from sirin.ui.workspace.seed import build_seed_runs

    runs = build_seed_runs()

    assert runs[-1].setup_snapshot.detector_preset == CENSUS_PRESET
    assert any(r.setup_snapshot.detector_preset == QWEN35_PRESET for r in runs)


def test_shared_env_key_serves_only_the_configured_default_model(monkeypatch):
    import pytest

    from sirin.ui.providers import OPENROUTER_PROVIDER, require_shared_key_model

    monkeypatch.setenv('SIRIN_UI_HOSTED', '1')
    monkeypatch.setenv(
        'SIRIN_OPENROUTER_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free'
    )
    # Shared env key + the configured default: allowed (the demo path).
    require_shared_key_model(
        OPENROUTER_PROVIDER, 'nvidia/nemotron-3-super-120b-a12b:free', None
    )
    # Any other model — even another free one — is blocked with actionable copy.
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', None)
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(
            OPENROUTER_PROVIDER, 'qwen/qwen3-8b:free', None
        )
    # A pasted key is the visitor's own: no restriction.
    require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', 'sk-user')


def test_shared_key_guard_is_hosted_only(monkeypatch):
    from sirin.ui.providers import OPENROUTER_PROVIDER, require_shared_key_model

    monkeypatch.delenv('SIRIN_UI_HOSTED', raising=False)
    # Local/campaign use keeps full env-key freedom.
    require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', None)


def test_external_consent_defaults_to_checked():
    import sirin.ui.streamlit_app as ui

    captured = {}

    class _Sidebar:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _St:
        sidebar = _Sidebar()

        @staticmethod
        def checkbox(label, value=None, **kwargs):
            captured['value'] = value
            return value

    confirmed = ui._external_confirmed(
        _St, {'preset_name': 'Judge — API Span (zero-shot)', 'backend': 'OpenRouter'}
    )
    assert captured['value'] is True
    assert confirmed is True
