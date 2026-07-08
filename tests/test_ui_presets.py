"""Tests moved from sirin/ui/presets.py demo block."""

import sys
import types

import pytest

from sirin.ui import presets


def test_presets_registry():
    assert presets.PRESETS
    assert list(presets.list_presets())
    for preset in presets.list_presets():
        if 'zero-shot' in preset.name:
            assert preset.requires_checkpoint is False
    assert 'Probing — Answerability TabPFN (checkpoint)' in presets.PRESETS
    assert 'Judge — API Token (zero-shot)' in presets.PRESETS


def test_openai_token_judge_preset_describes_as_token_heatmap(monkeypatch):
    detector = _build_openai_token_judge_with_fakes(monkeypatch)
    info = presets.describe_detector(detector)
    assert info['level'] == 'token'
    assert info['display_mode'] == 'heatmap'


def test_openai_judge_uses_provider_specific_base_url_and_key(monkeypatch):
    detector = _build_openai_token_judge_with_fakes(monkeypatch, provider='OpenAI')

    assert detector.model_adapter.config.base_url == 'https://api.openai.com/v1'
    assert detector.model_adapter.config.api_key == 'openai-key'


def test_openrouter_judge_does_not_use_openai_key(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)

    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        _build_openai_token_judge_with_fakes(
            monkeypatch, provider='OpenRouter', set_provider_key=False
        )


def _build_openai_token_judge_with_fakes(
    monkeypatch, provider='OpenRouter', set_provider_key=True
):
    if provider == 'OpenAI':
        if set_provider_key:
            monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
        monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    else:
        if set_provider_key:
            monkeypatch.setenv('OPENROUTER_API_KEY', 'openrouter-key')
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)

    class FakeAdapter:
        def __init__(self, config):
            self.config = config

    class FakeJudge:
        def __init__(self, config, model_adapter):
            self.config = config
            self.model_adapter = model_adapter

    class FakeConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setitem(sys.modules, 'sirin.detection', types.ModuleType('sirin.detection'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.judging',
        types.SimpleNamespace(TokenOpenAIJudge=FakeJudge),
    )
    monkeypatch.setitem(sys.modules, 'sirin.inference', types.ModuleType('sirin.inference'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.inference.adapters',
        types.SimpleNamespace(OpenAIModelAdapter=FakeAdapter),
    )
    monkeypatch.setitem(sys.modules, 'sirin.models', types.ModuleType('sirin.models'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.detection',
        types.SimpleNamespace(OpenAIJudgeConfig=FakeConfig),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.inference',
        types.SimpleNamespace(OpenAIConfig=FakeConfig),
    )

    return presets._build_openai_token_judge(api_provider=provider)


def test_answerability_preset_uses_env_checkpoint(monkeypatch, tmp_path):
    detector = _build_answerability_with_fakes(monkeypatch, tmp_path / 'env-ckpt')
    assert detector.loaded_path == str(tmp_path / 'env-ckpt')


def test_answerability_preset_has_nonempty_fallback_checkpoint(monkeypatch):
    detector = _build_answerability_with_fakes(monkeypatch, None)
    assert detector.loaded_path.endswith(
        'trust_assistant/checkpoints/probing/answerability_tabpfn/Hiddens_L_TabPFN'
    )


def _build_answerability_with_fakes(monkeypatch, env_value):
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

    class FakeSide:
        LEFT = 'left'

    class FakeConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        'sirin.definitions',
        types.SimpleNamespace(SideType=FakeSide),
    )
    monkeypatch.setitem(sys.modules, 'sirin.detection', types.ModuleType('sirin.detection'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.probing',
        types.SimpleNamespace(SequenceTabPFNProbingDetector=FakeDetector),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.processors',
        types.SimpleNamespace(HiddensProcessor=FakeProcessor),
    )
    monkeypatch.setitem(sys.modules, 'sirin.inference', types.ModuleType('sirin.inference'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.inference.adapters',
        types.SimpleNamespace(HfModelAdapter=FakeAdapter),
    )
    monkeypatch.setitem(sys.modules, 'sirin.models', types.ModuleType('sirin.models'))
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.detection',
        types.SimpleNamespace(
            HiddensProcessorConfig=FakeConfig,
            ProbingDetectorConfig=FakeConfig,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.inference',
        types.SimpleNamespace(HFConfig=FakeConfig, TokenLocatorConfig=FakeConfig),
    )

    return presets._build_probing_answerability(device='cpu')
