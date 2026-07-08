"""Tests moved from sirin/ui/presets.py demo block."""

from sirin.ui import presets


def test_presets_registry():
    assert presets.PRESETS
    assert list(presets.list_presets())
    for preset in presets.list_presets():
        if 'zero-shot' in preset.name:
            assert preset.requires_checkpoint is False
    assert 'Probing — Answerability TabPFN (checkpoint)' in presets.PRESETS


def test_answerability_preset_uses_env_checkpoint(monkeypatch, tmp_path):
    detector = _build_answerability_with_fakes(monkeypatch, tmp_path / 'env-ckpt')
    assert detector.loaded_path == str(tmp_path / 'env-ckpt')


def test_answerability_preset_has_nonempty_fallback_checkpoint(monkeypatch):
    detector = _build_answerability_with_fakes(monkeypatch, None)
    assert detector.loaded_path.endswith(
        'trust_assistant/checkpoints/probing/answerability_tabpfn/Hiddens_L_TabPFN'
    )


def _build_answerability_with_fakes(monkeypatch, env_value):
    import sirin.detection.probing as probing
    import sirin.detection.processors as processors
    import sirin.inference.adapters as adapters

    if env_value is None:
        monkeypatch.delenv('SIRIN_ANSWERABILITY_CKPT', raising=False)
    else:
        monkeypatch.setenv('SIRIN_ANSWERABILITY_CKPT', str(env_value))

    class FakeAdapter:
        def __init__(self, config):
            self.config = config

    class FakeProcessor:
        def __init__(self, config, extractor):
            self.config = config
            self.extractor = extractor

    class FakeDetector:
        def __init__(self, config, feature_processor):
            self.config = config
            self.feature_processor = feature_processor
            self.loaded_path = None

        def load(self, checkpoint_dir):
            self.loaded_path = checkpoint_dir

    monkeypatch.setattr(adapters, 'HfModelAdapter', FakeAdapter)
    monkeypatch.setattr(processors, 'HiddensProcessor', FakeProcessor)
    monkeypatch.setattr(probing, 'SequenceTabPFNProbingDetector', FakeDetector)

    return presets._build_probing_answerability(device='cpu')
