import pytest

from sirin.ui import streamlit_app as ui


def test_build_sample_uses_two_message_shape():
    assert ui.build_sample('Question?', 'Answer.') == [
        {'role': 'user', 'content': 'Question?'},
        {'role': 'assistant', 'content': 'Answer.'},
    ]


def test_score_heatmap_escapes_text_and_handles_short_scores():
    html_out = ui.score_heatmap('<bad>&ok', [0.9, 0.1])

    assert '<bad>' not in html_out
    assert '&lt;' in html_out
    assert '&gt;' in html_out
    assert '&amp;' in html_out
    assert 'sirin-token-evidence' in html_out
    assert 'data-index="0"' in html_out
    assert 'data-score="0.900"' in html_out


def test_score_heatmap_marks_missing_scores_neutral_and_preserves_whitespace():
    html_out = ui.score_heatmap('A B\nC', [0.1, 0.8], predictions=[0, 1])

    assert 'white-space:pre-wrap' in html_out
    assert 'data-score="missing"' in html_out
    assert 'data-missing="true"' in html_out
    assert 'data-pred="1"' in html_out
    assert '&nbsp;' in html_out
    assert '<br>' in html_out


def test_split_thinking_hides_qwen_think_block():
    visible, thinking = ui._split_thinking(
        '<think>private chain</think>\n{ "answer": "2" }'
    )

    assert visible == '{ "answer": "2" }'
    assert thinking == 'private chain'


def test_split_thinking_reports_when_model_only_thought():
    visible, thinking = ui._split_thinking('<think>private chain</think>')

    assert visible.startswith('No final answer produced')
    assert thinking == 'private chain'


def test_split_thinking_hides_json_reasoning_field():
    visible, thinking = ui._split_thinking(
        '<think>private chain</think>\n'
        '{ "reasoning": "counted two movies", "answer": "2" }'
    )

    assert visible == '2'
    assert 'private chain' in thinking
    assert 'counted two movies' in thinking


def test_detector_setup_error_checks_checkpoint_roots(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.delenv('SIRIN_UI_CHECKPOINT_ROOTS', raising=False)

    error = ui._detector_setup_error({
        'use_hydra': False,
        'checkpoint_dir': '/tmp/checkpoint',
    })

    assert 'SIRIN_UI_CHECKPOINT_ROOTS' in error


def test_detector_setup_error_preflights_sequence_tabpfn_shape(monkeypatch, tmp_path):
    import joblib

    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    joblib.dump(
        {'feature_shapes': [(4, 1, 1, 2048)]},
        tmp_path / 'compressor_config.joblib',
    )

    error = ui._detector_setup_error({
        'use_hydra': False,
        'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        'checkpoint_dir': str(tmp_path),
    })

    assert error.startswith('Checkpoint/processor mismatch before generation')
    assert '(1, 1, 2048)' in error


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
    def __init__(self, selectbox_values=None, text_values=None, button_values=None):
        self.selectbox_values = selectbox_values or {}
        self.text_values = text_values or {}
        self.button_values = button_values or {}
        self.selectbox_calls = []
        self.text_input_calls = []
        self.button_calls = []
        self.session_state = {}
        self.rerun_called = False

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

    def selectbox(self, label, options, **kwargs):
        self.selectbox_calls.append((label, list(options)))
        return self.selectbox_values.get(label, list(options)[0])

    def text_input(self, label, value='', **kwargs):
        self.text_input_calls.append((label, value))
        return self.text_values.get(label, value)

    def number_input(self, label, min_value=None, value=0, **kwargs):
        return value

    def slider(self, label, min_value=None, max_value=None, value=0.0, **kwargs):
        return value

    def button(self, label, **kwargs):
        self.button_calls.append((label, kwargs.get('key')))
        return self.button_values.get(label, False)

    def rerun(self):
        self.rerun_called = True


def test_sidebar_uses_requested_defaults(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    cfg = ui._sidebar(_SidebarHarness())

    assert cfg['preset_name'] == 'Probing — Sequence TabPFN (checkpoint)'
    assert cfg['model_path'] == 'Qwen/Qwen3.5-4B'
    assert cfg['max_tokens'] == 8192


def test_appearance_defaults_are_light_and_lively():
    st = _SidebarHarness()

    ui._appearance_sidebar(st)

    assert ('Theme', ['Light', 'Dark']) in st.selectbox_calls
    assert ('Background motion', ['Lively', 'Subtle', 'Static']) in st.selectbox_calls


def test_attention_tools_sidebar_replaces_view_selector():
    st = _SidebarHarness()

    assert ui._attention_tools_sidebar(st) == ''

    assert ('A* Marvel demo', 'attention_open_marvel_demo') in st.button_calls
    assert ('Cached explorer', 'attention_open_explorer') in st.button_calls
    assert ('Live capture', 'attention_open_live') in st.button_calls
    assert not any(label == 'View' for label, _ in st.selectbox_calls)


def test_main_marvel_demo_skips_chat_shell(monkeypatch):
    import sys
    import types

    calls = []

    class SessionState(dict):
        pass

    fake_st = types.SimpleNamespace()
    fake_st.session_state = SessionState({
        'attention_tool': 'marvel_demo',
        'bg_motion': 'Static',
        'ui_theme': 'Light',
    })
    fake_st.set_page_config = lambda **kwargs: calls.append(('page_config', kwargs))
    fake_st.html = lambda body: calls.append(('html', body))
    fake_st.markdown = lambda body, **kwargs: calls.append(('markdown', body))
    fake_st.caption = lambda body: calls.append(('caption', body))
    monkeypatch.setitem(sys.modules, 'streamlit', fake_st)

    from sirin.ui import attention_explorer

    monkeypatch.setattr(attention_explorer, 'render_marvel_demo', lambda st: calls.append(('marvel', st)))
    monkeypatch.setattr(ui, '_attention_tools_sidebar', lambda st: calls.append(('sidebar', st)))
    monkeypatch.setattr(ui, '_appearance_sidebar', lambda st: calls.append(('appearance', st)))

    ui.main()

    assert any(kind == 'marvel' for kind, _ in calls)
    assert not any(kind == 'sidebar' for kind, _ in calls)
    assert not any(kind == 'appearance' for kind, _ in calls)
    assert not any(kind == 'markdown' and '>SIRIN</h1>' in body for kind, body in calls)
    assert not any(kind == 'caption' and 'Semantic Inconsistency' in body for kind, body in calls)


def test_sidebar_clear_chat_button_resets_session_state(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    st = _SidebarHarness(button_values={'Clear chat': True})
    st.session_state['messages'] = [{'role': 'user', 'content': 'stuck'}]
    st.session_state['pending'] = 'queued'

    ui._sidebar(st)

    assert st.session_state['messages'] == []
    assert 'pending' not in st.session_state
    assert st.rerun_called


def test_sidebar_unload_gpu_models_button_calls_unloader(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    called = []
    monkeypatch.setattr(ui, '_unload_cached_models', lambda: called.append(True))
    st = _SidebarHarness(button_values={'Unload GPU models': True})

    ui._sidebar(st)

    assert called == [True]


def test_sidebar_load_demo_replay_populates_chat_without_gpu(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    st = _SidebarHarness(button_values={'Load A* recorded generation': True})

    ui._sidebar(st)

    assert len(st.session_state['messages']) == 2
    assert st.session_state['messages'][0]['role'] == 'user'
    assert st.session_state['messages'][1]['content'] == 'One'
    assert st.session_state['messages'][1]['artifact']['gold_answer'] == '2'
    assert st.session_state['messages'][1]['artifact']['evidence_quotes'] == list(ui.RECORDED_DEMO_QUOTES)
    assert st.session_state['messages'][1]['view']['probability'] == 0.9983455751552265
    assert st.rerun_called


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


def test_hf_model_is_editable_not_allowlisted(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setattr(presets, 'list_presets', lambda: [_Preset()])

    st = _SidebarHarness(
        selectbox_values={'Backend': 'HF'},
        text_values={'Model': 'Qwen/Qwen3.5-35B-A3B'},
    )
    cfg = ui._sidebar(st)

    assert cfg['model_path'] == 'Qwen/Qwen3.5-35B-A3B'
    assert ('Model', 'Qwen/Qwen3.5-4B') in st.text_input_calls
    assert not any(label == 'Model' for label, _ in st.selectbox_calls)


def test_large_hf_model_on_plain_cuda_uses_auto_device_map(monkeypatch):
    monkeypatch.setattr(ui, '_device_map_max_memory', lambda: {1: '68GiB', 2: '68GiB'})

    cfg = ui._make_hf_config('Qwen/Qwen3.5-35B-A3B', 'cuda')

    assert cfg.device is None
    assert cfg.device_map == 'auto'
    assert cfg.max_memory == {1: '68GiB', 2: '68GiB'}
    assert cfg.attn_implementation == 'sdpa'


def test_device_map_memory_uses_only_freest_two_gpus_by_default(monkeypatch):
    import sys

    class FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def device_count():
            return 4

        @staticmethod
        def mem_get_info(idx):
            free_gib = [1, 80, 72, 64][idx]
            return free_gib * 1024 ** 3, 80 * 1024 ** 3

    class FakeTorch:
        cuda = FakeCuda

    monkeypatch.delenv('SIRIN_UI_AUTO_DEVICE_MAP_GPUS', raising=False)
    monkeypatch.setitem(sys.modules, 'torch', FakeTorch)

    assert ui._device_map_max_memory() == {1: '68GiB', 2: '61GiB'}


def test_device_map_memory_skips_gpus_that_fail_memory_probe(monkeypatch):
    import sys

    class FakeCuda:
        @staticmethod
        def is_available():
            return True

        @staticmethod
        def device_count():
            return 3

        @staticmethod
        def mem_get_info(idx):
            if idx == 0:
                raise RuntimeError('CUDA out of memory')
            free_gib = [0, 80, 72][idx]
            return free_gib * 1024 ** 3, 80 * 1024 ** 3

    class FakeTorch:
        cuda = FakeCuda

    monkeypatch.delenv('SIRIN_UI_AUTO_DEVICE_MAP_GPUS', raising=False)
    monkeypatch.setitem(sys.modules, 'torch', FakeTorch)

    assert ui._device_map_max_memory() == {1: '68GiB', 2: '61GiB'}


def test_small_hf_model_on_cuda_stays_single_device():
    cfg = ui._make_hf_config('Qwen/Qwen3.5-4B', 'cuda')

    assert cfg.device == 'cuda'
    assert cfg.device_map is None


def test_sidebar_strips_accidental_text_input_whitespace(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    preset = _Preset(
        name='Probing — Sequence TabPFN (checkpoint)',
        family='probing',
    )
    preset.requires_checkpoint = True
    monkeypatch.setattr(presets, 'list_presets', lambda: [preset])

    st = _SidebarHarness(
        selectbox_values={'Backend': 'HF'},
        text_values={
            'Model': ' Qwen/Qwen3.5-35B-A3B ',
            'Checkpoint directory': ' /tmp/probe ',
        },
    )

    cfg = ui._sidebar(st)

    assert cfg['model_path'] == 'Qwen/Qwen3.5-35B-A3B'
    assert cfg['checkpoint_dir'] == '/tmp/probe'


def test_sidebar_strips_trailing_pasted_ui_fields_from_checkpoint(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    preset = _Preset(
        name='Probing — Sequence TabPFN (checkpoint)',
        family='probing',
    )
    preset.requires_checkpoint = True
    monkeypatch.setattr(presets, 'list_presets', lambda: [preset])

    path = (
        '/home/jovyan/parchiev/magistr/dynmem/results/longmemeval/'
        'pure_simplemem_qwen35_35b_a3b/20260703_120500_qwen35_35b_a3b_s_full_combined_500/'
        'sirin_datasets/parallel/hiddens/saved_detectors/hallucination_strict/Hiddens_R_TabPFN'
    )
    st = _SidebarHarness(
        selectbox_values={'Backend': 'HF'},
        text_values={
            'Checkpoint directory': (
                f'{path} Backend HF Model Qwen/Qwen3.5-35B-A3B Device cuda Max tokens 192'
            ),
        },
    )

    cfg = ui._sidebar(st)

    assert cfg['checkpoint_dir'] == path


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


def test_sequence_probing_token_view_broadcasts_tabpfn_score():
    view = {
        'level': 'sequence',
        'family': 'probing',
        'probability': 0.82,
        'prediction': 1,
        'calibrated': True,
    }

    token_view = ui._sequence_probing_token_view(view, 'Red Rocks and Larimer Lounge.')

    assert token_view['level'] == 'token'
    assert token_view['display_mode'] == 'sequence-broadcast'
    assert token_view['family'] == 'probing'
    assert token_view['scores'] == [0.82, 0.82, 0.82, 0.82, 0.82]
    assert token_view['predictions'] == [1, 1, 1, 1, 1]
    assert token_view['scale_label'] == 'sequence TabPFN score'
    assert 'broadcast' in token_view['signal_note']


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

    def expander(self, label, **kwargs):
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


def test_render_analysis_adds_probing_tabpfn_broadcast_token_view():
    calls = []

    class Visualizers:
        @staticmethod
        def render_result(st, view):
            calls.append(view)

    ui._render_analysis(
        _FakeSt(),
        {
            'content': 'Red Rocks and Larimer Lounge.',
            'view': {
                'level': 'sequence',
                'family': 'probing',
                'probability': 0.82,
                'prediction': 1,
                'calibrated': True,
            },
        },
        Visualizers,
    )

    assert [view['level'] for view in calls] == ['sequence', 'token']
    assert calls[1]['scale_label'] == 'sequence TabPFN score'


def test_run_turn_replays_recorded_demo_without_generator_or_detector(monkeypatch):
    from sirin.ui import visualizers

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []

        def spinner(self, body):
            raise AssertionError('recorded demo should not start live generation or detection')

        def error(self, body):
            self.errors.append(body)

    monkeypatch.setattr(ui, 'load_generator', lambda *a, **k: (_ for _ in ()).throw(AssertionError('generator called')))
    monkeypatch.setattr(ui, '_build_detector', lambda *a, **k: (_ for _ in ()).throw(AssertionError('detector called')))

    msg = ui._run_turn(
        St(),
        ui.RECORDED_DEMO_PROMPT,
        {'use_hydra': False, 'checkpoint_dir': ''},
        visualizers,
    )

    assert msg['content'] == 'One'
    assert msg['artifact']['source'] == 'recorded_offline_replay'
    assert msg['artifact']['gold_answer'] == '2'
    assert msg['view']['probability'] == 0.9983455751552265
    assert msg['token_view']['answer'] == 'One'


def test_run_turn_preloads_probing_detector_before_generation(monkeypatch):
    class Spinner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []

        def spinner(self, body):
            return Spinner()

        def error(self, body):
            self.errors.append(body)

    def fail_detector(cfg):
        raise RuntimeError('CUDA out of memory. PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True')

    monkeypatch.setattr(ui, '_build_detector', fail_detector)
    monkeypatch.setattr(
        ui,
        'load_generator',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('generator loaded')),
    )
    monkeypatch.setattr(
        ui,
        'generate_answer',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('generation called')),
    )

    msg = ui._run_turn(
        St(),
        'ordinary prompt',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 192,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        },
        object(),
    )

    assert msg['content'].startswith('Detection setup failed before generation')
    assert 'Unload GPU models' in msg['content']
    assert 'CUDA out of memory' not in msg['content']
    assert 'PYTORCH_CUDA_ALLOC_CONF' not in msg['content']


def test_run_turn_preflights_large_prompt_detector_before_generation(monkeypatch):
    class Detector:
        def detect(self, samples):
            raise RuntimeError(
                'CUDA out of memory. Tried to allocate 1024.00 MiB. '
                'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True'
            )

    class Spinner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []

        def spinner(self, body):
            return Spinner()

        def error(self, body):
            self.errors.append(body)

    monkeypatch.setattr(ui, '_build_detector', lambda cfg: Detector())
    monkeypatch.setattr(
        ui,
        'load_generator',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('generator loaded')),
    )
    monkeypatch.setattr(
        ui,
        'generate_answer',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('generation called')),
    )

    msg = ui._run_turn(
        St(),
        'long prompt',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 192,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        },
        object(),
    )

    assert msg['content'].startswith('Detection setup failed before generation')
    assert 'Unload GPU models' in msg['content']
    assert 'CUDA out of memory' not in msg['content']


def test_detector_error_message_explains_hidden_size_mismatch():
    msg = ui._detector_error_message(
        RuntimeError('Feature 0 shape mismatch: expected (6, 1, 2048), got (6, 1, 2560)'),
        after_generation=False,
        cfg={'model_path': 'Qwen/Qwen3.5-35B-A3B'},
    )

    assert msg.startswith('Detection setup failed before generation')
    assert 'checkpoint/model hidden-size mismatch' in msg
    assert 'expects hidden size 2048' in msg
    assert 'produced 2560' in msg
    assert 'Selected model: `Qwen/Qwen3.5-35B-A3B`' in msg
    assert 'Unload GPU models' in msg


def test_run_turn_retries_once_when_preflight_looks_like_stale_extractor(monkeypatch):
    class Spinner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []

        def spinner(self, body):
            return Spinner()

        def error(self, body):
            self.errors.append(body)

    class Detector:
        def __init__(self, stale=False):
            self.stale = stale
            self.last_method_scores = None
            self.feature_processor = None

        def detect(self, samples):
            if self.stale:
                raise RuntimeError(
                    'Feature 0 shape mismatch: expected (6, 1, 2048), got (6, 1, 2560)'
                )
            return ([0.2], [0], None)

    builds = []
    unloads = []

    def build_detector(cfg):
        builds.append(cfg)
        return Detector(stale=len(builds) == 1)

    monkeypatch.setattr(ui, '_build_detector', build_detector)
    monkeypatch.setattr(ui, '_selected_hf_hidden_size', lambda model_path: 2048)
    monkeypatch.setattr(ui, '_unload_cached_models', lambda: unloads.append(True))
    monkeypatch.setattr(ui, 'load_generator', lambda *a, **k: object())
    monkeypatch.setattr(ui, 'generate_answer', lambda *a, **k: 'Answer')
    monkeypatch.setattr(
        ui,
        'detection_view_model',
        lambda result, answer, detector: {
            'level': 'sequence',
            'family': 'probing',
            'probability': 0.2,
        },
    )

    class Visualizers:
        @staticmethod
        def render_result(st, view):
            pass

    msg = ui._run_turn(
        St(),
        'prompt',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 192,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        },
        Visualizers,
    )

    assert len(builds) == 2
    assert unloads == [True]
    assert msg['content'] == 'Answer'
    assert 'detector_error' not in msg


def test_run_turn_rejects_oversized_detector_input_before_generation(monkeypatch):
    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []

        def error(self, body):
            self.errors.append(body)

    monkeypatch.setenv('SIRIN_UI_MAX_DETECTOR_INPUT_CHARS', '10')
    monkeypatch.setattr(
        ui,
        '_build_detector',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('detector built')),
    )
    monkeypatch.setattr(
        ui,
        'load_generator',
        lambda *a, **k: (_ for _ in ()).throw(AssertionError('generator loaded')),
    )

    msg = ui._run_turn(
        St(),
        'prompt that is too long',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 192,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        },
        object(),
    )

    assert msg['content'].startswith('Detection setup failed before generation')
    assert 'Detector input is too large' in msg['content']
    assert 'SIRIN_UI_MAX_DETECTOR_INPUT_CHARS' in msg['content']


def test_run_turn_skips_detector_when_generated_answer_exceeds_guard(monkeypatch):
    class Detector:
        def detect(self, samples):
            return ([0.2], [0], None)

    class Spinner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.warnings = []

        def spinner(self, body):
            return Spinner()

        def warning(self, body):
            self.warnings.append(body)

    monkeypatch.setenv('SIRIN_UI_MAX_DETECTOR_INPUT_CHARS', '40')
    monkeypatch.setattr(ui, '_build_detector', lambda cfg: Detector())
    monkeypatch.setattr(ui, 'load_generator', lambda *a, **k: object())
    monkeypatch.setattr(ui, 'generate_answer', lambda *a, **k: 'A' * 80)

    msg = ui._run_turn(
        St(),
        'short',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 192,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        },
        object(),
    )

    assert msg['content'] == 'A' * 80
    assert msg['detector_error'].startswith('Detector skipped')
    assert 'Detector input is too large' in msg['detector_error']


def test_sequence_gauge_score_has_explicit_contrast():
    from sirin.ui import visualizers

    fake = _FakeSt()

    visualizers.render_result(
        fake,
        {
            'level': 'sequence',
            'probability': 0.998,
            'prediction': 1,
            'calibrated': True,
            'threshold': 0.5,
        },
    )

    html = ''.join(fake.rendered)
    assert '99.8%' in html
    assert 'color:#8f123c' in html
    assert 'background:#fff1f5' in html


def test_run_turn_detector_oom_preserves_answer_and_sanitizes_error(monkeypatch):
    class Adapter:
        pass

    class Detector:
        def detect(self, samples):
            raise RuntimeError(
                'CUDA out of memory. Tried to allocate 1.19 GiB. '
                'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True'
            )

    class Spinner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class St(_FakeSt):
        def __init__(self):
            super().__init__()
            self.errors = []
            self.warnings = []

        def spinner(self, body):
            return Spinner()

        def error(self, body):
            self.errors.append(body)

        def warning(self, body):
            self.warnings.append(body)

    monkeypatch.setattr(ui, 'load_generator', lambda *a, **k: Adapter())
    monkeypatch.setattr(ui, 'generate_answer', lambda *a, **k: 'One')
    monkeypatch.setattr(ui, '_build_detector', lambda cfg: Detector())

    msg = ui._run_turn(
        St(),
        'ordinary prompt',
        {
            'backend': 'HF',
            'model_path': 'Qwen/Qwen3.5-35B-A3B',
            'device': 'cuda',
            'max_tokens': 1,
            'temperature': 0.0,
            'use_hydra': False,
            'checkpoint_dir': '',
        },
        object(),
    )

    assert msg['content'] == 'One'
    assert msg['detector_error'].startswith('Detector skipped')
    assert 'Unload GPU models' in msg['detector_error']
    assert 'CUDA out of memory' not in msg['detector_error']
    assert 'PYTORCH_CUDA_ALLOC_CONF' not in msg['detector_error']


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
