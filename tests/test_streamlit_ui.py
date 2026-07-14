import json

import pytest

from sirin.ui import streamlit_app as ui


def test_build_sample_uses_two_message_shape():
    assert ui.build_sample('Question?', 'Answer.') == [
        {'role': 'user', 'content': 'Question?'},
        {'role': 'assistant', 'content': 'Answer.'},
    ]


def test_generate_answer_preserves_recorded_message_sequence():
    class Adapter:
        def sample(self, inputs, **kwargs):
            self.inputs = inputs
            self.kwargs = kwargs
            return ['answer']

    adapter = Adapter()
    messages = [
        {'role': 'system', 'content': 'System.'},
        {'role': 'user', 'content': 'Question?'},
    ]

    assert (
        ui.generate_answer(adapter, 'OpenAI', 'ignored', 192, 0.1, messages) == 'answer'
    )
    assert adapter.inputs == [messages]
    assert adapter.kwargs == {'max_tokens': 192, 'temperature': 0.1}


def test_generate_answer_renders_recorded_messages_for_vllm():
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            self.call = (messages, kwargs)
            return 'rendered chat prompt'

    class Model:
        def __init__(self, tokenizer):
            self.tokenizer = tokenizer

        def get_tokenizer(self):
            return self.tokenizer

    class Adapter:
        is_loaded = True
        tokenizer = None

        def __init__(self):
            self.model = Model(Tokenizer())

        def sample(self, inputs, **kwargs):
            self.inputs = inputs
            return ['answer']

    adapter = Adapter()
    messages = [
        {'role': 'system', 'content': 'System.'},
        {'role': 'user', 'content': 'Question?'},
    ]

    assert (
        ui.generate_answer(adapter, 'vLLM', 'ignored', 192, 0.1, messages) == 'answer'
    )
    assert adapter.inputs == ['rendered chat prompt']
    assert adapter.model.tokenizer.call == (
        messages,
        {'tokenize': False, 'add_generation_prompt': True},
    )


def test_generate_answer_preserves_hf_max_tokens_and_sets_native_timeout():
    class Adapter:
        def sample(self, inputs, **kwargs):
            self.inputs = inputs
            self.kwargs = kwargs
            return ['answer']

    adapter = Adapter()

    assert ui.generate_answer(adapter, 'HF', 'Prompt.', 8192, 0.7) == 'answer'
    assert adapter.kwargs == {
        'max_tokens': 8192,
        'temperature': 0.7,
        'max_time': 60.0,
    }


def test_hf_generation_adds_nonthinking_assistant_prompt():
    from types import SimpleNamespace

    from sirin.inference.adapters.hf_adapter import HfModelAdapter

    class Tokenizer:
        chat_template = 'template'

        def apply_chat_template(self, messages, **kwargs):
            self.call = (messages, kwargs)
            return 'rendered prompt'

    adapter = object.__new__(HfModelAdapter)
    adapter.config = SimpleNamespace(use_chat_template=True)
    adapter.tokenizer = Tokenizer()
    messages = [[{'role': 'user', 'content': 'Question?'}]]

    assert adapter._preprocess_input(
        messages,
        add_generation_prompt=True,
        enable_thinking=False,
    ) == ['rendered prompt']
    assert adapter.tokenizer.call == (
        messages[0],
        {
            'tokenize': False,
            'add_generation_prompt': True,
            'padding': False,
            'truncation': False,
            'enable_thinking': False,
        },
    )


def test_hf_adapter_streams_native_generation_chunks(monkeypatch):
    from queue import Queue
    from types import SimpleNamespace

    import torch

    from sirin.inference.adapters import hf_adapter
    from sirin.inference.model_manager import ModelManager

    class Batch(dict):
        def to(self, device):
            return self

    class Tokenizer:
        max_length = 1024
        eos_token_id = 0

        def __call__(self, inputs, **kwargs):
            return Batch(
                input_ids=torch.tensor([[1]]),
                attention_mask=torch.tensor([[1]]),
            )

    class Streamer:
        stop = object()

        def __init__(self, tokenizer, **kwargs):
            self.queue = Queue()

        def on_finalized_text(self, text, stream_end=False):
            if text:
                self.queue.put(text)
            if stream_end:
                self.queue.put(self.stop)

        def __iter__(self):
            while (item := self.queue.get()) is not self.stop:
                yield item

    class Model:
        def generate(self, **kwargs):
            self.kwargs = kwargs
            kwargs['streamer'].on_finalized_text('Hello', stream_end=False)
            kwargs['streamer'].on_finalized_text(' world', stream_end=True)

    adapter = object.__new__(hf_adapter.HfModelAdapter)
    adapter.config = SimpleNamespace(padding=False, truncation=False)
    adapter.tokenizer = Tokenizer()
    adapter.model = Model()
    adapter._preprocess_input = lambda inputs, **kwargs: ['prompt']
    adapter._get_primary_device = lambda: 'cpu'
    monkeypatch.setattr(hf_adapter, 'TextIteratorStreamer', Streamer)
    monkeypatch.setattr(
        ModelManager,
        'load_model',
        classmethod(lambda cls, selected: selected),
    )

    chunks = list(
        adapter.stream(
            [[{'role': 'user', 'content': 'Question?'}]],
            max_tokens=32,
            temperature=0.0,
            max_time=1.0,
        )
    )

    assert chunks == ['Hello', ' world']
    assert adapter.model.kwargs['max_new_tokens'] == 32
    assert adapter.model.kwargs['max_time'] == 1.0


def test_openai_adapter_streams_and_retains_exact_logprob_trace(monkeypatch):
    from types import SimpleNamespace

    from sirin.inference.adapters import openai_adapter
    from sirin.inference.model_manager import ModelManager

    def token(piece, logprob):
        return SimpleNamespace(
            token=piece,
            bytes=list(piece.encode()),
            logprob=logprob,
            top_logprobs=[
                SimpleNamespace(token=piece, logprob=logprob),
                SimpleNamespace(token='x', logprob=-2.0),
            ],
        )

    events = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content='1'),
                    logprobs=SimpleNamespace(content=[token('1', -0.2)]),
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content=' sport'),
                    logprobs=SimpleNamespace(
                        content=[token(' sp', -0.4), token('ort', -0.1)]
                    ),
                )
            ]
        ),
    ]
    calls = []

    class Completions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return events

    adapter = object.__new__(openai_adapter.OpenAIModelAdapter)
    adapter.config = SimpleNamespace(
        model_path='Qwen/Qwen3.5-35B-A3B',
        base_url='http://127.0.0.1:30110/v1',
    )
    adapter._client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    monkeypatch.setattr(
        ModelManager,
        'load_model',
        classmethod(lambda cls, selected: selected),
    )

    chunks = list(
        adapter.stream(
            [[{'role': 'user', 'content': 'Question?'}]],
            max_tokens=16,
            temperature=0.0,
            capture_token_uncertainty=True,
        )
    )

    assert chunks == ['1', ' sport']
    assert calls[0]['stream'] is True
    assert calls[0]['logprobs'] is True
    assert calls[0]['extra_body']['chat_template_kwargs']['enable_thinking'] is False
    assert adapter.last_generation_trace['text'] == '1 sport'
    assert adapter.last_generation_trace['pieces'] == ['1', ' sp', 'ort']
    assert adapter.last_generation_trace['offsets'] == [[0, 1], [1, 4], [4, 7]]
    assert adapter.last_generation_trace['MaximumTokenProbability'] == pytest.approx(
        [0.2, 0.4, 0.1]
    )
    assert adapter.last_generation_trace['entropy_scope'] == 'top-20'


def test_preset_detector_reuses_canonical_generator_cache_key(monkeypatch):
    from sirin.ui import presets

    class Preset:
        family = 'probing'

        @staticmethod
        def build(**kwargs):
            return kwargs['generator_adapter']

    calls = []
    adapter = object()
    monkeypatch.setitem(presets.PRESETS, 'test', Preset())
    monkeypatch.setattr(
        ui,
        'load_generator',
        lambda *args: calls.append(args) or adapter,
    )
    result = ui.build_preset_detector(
        'test', 'cuda', '', 'HF', 'model', '', '', 'OpenRouter', ''
    )

    assert result is adapter
    assert calls == [('HF', 'model', 'cuda', '')]


def test_preset_detector_does_not_cache_a_stale_extractor(monkeypatch):
    from sirin.ui import presets

    built = []

    class Preset:
        family = 'probing'

        @staticmethod
        def build(**kwargs):
            detector = object()
            built.append(detector)
            return detector

    monkeypatch.setitem(presets.PRESETS, 'fresh detector', Preset())
    monkeypatch.setattr(ui, 'load_generator', lambda *args: object())
    args = ('fresh detector', 'cuda', '', 'HF', 'model', '', '', 'OpenRouter', '')
    first = ui.build_preset_detector(*args)
    second = ui.build_preset_detector(*args)

    assert first is not second
    assert built == [first, second]


class _FakeSequenceDetector:
    _ui_family = 'uncertainty'
    _ui_level = 'sequence'
    _ui_calibrated = False
    _ui_display_mode = 'raw'
    _ui_threshold = None
    _ui_task = 'hallucination'
    last_generated_text = None

    def __init__(self, chunk_scores):
        self.last_context_chunk_scores = chunk_scores


def test_view_model_surfaces_per_chunk_scores_for_multi_chunk_sequence_run():
    detector = _FakeSequenceDetector([
        {'index': 0, 'score': 0.2, 'chars': [0, 100]},
        {'index': 1, 'score': 0.9, 'chars': [100, 220]},
    ])

    view = ui.detection_view_model(([0.7], [1], None), 'answer text', detector)

    assert view['level'] == 'sequence'
    chunks = view['context_chunk_scores']
    assert [chunk['index'] for chunk in chunks] == [0, 1]
    assert chunks[1]['chars'] == [100, 220]
    assert chunks[1]['score'] == 0.9


def test_view_model_omits_chunk_scores_when_context_is_not_split():
    detector = _FakeSequenceDetector([{'index': 0, 'score': 0.5, 'chars': [0, 40]}])

    view = ui.detection_view_model(([0.5], [0], None), 'answer text', detector)

    assert 'context_chunk_scores' not in view


def test_qwen35_sequence_uncertainty_does_not_mix_calibration_contracts(monkeypatch):
    from sirin.ui import presets

    class Preset:
        family = 'uncertainty'

        @staticmethod
        def build(**kwargs):
            return kwargs

    monkeypatch.setitem(
        presets.PRESETS,
        'Uncertainty — Sequence (zero-shot)',
        Preset(),
    )
    monkeypatch.setattr(ui, 'load_generator', lambda *args: object())
    kwargs = ui.build_preset_detector(
        'Uncertainty — Sequence (zero-shot)',
        'cuda',
        '',
        'HF',
        'Qwen/Qwen3.5-35B-A3B',
        '',
        '',
        'OpenRouter',
        '',
    )

    assert kwargs['uncertainty_threshold'] is None
    assert kwargs['uncertainty_max_new_tokens'] is None
    assert kwargs['uncertainty_threshold_source'] is None


def test_qwen35_sequence_probe_records_threshold_source(monkeypatch):
    from sirin.ui import presets

    class Detector:
        pass

    class Preset:
        family = 'probing'

        @staticmethod
        def build(**kwargs):
            return Detector()

    preset_name = ui.LONGMEMEVAL_PROFILE['ui']['default_preset']
    monkeypatch.setitem(presets.PRESETS, preset_name, Preset())
    monkeypatch.setattr(ui, 'load_generator', lambda *args: object())

    detector = ui.build_preset_detector(
        preset_name,
        'cuda',
        '',
        'HF',
        'Qwen/Qwen3.5-35B-A3B',
        '',
        '',
        'OpenRouter',
        '',
    )

    assert 'validation split' in detector._ui_threshold_source


def test_longmemeval_profile_records_every_qwen35_checkpoint():
    profile = ui.load_longmemeval_profile()

    assert profile['model']['path'] == 'Qwen/Qwen3.5-35B-A3B'
    assert profile['uncertainty']['token']['threshold'] is None
    for task in ('hallucination_strict', 'answerability_strict'):
        assert set(profile['checkpoints'][task]) == {
            'linear',
            'catboost',
            'tabpfn',
            'best',
        }
        assert all(
            checkpoint['path'] for checkpoint in profile['checkpoints'][task].values()
        )
    # The multi-profile scan still surfaces this 35B profile as the default (first) option.
    assert ui.longmemeval_profiles()[0][0] == 'LongMemEval / Qwen3.5-35B-A3B'


def test_longmemeval_scan_loads_every_qwen35_4b_variant(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    profiles = dict(ui.longmemeval_profiles())

    # The 35B default plus the three 4B memory-variant profiles, all loaded without raising.
    assert set(profiles) == {
        'LongMemEval / Qwen3.5-35B-A3B',
        'Qwen3.5-4B · SimpleMem',
        'Qwen3.5-4B · LightMem',
        'Qwen3.5-4B · Mem0',
    }
    for label in ('Qwen3.5-4B · SimpleMem', 'Qwen3.5-4B · LightMem', 'Qwen3.5-4B · Mem0'):
        profile = profiles[label]
        assert profile['model']['path'] == 'Qwen/Qwen3.5-4B'
        assert profile['model']['revision'] == '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'
        probing = profile['probing']['hallucination_strict']
        assert probing['layers'] == [16, 27, 28, 29, 30, 31]
        assert probing['checkpoint_feature_shape'] == [6, 1, 2560]
        for task in ('hallucination_strict', 'answerability_strict'):
            assert set(profile['checkpoints'][task]) == {
                'linear',
                'catboost',
                'tabpfn',
                'best',
            }
            assert all(ck['path'] for ck in profile['checkpoints'][task].values())
            assert profile['checkpoints'][task]['best']['target'] == 'tabpfn'


def test_trusted_sidebar_profile_select_defaults_to_35b(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    st = _SidebarHarness()

    ui._sidebar(st)

    # With >1 profile the sidebar shows a profile select whose first (default) option is the 35B.
    select = next(
        (opts for label, opts in st.selectbox_calls if label == 'LongMemEval profile'),
        None,
    )
    assert select is not None
    assert select[0] == 'LongMemEval / Qwen3.5-35B-A3B'


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


def test_split_thinking_extracts_answer_from_fenced_json():
    visible, thinking = ui._split_thinking(
        '```json\n{"reasoning": "The context names two movies.", "answer": "2"}\n```'
    )

    assert visible == '2'
    assert thinking == 'The context names two movies.'


def test_detector_setup_error_checks_checkpoint_roots(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.delenv('SIRIN_UI_CHECKPOINT_ROOTS', raising=False)

    error = ui._detector_setup_error(
        {
            'use_hydra': False,
            'checkpoint_dir': '/tmp/checkpoint',
        }
    )

    assert 'SIRIN_UI_CHECKPOINT_ROOTS' in error


def test_detector_setup_error_requires_sequence_probe_checkpoint():
    error = ui._detector_setup_error(
        {
            'use_hydra': False,
            'checkpoint_dir': '',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        }
    )

    assert error == 'This preset needs a trained checkpoint directory.'


def test_compare_picker_omits_checkpoint_presets_that_cannot_run_as_side_b():
    from sirin.ui import presets

    offered = ui._compare_available_presets(
        presets.PSILOQA_TOKEN_LINEAR_PRESET, 'faithfulness'
    )

    # Side B never takes a typed checkpoint, so this preset could never run there.
    assert 'Probing — Sequence TabPFN (checkpoint)' not in offered
    assert presets.PSILOQA_TOKEN_LINEAR_PRESET not in offered  # side A itself
    # Bundled-checkpoint and zero-shot presets stay offered.
    assert presets.PSILOQA_TOKEN_LINEAR_PRESET_QWEN35 in offered
    assert 'Judge — API Sequence (zero-shot)' in offered
    assert all('Uncertainty' not in name for name in offered)


def test_compare_side_b_error_names_checkpoint_preset_and_gives_fix():
    import types

    from sirin.ui import presets

    cfg = {
        'use_hydra': False,
        'preset_name': presets.PSILOQA_TOKEN_LINEAR_PRESET,
        'checkpoint_dir': '',
    }

    error = ui._compare_side_b_error(
        cfg,
        types.SimpleNamespace(session_state={}),
        'Probing — Sequence TabPFN (checkpoint)',
    )

    assert 'Probing — Sequence TabPFN (checkpoint)' in error
    assert 'side A' in error


def test_compare_side_b_accepts_bundled_checkpoint_preset():
    import types

    from sirin.ui import presets

    cfg = {
        'use_hydra': False,
        'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        'checkpoint_dir': '/tmp/probe',
        'backend': 'HF',
    }

    error = ui._compare_side_b_error(
        cfg,
        types.SimpleNamespace(session_state={}),
        presets.PSILOQA_TOKEN_LINEAR_PRESET,
    )

    assert error is None


def test_detector_setup_error_rejects_api_backend_for_sequence_probe():
    error = ui._detector_setup_error(
        {
            'use_hydra': False,
            'backend': 'Custom OpenAI-compatible',
            'checkpoint_dir': '/tmp/checkpoint',
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
        }
    )

    assert error == (
        'Sequence probing requires the HF backend so SIRIN can extract hidden '
        'states from the selected generator model.'
    )


def test_detector_setup_error_preflights_sequence_tabpfn_shape(monkeypatch, tmp_path):
    import joblib

    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    joblib.dump(
        {'feature_shapes': [(4, 1, 1, 2048)]},
        tmp_path / 'compressor_config.joblib',
    )

    error = ui._detector_setup_error(
        {
            'use_hydra': False,
            'preset_name': 'Probing — Sequence TabPFN (checkpoint)',
            'checkpoint_dir': str(tmp_path),
        }
    )

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
    custom = ui.resolve_api_provider(
        'Custom OpenAI-compatible', 'http://localhost:11434/v1'
    )
    assert custom.api_key == 'EMPTY'
    assert custom.base_url == 'http://localhost:11434/v1'


def test_hydra_detector_is_blocked_unless_trusted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    with pytest.raises(ValueError, match='SIRIN_UI_TRUSTED_LOCAL'):
        ui._build_detector(
            {
                'use_hydra': True,
                'config_dir': '/tmp',
                'config_name': 'train',
                'overrides_text': '',
                'hydra_checkpoint': '',
            }
        )


def test_hydra_detector_preserves_answerability_task(monkeypatch, tmp_path):
    from contextlib import nullcontext
    from types import SimpleNamespace

    import hydra

    detector = SimpleNamespace()
    config = SimpleNamespace(
        model_adapter='adapter',
        feature_processor='processor',
        detector='detector',
        task_type='answerability',
    )
    objects = {
        'adapter': object(),
        'processor': object(),
        'detector': detector,
    }
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.setattr(hydra, 'compose', lambda **kwargs: config)
    monkeypatch.setattr(hydra, 'initialize_config_dir', lambda **kwargs: nullcontext())
    monkeypatch.setattr(
        hydra.utils, 'instantiate', lambda spec, **kwargs: objects[spec]
    )
    ui.load_detector.clear()

    loaded = ui.load_detector(str(tmp_path), 'train', (), '')

    assert loaded._ui_task == 'answerability'
    ui.load_detector.clear()


def test_external_confirmation_required_for_api_paths():
    assert ui.requires_external_confirmation({'backend': 'OpenAI', 'preset_name': 'x'})
    assert ui.requires_external_confirmation(
        {'backend': 'OpenRouter', 'preset_name': 'x'}
    )
    assert ui.requires_external_confirmation(
        {'backend': 'Anthropic', 'preset_name': 'x'}
    )
    assert ui.requires_external_confirmation(
        {
            'backend': 'HF',
            'preset_name': 'Judge — API Sequence (zero-shot)',
        }
    )
    assert not ui.requires_external_confirmation(
        {
            'backend': 'HF',
            'preset_name': 'Uncertainty — Sequence (zero-shot)',
        }
    )
    assert not ui.requires_external_confirmation(
        {
            'backend': 'Custom OpenAI-compatible',
            'custom_base_url': 'http://127.0.0.1:30110/v1',
            'preset_name': 'Uncertainty — Token (zero-shot)',
        }
    )
    assert ui.requires_external_confirmation(
        {
            'backend': 'Custom OpenAI-compatible',
            'custom_base_url': 'https://remote.example/v1',
            'preset_name': 'Uncertainty — Token (zero-shot)',
        }
    )


class _Preset:
    def __init__(self, name='Uncertainty — Sequence (zero-shot)', family='uncertainty'):
        self.name = name
        self.family = family
        self.description = 'desc'
        self.requires_checkpoint = False
        self.is_judge = family == 'judge'
        self.builtin_checkpoint = None


class _SidebarHarness:
    def __init__(self, selectbox_values=None, text_values=None, button_values=None):
        self.selectbox_values = selectbox_values or {}
        self.text_values = text_values or {}
        self.button_values = button_values or {}
        self.selectbox_calls = []
        self.text_input_calls = []
        self.button_calls = []
        self.caption_calls = []
        self.html_calls = []
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

    def html(self, body):
        self.html_calls.append(body)

    def caption(self, body):
        self.caption_calls.append(body)

    def divider(self):
        pass

    def expander(self, label, **kwargs):
        return self

    def container(self):
        return self

    def checkbox(self, label, value=False, **kwargs):
        return value

    def text_area(self, label, value='', **kwargs):
        return value

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
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    cfg = ui._sidebar(_SidebarHarness())

    assert cfg['preset_name'] == presets.PSILOQA_TOKEN_LINEAR_PRESET
    assert cfg['model_path'] == presets.PSILOQA_MODEL_ID
    assert ui._detector_setup_error(cfg) is None
    assert cfg['max_tokens'] == 192


def test_psiloqa_generator_uses_checkpoint_model_revision():
    from sirin.ui import presets

    cfg = ui._make_hf_config(presets.PSILOQA_MODEL_ID, 'cuda')

    assert cfg.revision == presets.PSILOQA_MODEL_REVISION


def test_native_streamlit_theme_matches_tokens_and_sets_fonts():
    import json
    import tomllib
    from pathlib import Path

    root = Path(ui.__file__).resolve().parents[2]
    theme = tomllib.loads((root / '.streamlit' / 'config.toml').read_text())['theme']
    light = json.loads((root / 'sirin' / 'ui' / 'tokens.json').read_text())['palette'][
        'light'
    ]
    expected = {
        'base': 'light',
        'primaryColor': light['brand'],
        'backgroundColor': light['canvas'],
        'secondaryBackgroundColor': light['card'],
        'textColor': light['ink'],
        'linkColor': light['link'],
    }
    assert {key: theme[key] for key in expected} == expected
    # Native widgets must resolve the same families as the host CSS and the component.
    assert theme['font'] == 'Manrope'
    assert theme['codeFont'] == 'IBM Plex Mono'


def test_trusted_sidebar_uses_longmemeval_qwen35_profile(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')

    cfg = ui._sidebar(_SidebarHarness())

    expected = ui.LONGMEMEVAL_PROFILE['checkpoints']['hallucination_strict']['tabpfn'][
        'path'
    ]
    assert cfg['preset_name'] == 'Probing — Sequence TabPFN (checkpoint)'
    assert cfg['model_path'] == 'Qwen/Qwen3.5-35B-A3B'
    assert cfg['checkpoint_dir'] == expected
    assert cfg['temperature'] == 0.0


def test_appearance_keeps_original_theme_and_motion_choices():
    st = _SidebarHarness()

    ui._appearance_sidebar(st)

    assert ('Theme', ['Light', 'Dark']) in st.selectbox_calls
    assert ('Background motion', ['Subtle', 'Static', 'Lively']) in st.selectbox_calls
    # Appearance is the single home for these controls and uses the census heading.
    assert any(
        'sirin-side-heading' in body and 'Appearance' in body for body in st.html_calls
    )
    motion_options = next(
        options for label, options in st.selectbox_calls if label == 'Background motion'
    )
    # Motion labels are exactly Static / Subtle / Lively — the 'Paused' alias is gone.
    assert set(motion_options) == {'Static', 'Subtle', 'Lively'}
    assert 'Paused' not in motion_options


def test_appearance_hydration_has_no_paused_alias():
    st = _SidebarHarness()
    st.session_state['sirin.workspace.v2'] = {'appearance': {'motion': 'static'}}

    ui._hydrate_v2_appearance(st)

    assert st.session_state['sirin.workspace.v2.bg_motion'] == 'Static'


def test_sidebar_renders_census_headings_and_meta_for_default_preset(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    st = _SidebarHarness()

    ui._sidebar(st)

    headings = ' '.join(st.html_calls)
    assert 'sirin-side-heading' in headings
    assert 'Detector' in headings and 'Generator' in headings
    assert 'layer 24 · τ = 0.38 · SHA-256-verified checkpoint' in st.caption_calls
    assert (
        'Device: cuda · bf16 · one shared model for generation and probing'
        in st.caption_calls
    )


def test_sidebar_hides_checkpoint_input_for_bundled_psiloqa_preset(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    st = _SidebarHarness()

    cfg = ui._sidebar(st)

    assert 'Using built-in PsiloQA checkpoint' in st.caption_calls
    assert not any(label == 'Checkpoint directory' for label, _ in st.text_input_calls)
    assert cfg['checkpoint_dir'] == ''
    assert ui._detector_setup_error(cfg) is None


def test_sidebar_still_shows_checkpoint_input_for_preset_needing_a_path(monkeypatch):
    from sirin.ui import presets

    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    preset = _Preset(name='Probing — Sequence TabPFN (checkpoint)', family='probing')
    preset.requires_checkpoint = True
    monkeypatch.setattr(presets, 'list_presets', lambda: [preset])

    st = _SidebarHarness(
        selectbox_values={'Backend': 'HF'},
        text_values={'Checkpoint directory': '/tmp/probe'},
    )
    cfg = ui._sidebar(st)

    assert any(label == 'Checkpoint directory' for label, _ in st.text_input_calls)
    assert 'Using built-in PsiloQA checkpoint' not in st.caption_calls
    assert cfg['checkpoint_dir'] == '/tmp/probe'


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
    assert ('Model', 'Qwen/Qwen3-4B') in st.text_input_calls
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
            return free_gib * 1024**3, 80 * 1024**3

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
            return free_gib * 1024**3, 80 * 1024**3

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
        lambda: [_Preset(name='Judge — API Span (zero-shot)', family='judge')],
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


def _judge_preset_sidebar(monkeypatch, **harness_kwargs):
    from sirin.ui import presets

    monkeypatch.setattr(
        presets,
        'list_presets',
        lambda: [_Preset(name='Judge — API Span (zero-shot)', family='judge')],
    )
    return _SidebarHarness(**harness_kwargs)


def test_trusted_custom_judge_lists_local_models(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.setattr(
        ui, 'local_openai_models', lambda base_url, timeout=1.5: ['Qwen/Qwen3.5-4B']
    )
    st = _judge_preset_sidebar(
        monkeypatch,
        selectbox_values={'Judge provider': ui.CUSTOM_PROVIDER, 'Backend': 'HF'},
    )

    cfg = ui._sidebar(st)

    assert cfg['judge_provider'] == ui.CUSTOM_PROVIDER
    assert cfg['judge_model'] == 'Qwen/Qwen3.5-4B'
    assert ('Judge model', ['Qwen/Qwen3.5-4B']) in st.selectbox_calls
    assert not any(label == 'Judge model' for label, _ in st.text_input_calls)


def test_custom_judge_falls_back_to_text_input_when_no_local_server(monkeypatch):
    monkeypatch.setenv('SIRIN_UI_TRUSTED_LOCAL', '1')
    monkeypatch.setattr(ui, 'local_openai_models', lambda base_url, timeout=1.5: [])
    st = _judge_preset_sidebar(
        monkeypatch,
        selectbox_values={'Judge provider': ui.CUSTOM_PROVIDER, 'Backend': 'HF'},
    )

    cfg = ui._sidebar(st)

    assert any(label == 'Judge model' for label, _ in st.text_input_calls)
    assert not any(label == 'Judge model' for label, _ in st.selectbox_calls)
    assert cfg['judge_provider'] == ui.CUSTOM_PROVIDER


def test_local_judge_model_probe_is_cached_per_session(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ui,
        'local_openai_models',
        lambda base_url, timeout=1.5: calls.append(base_url) or [],
    )
    st = _SidebarHarness()

    assert ui._local_judge_models(st) == []
    assert ui._local_judge_models(st) == []

    assert len(calls) == 1


def test_judge_preset_reserves_consent_slot_under_judge_key(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    st = _judge_preset_sidebar(monkeypatch, selectbox_values={'Backend': 'HF'})

    cfg = ui._sidebar(st)
    slot = cfg.pop('_consent_slot')

    assert slot is not None
    # The checkbox renders into the reserved slot; it now defaults to checked, so the
    # harness (which returns the widget default) reports consent granted.
    assert ui._external_confirmed(st, cfg, slot=slot) is True


def test_non_judge_sidebar_reserves_no_consent_slot(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)

    cfg = ui._sidebar(_SidebarHarness())

    assert cfg.pop('_consent_slot') is None


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
    view = ui.detection_view_model(
        ([[2.0, 0.5, 3.0]], [[1, 0, 1]], None), 'abc', detector
    )
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

    def expander(self, label, **kwargs):
        return _FakeExpander()


def test_visualizers_render_result_smoke():
    from sirin.ui import visualizers

    seq = {
        'level': 'sequence',
        'probability': 0.8,
        'prediction': 1,
        'calibrated': True,
        'threshold': 0.5,
    }
    tok = {
        'level': 'token',
        'answer': 'abc',
        'scores': [0.2, 0.8, 0.5],
        'norm_scores': [0.2, 0.8, 0.5],
        'calibrated': False,
    }
    claim = {
        'level': 'claim',
        'claims': [{'fact': 'x', 'prob': 0.4, 'pred': 0}],
        'overall_prob': 0.4,
        'overall_pred': 0,
    }
    for view in (seq, tok, claim):
        fake = _FakeSt()
        visualizers.render_result(fake, view)
        assert fake.rendered, f'nothing rendered for {view["level"]}'


def test_default_detector_input_guard_is_30k(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_MAX_DETECTOR_INPUT_CHARS', raising=False)

    assert ui._detector_input_size_error('x' * 30_000) is None
    assert 'limit 30,000' in ui._detector_input_size_error('x' * 30_001)


def test_only_exact_recorded_prompts_bypass_the_live_size_guard(monkeypatch):
    from sirin.ui.demo_cases import get_demo_case

    case = get_demo_case('e3038f8c')
    prompt = case['answer_prompt']
    monkeypatch.setenv('SIRIN_UI_MAX_DETECTOR_INPUT_CHARS', '10')

    assert ui._detector_input_size_error(prompt, 'A generated answer.') is None
    assert ui._detector_input_size_error(prompt + 'changed')


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
    judge = _Detector('token', 'judge', True, last_generations=['wa[SPAN]ter[/SPAN]'])
    scores = [0.1, 0.2, 0.3, 0.4, 0.5]  # len 5 == len('water')
    view = ui.detection_view_model(
        ([scores], [[0, 0, 1, 1, 0]], None), 'CHAT-ANSWER', judge
    )
    assert view['answer'] == 'water'
    assert view['answer_source'] == 'generation'
    assert view['tagged_generation'] == 'wa[SPAN]ter[/SPAN]'


def test_token_uncertainty_answer_source_is_original():
    unc = _Detector('token', 'uncertainty', False)
    view = ui.detection_view_model(([[0.2, 0.5, 0.9]], [[0, 1, 1]], None), 'abc', unc)
    assert view['answer'] == 'abc'
    assert view['answer_source'] == 'original'


def test_sequence_verdict_suppresses_reasoning():
    judge = _Detector(
        'sequence', 'judge', False, display_mode='verdict', last_generations=['1']
    )
    view = ui.detection_view_model(([2.3], [1], None), 'answer', judge)
    assert view['display_mode'] == 'verdict'
    assert view['reasoning'] is None
    assert view['prediction'] == 1


def test_claim_openai_view_is_uncalibrated():
    judge = _Detector('claim', 'judge', False)
    judge.claim_results = [
        {
            'overall_prob': 3.1,
            'overall_pred': 1,
            'facts': [{'fact': 'a', 'prob': 2.2, 'pred': 1}],
        }
    ]
    view = ui.detection_view_model(([3.1], [1], None), 'answer', judge)
    assert view['level'] == 'claim'
    assert view['calibrated'] is False


def test_claim_openai_judge_facts_carry_verdict_not_nll_score():
    """Regression: ClaimOpenAIJudge must put the 0/1 verdict in ``pred`` and the NLL score in
    ``prob`` (they were zipped in swapped order, so every claim rendered flagged). Runs the real
    detect() with a fake adapter + regex SENTENCE split (no network, no local model)."""
    from sirin.definitions import SplitStrategy
    from sirin.detection.judging import ClaimOpenAIJudge
    from sirin.detection.splitters import SplitManager
    from sirin.models.detection import OpenAIJudgeConfig, SplitConfig

    class FakeAdapter:
        # per-claim verdict: claim 1 -> '1' (hallucinated), claim 2 -> '0' (grounded).
        def sample(self, inputs, return_logprobs=False, **kwargs):
            digits = ['1', '0'][: len(inputs)]
            logprobs = [[[-0.1, -2.0]] for _ in inputs]  # first-token top-2
            return (digits, logprobs) if return_logprobs else digits

    judge = object.__new__(ClaimOpenAIJudge)  # bypass model-loading __init__
    judge.config = OpenAIJudgeConfig(user_prompt='{sample}', temperature=0.0)
    judge.model_adapter = FakeAdapter()
    judge.response_splitter_config = SplitConfig(strategy=SplitStrategy.SENTENCE)
    judge.response_splitter = SplitManager(config=judge.response_splitter_config)
    judge.split_model = judge.model_adapter
    judge.threshold = 0.5
    judge._context_splitter = None
    judge.claim_results = None

    sample = ui.build_sample('ctx + question', 'Alpha is false. Beta is true.')
    result = judge.detect([sample])
    facts = judge.claim_results[0]['facts']

    # pred is the 0/1 verdict, prob is the NLL score — never swapped.
    assert [f['pred'] for f in facts] == [1, 0]
    assert facts[0]['prob'] == pytest.approx(0.1)

    view = ui.detection_view_model(result, 'Alpha is false. Beta is true.', judge)
    assert view['level'] == 'claim'
    assert [row['pred'] for row in view['claims']] == [1, 0]


def test_styles_inject_substitutes_placeholders_and_honors_motion():
    from sirin.ui import styles

    calls = []

    class _S:
        def html(self, body):
            calls.append(body)

    styles.inject_global_styles(_S(), motion='subtle')
    css = calls[0]
    assert '@@' not in css  # every placeholder substituted
    assert 'url("app/static/silk_bg.jpg")' in css  # silk served as a static file, not base64
    assert '@keyframes sirin-breathe-subtle' in css
    assert 'sirin-breathe-subtle' in css  # subtle animation wired

    static_calls = []

    class _S2:
        def html(self, body):
            static_calls.append(body)

    styles.inject_global_styles(_S2(), motion='static')
    assert 'animation: none' in static_calls[0]
