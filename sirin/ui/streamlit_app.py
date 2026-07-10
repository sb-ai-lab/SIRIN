from __future__ import annotations

import base64
import json
import math
import os
import re
import shlex
from html import escape
from pathlib import Path
from typing import Any

from sirin.ui.path_policy import (
    is_trusted_local,
    require_checkpoint_path,
)
from sirin.ui.providers import (
    ANTHROPIC_PROVIDER,
    CUSTOM_PROVIDER,
    OPENAI_PROVIDER,
    OPENROUTER_PROVIDER,
    API_PROVIDER_KEY_ENVS,
    provider_models,
    resolve_api_provider,
)
from sirin.ui.styles import risk_color, risk_ink

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


def _segments(text: str) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(0)) for m in re.finditer(r'\s+|\S+', text)]


def _segment_values(
    text: str,
    segments: list[tuple[int, int, str]],
    values: list[Any] | None,
) -> list[Any | None]:
    values = values or []
    if len(values) == len(text):
        return [
            max(values[start:end], default=None)
            for start, end, _ in segments
        ]
    if len(values) == len(segments):
        return list(values)

    non_ws = [i for i, (_, _, piece) in enumerate(segments) if not piece.isspace()]
    if len(values) <= len(non_ws):
        out: list[Any | None] = [None] * len(segments)
        for slot, value in zip(non_ws, values):
            out[slot] = value
        return out
    return [values[i] if i < len(values) else None for i in range(len(segments))]


def _pred_attr(pred: Any) -> str:
    if pred in (0, 0.0, '0', False):
        return '0'
    if pred in (1, 1.0, '1', True):
        return '1'
    return ''


def _html_piece(piece: str) -> str:
    out = []
    for char in piece:
        if char == '\n':
            out.append('<br>')
        elif char == ' ':
            out.append('&nbsp;')
        elif char == '\t':
            out.append('&nbsp;&nbsp;&nbsp;&nbsp;')
        else:
            out.append(escape(char))
    return ''.join(out) or '&nbsp;'


def score_heatmap(
    text: str,
    scores: list[float],
    *,
    predictions: list[Any] | None = None,
) -> str:
    segments = _segments(text)
    segment_scores = _segment_values(text, segments, scores)
    segment_preds = _segment_values(text, segments, predictions)
    spans = []
    for index, ((start, end, piece), score, pred) in enumerate(
        zip(segments, segment_scores, segment_preds)
    ):
        score_num = _to_float(score)
        pred_value = _pred_attr(pred)
        attrs = [
            'class="sirin-token-evidence"',
            f'data-index="{start}"',
            f'data-end="{end}"',
        ]
        if pred_value:
            attrs.append(f'data-pred="{pred_value}"')
        if score_num is None:
            attrs.extend(['data-score="missing"', 'data-missing="true"'])
            title = f'chars {start}-{end} | score missing'
            style = (
                'display:inline;white-space:pre-wrap;padding:0.05rem 0.14rem;'
                'border-radius:0.25rem;background:rgba(148,163,184,0.14);'
                'border-bottom:3px dashed var(--sirin-faint);'
            )
        else:
            score_num = _clamp01(score_num)
            fill = risk_color(score_num)
            attrs.append(f'data-score="{score_num:.3f}"')
            title = f'chars {start}-{end} | score {score_num:.3f}'
            if pred_value:
                title += f' | pred {pred_value}'
            style = (
                'display:inline;white-space:pre-wrap;padding:0.05rem 0.14rem;'
                f'border-radius:0.25rem;background:{fill}26;'
                f'border-bottom:3px solid {fill};color:var(--sirin-text);'
            )
        attrs.append(f'title="{escape(title)}"')
        attrs.append(f'style="{style}"')
        spans.append(f'<span {" ".join(attrs)}>{_html_piece(piece)}</span>')
    return '<span class="sirin-heatmap" style="line-height:2.25;white-space:pre-wrap;">' + ''.join(spans) + '</span>'


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


_NO_FINAL_ANSWER = 'No final answer produced after the hidden thinking block.'


def _split_thinking(text: str) -> tuple[str, str | None]:
    match = re.search(r'<think>\s*(.*?)\s*</think>\s*', text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return _split_json_reasoning(text, None)
    visible = (text[:match.start()] + text[match.end():]).strip()
    thinking = match.group(1).strip()
    return _split_json_reasoning(visible, thinking or None)


def _split_json_reasoning(text: str, thinking: str | None) -> tuple[str, str | None]:
    if not str(text or '').strip() and thinking:
        return _NO_FINAL_ANSWER, thinking
    try:
        obj = json.loads(text)
    except (TypeError, ValueError):
        return text, thinking
    if not isinstance(obj, dict) or 'answer' not in obj or 'reasoning' not in obj:
        return text, thinking
    answer = obj.get('answer')
    visible = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
    reasoning = str(obj.get('reasoning') or '').strip()
    hidden = '\n\n'.join(part for part in (thinking, reasoning) if part)
    return visible.strip(), hidden or None


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


def _clean_field(value: Any) -> str:
    return '' if value is None else str(value).strip()


def _clean_path_field(value: Any) -> str:
    text = _clean_field(value)
    if not text:
        return ''
    for part in text.split('|'):
        part = part.strip(' `')
        if part.startswith(('/', '~')):
            text = part
            break
    text = text.splitlines()[0].strip(' `|')
    return re.split(
        r'\s+(?:Backend|Model|Device|Max tokens|Temperature|Theme|Background motion)\b',
        text,
        maxsplit=1,
    )[0].strip(' `|')


_LARGE_HF_MODEL_RE = re.compile(r'(?<!\d)(?:3[0-9]|[4-9]\d|[1-9]\d{2,})B', re.IGNORECASE)
_FEATURE_SHAPE_MISMATCH_RE = re.compile(
    r'Feature \d+ shape mismatch: expected \(([^)]*)\), got \(([^)]*)\)'
)
_AUTO_DEVICE_MAP_GPUS_ENV = 'SIRIN_UI_AUTO_DEVICE_MAP_GPUS'
_MAX_DETECTOR_INPUT_CHARS_ENV = 'SIRIN_UI_MAX_DETECTOR_INPUT_CHARS'
_DEFAULT_MAX_DETECTOR_INPUT_CHARS = 12_000
_DETECTOR_PREFLIGHT_ANSWER = 'SIRIN detector preflight answer.'


def _looks_large_hf_model(model_path: str) -> bool:
    return bool(_LARGE_HF_MODEL_RE.search(_clean_field(model_path).replace(' ', '')))


def _device_map_max_memory() -> dict[int, str]:
    try:
        import torch

        if not torch.cuda.is_available():
            return {}
        candidates: list[tuple[int, int]] = []
        for idx in range(torch.cuda.device_count()):
            try:
                free_bytes, _total_bytes = torch.cuda.mem_get_info(idx)
            except Exception:
                continue
            usable_gib = int((free_bytes / (1024 ** 3)) * 0.85)
            if usable_gib >= 8:
                candidates.append((idx, usable_gib))
        try:
            limit = max(1, int(os.getenv(_AUTO_DEVICE_MAP_GPUS_ENV, '2')))
        except ValueError:
            limit = 2
        picked = sorted(candidates, key=lambda item: item[1], reverse=True)[:limit]
        return {idx: f'{usable_gib}GiB' for idx, usable_gib in picked}
    except Exception:
        return {}


def _make_hf_config(model_path: str, device: str) -> Any:
    from sirin.models.inference import HFConfig

    model_path = _clean_field(model_path)
    device = _clean_field(device)
    auto_device_map = (
        device.lower() in ('auto', 'device_map:auto', 'device-map:auto')
        or (device.lower() == 'cuda' and _looks_large_hf_model(model_path))
    )
    if auto_device_map:
        return HFConfig(
            model_path=model_path,
            device=None,
            device_map='auto',
            max_memory=_device_map_max_memory() or None,
            attn_implementation='sdpa',
        )
    return HFConfig(model_path=model_path, device=device)


JUDGE_MODELS = [
    'openai/gpt-3.5-turbo',
    'nvidia/nemotron-3-super-120b-a12b:free',
]
HF_MODELS = ['Qwen/Qwen3.5-4B', 'Qwen/Qwen2.5-3B-Instruct']
LOCAL_DEVICES = ['cuda', 'cpu']
API_BACKENDS = (OPENAI_PROVIDER, OPENROUTER_PROVIDER, ANTHROPIC_PROVIDER, CUSTOM_PROVIDER)


@_cache_resource
def load_generator(
    backend: str,
    model_path: str,
    device: str,
    custom_base_url: str = '',
) -> Any:
    model_path = _clean_field(model_path)
    device = _clean_field(device)
    custom_base_url = _clean_field(custom_base_url)
    if backend == 'HF':
        from sirin.inference.adapters.hf_adapter import HfModelAdapter

        return HfModelAdapter(_make_hf_config(model_path, device))
    if backend in API_BACKENDS:
        from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter
        from sirin.models.inference import OpenAIConfig

        provider = resolve_api_provider(backend, custom_base_url)
        return OpenAIModelAdapter(
            OpenAIConfig(
                model_path=model_path,
                device='cpu',
                base_url=provider.base_url,
                api_key=provider.api_key,
            )
        )
    if backend == 'vLLM':
        from sirin.inference.adapters.vllm_adapter import VllmModelAdapter
        from sirin.models.inference import VLLMConfig

        return VllmModelAdapter(VLLMConfig(model_path=model_path, device=device))
    raise ValueError(f"Unknown backend: {backend}")


def _unload_cached_models() -> None:
    try:
        from sirin.inference.model_manager import ModelManager

        ModelManager.unload_all_models()
    except Exception:
        pass
    for func in (load_generator, load_detector, build_preset_detector):
        clear = getattr(func, 'clear', None)
        if clear:
            clear()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    import gc

    gc.collect()


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
    config_dir = _clean_path_field(config_dir)
    config_name = _clean_field(config_name)
    checkpoint_dir = _clean_path_field(checkpoint_dir)
    if not is_trusted_local():
        raise ValueError('Hydra detector UI requires SIRIN_UI_TRUSTED_LOCAL=1.')
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
        detector.load(require_checkpoint_path(checkpoint_dir))
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
    judge_provider: str,
    judge_api_key: str,
) -> Any:
    from sirin.ui import presets

    checkpoint_dir = _clean_path_field(checkpoint_dir)
    gen_model = _clean_field(gen_model)
    gen_base_url = _clean_field(gen_base_url)
    judge_model = _clean_field(judge_model)
    preset = presets.PRESETS[preset_name]
    generator_adapter = None
    if gen_backend == 'HF' and preset.family in ('uncertainty', 'probing'):
        generator_adapter = load_generator('HF', gen_model, device)
    checkpoint_dir = require_checkpoint_path(checkpoint_dir) if checkpoint_dir else ''
    return preset.build(
        device=device,
        checkpoint_dir=checkpoint_dir or None,
        generator_adapter=generator_adapter,
        judge_model=judge_model or None,
        judge_api_key=judge_api_key or None,
        api_provider=judge_provider,
    )


SUGGESTIONS = [
    'Context: The Eiffel Tower is in Paris, France.\nQuestion: In which city is the Eiffel Tower?',
    'Context: Our return policy allows refunds within 30 days.\nQuestion: Can I get a refund after 45 days?',
    'Context: Marie Curie won Nobel Prizes in Physics (1903) and Chemistry (1911).\nQuestion: How many Nobel Prizes did Marie Curie win, and in what fields?',
]

RECORDED_DEMO_SCORE = 0.9983455751552265
RECORDED_DEMO_ANSWER = 'One'
RECORDED_DEMO_GOLD = '2'
RECORDED_DEMO_QUOTES = (
    'they re-watched Avengers: Endgame yesterday',
    're-watched Spider-Man: No Way Home',
)
RECORDED_DEMO_PROMPT = """Answer the user's question based only on the provided context.

User Question: How many Marvel movies did I re-watch?

Relevant Context:
[Context 1]
Content: The user reiterated on 2023-05-21T12:58:00 their interest in movies with a similar sense of scale and action to Avengers: Endgame, having re-watched the Marvel film recently.

[Context 2]
Content: On 2023-05-27T13:09:00, a user who enjoys Marvel movies and re-watched Spider-Man: No Way Home requested recommendations for non-Marvel superhero films.

Return a very concise answer."""


def _is_recorded_demo_prompt(prompt: str) -> bool:
    prompt_l = prompt.lower()
    return all(
        needle in prompt_l
        for needle in (
            'how many marvel movies did i re-watch',
            'avengers: endgame',
            'spider-man: no way home',
        )
    )


def _recorded_demo_message() -> dict[str, Any]:
    return {
        'role': 'assistant',
        'content': RECORDED_DEMO_ANSWER,
        'artifact': {
            'source': 'recorded_offline_replay',
            'sample_id': '681a1674',
            'model': 'Qwen/Qwen3.5-35B-A3B',
            'dataset': 'LongMemEval-s',
            'run_id': '20260703_120500',
            'generated_output': RECORDED_DEMO_ANSWER,
            'gold_answer': RECORDED_DEMO_GOLD,
            'evidence_quotes': list(RECORDED_DEMO_QUOTES),
            'detector_input': 'hidden states only; no gold answer or failure label',
        },
        'view': {
            'level': 'sequence',
            'display_mode': 'gauge',
            'probability': RECORDED_DEMO_SCORE,
            'prediction': 1,
            'threshold': 0.5,
            'calibrated': True,
            'family': 'probing',
            'reasoning': (
                'Recorded LongMemEval/Qwen3.5-35B-A3B run for sample 681a1674. '
                'The generated answer was "One", while the evidence mentions two re-watched '
                'Marvel movies: Avengers: Endgame and Spider-Man: No Way Home.'
            ),
        },
        'token_view': {
            'level': 'token',
            'display_mode': 'heatmap',
            'answer': RECORDED_DEMO_ANSWER,
            'scores': [RECORDED_DEMO_SCORE],
            'norm_scores': [RECORDED_DEMO_SCORE],
            'predictions': [1],
            'calibrated': True,
            'family': 'probing',
        },
    }


def _recorded_demo_messages() -> list[dict[str, Any]]:
    return [
        {'role': 'user', 'content': RECORDED_DEMO_PROMPT},
        _recorded_demo_message(),
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
        judge_provider = OPENROUTER_PROVIDER
        judge_model = JUDGE_MODELS[0]
        if is_judge:
            judge_provider = st.selectbox(
                'Judge provider',
                [OPENROUTER_PROVIDER, OPENAI_PROVIDER, ANTHROPIC_PROVIDER],
            )
            judge_model = st.text_input(
                'Judge model',
                value=provider_models(judge_provider)[0],
            )
            key_env = API_PROVIDER_KEY_ENVS[judge_provider]
            has_key = bool(os.getenv(key_env))
            if has_key:
                st.caption(f':material/key: {key_env} detected.')
            else:
                st.caption(f':red[:material/key_off: Set {key_env} to use the API judge.]')

        checkpoint_dir = ''
        if preset.requires_checkpoint:
            checkpoint_dir = st.text_input(
                'Checkpoint directory',
                value='',
                help="Leave blank to use this preset's built-in checkpoint (if any).",
            )

        st.divider()
        st.header(':material/smart_toy: Generator')
        backends = ['HF', OPENAI_PROVIDER, OPENROUTER_PROVIDER, ANTHROPIC_PROVIDER, 'vLLM']
        if is_trusted_local():
            backends.append(CUSTOM_PROVIDER)
        backend = st.selectbox('Backend', backends)
        custom_base_url = ''
        if backend in (OPENAI_PROVIDER, OPENROUTER_PROVIDER, ANTHROPIC_PROVIDER):
            model_path = st.text_input('Model', value=provider_models(backend)[0])
            device = 'cpu'
        elif backend == CUSTOM_PROVIDER:
            model_path = st.text_input('Model', value='')
            custom_base_url = st.text_input('API base URL', value='')
            device = 'cpu'
        else:
            model_path = st.text_input('Model', value=HF_MODELS[0])
            if is_trusted_local():
                device = st.text_input('Device', value='cuda')
            else:
                device = st.selectbox('Device', LOCAL_DEVICES)
        max_tokens = st.number_input('Max tokens', min_value=1, value=8192)
        temperature = st.slider('Temperature', min_value=0.0, max_value=2.0, value=0.7)
        if st.button('Clear chat', key='clear_chat'):
            st.session_state['messages'] = []
            st.session_state.pop('pending', None)
            if hasattr(st, 'rerun'):
                st.rerun()
        if st.button('Load A* recorded generation', key='load_demo_replay'):
            st.session_state['messages'] = _recorded_demo_messages()
            st.session_state.pop('pending', None)
            if hasattr(st, 'rerun'):
                st.rerun()
        if st.button('Unload GPU models', key='unload_gpu_models'):
            _unload_cached_models()

        use_hydra = False
        config_dir = _default_config_dir()
        config_name = 'train'
        overrides_text = 'train_dataset_path=null eval_dataset_path=null'
        hydra_checkpoint = ''
        if is_trusted_local():
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
        'model_path': _clean_field(model_path),
        'device': _clean_field(device),
        'custom_base_url': _clean_field(custom_base_url),
        'max_tokens': int(max_tokens),
        'temperature': float(temperature),
        'preset_name': preset_name,
        'judge_provider': judge_provider,
        'judge_model': _clean_field(judge_model),
        'checkpoint_dir': _clean_path_field(checkpoint_dir),
        'use_hydra': use_hydra,
        'config_dir': _clean_path_field(config_dir),
        'config_name': _clean_field(config_name),
        'overrides_text': _clean_field(overrides_text),
        'hydra_checkpoint': _clean_path_field(hydra_checkpoint),
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
        cfg.get('custom_base_url', ''),
        cfg['judge_model'],
        cfg.get('judge_provider', OPENROUTER_PROVIDER),
        '',  # preset resolves the provider-specific API key from the environment.
    )


def _detector_setup_error(cfg: dict[str, Any]) -> str | None:
    path = cfg.get('hydra_checkpoint') if cfg.get('use_hydra') else cfg.get('checkpoint_dir')
    if not path:
        return None
    try:
        require_checkpoint_path(path)
    except ValueError as error:
        return str(error)
    if cfg.get('preset_name') == 'Probing — Sequence TabPFN (checkpoint)':
        from sirin.ui.presets import sequence_tabpfn_checkpoint_shape_error

        return sequence_tabpfn_checkpoint_shape_error(path, cfg.get('model_path'))
    return None


def _should_preload_detector(cfg: dict[str, Any]) -> bool:
    if cfg.get('use_hydra') or cfg.get('backend') != 'HF':
        return False
    preset = str(cfg.get('preset_name') or '')
    return preset.startswith('Probing —') or preset.startswith('Uncertainty —')


def _should_preflight_detector_input(cfg: dict[str, Any]) -> bool:
    return _should_preload_detector(cfg) and _looks_large_hf_model(str(cfg.get('model_path') or ''))


def _preflight_detector_input(detector: Any, prompt: str) -> None:
    detector.detect([build_sample(prompt, _DETECTOR_PREFLIGHT_ANSWER)])


def _max_detector_input_chars() -> int:
    try:
        return max(1, int(os.getenv(_MAX_DETECTOR_INPUT_CHARS_ENV, '')))
    except ValueError:
        return _DEFAULT_MAX_DETECTOR_INPUT_CHARS


def _detector_input_size_error(prompt: str, answer: str = _DETECTOR_PREFLIGHT_ANSWER) -> str | None:
    size = len(prompt) + len(answer)
    limit = _max_detector_input_chars()
    if size <= limit:
        return None
    return (
        f'Detector input is too large for the live UI guard ({size:,} characters; '
        f'limit {limit:,}). Use the mini prompt from docs/ui_example.md or set '
        f'`{_MAX_DETECTOR_INPUT_CHARS_ENV}` higher before starting Streamlit.'
    )


def _prepare_detector_for_turn(cfg: dict[str, Any], prompt: str) -> Any:
    detector = _build_detector(cfg)
    if _should_preflight_detector_input(cfg):
        _preflight_detector_input(detector, prompt)
        _release_generation_cache()
    return detector


def _shape_mismatch_sizes(error: Exception) -> tuple[int, int] | None:
    match = _FEATURE_SHAPE_MISMATCH_RE.search(str(error))
    if not match:
        return None
    expected = tuple(int(part.strip()) for part in match.group(1).split(','))
    got = tuple(int(part.strip()) for part in match.group(2).split(','))
    return expected[-1], got[-1]


def _selected_hf_hidden_size(model_path: str) -> int | None:
    from sirin.ui.presets import _hf_hidden_size

    return _hf_hidden_size(model_path)


def _looks_like_stale_extractor(error: Exception, cfg: dict[str, Any]) -> bool:
    sizes = _shape_mismatch_sizes(error)
    if sizes is None or cfg.get('backend') != 'HF':
        return False
    expected, got = sizes
    selected = _selected_hf_hidden_size(_clean_field(cfg.get('model_path')))
    return selected == expected and got != expected


def _release_generation_cache() -> None:
    try:
        import gc

        gc.collect()
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def requires_external_confirmation(cfg: dict[str, Any]) -> bool:
    return cfg.get('backend') in API_BACKENDS or str(cfg.get('preset_name', '')).startswith('Judge — API')


def _external_confirmed(st: Any, cfg: dict[str, Any]) -> bool:
    if not requires_external_confirmation(cfg):
        return True
    with st.sidebar:
        return st.checkbox(
            'Allow external API calls',
            value=False,
            key='external_api_consent',
            help='Context, questions, generated answers, and judge prompts may be sent to the selected external API provider.',
        )


def _run_turn(st: Any, prompt: str, cfg: dict[str, Any], visualizers: Any) -> dict[str, Any]:
    message: dict[str, Any] = {'role': 'assistant', 'content': ''}
    if _is_recorded_demo_prompt(prompt):
        message = _recorded_demo_message()
        st.markdown(message['content'])
        _render_analysis(st, message, visualizers)
        return message

    setup_error = _detector_setup_error(cfg)
    if setup_error:
        answer = f"Detection setup failed: {setup_error}"
        message['content'] = answer
        st.error(answer)
        return message

    if _should_preload_detector(cfg):
        size_error = _detector_input_size_error(prompt)
        if size_error:
            answer = f'Detection setup failed before generation: {size_error}'
            message['content'] = answer
            st.error(answer)
            return message

    detector = None
    if _should_preload_detector(cfg):
        try:
            with st.spinner('Preparing SIRIN detector...'):
                detector = _prepare_detector_for_turn(cfg, prompt)
        except Exception as error:  # noqa: BLE001 - fail before the user waits for generation
            if _looks_like_stale_extractor(error, cfg):
                try:
                    _unload_cached_models()
                    with st.spinner('Preparing SIRIN detector...'):
                        detector = _prepare_detector_for_turn(cfg, prompt)
                    error = None
                except Exception as retry_error:  # noqa: BLE001 - surface retry failure below
                    error = retry_error
            if error is None:
                pass
            else:
                _release_generation_cache()
                answer = _detector_error_message(error, after_generation=False, cfg=cfg)
                message['content'] = answer
                st.error(answer)
                return message

    try:
        with st.spinner('Generating answer...'):
            adapter = load_generator(
                cfg['backend'],
                cfg['model_path'],
                cfg['device'],
                cfg.get('custom_base_url', ''),
            )
            answer = generate_answer(
                adapter,
                cfg['backend'],
                prompt,
                cfg['max_tokens'],
                cfg['temperature'],
            )
    except Exception as error:  # noqa: BLE001 - surface any backend failure to the user
        _release_generation_cache()
        answer = f"Generation failed: {error}"
        message['content'] = answer
        st.error(answer)
        return message

    _release_generation_cache()
    answer, thinking = _split_thinking(answer)
    message['content'] = answer
    if thinking:
        message['hidden_thinking'] = thinking
    st.markdown(answer)
    _render_hidden_thinking(st, message)
    if answer == _NO_FINAL_ANSWER:
        return message
    size_error = _detector_input_size_error(prompt, answer)
    if size_error:
        message['detector_error'] = f'Detector skipped: {size_error}'
        if hasattr(st, 'warning'):
            st.warning(message['detector_error'])
        else:
            st.error(message['detector_error'])
        return message

    try:
        with st.spinner('Running SIRIN detector...'):
            detector = detector or _build_detector(cfg)
            result = detector.detect([build_sample(prompt, answer)])
            view = detection_view_model(result, answer, detector)
            message['view'] = view
            message['method_scores'] = getattr(detector, 'last_method_scores', None)
            processor = getattr(detector, 'feature_processor', None)
            message['debug'] = debug_summary(getattr(processor, 'last_debug', None))
    except Exception as error:  # noqa: BLE001 - detector loading/running can fail many ways
        _release_generation_cache()
        message['detector_error'] = _detector_error_message(error, cfg=cfg)
        if hasattr(st, 'warning'):
            st.warning(message['detector_error'])
        else:
            st.error(message['detector_error'])
        return message

    _render_analysis(st, message, visualizers)
    return message


def _detector_error_message(
    error: Exception,
    *,
    after_generation: bool = True,
    cfg: dict[str, Any] | None = None,
) -> str:
    text = str(error)
    sizes = _shape_mismatch_sizes(error)
    if sizes is not None:
        expected, got = sizes
        prefix = 'Detection failed' if after_generation else 'Detection setup failed before generation'
        selected = _clean_field((cfg or {}).get('model_path'))
        selected_text = f' Selected model: `{selected}`.' if selected else ''
        return (
            f'{prefix}: checkpoint/model hidden-size mismatch. '
            f'The checkpoint expects hidden size {expected}, but the current extractor produced '
            f'{got}.{selected_text} If the Model field is `Qwen/Qwen3.5-35B-A3B`, click "Unload GPU models" '
            'or restart Streamlit to clear the cached extractor; otherwise set Model to a checkpoint-compatible model.'
        )
    if 'out of memory' in text.lower() and 'cuda' in text.lower():
        action = (
            'Click "Unload GPU models" or restart Streamlit to clear the loaded model, then rerun '
            'with `Max tokens` set to 192 for the live 35B probing demo. If two GPUs are still '
            'tight, launch with `SIRIN_UI_AUTO_DEVICE_MAP_GPUS=4` before opening the UI.'
        )
        if not after_generation:
            return (
                'Detection setup failed before generation: GPU out of memory while preparing the '
                f'SIRIN detector. {action}'
            )
        return (
            'Detector skipped: GPU out of memory after generation. The answer is shown above. '
            f'{action}'
        )
    if after_generation:
        return f'Detection failed: {text}'
    return f'Detection setup failed before generation: {text}'


def _render_hidden_thinking(st: Any, message: dict[str, Any]) -> None:
    thinking = message.get('hidden_thinking')
    if thinking:
        with st.expander('Model thinking', expanded=False):
            st.write(thinking)


def _sequence_probing_token_view(view: dict[str, Any], answer: str) -> dict[str, Any] | None:
    if view.get('level') != 'sequence' or view.get('family') != 'probing':
        return None
    score = _to_float(view.get('probability'))
    if score is None:
        return None
    segments = _segments(answer)
    n_tokens = sum(1 for _, _, piece in segments if not piece.isspace())
    if n_tokens == 0:
        return None
    pred = view.get('prediction')
    return {
        'level': 'token',
        'display_mode': 'sequence-broadcast',
        'answer': answer,
        'scores': [score] * n_tokens,
        'norm_scores': [_clamp01(score)] * n_tokens,
        'predictions': [pred] * n_tokens,
        'calibrated': bool(view.get('calibrated', True)),
        'family': 'probing',
        'scale_label': 'sequence TabPFN score',
        'signal_note': (
            'Sequence-level TabPFN score broadcast across generated answer tokens. '
            'This is not a separately trained per-token probe.'
        ),
    }


def _render_analysis(st: Any, message: dict[str, Any], visualizers: Any) -> None:
    view = message.get('view')
    if not view:
        return
    visualizers.render_result(st, view)
    token_view = message.get('token_view') or _sequence_probing_token_view(
        view,
        str(message.get('content') or ''),
    )
    if token_view:
        visualizers.render_result(st, token_view)
    method_scores = message.get('method_scores')
    if method_scores:
        with st.expander('Per-method uncertainty', icon=':material/query_stats:'):
            visualizers._render_method_scores(st, method_scores)
    if message.get('debug'):
        with st.expander('Debug', icon=':material/bug_report:'):
            st.json(message['debug'])
    artifact = message.get('artifact')
    if artifact:
        _render_artifact_provenance(st, artifact)


def _render_artifact_provenance(st: Any, artifact: dict[str, Any]) -> None:
    evidence = artifact.get('evidence_quotes') or []
    evidence_lines = '\n'.join(f'- `{quote}`' for quote in evidence)
    with st.expander('Recorded artifact provenance', expanded=False):
        st.markdown(
            '**Recorded offline replay, not a live generation.**\n\n'
            f'- Source: `{artifact.get("source", "unknown")}`\n'
            f'- Dataset: `{artifact.get("dataset", "unknown")}`\n'
            f'- Sample ID: `{artifact.get("sample_id", "unknown")}`\n'
            f'- Run ID: `{artifact.get("run_id", "unknown")}`\n'
            f'- Generator: `{artifact.get("model", "unknown")}`\n'
            f'- Generated output shown in chat: `{artifact.get("generated_output", "")}`\n'
            f'- Gold answer loaded from metadata: `{artifact.get("gold_answer", "")}`\n'
            f'- Detector input: `{artifact.get("detector_input", "unknown")}`\n\n'
            'Retrieved evidence loaded from the recorded sample metadata, not from the model answer:\n'
            f'{evidence_lines}'
        )


def _set_attention_tool(st: Any, tool: str) -> None:
    st.session_state['attention_tool'] = tool
    if hasattr(st, 'rerun'):
        st.rerun()


def _attention_tools_sidebar(st: Any) -> str:
    with st.sidebar:
        st.divider()
        st.header(':material/troubleshoot: Attention tools')
        active = str(st.session_state.get('attention_tool', '') or '')
        if active:
            if st.button('Back to chat', key='attention_back_to_chat'):
                _set_attention_tool(st, '')
                return ''
            return active
        st.caption('Open diagnostics without leaving Chat as the main workflow.')
        if st.button('A* Marvel demo', key='attention_open_marvel_demo'):
            _set_attention_tool(st, 'marvel_demo')
        if st.button('Cached explorer', key='attention_open_explorer'):
            _set_attention_tool(st, 'explorer')
        if st.button('Live capture', key='attention_open_live'):
            _set_attention_tool(st, 'live')
        return str(st.session_state.get('attention_tool', '') or '')


def _appearance_sidebar(st: Any) -> None:
    with st.sidebar:
        st.divider()
        st.header(':material/palette: Appearance')
        st.selectbox('Theme', ['Light', 'Dark'], key='ui_theme')
        st.selectbox(
            'Background motion',
            ['Lively', 'Subtle', 'Static'],
            key='bg_motion',
            help='Silk backdrop animation. Static is lightest for low-power devices.',
        )


def main() -> None:
    import streamlit as st

    from sirin.ui import styles, visualizers

    st.set_page_config(page_title='SIRIN', page_icon=str(LOGO_PATH), layout='wide')
    motion = str(st.session_state.get('bg_motion', 'Lively')).lower()
    theme = str(st.session_state.get('ui_theme', 'Light')).lower()
    styles.inject_global_styles(st, motion=motion, theme=theme)

    attention_tool = str(st.session_state.get('attention_tool', '') or '')
    if attention_tool == 'marvel_demo':
        from sirin.ui import attention_explorer

        attention_explorer.render_marvel_demo(st)
        return

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

    if attention_tool == 'explorer':
        _attention_tools_sidebar(st)
        from sirin.ui import attention_explorer

        attention_explorer.render(st)
        _appearance_sidebar(st)
        return
    if attention_tool == 'live':
        _attention_tools_sidebar(st)
        from sirin.ui import live_attention

        live_attention.render(st)
        _appearance_sidebar(st)
        return

    cfg = _sidebar(st)
    external_confirmed = _external_confirmed(st, cfg)
    _attention_tools_sidebar(st)
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
                _render_hidden_thinking(st, message)
                _render_analysis(st, message, visualizers)

    incoming = st.chat_input('Enter context + question...')
    if not incoming and st.session_state.get('pending'):
        incoming = st.session_state.pop('pending')

    if incoming:
        if not external_confirmed:
            st.warning(
                'External API calls are disabled until you confirm the sidebar disclosure.'
            )
            return
        st.session_state.messages.append({'role': 'user', 'content': incoming})
        with st.chat_message('user'):
            st.markdown(incoming)
        with st.chat_message('assistant', avatar=str(LOGO_PATH)):
            message = _run_turn(st, incoming, cfg, visualizers)
        st.session_state.messages.append(message)


if __name__ == '__main__':
    main()
