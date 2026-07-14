"""Convert detector outputs into truthful, detector-typed presentation data."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .contracts import (
    AnalysisKind,
    AnalysisResult,
    CategoryScore,
    ClaimScore,
    ScoreSemantics,
    SetupSnapshot,
    TaskType,
    TextSegment,
    derive_score_semantics,
)


def _plain(value: Any) -> Any:
    return value.tolist() if hasattr(value, 'tolist') else value


def _scalar(value: Any) -> float | None:
    value = _plain(value)
    while isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            return None
        value = value[0]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _semantics(setup: SetupSnapshot, kind: AnalysisKind) -> ScoreSemantics:
    if setup.score_semantics != ScoreSemantics.UNAVAILABLE:
        return setup.score_semantics
    return derive_score_semantics(
        calibrated=setup.calibrated,
        family=setup.detector_family,
        level=setup.detector_level,
        threshold=setup.threshold,
        kind=kind,
    )


def _span_segments(answer: str, spans: Sequence[Any]) -> list[TextSegment]:
    parsed: list[tuple[int, int, float | None, bool | None]] = []
    for item in spans:
        if isinstance(item, Mapping):
            start, end = item.get('start'), item.get('end')
            score, verdict = item.get('score'), item.get('verdict', True)
        elif isinstance(item, Sequence) and len(item) >= 2:
            start, end = item[0], item[1]
            score = item[2] if len(item) > 2 else None
            verdict = item[3] if len(item) > 3 else True
        else:
            continue
        if (
            isinstance(start, int) and not isinstance(start, bool)
            and isinstance(end, int) and not isinstance(end, bool)
            and 0 <= start < end <= len(answer)
        ):
            parsed.append((
                start,
                end,
                _scalar(score),
                None if verdict is None else bool(verdict),
            ))
    parsed.sort()
    segments: list[TextSegment] = []
    cursor = 0
    for start, end, score, verdict in parsed:
        if start < cursor:
            continue
        if cursor < start:
            segments.append(TextSegment(
                text=answer[cursor:start], start_code_point=cursor, end_code_point=start
            ))
        segments.append(TextSegment(
            text=answer[start:end], start_code_point=start, end_code_point=end,
            score=score, verdict=verdict,
        ))
        cursor = end
    if cursor < len(answer):
        segments.append(TextSegment(
            text=answer[cursor:], start_code_point=cursor, end_code_point=len(answer)
        ))
    return segments


def _character_segments(answer: str, scores: Sequence[Any], predictions: Sequence[Any]) -> list[TextSegment]:
    if len(scores) != len(answer) or len(predictions) != len(answer):
        return []
    segments: list[TextSegment] = []
    start = 0
    current = bool(predictions[0]) if answer else False
    for index in range(1, len(answer) + 1):
        changed = index == len(answer) or bool(predictions[index]) != current
        if changed:
            numeric = [_scalar(score) for score in scores[start:index]]
            values = [score for score in numeric if score is not None]
            segments.append(TextSegment(
                text=answer[start:index],
                start_code_point=start,
                end_code_point=index,
                score=max(values) if current and values else None,
                verdict=current if current else None,
            ))
            if index < len(answer):
                start, current = index, bool(predictions[index])
    return segments


def _normalize_legacy_view(answer: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Map the existing Streamlit detector view onto the typed presenter keys."""
    normalized = dict(data)
    probability = normalized.get('probability')
    if probability is not None and not isinstance(probability, Sequence):
        raw_score = normalized.get('raw_prob')
        normalized.setdefault('score', probability if raw_score is None else raw_score)
        normalized.setdefault('verdict', normalized.get('prediction'))
    class_probs = normalized.get('class_probs')
    if isinstance(class_probs, Sequence):
        normalized['categories'] = [
            (f'Class {index}', value) for index, value in enumerate(class_probs)
        ]
        normalized.pop('verdict', None)

    claims = normalized.get('claims')
    if isinstance(claims, Sequence):
        normalized['claims'] = [
            {
                'text': str(item.get('text') or item.get('fact') or 'Claim'),
                'score': item.get('score', item.get('prob')),
                'verdict': item.get('verdict', item.get('pred')),
            }
            for item in claims
            if isinstance(item, Mapping)
        ]
        normalized.setdefault('score', normalized.get('overall_prob'))
        normalized.setdefault('verdict', normalized.get('overall_pred'))

    spans = normalized.get('spans')
    if not spans:
        normalized.pop('spans', None)
    scores = normalized.get('scores')
    predictions = normalized.get('predictions')
    if isinstance(scores, Sequence) and isinstance(predictions, Sequence):
        if len(scores) == len(answer) and len(predictions) == len(answer):
            normalized['char_scores'] = scores
            normalized['char_predictions'] = predictions
        elif normalized.get('token_offsets') and len(scores) == len(normalized['token_offsets']):
            normalized['spans'] = [
                {
                    'start': offsets[0],
                    'end': offsets[1],
                    'score': scores[index],
                    'verdict': predictions[index] if index < len(predictions) else None,
                }
                for index, offsets in enumerate(normalized['token_offsets'])
                if isinstance(offsets, Sequence) and len(offsets) >= 2
            ]
    return normalized


def present_analysis(answer: str, setup: SetupSnapshot, output: Any) -> AnalysisResult:
    """Normalize common SIRIN detector outputs without inventing missing localization."""
    if isinstance(output, AnalysisResult):
        return output
    data = _normalize_legacy_view(answer, output) if isinstance(output, Mapping) else {}
    level = setup.detector_level.lower()
    kind = AnalysisKind(level) if level in {item.value for item in AnalysisKind} else AnalysisKind.SEQUENCE
    if setup.detector_family == 'uncertainty':
        kind = AnalysisKind.UNCERTAINTY if kind == AnalysisKind.SEQUENCE else kind

    if data.get('kind'):
        return AnalysisResult.model_validate(data)

    score = _scalar(data.get('score'))
    verdict = data.get('verdict')
    segments: list[TextSegment] = []
    categories: list[CategoryScore] = []
    claims: list[ClaimScore] = []

    if 'spans' in data:
        kind = AnalysisKind.SPAN
        segments = _span_segments(answer, _plain(data['spans']))
    elif 'char_scores' in data and 'char_predictions' in data:
        kind = AnalysisKind.SPAN
        segments = _character_segments(
            answer, _plain(data['char_scores']), _plain(data['char_predictions'])
        )
    elif 'categories' in data:
        kind = AnalysisKind.MULTICLASS
        source = data['categories']
        pairs = source.items() if isinstance(source, Mapping) else source
        categories = [CategoryScore(label=str(label), score=float(value)) for label, value in pairs]
    elif 'claims' in data:
        kind = AnalysisKind.CLAIM
        claims = [ClaimScore.model_validate(item) for item in data['claims']]
    elif isinstance(output, Sequence) and not isinstance(output, (str, bytes)):
        values = [_plain(value) for value in output]
        if kind in {AnalysisKind.SPAN, AnalysisKind.TOKEN} and len(values) >= 2:
            raw_scores, raw_predictions = values[0], values[1]
            while isinstance(raw_scores, Sequence) and len(raw_scores) == 1:
                raw_scores = raw_scores[0]
            while isinstance(raw_predictions, Sequence) and len(raw_predictions) == 1:
                raw_predictions = raw_predictions[0]
            if isinstance(raw_scores, Sequence) and isinstance(raw_predictions, Sequence):
                segments = _character_segments(answer, raw_scores, raw_predictions)
                kind = AnalysisKind.SPAN
        score = score if score is not None else _scalar(values[0] if values else None)

    if verdict is None and score is not None and setup.threshold is not None:
        verdict = score >= setup.threshold
    if verdict is not None:
        verdict = bool(verdict)
    if score is None and segments:
        suspect_scores = [segment.score for segment in segments if segment.verdict and segment.score is not None]
        score = max(suspect_scores) if suspect_scores else None
        verdict = any(segment.verdict for segment in segments)

    semantics = _semantics(setup, kind)
    if setup.task == TaskType.ANSWERABILITY:
        label = 'Answerable' if verdict else 'Unanswerable'
        if verdict is None:
            label = 'Answerability detector result'
    else:
        label = 'Unsupported content detected' if verdict else 'No unsupported content detected'
        if verdict is None:
            label = 'Detector result'
    note = None
    if semantics == ScoreSemantics.UNAVAILABLE:
        note = 'This detector does not expose a calibrated or thresholded score.'
    # A detector view may carry its own honest scale disclosure (e.g. judge k/n span agreement);
    # surface it as the result note so the card states what the score means, not what it is not.
    signal_note = data.get('signal_note')
    if isinstance(signal_note, str) and signal_note.strip():
        note = signal_note.strip()[:500]
    return AnalysisResult(
        kind=kind,
        score_semantics=semantics,
        label=label,
        verdict=verdict,
        score=score,
        threshold=setup.threshold,
        calibrated=setup.calibrated,
        segments=segments,
        categories=categories,
        claims=claims,
        note=note,
    )
