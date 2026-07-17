import pytest


def test_v2_workspace_is_default_and_mounts_without_loading_models(monkeypatch):
    monkeypatch.delenv('HF_TOKEN', raising=False)
    streamlit_testing = pytest.importorskip('streamlit.testing.v1')

    app = streamlit_testing.AppTest.from_file('sirin/ui/streamlit_app.py').run(
        timeout=60
    )

    assert not app.exception
    state = app.session_state.filtered_state
    assert 'sirin.workspace.v2' in state
    assert 'sirin.workspace.v2.session' in state
    from sirin.ui.workspace.seed import build_seed_runs

    protocol_state = app.session_state['sirin.workspace.v2.session']
    # A fresh faithfulness session lands on the model-free recorded-result seeds (hero probe card plus
    # any present judge / Qwen3.5-4B probe cards), created without loading a model or advancing the
    # engine. The hero probe seed is added last so it stays the selected card.
    expected = len(build_seed_runs(0))
    assert protocol_state.setup_revision == 0
    assert protocol_state.runs_revision == expected
    assert len(protocol_state.runs) == expected
    assert all(run.origin.value == 'recordedResultVerified' for run in protocol_state.runs)
    assert all(run.status.value == 'succeeded' for run in protocol_state.runs)
    hero = protocol_state.runs[-1]
    assert hero.analysis.kind.value == 'span'
    assert hero.setup_snapshot.detector_preset == 'Probing — Token Linear · PsiloQA/Qwen3-4B'
