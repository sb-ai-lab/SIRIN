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
    protocol_state = app.session_state['sirin.workspace.v2.session']
    # A fresh faithfulness session lands on the model-free recorded-result seed: one terminal run,
    # created without loading a model, reserving, or advancing the engine.
    assert protocol_state.setup_revision == 0
    assert protocol_state.runs_revision == 1
    assert len(protocol_state.runs) == 1
    seed = protocol_state.runs[0]
    assert seed.origin.value == 'recordedResultVerified'
    assert seed.status.value == 'succeeded'
    assert seed.analysis.kind.value == 'span'
