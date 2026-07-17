"""Synchronous execution wrapper around injected SIRIN generation/detection calls."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from loguru import logger as lg

from .contracts import (
    Provenance,
    PublicError,
    RunInputs,
    RunMode,
    RunOrigin,
    RunRecord,
    RunRequest,
    RunStatus,
    SafeTimings,
    SetupSnapshot,
    TaskType,
    derive_score_semantics,
    utc_now,
)
from .presenter import present_analysis


Generate = Callable[[RunRequest, SetupSnapshot], str | Mapping[str, Any]]
Detect = Callable[[str, RunRequest, SetupSnapshot], Any]


class ConsentRequiredError(PermissionError):
    """Raised when a run needs external-API consent the viewer has not yet granted.

    A ``PermissionError`` subclass so existing ``except PermissionError`` sites still catch it, but a
    distinct type lets the engine surface its own actionable message verbatim. A stray filesystem
    ``PermissionError`` (whose text can embed a path) is deliberately NOT surfaced — it falls through
    to the generic, sanitized failure instead.
    """


def _digest(request: RunRequest) -> str:
    encoded = json.dumps(
        request.model_dump(mode='json', by_alias=True),
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _is_judge_annotation_error(exc: BaseException) -> bool:
    """A judge produced no verbatim annotation to align (``JudgeAnnotationError``).

    Matched by class name so this light engine module stays decoupled from the heavy
    ``sirin.detection`` import stack (already loaded by the time a detector runs).
    """
    return any(cls.__name__ == 'JudgeAnnotationError' for cls in type(exc).__mro__)


def _exception_name_matches(exc: BaseException, name: str) -> bool:
    """Class-name MRO match, same decoupling rationale as ``_is_judge_annotation_error``
    (here it also avoids importing the openai SDK in this light module)."""
    return any(cls.__name__ == name for cls in type(exc).__mro__)


# Common provider failures a public paste-a-key demo hits constantly. The copy is ours,
# never raw provider output (which can echo request details).
_PROVIDER_ERROR_COPY: tuple[tuple[str, str, str], ...] = (
    (
        'RateLimitError',
        'provider_rate_limited',
        'The judge provider rate-limited this API key (free-tier daily quotas are '
        'small, and one span run makes several requests). Wait for the daily reset, '
        'add provider credits, or paste a different key.',
    ),
    (
        'AuthenticationError',
        'provider_auth_failed',
        'The judge provider rejected this API key. Check the pasted key and the '
        'selected provider, then try again.',
    ),
)


def _origin(request: RunRequest) -> RunOrigin:
    if request.source_run_id:
        return RunOrigin.RERUN_IMPORTED
    if request.mode == RunMode.RECORDED_REPLAY:
        return RunOrigin.RECORDED_ANSWER
    if request.mode == RunMode.ANSWERABILITY:
        return RunOrigin.ANSWERABILITY
    if request.mode == RunMode.SCORE_SUPPLIED_ANSWER:
        return RunOrigin.SUPPLIED_ANSWER
    return RunOrigin.GENERATED_NOW


class RunEngine:
    def __init__(self, *, generate: Generate | None, detect: Detect) -> None:
        self.generate = generate
        self.detect = detect

    def reserve(
        self,
        request: RunRequest,
        setup: SetupSnapshot,
        setup_revision: int,
        provenance: Provenance | None = None,
    ) -> RunRecord:
        input_values = {
            'context': request.context,
            'question': request.question,
            'supplied_answer': request.supplied_answer,
            'prompt': request.prompt,
            'example_id': request.example_id,
        }
        inputs = (
            RunInputs.model_construct(**input_values)
            if request.mode == RunMode.RECORDED_REPLAY
            else RunInputs.model_validate(input_values)
        )
        return RunRecord(
            id=str(uuid4()),
            created_at=utc_now(),
            status=RunStatus.QUEUED,
            origin=_origin(request),
            setup_revision=setup_revision,
            setup_snapshot=setup,
            inputs=inputs,
            provenance=provenance or Provenance(source_run_id=request.source_run_id),
            request_digest=_digest(request),
        )

    def execute(self, queued: RunRecord, request: RunRequest) -> RunRecord:
        from sirin.inference.model_manager import ModelManager

        try:
            with ModelManager.exclusive_run():
                return self._execute_exclusive(queued, request)
        except RuntimeError:
            return self._failure(queued, 'busy', 'Another model operation is running.')

    def _execute_exclusive(self, queued: RunRecord, request: RunRequest) -> RunRecord:
        started = time.monotonic()
        generation_seconds: float | None = None
        detection_seconds: float | None = None
        answer = request.supplied_answer
        running = queued.model_copy(update={'status': RunStatus.RUNNING})
        try:
            should_generate = (
                request.task != TaskType.ANSWERABILITY
                and request.mode in {RunMode.GENERATE_AND_SCORE, RunMode.QUICK_PROMPT}
            )
            if should_generate:
                if self.generate is None:
                    return self._failure(running, 'generation_unavailable', 'Generation is unavailable.')
                before = time.monotonic()
                generated = self.generate(request, running.setup_snapshot)
                generation_seconds = time.monotonic() - before
                answer = generated.get('answer', '') if isinstance(generated, Mapping) else generated
                if not isinstance(answer, str) or not answer:
                    return self._failure(running, 'empty_answer', 'The generator returned no answer.')

            before = time.monotonic()
            try:
                detected = self.detect(answer, request, running.setup_snapshot)
                detection_seconds = time.monotonic() - before
                effective_setup = running.setup_snapshot
                if isinstance(detected, Mapping):
                    family = str(detected.get('family') or effective_setup.detector_family)
                    level = str(detected.get('level') or effective_setup.detector_level)
                    calibrated = bool(detected.get('calibrated', effective_setup.calibrated))
                    raw_threshold = detected.get('threshold')
                    threshold = (
                        float(raw_threshold)
                        if isinstance(raw_threshold, (int, float))
                        and not isinstance(raw_threshold, bool)
                        and math.isfinite(float(raw_threshold))
                        else effective_setup.threshold
                    )
                    semantics = derive_score_semantics(
                        calibrated=calibrated,
                        family=family,
                        level=level,
                        threshold=threshold,
                    )
                    raw_layer = detected.get('layer')
                    layer = (
                        raw_layer
                        if isinstance(raw_layer, int)
                        and not isinstance(raw_layer, bool)
                        and raw_layer >= 0
                        else effective_setup.layer
                    )
                    effective_setup = effective_setup.model_copy(update={
                        'detector_family': family,
                        'detector_level': level,
                        'calibrated': calibrated,
                        'threshold': threshold,
                        'threshold_source': detected.get('threshold_source') or effective_setup.threshold_source,
                        'score_semantics': semantics,
                        'layer': layer,
                    })
                analysis = present_analysis(answer, effective_setup, detected)
            except ConsentRequiredError as exc:
                # An actionable pre-condition, not a detection failure: surface it directly instead of
                # preserving a misleading partial run.
                return self._failure(running, 'consent_required', str(exc)[:240], started)
            except Exception as exc:
                if not answer:
                    raise
                provider_copy = next(
                    (
                        (error_code, copy)
                        for name, error_code, copy in _PROVIDER_ERROR_COPY
                        if _exception_name_matches(exc, name)
                    ),
                    None,
                )
                if _is_judge_annotation_error(exc):
                    # The judge produced nothing alignable (no verbatim echo / no digit verdict):
                    # preserve the answer and surface the judge's own actionable message. These
                    # messages are authored in sirin code, never raw provider output.
                    code = 'judge_no_aligned_annotation'
                    message = str(exc)[:240] or (
                        'The judge model did not return a verbatim annotated answer. '
                        'Try another judge model, or lower the temperature.'
                    )
                    correlation_id = str(uuid4())
                elif provider_copy:
                    code, message = provider_copy
                    correlation_id = str(uuid4())
                    lg.warning(f'Provider error {code} [reference {correlation_id}]')
                else:
                    code, message = 'detection_failed', 'The answer was preserved, but detection failed.'
                    correlation_id = str(uuid4())
                    lg.exception(f'Detection failed [reference {correlation_id}]')
                return running.model_copy(update={
                    'status': RunStatus.PARTIAL,
                    'answer': answer,
                    'completed_at': utc_now(),
                    'timings': SafeTimings(
                        total_seconds=time.monotonic() - started,
                        generation_seconds=generation_seconds,
                    ),
                    'error': PublicError(
                        code=code, message=message, correlation_id=correlation_id
                    ),
                })
            update: dict[str, Any] = {
                'status': RunStatus.SUCCEEDED,
                'answer': answer,
                'analysis': analysis,
                'setup_snapshot': effective_setup,
                'completed_at': utc_now(),
                'timings': SafeTimings(
                    total_seconds=time.monotonic() - started,
                    generation_seconds=generation_seconds,
                    detection_seconds=detection_seconds,
                ),
            }
            if isinstance(detected, Mapping):
                disclosures = detected.get('judge_disclosures')
                if isinstance(disclosures, list) and disclosures:
                    update['provenance'] = running.provenance.model_copy(update={
                        'disclosures': [
                            *running.provenance.disclosures,
                            *(str(item) for item in disclosures),
                        ][:12],
                    })
                warnings = detected.get('run_warnings')
                if isinstance(warnings, list) and warnings:
                    update['warnings'] = [str(item) for item in warnings][:20]
            return running.model_copy(update=update)
        except ConsentRequiredError as exc:
            # Consent is a known, actionable gate (raised before generation reaches the model), so
            # surface its own message rather than the generic catch-all.
            return self._failure(running, 'consent_required', str(exc)[:240], started)
        except Exception:
            correlation_id = str(uuid4())
            lg.exception(f'Run failed [reference {correlation_id}]')
            return self._failure(
                running, 'operation_failed', 'The operation failed.', started,
                correlation_id=correlation_id,
            )

    @staticmethod
    def _failure(
        run: RunRecord,
        code: str,
        message: str,
        started: float | None = None,
        correlation_id: str | None = None,
    ) -> RunRecord:
        timings = None
        if started is not None:
            timings = SafeTimings(total_seconds=time.monotonic() - started)
        return run.model_copy(update={
            'status': RunStatus.FAILED,
            'completed_at': utc_now(),
            'timings': timings,
            'error': PublicError(
                code=code,
                message=message,
                correlation_id=correlation_id or str(uuid4()),
            ),
        })
