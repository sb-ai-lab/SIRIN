"""Tests moved from sirin/ui/presets.py demo block."""

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

from sirin.ui import presets


def test_presets_registry():
    assert presets.PRESETS
    assert list(presets.list_presets())
    for preset in presets.list_presets():
        assert preset.task in {'hallucination', 'answerability'}
        if 'zero-shot' in preset.name:
            assert preset.requires_checkpoint is False
    assert 'Probing — Answerability TabPFN (checkpoint)' in presets.PRESETS
    assert 'Judge — API Token (zero-shot)' in presets.PRESETS


def test_hf_adapter_reuses_hidden_state_capability_across_hot_reload():
    class ReloadedAdapter:
        def generate_hiddens(self):
            pass

    adapter = ReloadedAdapter()

    assert presets._hf_adapter('cuda', adapter) is adapter


def test_psiloqa_token_probe_uses_locked_model_and_manifest_layer_threshold(
    monkeypatch, tmp_path
):
    revision = '1cfa9a7208912126459214e8b04321603b3df60c'
    (tmp_path / 'manifest.json').write_text(
        json.dumps(
            {
                'schema_version': 1,
                'detector': 'token_linear_probe',
                'model_id': 'Qwen/Qwen3-4B',
                'model_revision': revision,
                'hidden_state_index': 18,
                'use_chat_template': False,
                'threshold': 0.5417775511741638,
                'threshold_method': 'validation_f1_optimal',
                'score_semantics': 'sigmoid_score_not_calibrated_probability',
                'checkpoint_format': 'sirin_token_linear_v1',
                'files': {},
            }
        )
    )

    detector = _build_psiloqa_token_probe_with_fakes(monkeypatch, tmp_path)

    adapter_cfg = detector.feature_processor.extractor.config
    processor_cfg = detector.feature_processor.config
    assert adapter_cfg.model_path == 'Qwen/Qwen3-4B'
    assert adapter_cfg.revision == revision
    assert adapter_cfg.use_chat_template is False
    assert processor_cfg.layers == [18]
    assert processor_cfg.cache_features is False
    assert detector.threshold == pytest.approx(0.5417775511741638)
    assert presets.describe_detector(detector)['display_mode'] == 'threshold-spans'


def _build_psiloqa_token_probe_with_fakes(monkeypatch, checkpoint_dir):
    class Config:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Adapter:
        def __init__(self, config):
            self.config = config

    class Processor:
        def __init__(self, config, extractor):
            self.config, self.extractor = config, extractor

    class Detector:
        def __init__(self, config, feature_processor):
            self.config, self.feature_processor = config, feature_processor
            self.threshold = 0.5

        def load(self, checkpoint_dir):
            self.loaded_path = checkpoint_dir

    monkeypatch.setitem(
        sys.modules, 'sirin.definitions', types.SimpleNamespace(SideType=types.SimpleNamespace(RIGHT='right'))
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.probing',
        types.SimpleNamespace(TokenLinearProbingDetector=Detector),
    )
    monkeypatch.setitem(
        sys.modules, 'sirin.detection.processors', types.SimpleNamespace(HiddensProcessor=Processor)
    )
    monkeypatch.setitem(
        sys.modules, 'sirin.inference.adapters', types.SimpleNamespace(HfModelAdapter=Adapter)
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.detection',
        types.SimpleNamespace(HiddensProcessorConfig=Config, ProbingDetectorConfig=Config),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.inference',
        types.SimpleNamespace(HFConfig=Config, TokenLocatorConfig=Config),
    )
    return presets._build_probing_token_linear_psiloqa(
        device='cuda:3', checkpoint_dir=str(checkpoint_dir)
    )


def test_openai_token_judge_preset_describes_as_token_heatmap(monkeypatch):
    detector = _build_openai_token_judge_with_fakes(monkeypatch)
    info = presets.describe_detector(detector)
    assert info['level'] == 'token'
    assert info['display_mode'] == 'heatmap'


def test_openai_token_judge_uses_span_tag_prompts(monkeypatch):
    detector = _build_openai_token_judge_with_fakes(monkeypatch)
    prompts = importlib.import_module('sirin.detection.judging.judges.utils.prompts')

    # The token judge must ship the span-annotation prompts, not the 0/1 verdict prompt (which
    # emitted no [SPAN] tags -> silent all-clear). These are the exact constants the judge parses.
    assert detector.config.system_prompt == prompts.SPAN_TAG_SYSTEM_PROMPT
    assert detector.config.user_prompt == prompts.SPAN_TAG_USER_PROMPT
    assert detector.config.user_prompt is not presets._JUDGE_PROMPT
    assert '[SPAN]' in prompts.SPAN_TAG_SYSTEM_PROMPT
    assert '[/SPAN]' in prompts.SPAN_TAG_SYSTEM_PROMPT
    assert '{sample}' in prompts.SPAN_TAG_USER_PROMPT
    # temperature > 0 so the sampled generations differ (consensus needs diversity).
    assert detector.config.temperature == 0.7


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
    # The builder imports the real span-tag prompt constants from this submodule; cache the real
    # module so it survives the fake `sirin.detection.judging` namespace registered below.
    importlib.import_module('sirin.detection.judging.judges.utils.prompts')
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

    monkeypatch.setitem(
        sys.modules, 'sirin.detection', types.ModuleType('sirin.detection')
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.judging',
        types.SimpleNamespace(TokenOpenAIJudge=FakeJudge),
    )
    monkeypatch.setitem(
        sys.modules, 'sirin.inference', types.ModuleType('sirin.inference')
    )
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
    assert detector.config.device == 'cpu'
    assert presets.describe_detector(detector)['task'] == 'answerability'


def test_answerability_preset_has_nonempty_fallback_checkpoint(monkeypatch):
    detector = _build_answerability_with_fakes(monkeypatch, None)
    assert detector.loaded_path.endswith(
        'trust_assistant/checkpoints/probing/answerability_tabpfn/Hiddens_L_TabPFN'
    )
    assert detector.config.device == 'cpu'


def test_sequence_tabpfn_setup_model_passes_device(monkeypatch):
    from sirin.detection.probing.detectors.sequence import tabpfn
    from sirin.models.detection import ProbingDetectorConfig

    calls = []

    class FakeTabPFN:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    detector = object.__new__(tabpfn.SequenceTabPFNProbingDetector)
    detector.config = ProbingDetectorConfig(
        checkpoint_path='/tmp/model.tabpfn', device='cpu'
    )
    detector.device = 'cpu'
    monkeypatch.setattr(tabpfn, 'TabPFNClassifier', FakeTabPFN)

    detector.setup_model()

    assert calls == [
        {
            'model_path': '/tmp/model.tabpfn',
            'device': 'cpu',
            'random_state': 42,
        }
    ]


def test_sequence_tabpfn_preset_matches_hiddens_r_checkpoint_shape(
    monkeypatch, tmp_path
):
    detector = _build_sequence_tabpfn_with_fakes(
        monkeypatch, tmp_path / 'ckpt', device='cuda:2'
    )
    profile = json.loads(
        (
            Path(presets.__file__).parent / 'assets' / 'longmemeval_qwen35.json'
        ).read_text()
    )
    contract = profile['probing']['hallucination_strict']
    preset_name = 'Probing — Sequence TabPFN (checkpoint)'

    assert profile['ui']['default_preset'] == next(iter(presets.PRESETS)) == preset_name
    processor_cfg = detector.feature_processor.config
    assert processor_cfg.layers == contract['layers'] == [20, 35, 36, 37, 38, 39]
    assert processor_cfg.side == contract['side'].lower() == 'right'
    assert processor_cfg.pooling_type == contract['pooling_type'] == 'mean'
    assert processor_cfg.token_locator_config.locate_answer_start is True
    assert contract['checkpoint_feature_shape'] == [6, 1, 2048]
    assert detector.config.max_length == 1
    assert detector.config.device == 'cuda:2'
    assert detector.loaded_path == str(tmp_path / 'ckpt')
    info = presets.describe_detector(detector)
    assert info['task'] == 'hallucination'
    assert info['calibrated'] is False


def test_sequence_tabpfn_preflight_rejects_model_hidden_size_mismatch(
    monkeypatch, tmp_path
):
    import joblib

    class FakeConfig:
        @staticmethod
        def to_dict():
            return {'text_config': {'hidden_size': 2560}}

    class FakeAutoConfig:
        @staticmethod
        def from_pretrained(model_path, trust_remote_code=True):
            return FakeConfig()

    monkeypatch.setitem(
        sys.modules,
        'transformers',
        types.SimpleNamespace(AutoConfig=FakeAutoConfig),
    )
    joblib.dump(
        {'feature_shapes': [(327, 6, 1, 2048)]}, tmp_path / 'compressor_config.joblib'
    )

    error = presets.sequence_tabpfn_checkpoint_shape_error(
        str(tmp_path),
        'Qwen/Qwen3.5-4B',
    )

    assert error.startswith('Checkpoint/model mismatch before generation')
    assert 'expects hidden size 2048' in error
    assert 'has hidden size 2560' in error


def _build_sequence_tabpfn_with_fakes(monkeypatch, checkpoint_dir, device='cpu'):
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
        RIGHT = 'right'

    class FakeConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        'sirin.definitions',
        types.SimpleNamespace(SideType=FakeSide),
    )
    monkeypatch.setitem(
        sys.modules, 'sirin.detection', types.ModuleType('sirin.detection')
    )
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
    monkeypatch.setitem(
        sys.modules, 'sirin.inference', types.ModuleType('sirin.inference')
    )
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

    return presets._build_probing_sequence_tabpfn(
        device=device,
        checkpoint_dir=str(checkpoint_dir),
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
    monkeypatch.setitem(
        sys.modules, 'sirin.detection', types.ModuleType('sirin.detection')
    )
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
    monkeypatch.setitem(
        sys.modules, 'sirin.inference', types.ModuleType('sirin.inference')
    )
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
