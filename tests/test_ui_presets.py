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
    assert 'Judge — API Span (zero-shot)' in presets.PRESETS


def test_every_preset_declares_an_honest_score_meaning():
    """Guard: a preset whose declared family/level/calibration yields no honest score meaning
    (UNAVAILABLE) is a card that cannot state what its score means. Every current preset must map to
    a real semantics, so a future preset with a meaningless score fails here instead of shipping."""
    from sirin.ui.workspace.contracts import ScoreSemantics, derive_score_semantics

    for preset in presets.list_presets():
        semantics = derive_score_semantics(
            calibrated=preset.calibrated,
            family=preset.family,
            level=preset.level,
        )
        assert semantics is not ScoreSemantics.UNAVAILABLE, preset.name


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


def test_psiloqa_qwen35_token_probe_uses_its_own_model_and_manifest(
    monkeypatch, tmp_path
):
    revision = presets.PSILOQA_QWEN35_MODEL_REVISION
    (tmp_path / 'manifest.json').write_text(
        json.dumps(
            {
                'schema_version': 1,
                'detector': 'token_linear_probe',
                'model_id': 'Qwen/Qwen3.5-4B',
                'model_revision': revision,
                'hidden_state_index': 16,
                'use_chat_template': False,
                'threshold': 0.3850546181201934,
                'threshold_method': 'validation_f1_optimal',
                'score_semantics': 'sigmoid_score_not_calibrated_probability',
                'checkpoint_format': 'sirin_token_linear_v1',
                'files': {},
            }
        )
    )

    detector = _build_psiloqa_token_probe_with_fakes(
        monkeypatch, tmp_path, builder=presets._build_probing_token_linear_psiloqa_qwen35
    )

    adapter_cfg = detector.feature_processor.extractor.config
    assert adapter_cfg.model_path == 'Qwen/Qwen3.5-4B'
    assert adapter_cfg.revision == revision
    assert adapter_cfg.use_chat_template is False
    assert detector.feature_processor.config.layers == [16]
    assert detector.threshold == pytest.approx(0.3850546181201934)


def test_psiloqa_qwen35_preset_is_selectable_not_default_and_pins_qwen3():
    # Present and selectable, but the TabPFN default still leads the registry order.
    assert presets.PSILOQA_TOKEN_LINEAR_PRESET_QWEN35 in presets.PRESETS
    assert next(iter(presets.PRESETS)) == 'Probing — Sequence TabPFN (checkpoint)'
    # The Qwen3-4B landing-seed constants are untouched by the second preset.
    assert presets.PSILOQA_MODEL_ID == 'Qwen/Qwen3-4B'
    assert presets.PSILOQA_MODEL_REVISION == '1cfa9a7208912126459214e8b04321603b3df60c'


def test_psiloqa_qwen35_census_caption_reports_layer_threshold_and_sha():
    preset = presets.PRESETS[presets.PSILOQA_TOKEN_LINEAR_PRESET_QWEN35]
    caption = presets.detector_census_caption(preset)
    # Real bundled checkpoint: layer 16, τ = 0.39 (0.385…), SHA-256 provenance.
    assert 'layer 16' in caption
    assert 'τ = 0.39' in caption
    assert 'SHA-256-pinned checkpoint' in caption


def test_psiloqa_qwen35_manifest_rejects_a_wrong_model_checkpoint():
    # Strict as the Qwen3-4B loader: the bundled Qwen3.5-4B checkpoint fails the default expectations.
    with pytest.raises(ValueError, match='model_id'):
        presets.load_psiloqa_probe_manifest(presets.PSILOQA_QWEN35_CHECKPOINT_DIR)


def _build_psiloqa_token_probe_with_fakes(
    monkeypatch, checkpoint_dir, builder=None
):
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
    builder = builder or presets._build_probing_token_linear_psiloqa
    return builder(device='cuda:3', checkpoint_dir=str(checkpoint_dir))


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
    # 3 samples (campaign protocol), not the config default 5: halves per-click cost on providers
    # that ignore n>1 (each vote is one request on OpenRouter free routes).
    assert detector.config.num_beams == 3


def test_sequence_judge_prompt_embeds_dialogue_via_sample_placeholder(monkeypatch):
    from sirin.detection.judging.judges.utils.prompts import build_prompt_messages
    from sirin.models.detection import OpenAIJudgeConfig

    detector = _build_openai_sequence_judge_with_fakes(monkeypatch)

    # The preset must ship the {sample} slot; without it build_prompt_messages drops the dialogue and
    # the judge scores an empty conversation.
    assert '{sample}' in detector.config.user_prompt
    # Single-digit format clause guards token 0 against a JSON '{' collapse under max_tokens=1.
    assert 'SINGLE character' in detector.config.user_prompt

    # A formatted message must actually embed the dialogue text (real formatter, real config defaults).
    config = OpenAIJudgeConfig(user_prompt=presets._JUDGE_PROMPT, temperature=0.0)
    sample = [
        {'role': 'user', 'content': 'Where is the Eiffel Tower?'},
        {'role': 'assistant', 'content': 'The Eiffel Tower is in Berlin.'},
    ]
    messages = build_prompt_messages(config, [sample])
    user_message = messages[0][1]['content']
    assert 'The Eiffel Tower is in Berlin.' in user_message
    assert 'Where is the Eiffel Tower?' in user_message


def test_sequence_probability_preset_wires_maximum_sequence_probability(monkeypatch):
    from lm_polygraph import estimators

    # The method name must resolve to a real single-pass, sdpa-safe lm-polygraph estimator.
    assert hasattr(estimators, 'MaximumSequenceProbability')

    detector = _build_uncertainty_sequence_msp_with_fakes(monkeypatch)
    assert detector.feature_processor.config.uncertainty_methods == [
        'MaximumSequenceProbability'
    ]
    assert presets.describe_detector(detector)['family'] == 'uncertainty'
    assert presets.describe_detector(detector)['calibrated'] is False


def test_every_uncertainty_and_judge_preset_has_a_one_line_census_caption():
    """Census sidebar copy must state each method's truth in one line (no dynamic checkpoint meta)."""
    for preset in presets.list_presets():
        if preset.family not in {'uncertainty', 'judge'}:
            continue
        caption = presets.detector_census_caption(preset)
        assert caption, preset.name
        assert '\n' not in caption, preset.name
        assert len(caption) <= 80, preset.name


def _build_openai_sequence_judge_with_fakes(monkeypatch, builder=None, **builder_kwargs):
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
        types.SimpleNamespace(SequenceOpenAIJudge=FakeJudge),
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

    return (builder or presets._build_openai_judge)(
        api_provider='OpenRouter', **builder_kwargs
    )


def test_answerability_judge_preset_is_verdict_answerability(monkeypatch):
    from sirin.ui.workspace.contracts import ScoreSemantics, derive_score_semantics

    detector = _build_openai_sequence_judge_with_fakes(
        monkeypatch, builder=presets._build_openai_answerability_judge
    )
    info = presets.describe_detector(detector)
    assert info['task'] == 'answerability'
    assert info['display_mode'] == 'verdict'
    # a sequence judge is a verdict, never a calibrated probability
    assert (
        derive_score_semantics(calibrated=False, family='judge', level='sequence')
        is ScoreSemantics.VERDICT
    )
    # reasoning models get room to think before the digit
    assert detector.config.verdict_max_tokens == 512
    # the context+question is fed straight through: no fake 'Answer:' trailer, no nested 'Question:'
    assert detector.config.dialogue_format == '{question}'


def test_answerability_judge_prompt_has_sample_slot_and_not_sufficient_polarity():
    prompt = presets._ANSWERABILITY_JUDGE_PROMPT
    # must carry {sample} or build_prompt_messages drops the dialogue and scores nothing
    assert '{sample}' in prompt
    # polarity: 1 == context NOT sufficient (unanswerable); single-digit clause guards token 0
    assert 'NOT sufficient' in prompt
    assert 'SINGLE character' in prompt


def test_answerability_judge_preset_registered_after_sequence_and_enables_task():
    from sirin.ui.streamlit_app import _preset_task

    name = 'Judge — API Answerability (zero-shot)'
    assert name in presets.PRESETS
    preset = presets.PRESETS[name]
    assert preset.task == 'answerability'
    assert preset.family == 'judge' and preset.requires_checkpoint is False
    # the UI derives the Task=Answerability capability from the preset name
    assert _preset_task(name) == 'answerability'
    # placed right after the sequence judge (registry order is load-bearing elsewhere)
    order = list(presets.PRESETS)
    assert order[order.index('Judge — API Sequence (zero-shot)') + 1] == name


def test_claim_judge_preset_registered_after_answerability_as_claim_cards():
    from sirin.ui.workspace.contracts import ScoreSemantics, derive_score_semantics

    name = 'Judge — API Claim (zero-shot)'
    assert name in presets.PRESETS
    preset = presets.PRESETS[name]
    assert preset.family == 'judge' and preset.level == 'claim'
    assert preset.display_mode == 'claim-cards'
    assert preset.requires_checkpoint is False
    assert (
        derive_score_semantics(calibrated=False, family='judge', level='claim')
        is ScoreSemantics.VERDICT
    )
    order = list(presets.PRESETS)
    assert order[order.index('Judge — API Answerability (zero-shot)') + 1] == name


def _build_uncertainty_sequence_msp_with_fakes(monkeypatch):
    class FakeConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeProcessor:
        def __init__(self, config, extractor):
            self.config = config
            self.extractor = extractor

    class FakeDetector:
        def __init__(self, config, feature_processor):
            self.config = config
            self.feature_processor = feature_processor
            self.threshold = 0.5

    class FakeGenerator:
        # non-None so _uncertainty_adapter returns it directly (no HfModelAdapter import needed).
        def generate_hiddens(self):
            pass

    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.processors',
        types.SimpleNamespace(
            SequenceUncertaintyFeatureProcessor=FakeProcessor,
            TokenUncertaintyFeatureProcessor=FakeProcessor,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.detection.uncertainty',
        types.SimpleNamespace(
            SequenceUncertaintyDetector=FakeDetector,
            TokenUncertaintyDetector=FakeDetector,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        'sirin.models.detection',
        types.SimpleNamespace(
            UncertaintyDetectorConfig=FakeConfig,
            UncertaintyFeatureProcessorConfig=FakeConfig,
        ),
    )
    return presets._build_uncertainty_sequence_msp(
        device='cuda:3', generator_adapter=FakeGenerator()
    )


def test_custom_judge_forwards_base_url_and_disables_thinking(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.setenv('SIRIN_CUSTOM_OPENAI_BASE_URL', 'http://127.0.0.1:8000/v1')
    monkeypatch.delenv('SIRIN_CUSTOM_JUDGE_THINKING', raising=False)
    monkeypatch.delenv('SIRIN_CUSTOM_OPENAI_API_KEY', raising=False)

    detector = _build_openai_token_judge_with_fakes(
        monkeypatch, provider=presets.CUSTOM_PROVIDER
    )
    cfg = detector.model_adapter.config

    assert cfg.base_url == 'http://127.0.0.1:8000/v1'
    assert cfg.api_key == 'EMPTY'  # no pasted/env key -> trusted-local EMPTY fallback
    assert cfg.extra_body == {'chat_template_kwargs': {'enable_thinking': False}}


def test_openai_judge_never_sends_extra_body(monkeypatch):
    # OpenAI may reject unknown fields, so it gets no extra_body at all.
    token = _build_openai_token_judge_with_fakes(monkeypatch, provider='OpenAI')
    assert token.model_adapter.config.extra_body is None


def test_openrouter_judges_disable_reasoning_for_the_default_model(monkeypatch):
    # The configured demo model is verified live to accept reasoning {'enabled': False}:
    # no chain-of-thought to overrun the completion budget (OpenRouter mirrors a truncated
    # CoT into content, failing the verbatim echo check) and no quota burned on thinking.
    token = _build_openai_token_judge_with_fakes(monkeypatch, provider='OpenRouter')
    assert token.model_adapter.config.extra_body == {'reasoning': {'enabled': False}}
    sequence = _build_openai_sequence_judge_with_fakes(monkeypatch)  # OpenRouter provider
    assert sequence.model_adapter.config.extra_body == {'reasoning': {'enabled': False}}


def test_openrouter_judges_cap_reasoning_for_other_models(monkeypatch):
    # A visitor-picked model is not verified to accept 'enabled': False, so it keeps the
    # official cap that stops an unbounded chain-of-thought from overrunning the budget.
    # The pasted key marks the model choice as the visitor's own (hosted-safe).
    token = _build_openai_token_judge_with_fakes(
        monkeypatch,
        provider='OpenRouter',
        judge_model='qwen/qwen3-8b',
        judge_api_key='sk-visitor',
    )
    assert token.model_adapter.config.extra_body == {'reasoning': {'max_tokens': 1024}}


def test_custom_judge_thinking_opt_out_env(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.setenv('SIRIN_CUSTOM_OPENAI_BASE_URL', 'http://127.0.0.1:8000/v1')
    monkeypatch.setenv('SIRIN_CUSTOM_JUDGE_THINKING', '1')

    detector = _build_openai_token_judge_with_fakes(
        monkeypatch, provider=presets.CUSTOM_PROVIDER
    )
    assert detector.model_adapter.config.extra_body is None


def test_custom_judge_requires_trusted_local(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setenv('SIRIN_CUSTOM_OPENAI_BASE_URL', 'http://127.0.0.1:8000/v1')

    with pytest.raises(ValueError, match='trusted local'):
        _build_openai_token_judge_with_fakes(
            monkeypatch, provider=presets.CUSTOM_PROVIDER
        )


def test_custom_judge_defaults_to_local_vllm_base_url(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.delenv('SIRIN_CUSTOM_OPENAI_BASE_URL', raising=False)

    detector = _build_openai_token_judge_with_fakes(
        monkeypatch, provider=presets.CUSTOM_PROVIDER
    )

    assert detector.model_adapter.config.base_url == 'http://localhost:8000/v1'


def test_local_openai_models_lists_served_ids(monkeypatch):
    import io
    import urllib.request

    from sirin.ui import providers

    body = json.dumps({'data': [{'id': 'Qwen/Qwen3.5-4B'}, {'object': 'junk'}]})
    monkeypatch.setattr(
        urllib.request, 'urlopen', lambda url, timeout: io.BytesIO(body.encode())
    )

    assert providers.local_openai_models('http://localhost:8000/v1') == [
        'Qwen/Qwen3.5-4B'
    ]


def test_local_openai_models_empty_when_unreachable():
    from sirin.ui import providers

    # Nothing listens on the discard port; the probe must fail silently and fast.
    assert providers.local_openai_models('http://127.0.0.1:9', timeout=0.2) == []


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
    monkeypatch, provider='OpenRouter', set_provider_key=True, **builder_kwargs
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

    return presets._build_openai_token_judge(api_provider=provider, **builder_kwargs)


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
