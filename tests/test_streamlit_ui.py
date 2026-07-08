import pytest

from sirin.ui import streamlit_app as ui


def test_build_sample_uses_two_message_shape():
    assert ui.build_sample('Question?', 'Answer.') == [
        {'role': 'user', 'content': 'Question?'},
        {'role': 'assistant', 'content': 'Answer.'},
    ]


def test_score_heatmap_escapes_text_and_handles_short_scores():
    html = ui.score_heatmap('<bad>&ok', [0.9, 0.1])

    assert '<bad>' not in html
    assert '&lt;' in html
    assert '&gt;' in html
    assert '&amp;' in html
    assert html.count(f'background: rgba({ui._RISK_RGB},') == len('<bad>&ok')


def test_external_provider_resolver_uses_matching_key_only(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'openrouter-key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'anthropic-key')

    openai = ui.resolve_api_provider('OpenAI')
    assert openai.base_url == 'https://api.openai.com/v1'
    assert openai.api_key == 'openai-key'

    openrouter = ui.resolve_api_provider('OpenRouter')
    assert openrouter.base_url == 'https://openrouter.ai/api/v1'
    assert openrouter.api_key == 'openrouter-key'

    anthropic = ui.resolve_api_provider('Anthropic')
    assert anthropic.base_url == 'https://api.anthropic.com/v1/'
    assert anthropic.api_key == 'anthropic-key'


def test_external_provider_resolver_never_cross_falls_back(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    with pytest.raises(ValueError, match='OPENROUTER_API_KEY'):
        ui.resolve_api_provider('OpenRouter')

    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'openrouter-key')
    with pytest.raises(ValueError, match='OPENAI_API_KEY'):
        ui.resolve_api_provider('OpenAI')

    monkeypatch.setenv('OPENAI_API_KEY', 'openai-key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'openrouter-key')
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    with pytest.raises(ValueError, match='ANTHROPIC_API_KEY'):
        ui.resolve_api_provider('Anthropic')


def test_custom_provider_requires_trusted_local(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    with pytest.raises(ValueError, match='trusted local'):
        ui.resolve_api_provider('Custom OpenAI-compatible', 'http://localhost:11434/v1')

    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.delenv('SIRIN_CUSTOM_OPENAI_API_KEY', raising=False)
    custom = ui.resolve_api_provider('Custom OpenAI-compatible', 'http://localhost:11434/v1')
    assert custom.api_key == 'EMPTY'
    assert custom.base_url == 'http://localhost:11434/v1'


def test_hydra_detector_is_blocked_unless_trusted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    with pytest.raises(ValueError, match='SIRIN_UI_TRUSTED_LOCAL'):
        ui._build_detector({
            'use_hydra': True,
            'config_dir': '/tmp',
            'config_name': 'train',
            'overrides_text': '',
            'hydra_checkpoint': '',
        })


def test_external_confirmation_required_for_api_paths():
    assert ui.requires_external_confirmation({'backend': 'OpenAI', 'preset_name': 'x'})
    assert ui.requires_external_confirmation({'backend': 'OpenRouter', 'preset_name': 'x'})
    assert ui.requires_external_confirmation({'backend': 'Anthropic', 'preset_name': 'x'})
    assert ui.requires_external_confirmation({
        'backend': 'HF',
        'preset_name': 'Judge — API Sequence (zero-shot)',
    })
    assert not ui.requires_external_confirmation({
        'backend': 'HF',
        'preset_name': 'Uncertainty — Sequence (zero-shot)',
    })


class _Preset:
    def __init__(self, name='Uncertainty — Sequence (zero-shot)', family='uncertainty'):
        self.name = name
        self.family = family
        self.description = 'desc'
        self.requires_checkpoint = False
        self.is_judge = family == 'judge'


class _SidebarHarness:
    def __init__(self, selectbox_values=None, text_values=None):
        self.selectbox_values = selectbox_values or {}
        self.text_values = text_values or {}
        self.selectbox_calls = []
        self.text_input_calls = []

    @property
    def sidebar(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def header(self, body):
        pass

    def caption(self, body):
        pass

    def divider(self):
        pass

    def selectbox(self, label, options):
        self.selectbox_calls.append((label, list(options)))
        return self.selectbox_values.get(label, list(options)[0])

    def text_input(self, label, value='', **kwargs):
        self.text_input_calls.append((label, value))
        return self.text_values.get(label, value)

    def number_input(self, label, min_value=None, value=0, **kwargs):
        return value

    def slider(self, label, min_value=None, max_value=None, value=0.0, **kwargs):
        return value


def test_api_provider_model_is_editable_not_allowlisted(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setattr(presets, 'list_presets', lambda: [_Preset()])

    st = _SidebarHarness(
        selectbox_values={'Backend': 'OpenAI'},
        text_values={'Model': 'gpt-4.1-mini'},
    )
    cfg = ui._sidebar(st)

    assert cfg['model_path'] == 'gpt-4.1-mini'
    assert ('Model', 'gpt-4.1-mini') in st.text_input_calls
    assert not any(label == 'Model' for label, _ in st.selectbox_calls)


def test_api_provider_model_default_can_be_set_by_env(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setenv('SIRIN_OPENAI_MODEL', 'admin-openai-model')
    monkeypatch.setattr(presets, 'list_presets', lambda: [_Preset()])

    st = _SidebarHarness(selectbox_values={'Backend': 'OpenAI'})
    cfg = ui._sidebar(st)

    assert cfg['model_path'] == 'admin-openai-model'
    assert ('Model', 'admin-openai-model') in st.text_input_calls


def test_anthropic_provider_model_default_can_be_set_by_env(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setenv('SIRIN_ANTHROPIC_MODEL', 'admin-anthropic-model')
    monkeypatch.setattr(presets, 'list_presets', lambda: [_Preset()])

    st = _SidebarHarness(selectbox_values={'Backend': 'Anthropic'})
    cfg = ui._sidebar(st)

    assert cfg['model_path'] == 'admin-anthropic-model'
    assert ('Model', 'admin-anthropic-model') in st.text_input_calls


def test_judge_provider_model_is_editable_not_allowlisted(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setattr(
        presets,
        'list_presets',
        lambda: [_Preset(name='Judge — API Token (zero-shot)', family='judge')],
    )

    st = _SidebarHarness(
        selectbox_values={'Judge provider': 'OpenAI', 'Backend': 'HF'},
        text_values={'Judge model': 'gpt-4.1'},
    )
    cfg = ui._sidebar(st)

    assert cfg['judge_provider'] == 'OpenAI'
    assert cfg['judge_model'] == 'gpt-4.1'
    assert ('Judge model', 'gpt-4.1-mini') in st.text_input_calls
    assert not any(label == 'Judge model' for label, _ in st.selectbox_calls)


def test_detection_view_model_handles_sequence_token_and_claim_outputs():
    sequence = ui.detection_view_model((0.75, 1, None), 'answer', None)
    assert sequence['level'] == 'sequence'
    assert sequence['probability'] == 0.75
    assert sequence['prediction'] == 1

    token = ui.detection_view_model(([[0.2, 0.8]], [[0, 1]], None), 'ok', None)
    assert token['level'] == 'token'
    assert token['scores'] == [0.2, 0.8]

    class Detector:
        claim_results = [{'fact': 'a', 'prob': 0.4, 'pred': 0}]

    claim = ui.detection_view_model(([0.4], [0], None), 'answer', Detector())
    assert claim['level'] == 'claim'
    assert claim['claims'] == [{'fact': 'a', 'prob': 0.4, 'pred': 0}]


def test_detection_view_model_uses_detector_level_for_multiclass_sequence():
    class Level:
        value = 'sequence'

    class Detector:
        detection_level = Level()

    view = ui.detection_view_model(([[0.1, 0.9]], [1], None), 'answer', Detector())

    assert view['level'] == 'sequence'
    assert view['probability'] == [0.1, 0.9]
    assert view['prediction'] == 1


def test_flatten_claims_expands_nested_fact_rows():
    rows = ui.flatten_claims(
        [
            {
                'overall_prob': 0.8,
                'overall_pred': 1,
                'facts': [
                    {'fact': 'alpha', 'prob': 0.3, 'pred': 0},
                    {'fact': 'beta', 'prob': 0.9, 'pred': 1},
                ],
            }
        ]
    )

    assert rows == [
        {
            'sample': 0,
            'fact': 'alpha',
            'prob': 0.3,
            'pred': 0,
            'overall_prob': 0.8,
            'overall_pred': 1,
        },
        {
            'sample': 0,
            'fact': 'beta',
            'prob': 0.9,
            'pred': 1,
            'overall_prob': 0.8,
            'overall_pred': 1,
        },
    ]


def test_debug_summary_preserves_precomputed_shape_fields():
    assert ui.debug_summary({'features_shape': [2, 3]}) == {
        'features_shape': [2, 3],
    }


class _Level:
    def __init__(self, value):
        self.value = value


class _FakeDetector:
    claim_results = None
    last_generations = None
    last_spans = None

    def __init__(self, level, family, calibrated, threshold=0.5):
        self.detection_level = _Level(level)
        self._ui_level = level
        self._ui_family = family
        self._ui_calibrated = calibrated
        self.threshold = threshold


def test_minmax_normalizes_and_survives_flat_and_empty():
    assert ui._minmax([2.0, 0.5, 3.0]) == [0.6, 0.0, 1.0]
    assert ui._minmax([5.0, 5.0]) == [0.5, 0.5]
    assert ui._minmax([]) == []


def test_token_uncertainty_view_is_uncalibrated_and_normalized():
    detector = _FakeDetector('token', 'uncertainty', calibrated=False)
    view = ui.detection_view_model(([[2.0, 0.5, 3.0]], [[1, 0, 1]], None), 'abc', detector)
    assert view['level'] == 'token'
    assert view['calibrated'] is False
    assert view['norm_scores'] == [0.6, 0.0, 1.0]
    assert view['scores'] == [2.0, 0.5, 3.0]


def test_sequence_uncertainty_view_keeps_raw_score():
    detector = _FakeDetector('sequence', 'uncertainty', calibrated=False, threshold=0.7)
    view = ui.detection_view_model((5.3, 1, None), 'answer', detector)
    assert view['level'] == 'sequence'
    assert view['calibrated'] is False
    assert view['raw_prob'] == 5.3
    assert view['threshold'] == 0.7


class _FakeExpander:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeSt:
    def __init__(self):
        self.rendered = []

    def html(self, body):
        self.rendered.append(body)

    def markdown(self, body, **kwargs):
        self.rendered.append(body)

    def info(self, body):
        self.rendered.append(body)

    def write(self, body):
        self.rendered.append(body)

    def expander(self, label):
        return _FakeExpander()


def test_visualizers_render_result_smoke():
    from sirin.ui import visualizers

    seq = {'level': 'sequence', 'probability': 0.8, 'prediction': 1, 'calibrated': True, 'threshold': 0.5}
    tok = {
        'level': 'token',
        'answer': 'abc',
        'scores': [0.2, 0.8, 0.5],
        'norm_scores': [0.2, 0.8, 0.5],
        'calibrated': False,
    }
    claim = {'level': 'claim', 'claims': [{'fact': 'x', 'prob': 0.4, 'pred': 0}], 'overall_prob': 0.4, 'overall_pred': 0}
    for view in (seq, tok, claim):
        fake = _FakeSt()
        visualizers.render_result(fake, view)
        assert fake.rendered, f'nothing rendered for {view["level"]}'


class _Detector:
    def __init__(self, level, family, calibrated, display_mode=None, **attrs):
        self.detection_level = _Level(level) if level else None
        self._ui_level = level
        self._ui_family = family
        self._ui_calibrated = calibrated
        if display_mode is not None:
            self._ui_display_mode = display_mode
        self.claim_results = None
        self.last_generations = None
        self.last_spans = None
        for key, value in attrs.items():
            setattr(self, key, value)


def test_multiclass_sequence_view_sets_class_probs():
    view = ui.detection_view_model(
        ([[0.1, 0.2, 0.7]], [2], None), 'answer', _Detector('sequence', 'probing', True)
    )
    assert view['level'] == 'sequence'
    assert view['display_mode'] == 'multiclass'
    assert view['class_probs'] == [0.1, 0.2, 0.7]
    assert view['class_index'] == 2


def test_strip_span_tags_removes_markers():
    assert ui._strip_span_tags('wa[SPAN]ter[/SPAN]') == 'water'


def test_token_judge_answer_source_prefers_stripped_generation():
    judge = _Detector(
        'token', 'judge', True, last_generations=['wa[SPAN]ter[/SPAN]']
    )
    scores = [0.1, 0.2, 0.3, 0.4, 0.5]  # len 5 == len('water')
    view = ui.detection_view_model(([scores], [[0, 0, 1, 1, 0]], None), 'CHAT-ANSWER', judge)
    assert view['answer'] == 'water'
    assert view['answer_source'] == 'generation'
    assert view['tagged_generation'] == 'wa[SPAN]ter[/SPAN]'


def test_token_uncertainty_answer_source_is_original():
    unc = _Detector('token', 'uncertainty', False)
    view = ui.detection_view_model(([[0.2, 0.5, 0.9]], [[0, 1, 1]], None), 'abc', unc)
    assert view['answer'] == 'abc'
    assert view['answer_source'] == 'original'


def test_sequence_verdict_suppresses_reasoning():
    judge = _Detector('sequence', 'judge', False, display_mode='verdict', last_generations=['1'])
    view = ui.detection_view_model(([2.3], [1], None), 'answer', judge)
    assert view['display_mode'] == 'verdict'
    assert view['reasoning'] is None
    assert view['prediction'] == 1


def test_claim_openai_view_is_uncalibrated():
    judge = _Detector('claim', 'judge', False)
    judge.claim_results = [
        {'overall_prob': 3.1, 'overall_pred': 1, 'facts': [{'fact': 'a', 'prob': 2.2, 'pred': 1}]}
    ]
    view = ui.detection_view_model(([3.1], [1], None), 'answer', judge)
    assert view['level'] == 'claim'
    assert view['calibrated'] is False


def test_styles_inject_substitutes_placeholders_and_honors_motion():
    from sirin.ui import styles

    calls = []

    class _S:
        def html(self, body):
            calls.append(body)

    styles.inject_global_styles(_S(), motion='subtle')
    css = calls[0]
    assert '@@' not in css  # every placeholder substituted
    assert 'data:image/jpeg;base64,' in css
    assert '@keyframes sirin-drift-subtle' in css
    assert 'sirin-drift-subtle' in css  # subtle animation wired

    static_calls = []

    class _S2:
        def html(self, body):
            static_calls.append(body)

    styles.inject_global_styles(_S2(), motion='static')
    assert 'animation: none' in static_calls[0]
