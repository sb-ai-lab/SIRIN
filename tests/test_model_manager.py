from types import SimpleNamespace

from sirin.inference.model_manager import ModelManager


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
