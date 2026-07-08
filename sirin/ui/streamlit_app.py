from __future__ import annotations

import base64
import math
import os
import shlex
from html import escape
from pathlib import Path
from typing import Any

from sirin.ui.styles import PALETTE

LOGO_PATH = Path(__file__).parent / 'assets' / 'logo.png'


def _cache_resource(func):
    try:
        import streamlit as st

        return st.cache_resource(show_spinner=False)(func)
    except Exception:
        return func


@_cache_resource
def _logo_data_uri() -> str:
    return 'data:image/png;base64,' + base64.b64encode(LOGO_PATH.read_bytes()).decode()


def build_sample(prompt: str, answer: str) -> list[dict[str, str]]:
    return [
        {'role': 'user', 'content': prompt},
        {'role': 'assistant', 'content': answer},
    ]


def _hex_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"


_RISK_RGB = _hex_rgb(PALETTE['risk'])


def score_heatmap(text: str, scores: list[float]) -> str:
    spans = []
    for index, char in enumerate(text):
        score = float(scores[index]) if index < len(scores) else 0.0
        score = min(1.0, max(0.0, score if math.isfinite(score) else 0.0))
        body = '<br>' if char == '\n' else escape(char) or '&nbsp;'
        spans.append(
            f'<span style="background: rgba({_RISK_RGB}, '
            f'{0.10 + score * 0.75:.3f});">{body}</span>'
        )
    return (
        '<span class="sirin-heatmap" style="line-height: 1.9;'
        'color: var(--sirin-text);">'
        + ''.join(spans)
        + '</span>'
    )


def _to_plain(value: Any) -> Any:
    if hasattr(value, 'tolist'):
        return value.tolist()
    return value


def _is_nested_list(value: Any) -> bool:
    value = _to_plain(value)
    return bool(value) and isinstance(value, list) and isinstance(value[0], list)


def _first(value: Any) -> Any:
    value = _to_plain(value)
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _detector_level(detector: Any) -> str | None:
    level = getattr(detector, 'detection_level', None)
    if level is None:
        return None
    return getattr(level, 'value', str(level)).lower()


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _clamp01(value: Any) -> float:
    number = _to_float(value)
    return min(1.0, max(0.0, number if number is not None else 0.0))


def _minmax(scores: list[float]) -> list[float]:
    numbers = [_to_float(s) for s in scores]
    valid = [n for n in numbers if n is not None]
    if not valid:
        return [0.0 for _ in scores]
    low, high = min(valid), max(valid)
    if high <= low:
        # flat scores -> mid intensity, avoids div-by-zero.
        return [0.5 if n is not None else 0.0 for n in numbers]
    span = high - low
    return [((n - low) / span) if n is not None else 0.0 for n in numbers]


def flatten_claims(claims: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    rows = []
    for sample_index, claim in enumerate(claims or []):
        for fact in claim.get('facts') or []:
            rows.append(
                {
                    'sample': sample_index,
                    'fact': fact.get('fact'),
                    'prob': fact.get('prob'),
                    'pred': fact.get('pred'),
                    'overall_prob': claim.get('overall_prob'),
                    'overall_pred': claim.get('overall_pred'),
                }
            )
        if not claim.get('facts'):
            rows.append(claim)
    return rows


def _describe(detector: Any) -> dict[str, Any]:
    if detector is None:
        return {
            'family': 'unknown',
            'calibrated': True,
            'threshold': None,
            'display_mode': None,
        }
    try:
        from sirin.ui import presets

        info = presets.describe_detector(detector)
        return {
            'family': info.get('family', 'unknown'),
            'calibrated': bool(info.get('calibrated', True)),
            'threshold': info.get('threshold', getattr(detector, 'threshold', None)),
            'display_mode': info.get('display_mode'),
        }
    except (KeyError, AttributeError) as e:
        from loguru import logger as lg
        lg.debug(f"Detector metadata lookup failed: {e}")
        return {
            'family': 'unknown',
            'calibrated': True,
            'threshold': getattr(detector, 'threshold', None),
            'display_mode': None,
        }


def _reasoning(detector: Any) -> str | None:
    gens = getattr(detector, 'last_generations', None)
    if isinstance(gens, list) and gens:
        return str(gens[0])
    if isinstance(gens, str) and gens:
        return gens
    return None


def _spans(detector: Any) -> Any:
    spans = getattr(detector, 'last_spans', None)
    if isinstance(spans, list) and spans:
        return spans[0]
    return None


def _overall(rows: list[dict[str, Any]], key: str) -> Any:
    for row in rows:
        if isinstance(row, dict) and row.get(key) is not None:
            return row.get(key)
    return None


def _strip_span_tags(text: str) -> str:
    # token judges wrap flagged spans in [SPAN]..[/SPAN]; char scores are tag-stripped.
    return text.replace('[SPAN]', '').replace('[/SPAN]', '')


def _pick_answer_text(
    n_scores: int, detector: Any, chat_answer: str, family: str
) -> tuple[str, str, str | None]:
    # per-char scores align to whichever answer text has the SAME length. Judges score
    # their own tag-stripped generation; probing/uncertainty score the original answer. Pick by
    # length match so we never hard-code the (disputed) original-vs-regenerated question.
    gens = getattr(detector, 'last_generations', None)
    tagged = gens[0] if isinstance(gens, list) and gens and isinstance(gens[0], str) else None
    generated = getattr(detector, 'last_generated_text', None)

    if family == 'judge' and tagged is not None:
        candidates = [(_strip_span_tags(tagged), 'generation'), (chat_answer or '', 'original')]
    else:
        candidates = [(chat_answer or '', 'original')]
        if generated:
            candidates.append((generated, 'generation'))
    for text, source in candidates:
        if len(text) == n_scores:
            return text, source, tagged
    text, source = candidates[0]
    return text, source, tagged


def detection_view_model(
    result: tuple[Any, Any, Any],
    answer: str,
    detector: Any,
) -> dict[str, Any]:
    probs, preds, _ = result
    level = _detector_level(detector)
    info = _describe(detector)
    reasoning = _reasoning(detector)
    spans = _spans(detector)

    claims = getattr(detector, 'claim_results', None)
    if claims or level == 'claim':
        rows = flatten_claims(claims)
        return {
            'level': 'claim',
            'display_mode': info.get('display_mode') or 'claim-cards',
            'claims': rows,
            'overall_prob': _overall(rows, 'overall_prob'),
            'overall_pred': _overall(rows, 'overall_pred'),
            'calibrated': info['calibrated'],
            'family': info['family'],
            'reasoning': reasoning,
        }

    probs = _to_plain(probs)
    preds = _to_plain(preds)
    if level == 'token' or (level is None and _is_nested_list(probs)):
        first_preds = _first(preds)
        scores = list(_first(probs) or [])
        norm = (
            [_clamp01(s) for s in scores]
            if info['calibrated']
            else _minmax(scores)
        )
        answer_text, answer_source, tagged = _pick_answer_text(
            len(scores), detector, answer, info['family']
        )
        return {
            'level': 'token',
            'display_mode': info.get('display_mode') or 'heatmap',
            'scores': scores,
            'predictions': first_preds if isinstance(first_preds, list) else [],
            'answer': answer_text,
            'answer_source': answer_source,
            'calibrated': info['calibrated'],
            'family': info['family'],
            'norm_scores': norm,
            'spans': spans,
            'tagged_generation': tagged,
            # tagged_generation already surfaces a judge's annotated answer.
            'reasoning': None,
        }

    probability = _first(probs)
    is_multiclass = isinstance(probability, list)
    if is_multiclass:
        # multiclass is a property of the result shape, not the detector -> it overrides
        # whatever display_mode describe_detector guessed from the detector alone.
        display_mode = 'multiclass'
    else:
        display_mode = info.get('display_mode')
        if not display_mode:
            if not info['calibrated']:
                display_mode = 'verdict' if info['family'] == 'judge' else 'raw'
            else:
                display_mode = 'gauge'

    class_probs = probability if is_multiclass else None
    class_index = (
        max(range(len(probability)), key=lambda i: probability[i])
        if is_multiclass and probability
        else None
    )
    return {
        'level': 'sequence',
        'display_mode': display_mode,
        'probability': probability,
        'prediction': _first(preds),
        'calibrated': info['calibrated'],
        'threshold': info['threshold'],
        'family': info['family'],
        'raw_prob': None if info['calibrated'] else _to_float(probability),
        'class_probs': class_probs,
        'class_index': class_index,
        'generated_text': getattr(detector, 'last_generated_text', None),
        # in verdict mode show a reasoning model's chain, but not a bare '0'/'1'.
        'reasoning': (
            (reasoning if reasoning and len(str(reasoning).strip()) > 3 else None)
            if display_mode == 'verdict'
            else reasoning
        ),
        'spans': spans,
    }


def debug_summary(debug: dict[str, Any] | None) -> dict[str, Any]:
    if not debug:
        return {}
    summary = {
        'processor': debug.get('processor'),
        'feature_type': debug.get('feature_type'),
    }
    for key, value in debug.items():
        if key.endswith('_shape'):
            summary[key] = value
    return {key: value for key, value in summary.items() if value is not None}


def _default_config_dir() -> str:
    return str(Path(__file__).resolve().parents[1] / 'configs')


JUDGE_MODELS = [
    'openai/gpt-3.5-turbo',
    'nvidia/nemotron-3-super-120b-a12b:free',
]


@_cache_resource
def load_generator(
    backend: str,
    model_path: str,
    device: str,
    base_url: str,
) -> Any:
    if backend == 'HF':
        from sirin.inference.adapters.hf_adapter import HfModelAdapter
        from sirin.models.inference import HFConfig

        return HfModelAdapter(HFConfig(model_path=model_path, device=device))
    if backend == 'OpenAI':
        from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter
        from sirin.models.inference import OpenAIConfig

        return OpenAIModelAdapter(
            OpenAIConfig(
                model_path=model_path,
                device='cpu',
                base_url=base_url or None,
                api_key=os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY'),
            )
        )
    if backend == 'vLLM':
        from sirin.inference.adapters.vllm_adapter import VllmModelAdapter
        from sirin.models.inference import VLLMConfig

        return VllmModelAdapter(VLLMConfig(model_path=model_path, device=device))
    raise ValueError(f"Unknown backend: {backend}")


def generate_answer(
    adapter: Any,
    backend: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    inputs: list[Any] = (
        [prompt] if backend == 'vLLM' else [[{'role': 'user', 'content': prompt}]]
    )
    return adapter.sample(
        inputs,
        max_tokens=max_tokens,
        temperature=temperature,
    )[0]


@_cache_resource
def load_detector(
    config_dir: str,
    config_name: str,
    overrides: tuple[str, ...],
    checkpoint_dir: str,
) -> Any:
    import hydra
    from hydra import compose, initialize_config_dir

    with initialize_config_dir(
        version_base=None,
        config_dir=str(Path(config_dir).expanduser().resolve()),
    ):
        cfg = compose(config_name=config_name, overrides=list(overrides))

    adapter = hydra.utils.instantiate(cfg.model_adapter)
    processor = hydra.utils.instantiate(cfg.feature_processor, extractor=adapter)
    detector = hydra.utils.instantiate(cfg.detector, feature_processor=processor)
    if checkpoint_dir:
        detector.load(str(Path(checkpoint_dir).expanduser()))
    return detector


@_cache_resource
def build_preset_detector(
    preset_name: str,
    device: str,
    checkpoint_dir: str,
    gen_backend: str,
    gen_model: str,
    gen_base_url: str,
    judge_model: str,
    judge_api_key: str,
) -> Any:
    from sirin.ui import presets

    preset = presets.PRESETS[preset_name]
    generator_adapter = None
    if gen_backend == 'HF' and preset.family in ('uncertainty', 'probing'):
        generator_adapter = load_generator('HF', gen_model, device, gen_base_url)
    return preset.build(
        device=device,
        checkpoint_dir=checkpoint_dir or None,
        generator_adapter=generator_adapter,
        judge_model=judge_model or None,
        judge_api_key=judge_api_key or None,
    )


SUGGESTIONS = [
    'Context: The Eiffel Tower is in Paris, France.\nQuestion: In which city is the Eiffel Tower?',
    'Context: Our return policy allows refunds within 30 days.\nQuestion: Can I get a refund after 45 days?',
    'Context: Marie Curie won Nobel Prizes in Physics (1903) and Chemistry (1911).\nQuestion: How many Nobel Prizes did Marie Curie win, and in what fields?',
]


def _hero(st: Any) -> None:
    st.html(
        '<div style="background:var(--sirin-surface);border:1px solid var(--sirin-border);border-radius:18px;'
        'padding:1.5rem 1.7rem;margin:0.2rem 0 1.1rem;box-shadow:0 20px 50px var(--sirin-shadow);'
        'backdrop-filter:blur(18px) saturate(135%);-webkit-backdrop-filter:blur(18px) saturate(135%);">'
        '<div style="font-family:var(--sirin-mono);font-size:0.72rem;letter-spacing:0.16em;'
        'text-transform:uppercase;color:var(--sirin-hot);margin-bottom:0.55rem;">'
        'Hallucination &amp; answerability detection</div>'
        '<div style="font-size:1.55rem;font-weight:700;letter-spacing:-0.015em;'
        'margin-bottom:0.45rem;">Chat with a model — then see what SIRIN sees.</div>'
        '<div style="color:var(--sirin-muted);max-width:62ch;line-height:1.6;">'
        'Give a question together with its context. SIRIN generates the answer, then flags '
        'unfaithful or unanswerable content at the sequence, token, or claim level.</div>'
        '<div style="margin-top:1.1rem;display:inline-flex;flex-direction:column;gap:0.2rem;'
        'font-family:var(--sirin-mono);font-size:0.82rem;background:var(--sirin-surface-2);'
        'border:1px solid var(--sirin-border);border-radius:10px;padding:0.65rem 0.85rem;'
        'color:var(--sirin-muted);">'
        '<span><span style="color:var(--sirin-mint);">Context:</span> The Eiffel Tower is in Paris.</span>'
        '<span><span style="color:var(--sirin-mint);">Question:</span> In which city is the Eiffel Tower?</span>'
        '</div></div>'
    )


def _sidebar(st: Any) -> dict[str, Any]:
    from sirin.ui import presets

    with st.sidebar:
        st.header(':material/tune: Detector')
        preset_objs = presets.list_presets()
        names = [p.name for p in preset_objs]
        by_name = {p.name: p for p in preset_objs}
        preset_name = st.selectbox('Preset', names)
        preset = by_name[preset_name]
        st.caption(preset.description)

        is_judge = bool(getattr(preset, 'is_judge', False)) or preset.family == 'judge'
        judge_model = JUDGE_MODELS[0]
        if is_judge:
            judge_model = st.selectbox('Judge model', JUDGE_MODELS)
            has_key = bool(os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY'))
            if has_key:
                st.caption(':material/key: API key detected (OpenRouter/OpenAI).')
            else:
                st.caption(':red[:material/key_off: Set OPENROUTER_API_KEY to use the API judge.]')

        checkpoint_dir = ''
        if preset.requires_checkpoint:
            checkpoint_dir = st.text_input(
                'Checkpoint directory',
                value='',
                help="Leave blank to use this preset's built-in checkpoint (if any).",
            )

        st.divider()
        st.header(':material/smart_toy: Generator')
        backend = st.selectbox('Backend', ['HF', 'OpenAI', 'vLLM'])
        default_model = 'gpt-4o-mini' if backend == 'OpenAI' else 'Qwen/Qwen2.5-3B-Instruct'
        model_path = st.text_input('Model', value=default_model)
        device = st.text_input('Device', value='cuda')
        base_url = st.text_input(
            'API base URL',
            value='https://api.openai.com/v1' if backend == 'OpenAI' else '',
        )
        max_tokens = st.number_input('Max tokens', min_value=1, value=256)
        temperature = st.slider('Temperature', min_value=0.0, max_value=2.0, value=0.7)

        with st.expander('Advanced: Hydra detector', icon=':material/build:'):
            use_hydra = st.checkbox('Use Hydra config instead of preset', value=False)
            config_dir = st.text_input('Config directory', value=_default_config_dir())
            config_name = st.text_input('Config name', value='train')
            overrides_text = st.text_area(
                'Hydra overrides',
                value='train_dataset_path=null eval_dataset_path=null',
            )
            hydra_checkpoint = st.text_input('Hydra checkpoint directory', value='')

    return {
        'backend': backend,
        'model_path': model_path,
        'device': device,
        'base_url': base_url,
        'max_tokens': int(max_tokens),
        'temperature': float(temperature),
        'preset_name': preset_name,
        'judge_model': judge_model,
        'checkpoint_dir': checkpoint_dir,
        'use_hydra': use_hydra,
        'config_dir': config_dir,
        'config_name': config_name,
        'overrides_text': overrides_text,
        'hydra_checkpoint': hydra_checkpoint,
    }


def _build_detector(cfg: dict[str, Any]) -> Any:
    if cfg['use_hydra']:
        return load_detector(
            cfg['config_dir'],
            cfg['config_name'],
            tuple(shlex.split(cfg['overrides_text'] or '')),
            cfg['hydra_checkpoint'],
        )
    return build_preset_detector(
        cfg['preset_name'],
        cfg['device'],
        cfg['checkpoint_dir'],
        cfg['backend'],
        cfg['model_path'],
        cfg['base_url'],
        cfg['judge_model'],
        '',  # preset resolves the key from OPENROUTER_API_KEY/OPENAI_API_KEY env.
    )


def _run_turn(st: Any, prompt: str, cfg: dict[str, Any], visualizers: Any) -> dict[str, Any]:
    message: dict[str, Any] = {'role': 'assistant', 'content': ''}
    try:
        with st.spinner('Generating answer...'):
            adapter = load_generator(
                cfg['backend'], cfg['model_path'], cfg['device'], cfg['base_url']
            )
            answer = generate_answer(
                adapter,
                cfg['backend'],
                prompt,
                cfg['max_tokens'],
                cfg['temperature'],
            )
    except Exception as error:  # noqa: BLE001 - surface any backend failure to the user
        answer = f"Generation failed: {error}"
        message['content'] = answer
        st.error(answer)
        return message

    message['content'] = answer
    st.markdown(answer)

    try:
        with st.spinner('Running SIRIN detector...'):
            detector = _build_detector(cfg)
            result = detector.detect([build_sample(prompt, answer)])
            view = detection_view_model(result, answer, detector)
            message['view'] = view
            message['method_scores'] = getattr(detector, 'last_method_scores', None)
            processor = getattr(detector, 'feature_processor', None)
            message['debug'] = debug_summary(getattr(processor, 'last_debug', None))
    except Exception as error:  # noqa: BLE001 - detector loading/running can fail many ways
        st.error(f"Detection failed: {error}")
        return message

    _render_analysis(st, message, visualizers)
    return message


def _render_analysis(st: Any, message: dict[str, Any], visualizers: Any) -> None:
    view = message.get('view')
    if not view:
        return
    visualizers.render_result(st, view)
    method_scores = message.get('method_scores')
    if method_scores:
        with st.expander('Per-method uncertainty', icon=':material/query_stats:'):
            visualizers._render_method_scores(st, method_scores)
    if message.get('debug'):
        with st.expander('Debug', icon=':material/bug_report:'):
            st.json(message['debug'])


def _view_switch(st: Any) -> str:
    with st.sidebar:
        return st.radio('View', ['Chat', 'Explorer'], key='ui_view', horizontal=True)


def _appearance_sidebar(st: Any) -> None:
    with st.sidebar:
        st.divider()
        st.header(':material/palette: Appearance')
        st.selectbox('Theme', ['Dark', 'Light'], key='ui_theme')
        st.selectbox(
            'Background motion',
            ['Subtle', 'Static', 'Lively'],
            key='bg_motion',
            help='Silk backdrop animation. Static is lightest for low-power devices.',
        )


def main() -> None:
    import streamlit as st

    from sirin.ui import styles, visualizers

    st.set_page_config(page_title='SIRIN', page_icon=str(LOGO_PATH), layout='wide')
    motion = str(st.session_state.get('bg_motion', 'Subtle')).lower()
    theme = str(st.session_state.get('ui_theme', 'Dark')).lower()
    styles.inject_global_styles(st, motion=motion, theme=theme)
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">'
        f'<img src="{_logo_data_uri()}" width="48" style="display:block;" alt="" aria-hidden="true"/>'
        f'<h1 style="margin:0;font-size:2.5rem;font-weight:700;line-height:1;">SIRIN</h1>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        'Semantic Inconsistency Recognition & Inspection Nexus — '
        'chat, then inspect hallucination & answerability signals.'
    )

    view_mode = _view_switch(st)
    if view_mode == 'Explorer':
        from sirin.ui import attention_explorer

        attention_explorer.render(st)
        _appearance_sidebar(st)
        return

    cfg = _sidebar(st)
    _appearance_sidebar(st)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        _hero(st)
        st.markdown('###### Quick starts')
        labels = [suggestion.split('\n')[0] for suggestion in SUGGESTIONS]
        choice = st.pills(
            'Suggestions',
            labels,
            selection_mode='single',
            label_visibility='collapsed',
        )
        if choice:
            st.session_state.pending = SUGGESTIONS[labels.index(choice)]
            st.rerun()

    for message in st.session_state.messages:
        avatar = str(LOGO_PATH) if message['role'] == 'assistant' else None
        with st.chat_message(message['role'], avatar=avatar):
            st.markdown(message['content'])
            if message['role'] == 'assistant':
                _render_analysis(st, message, visualizers)

    incoming = st.chat_input('Enter context + question...')
    if not incoming and st.session_state.get('pending'):
        incoming = st.session_state.pop('pending')

    if incoming:
        st.session_state.messages.append({'role': 'user', 'content': incoming})
        with st.chat_message('user'):
            st.markdown(incoming)
        with st.chat_message('assistant', avatar=str(LOGO_PATH)):
            message = _run_turn(st, incoming, cfg, visualizers)
        st.session_state.messages.append(message)


if __name__ == '__main__':
    main()
