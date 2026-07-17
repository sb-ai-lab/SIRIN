from types import SimpleNamespace

import pytest

from sirin.inference.model_manager import ModelManager


class _FakeAdapter:
    """Pure-python stand-in for a model adapter — no torch, no GPU."""

    def __init__(self, tag):
        self.tag = tag
        self.loaded = False
        self.unloaded = False

    def load(self):
        self.loaded = True

    def unload(self):
        self.unloaded = True


def test_high_memory_does_not_unload_the_only_active_model(monkeypatch):
    original_models = ModelManager._active_models
    original_config = ModelManager.config
    adapter = SimpleNamespace(load=lambda: None, unload=lambda: None)
    unloaded = []
    adapter.unload = lambda: unloaded.append(True)
    try:
        ModelManager._active_models = {}
        ModelManager.config = SimpleNamespace(
            max_active_models=1,
            auto_unload=True,
            memory_threshold=0.8,
        )
        monkeypatch.setattr(
            ModelManager,
            '_is_gpu_memory_high',
            classmethod(lambda cls: True),
        )

        loaded = ModelManager.load_model(adapter)

        assert loaded is adapter
        assert list(ModelManager._active_models.values()) == [adapter]
        assert unloaded == []
    finally:
        ModelManager._active_models = original_models
        ModelManager.config = original_config


def test_ui_load_generator_memoizes_by_config_and_evicts_previous_local_model(monkeypatch):
    """PR-7: switching HF models routes through ModelManager (max_active=1 -> previous evicted); a
    repeated config returns the same memoized adapter instead of building/loading a second one."""
    from sirin.ui import streamlit_app as ui

    monkeypatch.setenv('SIRIN_UI_MAX_ACTIVE_MODELS', '1')
    monkeypatch.setattr(ModelManager, '_active_models', {})
    monkeypatch.setattr(ui, '_adapter_memo', {})
    built = []

    def fake_new(backend, model_path, device, custom_base_url, api_key):
        adapter = _FakeAdapter(f'{backend}:{model_path}')
        built.append(adapter)
        return adapter

    monkeypatch.setattr(ui, '_new_generator_adapter', fake_new)

    first = ui.load_generator('HF', 'model-a', 'cuda')
    again = ui.load_generator('HF', 'model-a', 'cuda')
    assert again is first  # same config -> memoized instance, not a second build
    assert len(built) == 1
    assert first.loaded  # routed through ModelManager, so the adapter was loaded

    second = ui.load_generator('HF', 'model-b', 'cuda')
    assert second is not first
    assert first.unloaded  # max_active=1 -> the previous local model was evicted (unload hook fired)
    assert second.loaded


def test_ui_api_adapter_skips_the_manager_and_never_evicts_a_local_model(monkeypatch):
    """PR-7: API adapters are cheap/stateless and hold no local VRAM, so acquiring one must not
    register with ModelManager and must not evict a loaded local model."""
    from sirin.ui import streamlit_app as ui

    monkeypatch.setenv('SIRIN_UI_MAX_ACTIVE_MODELS', '1')
    monkeypatch.setattr(ModelManager, '_active_models', {})
    monkeypatch.setattr(ui, '_adapter_memo', {})
    monkeypatch.setattr(
        ui, '_new_generator_adapter', lambda *args: _FakeAdapter(args[0])
    )

    local = ui.load_generator('HF', 'model-a', 'cuda')
    api = ui.load_generator('OpenAI', 'gpt-x', 'cpu')

    assert api not in ModelManager._active_models.values()
    assert local.unloaded is False  # the local model stays resident


def test_exclusive_run_is_not_reentrant():
    """PR-7: exclusive_run still serializes — a second acquisition while one is held fails fast."""
    with ModelManager.exclusive_run():
        with pytest.raises(RuntimeError):
            with ModelManager.exclusive_run():
                pass
