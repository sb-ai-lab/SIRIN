from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shlex
import traceback
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sirin.ui.path_policy import (
    is_hosted,
    is_trusted_local,
    require_checkpoint_path,
)
from sirin.ui.demo_cases import load_demo_cases
from sirin.ui.providers import (
    ANTHROPIC_PROVIDER,
    CUSTOM_PROVIDER,
    OPENAI_PROVIDER,
    OPENROUTER_PROVIDER,
    API_PROVIDER_KEY_ENVS,
    custom_openai_base_url,
    local_openai_models,
    provider_models,
    require_shared_key_model,
    resolve_api_provider,
)
from sirin.ui.styles import risk_color

LOGO_PATH = Path(__file__).parent / 'assets' / 'logo.png'
REPO_ROOT = Path(__file__).resolve().parents[2]
LONGMEMEVAL_PROFILE_PATH = Path(__file__).parent / 'assets' / 'longmemeval_qwen35.json'


def load_longmemeval_profile(
    path: str | Path = LONGMEMEVAL_PROFILE_PATH,
) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or payload.get('schema_version') != 1:
        raise ValueError('LongMemEval UI profile must use schema version 1')
    repo_root = Path(__file__).resolve().parents[2]
    for task in payload.get('checkpoints', {}).values():
        for checkpoint in task.values():
            checkpoint_path = Path(str(checkpoint.get('path') or ''))
            if checkpoint_path and not checkpoint_path.is_absolute():
                checkpoint['portable_path'] = str(checkpoint_path)
                checkpoint['path'] = str((repo_root / checkpoint_path).resolve())
    return payload


LONGMEMEVAL_PROFILE = load_longmemeval_profile()
LONGMEMEVAL_ASSETS_DIR = Path(__file__).parent / 'assets'
LONGMEMEVAL_DEFAULT_PROFILE = LONGMEMEVAL_PROFILE_PATH.name


def longmemeval_profiles() -> list[tuple[str, dict[str, Any]]]:
    """Every discovered LongMemEval UI profile as ``(label, profile)``; the 35B default leads.

    Scans ``assets/longmemeval_*.json``. Each is schema_version 1; optional top-level ``variant`` /
    ``label`` fields are additive (display only). The default 35B profile stays first (the trusted-
    local default); the rest sort by label so the sidebar profile select is stable.
    """
    discovered: list[tuple[bool, str, dict[str, Any]]] = []
    for path in sorted(LONGMEMEVAL_ASSETS_DIR.glob('longmemeval_*.json')):
        profile = load_longmemeval_profile(path)
        label = str(profile.get('label') or profile.get('name') or path.stem)
        discovered.append((path.name != LONGMEMEVAL_DEFAULT_PROFILE, label, profile))
    discovered.sort(key=lambda item: (item[0], item[1]))
    return [(label, profile) for _, label, profile in discovered]


LIVE_CAPTURE_DIR = REPO_ROOT / 'output' / 'sirin_a_star_demo' / 'provenance' / 'live'


def _cache_resource(func):
    try:
        import streamlit as st

        return st.cache_resource(show_spinner=False)(func)
    except Exception:
        return func


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
        return [max(values[start:end], default=None) for start, end, _ in segments]
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
    for (start, end, piece), score, pred in zip(
        segments, segment_scores, segment_preds
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
    return (
        '<span class="sirin-heatmap" style="line-height:2.25;white-space:pre-wrap;">'
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
            'threshold_source': None,
            'display_mode': None,
            'task': 'hallucination',
        }
    try:
        from sirin.ui import presets

        info = presets.describe_detector(detector)
        return {
            'family': info.get('family', 'unknown'),
            'calibrated': bool(info.get('calibrated', True)),
            'threshold': info.get('threshold', getattr(detector, 'threshold', None)),
            'threshold_source': info.get('threshold_source'),
            'display_mode': info.get('display_mode'),
            'task': info.get('task', 'hallucination'),
        }
    except (KeyError, AttributeError) as e:
        from loguru import logger as lg

        lg.debug(f"Detector metadata lookup failed: {e}")
        return {
            'family': 'unknown',
            'calibrated': True,
            'threshold': getattr(detector, 'threshold', None),
            'threshold_source': getattr(detector, '_ui_threshold_source', None),
            'display_mode': None,
            'task': 'hallucination',
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
    match = re.search(
        r'<think>\s*(.*?)\s*</think>\s*', text, flags=re.IGNORECASE | re.DOTALL
    )
    if not match:
        return _split_json_reasoning(text, None)
    visible = (text[: match.start()] + text[match.end() :]).strip()
    thinking = match.group(1).strip()
    return _split_json_reasoning(visible, thinking or None)


def _split_json_reasoning(text: str, thinking: str | None) -> tuple[str, str | None]:
    if not str(text or '').strip() and thinking:
        return _NO_FINAL_ANSWER, thinking
    candidate = str(text or '').strip()
    fence = re.fullmatch(
        r'```(?:json)?\s*(.*?)\s*```',
        candidate,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fence:
        candidate = fence.group(1)
    try:
        obj = json.loads(candidate)
    except (TypeError, ValueError):
        return text, thinking
    if not isinstance(obj, dict) or 'answer' not in obj or 'reasoning' not in obj:
        return text, thinking
    answer = obj.get('answer')
    visible = (
        answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
    )
    reasoning = str(obj.get('reasoning') or '').strip()
    hidden = '\n\n'.join(part for part in (thinking, reasoning) if part)
    return visible.strip(), hidden or None


def _pick_answer_text(
    n_scores: int, detector: Any, chat_answer: str, family: str
) -> tuple[str, str, str | None]:
    # Per-char scores align to whichever answer text has the same length. Judges score their own
    # tag-stripped generation; probing/uncertainty normally score the original answer.
    gens = getattr(detector, 'last_generations', None)
    tagged = (
        gens[0]
        if isinstance(gens, list) and gens and isinstance(gens[0], str)
        else None
    )
    generated = getattr(detector, 'last_generated_text', None)

    if family == 'judge' and tagged is not None:
        candidates = [
            (_strip_span_tags(tagged), 'generation'),
            (chat_answer or '', 'original'),
        ]
    elif family == 'uncertainty' and generated:
        candidates = (
            [(chat_answer or '', 'original')]
            if generated == chat_answer
            else [(generated, 'generation')]
        )
    else:
        candidates = [(chat_answer or '', 'original')]
        if generated:
            candidates.append((generated, 'generation'))
    for text, source in candidates:
        if len(text) == n_scores:
            return text, source, tagged
    text, source = candidates[0]
    return text, source, tagged


def _detector_context_chunks(detector: Any) -> list[dict[str, Any]]:
    """Pre-aggregation per-chunk scores a sequence detector may publish for a split context.

    A long context can be split into chunks; the detector aggregates their scores into one. When it also
    exposes the per-chunk scores as ``last_context_chunk_scores`` (a list of
    ``{'index', 'score', 'chars': [start, end]}``), surface them so the card can draw a per-chunk
    heat-bar. Only meaningful with >1 chunk. No bundled preset configures a context split today, so this
    is dormant until one does (or an imported/fixture payload carries it) — never fabricated here.
    """
    chunks = getattr(detector, 'last_context_chunk_scores', None)
    if not isinstance(chunks, (list, tuple)) or len(chunks) < 2:
        return []
    return [dict(chunk) for chunk in chunks if isinstance(chunk, dict)]


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
            'task': info['task'],
            'attribution_scope': 'claim',
            'reasoning': reasoning,
        }

    probs = _to_plain(probs)
    preds = _to_plain(preds)
    if level == 'token' or (level is None and _is_nested_list(probs)):
        first_preds = _first(preds)
        scores = list(_first(probs) or [])
        absolute_raw_scores = (
            info['family'] == 'probing'
            and info.get('display_mode') == 'threshold-spans'
        )
        norm = (
            [_clamp01(s) for s in scores]
            if info['calibrated'] or absolute_raw_scores
            else _minmax(scores)
        )
        answer_text, answer_source, tagged = _pick_answer_text(
            len(scores), detector, answer, info['family']
        )
        predictions = first_preds if isinstance(first_preds, list) else []
        if not scores or not predictions:
            raise ValueError('Token detector returned empty scores or predictions.')
        if len(scores) != len(answer_text) or len(predictions) != len(answer_text):
            raise ValueError(
                'Token detector output alignment mismatch: '
                f'{len(answer_text)} answer characters, {len(scores)} scores, '
                f'and {len(predictions)} predictions.'
            )
        view = {
            'level': 'token',
            'display_mode': info.get('display_mode') or 'heatmap',
            'scores': scores,
            'predictions': predictions,
            'answer': answer_text,
            'answer_source': answer_source,
            'aligned': len(answer_text) == len(scores),
            'calibrated': info['calibrated'],
            'family': info['family'],
            'task': info['task'],
            'threshold': info.get('threshold'),
            'threshold_source': info.get('threshold_source'),
            'attribution_scope': 'token',
            'norm_scores': norm,
            'spans': spans,
            'tagged_generation': tagged,
            # tagged_generation already surfaces a judge's annotated answer.
            'reasoning': None,
        }
        if absolute_raw_scores:
            view.update(
                scale_label='raw linear-probe score',
                signal_note=(
                    'Fresh hidden-state linear-probe scores; raw sigmoid output, '
                    'not a calibrated probability.'
                ),
            )
        consensus = getattr(detector, 'last_consensus', None) or []
        if info['family'] == 'judge' and consensus:
            # last_spans are offsets into the raw tagged generation, NOT the answer characters; the
            # aligned per-character k/n scores are authoritative, so drop the raw spans before they
            # shadow char_scores in the presenter.
            view['spans'] = None
            first = consensus[0]
            requested, valid = first.get('requested'), first.get('valid')
            temperature = first.get('temperature')
            view.update(
                scale_label='span-tag agreement across sampled judge annotations',
                signal_note=(
                    f"Each character's score is the fraction of {valid}/{requested} judge samples "
                    'that tagged it. Agreement is judge consensus, not a calibrated probability and '
                    'not ground truth.'
                ),
            )
            disclosures = []
            judge_model = getattr(detector, '_ui_judge_model', None)
            provider_label = getattr(detector, '_ui_judge_provider', None)
            if judge_model:
                disclosures.append(f'Judge model: {judge_model}')
            if provider_label:
                disclosures.append(f'Judge provider: {provider_label}')
            if isinstance(valid, int) and isinstance(requested, int):
                disclosures.append(f'Judge samples: {valid}/{requested} verbatim-aligned')
            if temperature is not None:
                disclosures.append(f'Judge temperature: {temperature}')
            if disclosures:
                view['judge_disclosures'] = disclosures
            if isinstance(valid, int) and isinstance(requested, int) and 0 < valid < requested:
                # Attribute the exclusions honestly when the judge classified them; without
                # attribution every dropped sample falls back to the not-verbatim sentence.
                invalid = first.get('invalid') or {}
                truncated = invalid.get('truncated', 0)
                empty = invalid.get('empty', 0)
                not_verbatim = (requested - valid) - truncated - empty
                warnings = []
                if truncated:
                    warnings.append(
                        f'{truncated} of {requested} judge samples hit the token limit '
                        f'mid-reasoning and {"was" if truncated == 1 else "were"} excluded.'
                    )
                if empty:
                    warnings.append(
                        f'{empty} of {requested} judge samples returned no text and '
                        f'{"was" if empty == 1 else "were"} excluded.'
                    )
                if not_verbatim > 0:
                    warnings.append(
                        f'{not_verbatim} of {requested} judge samples were not '
                        'verbatim and were excluded.'
                    )
                view['run_warnings'] = warnings
        trace = getattr(detector, 'last_generation_trace', None)
        if isinstance(trace, dict) and trace.get('text') == answer_text:
            view.update(
                token_pieces=list(trace.get('pieces') or []),
                token_offsets=list(trace.get('offsets') or []),
                scale_label='relative heuristic token uncertainty',
                signal_note=(
                    'Uncalibrated arithmetic mean of chosen-token NLL and '
                    f'{trace.get("entropy_scope", "model-vocabulary")} token entropy '
                    'from this exact streamed answer; min-max normalized only within '
                    'this answer. Color ranks tokens here and is not evidence, a '
                    'probability, or a verdict.'
                ),
            )
        return view

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
    generated_text = getattr(detector, 'last_generated_text', None)
    scored_answer = (
        str(generated_text)
        if info['family'] == 'uncertainty' and generated_text
        else answer
    )
    sequence_view = {
        'level': 'sequence',
        'display_mode': display_mode,
        'probability': probability,
        'prediction': _first(preds),
        'calibrated': info['calibrated'],
        'threshold': info['threshold'],
        'threshold_source': info.get('threshold_source'),
        'family': info['family'],
        'task': info['task'],
        'attribution_scope': 'sequence',
        'answer': scored_answer,
        'answer_source': 'generation' if scored_answer != answer else 'original',
        'raw_prob': None if info['calibrated'] else _to_float(probability),
        'class_probs': class_probs,
        'class_index': class_index,
        'generated_text': generated_text,
        # in verdict mode show a reasoning model's chain, but not a bare '0'/'1'.
        'reasoning': (
            (reasoning if reasoning and len(str(reasoning).strip()) > 3 else None)
            if display_mode == 'verdict'
            else reasoning
        ),
        'spans': spans,
    }
    # Sequence-only: per-chunk context scores never localize within the answer (the honesty gate in
    # the presenter also drops them for token/span/claim/multiclass kinds).
    context_chunks = _detector_context_chunks(detector)
    if context_chunks:
        sequence_view['context_chunk_scores'] = context_chunks
    return sequence_view


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


_LARGE_HF_MODEL_RE = re.compile(
    r'(?<!\d)(?:3[0-9]|[4-9]\d|[1-9]\d{2,})B', re.IGNORECASE
)
_AUTO_DEVICE_MAP_GPUS_ENV = 'SIRIN_UI_AUTO_DEVICE_MAP_GPUS'
_MAX_DETECTOR_INPUT_CHARS_ENV = 'SIRIN_UI_MAX_DETECTOR_INPUT_CHARS'
_DEFAULT_MAX_DETECTOR_INPUT_CHARS = 30_000
_DEFAULT_UI_GENERATION_TOKENS = 192
_HF_GENERATION_MAX_TIME_SECONDS = 60.0


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
                free_bytes, _ = torch.cuda.mem_get_info(idx)
            except Exception:
                continue
            usable_gib = int((free_bytes / (1024**3)) * 0.85)
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
    from sirin.ui import presets

    model_path = _clean_field(model_path)
    device = _clean_field(device)
    auto_device_map = device.lower() in (
        'auto',
        'device_map:auto',
        'device-map:auto',
    ) or (device.lower() == 'cuda' and _looks_large_hf_model(model_path))
    revision = (
        LONGMEMEVAL_PROFILE['model'].get('revision')
        if model_path == LONGMEMEVAL_PROFILE['model']['path']
        else presets.PSILOQA_MODEL_REVISION
        if model_path == presets.PSILOQA_MODEL_ID
        else None
    )
    if auto_device_map:
        return HFConfig(
            model_path=model_path,
            revision=revision,
            device=None,
            device_map='auto',
            max_memory=_device_map_max_memory() or None,
            attn_implementation='sdpa',
        )
    return HFConfig(model_path=model_path, device=device, revision=revision)


HF_MODELS = ['Qwen/Qwen3-4B', 'Qwen/Qwen2.5-3B-Instruct', 'Qwen/Qwen3.5-4B']
LOCAL_DEVICES = ['cuda', 'cpu']
API_BACKENDS = (
    OPENAI_PROVIDER,
    OPENROUTER_PROVIDER,
    ANTHROPIC_PROVIDER,
    CUSTOM_PROVIDER,
)


# ModelManager owns model load/unload/LRU + exclusive_run. This module-level, config-keyed memo only
# avoids rebuilding the lightweight adapter WRAPPER for a repeated config (it survives Streamlit reruns
# like st.cache_resource did, but is plain Python so it works — and is testable — without a Streamlit
# runtime). Local (VRAM-holding) adapters are handed to ModelManager so switching models evicts the
# previous one; API adapters are cheap/stateless and hold no local VRAM, so they skip the manager and
# never evict a loaded local model.
# ponytail: unbounded memo of tiny wrappers (VRAM stays bounded by ModelManager); add an LRU cap only if
# a single session ever cycles through enough distinct configs to matter.
_MAX_ACTIVE_MODELS_ENV = 'SIRIN_UI_MAX_ACTIVE_MODELS'
_LOCAL_MODEL_BACKENDS = {'HF', 'vLLM'}
_adapter_memo: dict[tuple[str, str, str, str, str], Any] = {}


def _ui_max_active_models() -> int:
    try:
        return max(1, int(os.getenv(_MAX_ACTIVE_MODELS_ENV, '1')))
    except (TypeError, ValueError):
        return 1


def _manage_local_model(adapter: Any) -> Any:
    """Hand a VRAM-holding adapter to ModelManager: register it, evict the least-recently-used model
    past SIRIN_UI_MAX_ACTIVE_MODELS (default 1), then load it. Idempotent for an already-active adapter."""
    from sirin.inference.model_manager import ModelManager

    ModelManager.config.max_active_models = _ui_max_active_models()
    return ModelManager.load_model(adapter)


def _new_generator_adapter(
    backend: str, model_path: str, device: str, custom_base_url: str, api_key: str
) -> Any:
    if backend == 'HF':
        from sirin.inference.adapters.hf_adapter import HfModelAdapter

        return HfModelAdapter(_make_hf_config(model_path, device))
    if backend in API_BACKENDS:
        from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter
        from sirin.models.inference import OpenAIConfig

        # An explicit pasted key wins; '' falls back to the provider env var inside resolve.
        provider = resolve_api_provider(backend, custom_base_url, api_key=api_key or None)
        require_shared_key_model(backend, model_path, api_key or None)
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


def load_generator(
    backend: str,
    model_path: str,
    device: str,
    custom_base_url: str = '',
    api_key: str = '',
) -> Any:
    model_path = _clean_field(model_path)
    device = _clean_field(device)
    custom_base_url = _clean_field(custom_base_url)
    key = (backend, model_path, device, custom_base_url, api_key)
    adapter = _adapter_memo.get(key)
    if adapter is None:
        adapter = _new_generator_adapter(
            backend, model_path, device, custom_base_url, api_key
        )
        _adapter_memo[key] = adapter
    if backend in _LOCAL_MODEL_BACKENDS:
        _manage_local_model(adapter)
    return adapter


def _unload_cached_models() -> None:
    _adapter_memo.clear()
    try:
        from sirin.inference.model_manager import ModelManager

        ModelManager.unload_all_models()
    except Exception:
        pass
    clear = getattr(load_detector, 'clear', None)
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
    messages: list[dict[str, str]] | None = None,
) -> str:
    if messages and backend == 'vLLM':
        if not adapter.is_loaded:
            adapter.load()
        tokenizer = adapter.tokenizer or adapter.model.get_tokenizer()
        inputs: list[Any] = [
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        ]
    elif messages:
        inputs = [messages]
    else:
        inputs = (
            [prompt] if backend == 'vLLM' else [[{'role': 'user', 'content': prompt}]]
        )
    sample_kwargs = (
        {'max_time': _HF_GENERATION_MAX_TIME_SECONDS} if backend == 'HF' else {}
    )
    return adapter.sample(
        inputs,
        max_tokens=max_tokens,
        temperature=temperature,
        **sample_kwargs,
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
    task = getattr(cfg, 'task_type', None)
    if task is not None:
        detector._ui_task = getattr(task, 'value', str(task))
    if checkpoint_dir:
        detector.load(require_checkpoint_path(checkpoint_dir))
    return detector


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
    sequence_uq = LONGMEMEVAL_PROFILE['uncertainty']['sequence']
    hallucination_threshold = sequence_uq['thresholds']['hallucination_strict']
    use_longmemeval_uq = (
        preset_name == 'Uncertainty — Sequence (zero-shot)'
        and gen_model == LONGMEMEVAL_PROFILE['model']['path']
        and hallucination_threshold.get('runtime_compatible', False)
    )
    generator_adapter = None
    locked_psiloqa_probe = preset_name in presets.PSILOQA_TOKEN_LINEAR_PRESETS
    if preset.family == 'uncertainty' or (
        gen_backend == 'HF'
        and preset.family == 'probing'
        and not locked_psiloqa_probe
    ):
        generator_adapter = load_generator(gen_backend, gen_model, device, gen_base_url)
    checkpoint_dir = require_checkpoint_path(checkpoint_dir) if checkpoint_dir else ''
    detector = preset.build(
        device=device,
        checkpoint_dir=checkpoint_dir or None,
        generator_adapter=generator_adapter,
        judge_model=judge_model or None,
        judge_api_key=judge_api_key or None,
        api_provider=judge_provider,
        uncertainty_threshold=(
            hallucination_threshold['value'] if use_longmemeval_uq else None
        ),
        uncertainty_max_new_tokens=(
            sequence_uq['max_new_tokens'] if use_longmemeval_uq else None
        ),
        uncertainty_threshold_source=(
            'LongMemEval-S hallucination_strict; Qwen3.5-35B-A3B; '
            'full-set optimal threshold (n=409)'
            if use_longmemeval_uq
            else None
        ),
    )
    if (
        preset_name == LONGMEMEVAL_PROFILE['ui']['default_preset']
        and gen_model == LONGMEMEVAL_PROFILE['model']['path']
    ):
        detector._ui_threshold_source = (
            'LongMemEval-S hallucination_strict; Qwen3.5-35B-A3B; '
            'optimal threshold selected on the checkpoint validation split'
        )
    return detector


SUGGESTIONS = [
    'Context: The Eiffel Tower is in Paris, France.\nQuestion: In which city is the Eiffel Tower?',
    'Context: Our return policy allows refunds within 30 days.\nQuestion: Can I get a refund after 45 days?',
    'Context: Marie Curie won Nobel Prizes in Physics (1903) and Chemistry (1911).\nQuestion: How many Nobel Prizes did Marie Curie win, and in what fields?',
]


def _api_key_input(st: Any, provider: str, *, label: str) -> str:
    """Masked API-key input for one provider; the pasted key lives only in session memory.

    Keyed by provider (``api_key:{provider}``) so a key never follows a provider switch, and so the
    judge and generator blocks can share one widget when both target the same provider. The key is
    never persisted, logged, exported, or echoed; the env var stays a fallback resolved off the empty
    return here. Caption is three-state: pasted / env detected / neither.
    """
    store_key = f'api_key:{provider}'
    pasted = st.text_input(
        label,
        type='password',
        key=store_key,
        help='Kept only in this browser session — never saved, logged, or exported.',
    )
    key_env = API_PROVIDER_KEY_ENVS.get(provider, '')
    if pasted:
        st.caption(':material/key: Key set for this session.')
    elif key_env and os.getenv(key_env):
        st.caption(f':material/key: ✓ {key_env} detected.')
    else:
        st.caption(f':red[:material/key_off: Paste a key or set {key_env}.]')
    return str(pasted or '')


def _local_judge_models(st: Any) -> list[str]:
    """Models served by the Custom judge endpoint, probed once per session (silent when down)."""
    base_url = custom_openai_base_url()
    cache_key = f'local_judge_models:{base_url}'
    if cache_key not in st.session_state:
        st.session_state[cache_key] = local_openai_models(base_url)
    return list(st.session_state[cache_key])


def _sidebar(st: Any) -> dict[str, Any]:
    from sirin.ui import presets

    key_rendered: set[str] = set()
    consent_slot = None

    with st.sidebar:
        st.html('<p class="sirin-side-heading">Detector</p>')
        preset_objs = presets.visible_presets()
        local_profile = None
        if is_trusted_local():
            profiles = longmemeval_profiles()
            if len(profiles) > 1:
                by_label = {label: profile for label, profile in profiles}
                chosen = st.selectbox(
                    'LongMemEval profile', [label for label, _ in profiles]
                )
                local_profile = by_label.get(chosen, profiles[0][1])
            elif profiles:
                local_profile = profiles[0][1]
        if local_profile:
            default_preset = local_profile['ui']['default_preset']
        elif is_hosted():
            default_preset = presets.JUDGE_SPAN_PRESET
        else:
            default_preset = presets.PSILOQA_TOKEN_LINEAR_PRESET
        names = [p.name for p in preset_objs]
        if default_preset in names:
            names.remove(default_preset)
            names.insert(0, default_preset)
        if presets.JUDGE_SPAN_PRESET in names and default_preset != presets.JUDGE_SPAN_PRESET:
            names.remove(presets.JUDGE_SPAN_PRESET)
            names.insert(1, presets.JUDGE_SPAN_PRESET)
        by_name = {p.name: p for p in preset_objs}
        preset_name = st.selectbox('Preset', names)
        preset = by_name[preset_name]
        census = presets.detector_census_caption(preset)
        st.caption(census or preset.description)

        is_judge = bool(getattr(preset, 'is_judge', False)) or preset.family == 'judge'
        judge_provider = OPENROUTER_PROVIDER
        judge_model = ''
        judge_api_key = ''
        if is_judge:
            judge_providers = [OPENROUTER_PROVIDER, OPENAI_PROVIDER, ANTHROPIC_PROVIDER]
            if is_trusted_local():
                judge_providers.append(CUSTOM_PROVIDER)
            judge_provider = st.selectbox('Judge provider', judge_providers)
            local_models = (
                _local_judge_models(st) if judge_provider == CUSTOM_PROVIDER else []
            )
            if local_models:
                judge_model = st.selectbox('Judge model', local_models)
            else:
                judge_model = st.text_input(
                    'Judge model',
                    value=provider_models(judge_provider)[0],
                )
            judge_api_key = _api_key_input(st, judge_provider, label='Judge API key')
            key_rendered.add(judge_provider)
            # Reserved for the consent checkbox so _external_confirmed renders it right here.
            consent_slot = st.container()

        checkpoint_dir = ''
        if preset.requires_checkpoint:
            checkpoint_default = ''
            if local_profile:
                default = local_profile['ui']['default_checkpoint']
                if default['preset'] == preset_name:
                    checkpoint_default = local_profile['checkpoints'][default['task']][
                        default['detector']
                    ]['path']
            if getattr(preset, 'builtin_checkpoint', None) and not checkpoint_default:
                st.caption('Using built-in PsiloQA checkpoint')
            else:
                checkpoint_dir = st.text_input(
                    'Checkpoint directory',
                    value=checkpoint_default,
                    key=f'checkpoint_dir:{preset_name}',
                    help="Leave blank to use this preset's built-in checkpoint (if any).",
                )

        st.divider()
        st.html('<p class="sirin-side-heading">Generator</p>')
        if is_hosted():
            backends = [OPENROUTER_PROVIDER, OPENAI_PROVIDER, ANTHROPIC_PROVIDER]
        else:
            backends = [
                'HF',
                OPENAI_PROVIDER,
                OPENROUTER_PROVIDER,
                ANTHROPIC_PROVIDER,
                'vLLM',
            ]
            if is_trusted_local():
                backends.append(CUSTOM_PROVIDER)
        backend = st.selectbox('Backend', backends)
        custom_base_url = ''
        gen_api_key = ''
        if backend in (OPENAI_PROVIDER, OPENROUTER_PROVIDER, ANTHROPIC_PROVIDER):
            model_path = st.text_input('Model', value=provider_models(backend)[0])
            device = 'cpu'
            if backend in key_rendered:
                # Judge and generator target the same provider — one pasted key serves both.
                gen_api_key = str(st.session_state.get(f'api_key:{backend}', '') or '')
                st.caption(f':material/key: Using the {backend} key pasted above.')
            else:
                gen_api_key = _api_key_input(st, backend, label='API key')
                key_rendered.add(backend)
        elif backend == CUSTOM_PROVIDER:
            generation_api = (
                local_profile.get('generation_api', {}) if local_profile else {}
            )
            model_path = st.text_input(
                'Model', value=(local_profile['model']['path'] if local_profile else '')
            )
            custom_base_url = st.text_input(
                'API base URL', value=str(generation_api.get('base_url') or '')
            )
            device = 'cpu'
        else:
            model_path = st.text_input(
                'Model',
                value=(
                    local_profile['model']['path'] if local_profile else HF_MODELS[0]
                ),
                key='generator_local_model',
            )
            if is_trusted_local():
                device = st.text_input(
                    'Device',
                    value=(
                        local_profile['model']['device'] if local_profile else 'cuda'
                    ),
                )
            else:
                device = st.selectbox('Device', LOCAL_DEVICES)
        if backend == 'HF':
            st.caption(
                f'Device: {device} · bf16 · one shared model for '
                'generation and probing'
            )
        else:
            st.caption(f'{backend} · remote generation')
        max_tokens = st.number_input(
            'Max tokens',
            min_value=1,
            value=(
                local_profile['ui']['max_tokens']
                if local_profile
                else _DEFAULT_UI_GENERATION_TOKENS
            ),
            key='generation_max_tokens',
        )
        temperature = st.slider(
            'Temperature',
            min_value=0.0,
            max_value=2.0,
            value=(local_profile['ui']['temperature'] if local_profile else 0.7),
            key='generation_temperature',
        )

        use_hydra = False
        config_dir = _default_config_dir()
        config_name = 'train'
        overrides_text = 'train_dataset_path=null eval_dataset_path=null'
        hydra_checkpoint = ''

    return {
        'backend': backend,
        'model_path': _clean_field(model_path),
        # Hosted runs on a public CPU box; no widget path may ever hand it a GPU device.
        'device': 'cpu' if is_hosted() else _clean_field(device),
        'custom_base_url': _clean_field(custom_base_url),
        'max_tokens': int(max_tokens),
        'temperature': float(temperature),
        'preset_name': preset_name,
        'judge_provider': judge_provider,
        'judge_model': _clean_field(judge_model),
        # Session-only pasted keys (never persisted/exported); '' means fall back to the env var.
        'judge_api_key': judge_api_key,
        'api_key': gen_api_key,
        'checkpoint_dir': _clean_path_field(checkpoint_dir),
        'use_hydra': use_hydra,
        'config_dir': _clean_path_field(config_dir),
        'config_name': _clean_field(config_name),
        'overrides_text': _clean_field(overrides_text),
        'hydra_checkpoint': _clean_path_field(hydra_checkpoint),
        # Popped by the caller before cfg is digested/exported; never part of run identity.
        '_consent_slot': consent_slot,
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
        # Pasted key wins; '' lets the preset resolve the provider env var as fallback.
        cfg.get('judge_api_key', ''),
    )


def _compare_cfg(cfg: dict[str, Any], st: Any, preset_name: str) -> dict[str, Any]:
    """A detector config for compare side B, honoring preset B's own defaults.

    Side A is the sidebar ``cfg``. For B we swap the preset, drop any typed checkpoint path (B uses its
    own built-in checkpoint if it has one), and for a judge preset resolve its default provider/model —
    reusing a key already pasted for that same provider. The generator settings stay A's, since B never
    generates (it scores the answer A produced/received).
    """
    from sirin.ui import presets

    preset_b = presets.PRESETS.get(preset_name)
    if preset_b is None or preset_name == cfg['preset_name']:
        return dict(cfg)
    cfg_b = dict(cfg)
    cfg_b['preset_name'] = preset_name
    cfg_b['checkpoint_dir'] = ''
    if getattr(preset_b, 'is_judge', False) or preset_b.family == 'judge':
        provider = cfg.get('judge_provider') or OPENROUTER_PROVIDER
        cfg_b['judge_provider'] = provider
        cfg_b['judge_model'] = provider_models(provider)[0]
        cfg_b['judge_api_key'] = str(st.session_state.get(f'api_key:{provider}', '') or '')
    return cfg_b


def _preset_task(name: str) -> str:
    return 'answerability' if 'Answerability' in name else 'faithfulness'


def _needs_checkpoint_side_b_cannot_take(preset: Any) -> bool:
    """True when a preset needs a checkpoint directory compare side B can never receive.

    Side B always drops the sidebar checkpoint path (see _compare_cfg), so a checkpoint-requiring
    preset can only run as B off its bundled checkpoint.
    """
    return bool(
        getattr(preset, 'requires_checkpoint', False)
        and not getattr(preset, 'builtin_checkpoint', None)
    )


def _compare_available_presets(active_preset: str, task: str) -> list[str]:
    """Presets offered in the compare picker: valid for the task AND actually runnable as side B.

    Excludes side A itself, uncertainty detectors (they must generate, so they cannot score side A's
    answer), and checkpoint-requiring presets without a bundled checkpoint (side B has no checkpoint
    input, so they could never run — see _needs_checkpoint_side_b_cannot_take).
    """
    from sirin.ui import presets

    return [
        preset.name
        for preset in presets.visible_presets()
        if preset.name != active_preset
        and _preset_task(preset.name) == task
        and preset.family != 'uncertainty'
        and not _needs_checkpoint_side_b_cannot_take(preset)
        # Replay-only hosted presets cannot score live, so they cannot be a compare side.
        and not presets.hosted_replay_only(preset.family)
    ]


def _compare_side_b_error(cfg: dict[str, Any], st: Any, preset_name: str) -> str | None:
    """Actionable reason side B cannot run (missing checkpoint / backend / API key), or None.

    Computed BEFORE any run is queued so a comparison that would fail on a missing resource is rejected
    up front. An unknown preset returns None here and is rejected by the controller with its own message.
    """
    from sirin.ui import presets

    preset_b = presets.PRESETS.get(preset_name)
    if preset_b is None:
        return None
    if preset_name != cfg.get('preset_name') and _needs_checkpoint_side_b_cannot_take(
        preset_b
    ):
        return (
            f'The comparison detector "{preset_name}" needs a trained checkpoint '
            'directory, and side B cannot take one. Select it as the sidebar detector '
            '(side A), enter its checkpoint directory there, and pick the other '
            'detector as side B.'
        )
    cfg_b = _compare_cfg(cfg, st, preset_name)
    error = _detector_setup_error(cfg_b)
    if error:
        return error
    if getattr(preset_b, 'is_judge', False) or preset_b.family == 'judge':
        provider = cfg_b.get('judge_provider') or OPENROUTER_PROVIDER
        env_var = API_PROVIDER_KEY_ENVS.get(provider, '')
        if not (cfg_b.get('judge_api_key') or (env_var and os.getenv(env_var))):
            return (
                f'The comparison detector "{preset_name}" needs an API key for {provider}. '
                f'Paste it in the sidebar or set {env_var}.'
            )
    return None


def _detector_setup_error(cfg: dict[str, Any]) -> str | None:
    if (
        cfg.get('preset_name') == 'Probing — Sequence TabPFN (checkpoint)'
        and cfg.get('backend')
        and cfg.get('backend') != 'HF'
    ):
        return (
            'Sequence probing requires the HF backend so SIRIN can extract hidden '
            'states from the selected generator model.'
        )
    path = (
        cfg.get('hydra_checkpoint')
        if cfg.get('use_hydra')
        else cfg.get('checkpoint_dir')
    )
    if not path:
        if cfg.get('preset_name') == 'Probing — Sequence TabPFN (checkpoint)':
            return 'This preset needs a trained checkpoint directory.'
        return None
    try:
        require_checkpoint_path(path)
    except ValueError as error:
        return str(error)
    if cfg.get('preset_name') == 'Probing — Sequence TabPFN (checkpoint)':
        from sirin.ui.presets import sequence_tabpfn_checkpoint_shape_error

        return sequence_tabpfn_checkpoint_shape_error(path, cfg.get('model_path'))
    return None


def _max_detector_input_chars() -> int:
    try:
        return max(1, int(os.getenv(_MAX_DETECTOR_INPUT_CHARS_ENV, '')))
    except ValueError:
        return _DEFAULT_MAX_DETECTOR_INPUT_CHARS


def _detector_input_size_error(
    prompt: str,
    answer: str = '',
) -> str | None:
    size = len(prompt) + len(answer)
    limit = _max_detector_input_chars()
    if any(prompt == case['answer_prompt'] for case in load_demo_cases().values()):
        limit = max(limit, size)
    if size <= limit:
        return None
    return (
        f'Detector input is too large for the live UI guard ({size:,} characters; '
        f'limit {limit:,}). Shorten the input or set '
        f'`{_MAX_DETECTOR_INPUT_CHARS_ENV}` higher before starting Streamlit.'
    )


def requires_external_confirmation(cfg: dict[str, Any]) -> bool:
    if cfg.get('backend') == CUSTOM_PROVIDER:
        host = urlparse(str(cfg.get('custom_base_url') or '')).hostname
        if host in {'127.0.0.1', 'localhost', '::1'}:
            return False
    return cfg.get('backend') in API_BACKENDS or str(
        cfg.get('preset_name', '')
    ).startswith('Judge — API')


def _external_confirmed(
    st: Any,
    cfg: dict[str, Any],
    *,
    key: str = 'external_api_consent',
    slot: Any = None,
) -> bool:
    if not requires_external_confirmation(cfg):
        return True
    # A judge preset reserves a slot under the Judge API key input; otherwise the checkbox lands
    # at the end of the sidebar's generator settings, as before. Checked by default — the demo's
    # whole point is the external judge call; unticking it still blocks every external request.
    with slot if slot is not None else st.sidebar:
        return st.checkbox(
            'Allow external API calls',
            value=True,
            key=key,
            help='Context, questions, generated answers, and judge prompts may be sent to the selected external API provider. Untick to block all external calls.',
        )


def _inspection_prompt(context: str, question: str) -> str:
    return f'Context:\n{context.strip()}\n\nQuestion:\n{question.strip()}'


def _appearance_sidebar(st: Any, *, key_prefix: str = '') -> None:
    def store_workspace_appearance() -> None:
        if key_prefix != 'sirin.workspace.v2.':
            return
        stored = st.session_state.get('sirin.workspace.v2.view_state')
        stored = dict(stored) if isinstance(stored, dict) else {}
        appearance = {
            'theme': str(st.session_state.get(f'{key_prefix}ui_theme', 'Light')).lower(),
            'motion': str(st.session_state.get(f'{key_prefix}bg_motion', 'Subtle')).lower(),
        }
        stored['appearance'] = appearance
        st.session_state['sirin.workspace.v2.view_state'] = stored

    with st.sidebar:
        st.divider()
        st.html('<p class="sirin-side-heading">Appearance</p>')
        st.selectbox(
            'Theme',
            ['Light', 'Dark'],
            key=f'{key_prefix}ui_theme',
            on_change=store_workspace_appearance,
        )
        st.selectbox(
            'Background motion',
            ['Subtle', 'Static', 'Lively'],
            key=f'{key_prefix}bg_motion',
            on_change=store_workspace_appearance,
            help='Silk backdrop animation. Static is lightest for low-power devices.',
        )


_V2_COMPONENT_KEY = 'sirin.workspace.v2'
_V2_SESSION_KEY = 'sirin.workspace.v2.session'
_V2_VIEW_STATE_KEY = 'sirin.workspace.v2.view_state'


def _hydrate_v2_appearance(st: Any) -> None:
    component_state = st.session_state.get(_V2_COMPONENT_KEY)
    appearance = (
        component_state.get('appearance')
        if hasattr(component_state, 'get')
        else None
    )
    if not isinstance(appearance, dict):
        return
    theme = {'light': 'Light', 'dark': 'Dark'}.get(
        str(appearance.get('theme', '')).lower()
    )
    motion = {
        'static': 'Static',
        'subtle': 'Subtle',
        'lively': 'Lively',
    }.get(str(appearance.get('motion', '')).lower())
    if theme:
        st.session_state['sirin.workspace.v2.ui_theme'] = theme
    if motion:
        st.session_state['sirin.workspace.v2.bg_motion'] = motion


def _pending_workspace(st: Any) -> str | None:
    """Return the workspace the client just navigated to via the transient viewState event.

    Client-side tab switches arrive as a one-shot ``viewState`` trigger on the component state.
    Reading it here — before the payload is built — lets a pure navigation reconcile within its own
    natural rerun without an extra ``st.rerun()`` and without the payload reverting the client's
    optimistic switch.
    """
    component_state = st.session_state.get(_V2_COMPONENT_KEY)
    view_state = component_state.get('viewState') if hasattr(component_state, 'get') else None
    workspace = view_state.get('workspace') if isinstance(view_state, dict) else None
    return workspace if workspace in {'analyze', 'runs', 'diagnostics', 'compare'} else None


def _v2_modules() -> tuple[Any, ...] | None:
    try:
        from sirin.ui.workspace import (
            ActionEnvelope,
            CapabilitySet,
            DiagnosticsSummary,
            RunEngine,
            SetupSnapshot,
            WorkspaceController,
            WorkspaceSession,
        )
        from sirin.ui.workspace.component import render_workspace
    except (ImportError, ModuleNotFoundError):
        return None
    return (
        ActionEnvelope,
        CapabilitySet,
        DiagnosticsSummary,
        RunEngine,
        SetupSnapshot,
        WorkspaceController,
        WorkspaceSession,
        render_workspace,
    )


def _dto(model: Any, values: dict[str, Any]) -> Any:
    """Build a workspace DTO while tolerating additive backend fields."""
    fields = getattr(model, 'model_fields', {})
    filtered = {name: values[name] for name in fields if name in values}
    return model.model_validate(filtered)


def _request_value(request: Any, name: str, default: Any = '') -> Any:
    if isinstance(request, dict):
        return request.get(name, default)
    return getattr(request, name, default)


def _render_v2_native_attention(st: Any, tool: str) -> None:
    with st.sidebar:
        st.header(':material/troubleshoot: Diagnostics')
        if st.button('Return to SIRIN workspace', key='sirin_v2_attention_return'):
            st.session_state['attention_tool'] = ''
            st.rerun()
        st.caption('Trusted-local native attention tooling.')
    _appearance_sidebar(st, key_prefix='sirin.workspace.v2.')
    if tool == 'explorer':
        from sirin.ui import attention_explorer

        attention_explorer.render(st)
        return
    from sirin.ui import live_attention

    live_attention.render(st)


def _v2_prompt(request: Any) -> str:
    context = str(_request_value(request, 'context') or '').strip()
    question = str(_request_value(request, 'question') or '').strip()
    prompt = str(_request_value(request, 'prompt') or '').strip()
    mode = str(_request_value(request, 'mode') or '')
    if prompt and (not context or mode == 'recordedReplay'):
        return prompt
    if context or question:
        if not context or not question:
            raise ValueError('Context and question are required.')
        return _inspection_prompt(context, question)
    if not prompt:
        raise ValueError('Enter a prompt or a context and question.')
    return prompt


def _render_v2_workspace(st: Any, modules: tuple[Any, ...]) -> None:
    (
        ActionEnvelope,
        CapabilitySet,
        DiagnosticsSummary,
        RunEngine,
        SetupSnapshot,
        WorkspaceController,
        WorkspaceSession,
        render_workspace,
    ) = modules

    from sirin.inference.model_manager import ModelManager
    from sirin.ui.workspace.run_engine import ConsentRequiredError

    cfg = _sidebar(st)
    external_confirmed = _external_confirmed(
        st,
        cfg,
        key='sirin.workspace.v2.external_api_consent',
        slot=cfg.pop('_consent_slot', None),
    )
    setup_error = _detector_setup_error(cfg)
    _appearance_sidebar(st, key_prefix='sirin.workspace.v2.')

    # Keys never enter any derived artifact (digest, snapshot, provenance) — drop them here.
    digest_cfg = {k: v for k, v in cfg.items() if k not in {'api_key', 'judge_api_key'}}
    setup_digest = hashlib.sha256(
        json.dumps(digest_cfg, sort_keys=True, default=str).encode('utf-8')
    ).hexdigest()
    from sirin.ui import presets
    from sirin.ui.workspace.contracts import derive_score_semantics

    preset = presets.PRESETS[cfg['preset_name']]
    detector_family = preset.family
    detector_level = 'token' if 'Token' in cfg['preset_name'] else 'sequence'
    calibrated = bool(getattr(preset, 'calibrated', False))
    preset_layer = getattr(preset, 'layer', None)
    if not isinstance(preset_layer, int) or preset_layer < 0:
        preset_layer = None
    score_semantics = derive_score_semantics(
        calibrated=calibrated,
        family=detector_family,
        level=detector_level,
    )
    model_id = cfg['model_path']
    if Path(model_id).is_absolute():
        model_id = Path(model_id).name
    setup_values = {
        'task': 'answerability'
        if 'Answerability' in cfg['preset_name']
        else 'faithfulness',
        'detector_preset': cfg['preset_name'],
        'detector_family': detector_family,
        'detector_level': detector_level,
        'model_id': model_id or None,
        'provider_label': cfg['backend'],
        'calibrated': calibrated,
        'score_semantics': score_semantics,
        'layer': preset_layer,
    }
    setup = _dto(SetupSnapshot, setup_values)

    # Compare side B: resolve a preset name into its OWN SetupSnapshot (built the same way as side A).
    # Raises ValueError (caught by the controller as a reject) when B is unknown, is A itself, or does
    # not support the active task.
    def compare_setup(preset_b_name: str, setup_a: SetupSnapshot) -> SetupSnapshot:
        preset_b = presets.PRESETS.get(preset_b_name)
        if preset_b is None:
            raise ValueError('The selected comparison detector is not available.')
        if preset_b_name == cfg['preset_name']:
            raise ValueError('Choose a different detector for side B.')
        if _preset_task(preset_b_name) != str(setup_a.task):
            raise ValueError('The comparison detector does not support this task.')
        if preset_b.family == 'uncertainty':
            # B always scores the answer A produced/received; an uncertainty detector needs to generate
            # to measure token uncertainty and cannot score a supplied answer (mirrors _submit's guard).
            raise ValueError('An uncertainty detector cannot score a supplied answer, so it cannot be side B.')
        return _dto(SetupSnapshot, {
            'task': _preset_task(preset_b_name),
            'detector_preset': preset_b.name,
            'detector_family': preset_b.family,
            'detector_level': preset_b.level,
            'calibrated': bool(getattr(preset_b, 'calibrated', False)),
            'score_semantics': derive_score_semantics(
                calibrated=bool(getattr(preset_b, 'calibrated', False)),
                family=preset_b.family,
                level=preset_b.level,
            ),
            'model_id': model_id or None,
            'provider_label': cfg['backend'],
        })

    available_presets = _compare_available_presets(cfg['preset_name'], setup_values['task'])
    model_loaded = bool(getattr(ModelManager, '_active_models', {}))
    trusted_local = is_trusted_local()
    capabilities = _dto(
        CapabilitySet,
        {
            'trusted_local': trusted_local,
            'external_calls': external_confirmed,
            'external_calls_confirmed': external_confirmed,
            'can_generate': external_confirmed and setup_error is None,
            'can_detect': external_confirmed and setup_error is None,
            'can_diagnose': is_trusted_local(),
            'can_capture': is_trusted_local(),
            'can_unload': is_trusted_local(),
            'can_import': True,
            'can_export': True,
            'detailed_diagnostics': trusted_local,
            'can_refresh_diagnostics': trusted_local,
            'can_capture_attention': False,
            'can_unload_models': trusted_local,
            'can_open_cached_attention': trusted_local,
            'can_open_live_attention': trusted_local,
        },
    )
    diagnostics = _dto(
        DiagnosticsSummary,
        {
            'runtime': 'Python · Streamlit',
            'device': cfg['device'] if trusted_local and model_loaded else 'Loads on first run',
            'model_loaded': model_loaded,
            'active_model': model_id if model_loaded else None,
            'attention_available': trusted_local,
            # Shared-safe redaction is already stated once by the diagnostics privacy banner; do not
            # echo it here. Only trusted-local carries an extra, non-redundant message.
            'message': 'Native attention tools are available.' if trusted_local else None,
        },
    )

    def generate(request: Any, _setup: Any) -> str:
        if requires_external_confirmation(cfg) and not external_confirmed:
            raise ConsentRequiredError(
                'External API calls need your consent. Turn on “Allow external '
                'API calls” in the sidebar, then run again.'
            )
        prompt = _v2_prompt(request)
        adapter = load_generator(
            cfg['backend'],
            cfg['model_path'],
            cfg['device'],
            cfg.get('custom_base_url', ''),
            cfg.get('api_key', ''),
        )
        raw = generate_answer(
            adapter,
            cfg['backend'],
            prompt,
            cfg['max_tokens'],
            cfg['temperature'],
        )
        answer, _reason = _split_thinking(raw)
        return answer

    def detect(answer: str, request: Any, run_setup: Any) -> dict[str, Any]:
        # Compare side B runs the SAME detect path with preset B's own config; the run's setup snapshot
        # names the preset, so a compare-B run builds its own detector while side A keeps the sidebar cfg.
        detect_cfg = _compare_cfg(
            cfg, st, getattr(run_setup, 'detector_preset', None) or cfg['preset_name']
        )
        if requires_external_confirmation(detect_cfg) and not external_confirmed:
            raise ConsentRequiredError(
                'External API calls need your consent. Turn on “Allow external '
                'API calls” in the sidebar, then run again.'
            )
        prompt = _v2_prompt(request)
        setup_error = _detector_setup_error(detect_cfg)
        if setup_error:
            raise ValueError(f'Detection setup failed: {setup_error}')
        size_error = _detector_input_size_error(prompt, answer)
        if size_error:
            raise ValueError(size_error)
        detector = _build_detector(detect_cfg)
        result = detector.detect([build_sample(prompt, answer.strip())])
        view = detection_view_model(result, answer.strip(), detector)
        return view

    def trusted_diagnostic(operation: Any) -> None:
        if not is_trusted_local():
            raise ValueError('Trusted-local mode is required for this action.')
        try:
            with ModelManager.exclusive_run():
                operation()
        except RuntimeError:
            raise ValueError('Model runtime is busy; try again after the active run.') from None
        except Exception:
            raise ValueError('The diagnostics action failed.') from None

    diagnostic_actions = {
        'refreshDiagnostics': lambda: trusted_diagnostic(lambda: None),
        'unloadModels': lambda: trusted_diagnostic(_unload_cached_models),
        'openCachedAttention': lambda: trusted_diagnostic(
            lambda: st.session_state.__setitem__('attention_tool', 'explorer')
        ),
        'openLiveAttention': lambda: trusted_diagnostic(
            lambda: st.session_state.__setitem__('attention_tool', 'live')
        ),
    }

    session = WorkspaceSession(st.session_state, key=_V2_SESSION_KEY)
    previous_setup = st.session_state.get('sirin.workspace.v2.setup_digest')
    if previous_setup is not None and previous_setup != setup_digest:
        session.state.setup_revision += 1
    st.session_state['sirin.workspace.v2.setup_digest'] = setup_digest
    # Execution-compatibility signature (preset/model/backend/task only, not appearance or generation
    # knobs) lets a late action survive a benign setup bump instead of being forced to resubmit.
    setup_signature = hashlib.sha256(
        json.dumps(
            {
                'preset': cfg['preset_name'],
                'model': cfg['model_path'],
                'backend': cfg['backend'],
                'task': setup_values['task'],
            },
            sort_keys=True,
        ).encode('utf-8')
    ).hexdigest()
    session.note_setup(setup_signature)
    session.recover_interrupted()
    controller = WorkspaceController(
        session,
        RunEngine(generate=generate, detect=detect),
        diagnostic_actions=diagnostic_actions,
        compare_setup=compare_setup,
    )
    controller.seed_landing(setup)
    stored_view = st.session_state.get(_V2_VIEW_STATE_KEY)
    stored_view = stored_view if isinstance(stored_view, dict) else {}
    # A client-side tab switch reaches the server as a transient viewState event. Fold it into the
    # canonical view BEFORE the payload is built so this rerun already reflects the clicked tab (no
    # reverting flash) and needs no extra st.rerun(). Server-initiated view changes still win: they
    # update the stored canonical, which this same read consults when no navigation event is pending.
    workspace = _pending_workspace(st) or stored_view.get('workspace', 'analyze')
    if workspace not in {'analyze', 'runs', 'diagnostics', 'compare'}:
        workspace = 'analyze'
    view_state = {
        'workspace': workspace,
        'appearance': {
            'theme': str(
                st.session_state.get('sirin.workspace.v2.ui_theme', 'Light')
            ).lower(),
            'motion': str(
                st.session_state.get('sirin.workspace.v2.bg_motion', 'Subtle')
            ).lower(),
        },
    }
    st.session_state[_V2_VIEW_STATE_KEY] = view_state
    payload_model = controller.build_payload(
        setup=setup,
        capabilities=capabilities,
        diagnostics=diagnostics,
        view_state=view_state,
        available_presets=available_presets,
    )
    payload = payload_model.model_dump(mode='json', by_alias=True, exclude_none=True)
    event = render_workspace(payload, key=_V2_COMPONENT_KEY) or {}
    action_data = event.get('action')
    if action_data:
        action = ActionEnvelope.model_validate(action_data)
        action_error = setup_error
        if action.type == 'runCompare':
            preset_b_name = action.payload.get('presetB')
            if isinstance(preset_b_name, str) and preset_b_name:
                b_error = _compare_side_b_error(cfg, st, preset_b_name)
                if b_error is None and requires_external_confirmation(
                    _compare_cfg(cfg, st, preset_b_name)
                ) and not external_confirmed:
                    b_error = (
                        f'Comparing with "{preset_b_name}" would call an external API. Make an API '
                        'detector or generator side A and turn on “Allow external API calls”, then '
                        'run the comparison again.'
                    )
                action_error = setup_error or b_error
        controller.handle(action, setup=setup, submission_error=action_error)
        st.rerun()
    if controller.advance():
        st.rerun()


def main() -> None:
    import streamlit as st

    from sirin.ui import styles

    modules = _v2_modules()
    if modules is None:
        raise RuntimeError(
            "The unified SIRIN workspace is unavailable. Install the UI dependencies "
            "and packaged component assets before starting Streamlit."
        )
    key_prefix = 'sirin.workspace.v2.'
    _hydrate_v2_appearance(st)
    motion = str(st.session_state.get(f'{key_prefix}bg_motion', 'Subtle')).lower()
    theme = str(st.session_state.get(f'{key_prefix}ui_theme', 'Light')).lower()

    st.set_page_config(page_title='SIRIN', page_icon=str(LOGO_PATH), layout='wide')
    styles.inject_global_styles(st, motion=motion, theme=theme)
    attention_tool = str(st.session_state.get('attention_tool', '') or '')
    if attention_tool in {'explorer', 'live'} and is_trusted_local():
        _render_v2_native_attention(st, attention_tool)
        return
    if attention_tool:
        st.session_state['attention_tool'] = ''
    _render_v2_workspace(st, modules)




if __name__ == '__main__':
    main()
