"""Canonical JSON contracts shared by Streamlit and the v2 component."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PROTOCOL_VERSION = 1
MAX_DETECTOR_CHARS = 30_000
_SHA256 = re.compile(r'^[0-9a-f]{64}$')


def _camel(name: str) -> str:
    head, *tail = name.split('_')
    return head + ''.join(part.capitalize() for part in tail)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DTO(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra='forbid',
    )


class TaskType(StrEnum):
    FAITHFULNESS = 'faithfulness'
    ANSWERABILITY = 'answerability'


class RunMode(StrEnum):
    GENERATE_AND_SCORE = 'generateAndScore'
    ANSWERABILITY = 'answerability'
    SCORE_SUPPLIED_ANSWER = 'scoreSuppliedAnswer'
    RECORDED_REPLAY = 'recordedReplay'
    RECORDED_RESULT = 'recordedResult'
    QUICK_PROMPT = 'quickPrompt'


class RunOrigin(StrEnum):
    GENERATED_NOW = 'generatedNow'
    RECORDED_ANSWER = 'recordedAnswerLiveDetection'
    RECORDED_RESULT = 'recordedResultVerified'
    IMPORTED = 'importedSnapshot'
    SUPPLIED_ANSWER = 'suppliedAnswerLiveDetection'
    RERUN_IMPORTED = 'rerunFromImportedRun'
    ANSWERABILITY = 'answerabilityLiveDetection'


class RunStatus(StrEnum):
    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    PARTIAL = 'partial'
    FAILED = 'failed'
    INTERRUPTED = 'interrupted'


TERMINAL_STATUSES = {
    RunStatus.SUCCEEDED,
    RunStatus.PARTIAL,
    RunStatus.FAILED,
    RunStatus.INTERRUPTED,
}


class AnalysisKind(StrEnum):
    SEQUENCE = 'sequence'
    TOKEN = 'token'
    SPAN = 'span'
    CLAIM = 'claim'
    MULTICLASS = 'multiclass'
    JUDGE = 'judge'
    UNCERTAINTY = 'uncertainty'
    UNAVAILABLE = 'unavailable'


class ScoreSemantics(StrEnum):
    CALIBRATED_PROBABILITY = 'calibratedProbability'
    THRESHOLDED_RAW_SCORE = 'thresholdedRawScore'
    RELATIVE_WITHIN_ANSWER = 'relativeWithinAnswer'
    CATEGORICAL_PROBABILITIES = 'categoricalProbabilities'
    SPAN_AGREEMENT = 'spanAgreement'
    VERDICT = 'verdict'
    UNAVAILABLE = 'unavailable'


def derive_score_semantics(
    *,
    calibrated: bool,
    family: str,
    level: str,
    threshold: float | None = None,
    kind: AnalysisKind | None = None,
) -> ScoreSemantics:
    """Single source of truth mapping a detector's family/level/calibration to score meaning.

    The presenter supplies ``kind`` (it has classified the concrete output); the setup-time callers
    (run engine, Streamlit setup) omit it and fall back to family+level.
    """
    # A token/span judge scores each character by k/n annotation agreement, not a calibrated
    # probability — this must win over the calibrated flag (the token judge display uses
    # calibrated=True only to show absolute scores, it is not a calibration claim).
    if family in {'judge', 'judging'} and level == 'token':
        return ScoreSemantics.SPAN_AGREEMENT
    if calibrated:
        return ScoreSemantics.CALIBRATED_PROBABILITY
    if family in {'judge', 'judging'}:
        return ScoreSemantics.VERDICT
    if kind == AnalysisKind.MULTICLASS:
        return ScoreSemantics.CATEGORICAL_PROBABILITIES
    if kind in {AnalysisKind.TOKEN, AnalysisKind.UNCERTAINTY}:
        return ScoreSemantics.RELATIVE_WITHIN_ANSWER
    if kind is None and family == 'uncertainty' and level == 'token':
        return ScoreSemantics.RELATIVE_WITHIN_ANSWER
    if threshold is not None:
        return ScoreSemantics.THRESHOLDED_RAW_SCORE
    return ScoreSemantics.UNAVAILABLE


class ReceiptStatus(StrEnum):
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    DUPLICATE = 'duplicate'


class PublicError(DTO):
    code: str = Field(min_length=1, max_length=64, pattern=r'^[a-z0-9_]+$')
    message: str = Field(min_length=1, max_length=240)
    correlation_id: str

    @field_validator('correlation_id')
    @classmethod
    def valid_uuid(cls, value: str) -> str:
        UUID(value)
        return value


class TextSegment(DTO):
    text: str
    start_code_point: int = Field(ge=0)
    end_code_point: int = Field(ge=0)
    score: float | None = None
    verdict: bool | None = None

    @model_validator(mode='after')
    def valid_segment(self) -> 'TextSegment':
        if self.end_code_point < self.start_code_point:
            raise ValueError('segment end precedes start')
        if len(self.text) != self.end_code_point - self.start_code_point:
            raise ValueError('segment offsets must count Unicode code points')
        if self.score is not None and not math.isfinite(self.score):
            raise ValueError('segment score must be finite')
        return self


class CategoryScore(DTO):
    label: str = Field(min_length=1, max_length=120)
    score: float

    @field_validator('score')
    @classmethod
    def finite_score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError('score must be finite')
        return value


class ClaimScore(DTO):
    text: str
    verdict: bool | None = None
    score: float | None = None

    @field_validator('score')
    @classmethod
    def finite_score(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError('score must be finite')
        return value


class AnalysisResult(DTO):
    kind: AnalysisKind
    score_semantics: ScoreSemantics
    label: str = Field(min_length=1, max_length=160)
    verdict: bool | None = None
    score: float | None = None
    threshold: float | None = None
    calibrated: bool = False
    segments: list[TextSegment] = Field(default_factory=list, max_length=10_000)
    categories: list[CategoryScore] = Field(default_factory=list, max_length=100)
    claims: list[ClaimScore] = Field(default_factory=list, max_length=2_000)
    note: str | None = Field(default=None, max_length=500)

    @field_validator('score', 'threshold')
    @classmethod
    def finite_number(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError('analysis values must be finite')
        return value


class CapabilitySet(DTO):
    can_generate: bool = True
    can_import: bool = True
    can_export: bool = True
    trusted_local: bool = False
    detailed_diagnostics: bool = False
    can_refresh_diagnostics: bool = False
    can_capture_attention: bool = False
    can_unload_models: bool = False
    can_open_cached_attention: bool = False
    can_open_live_attention: bool = False


class SetupSnapshot(DTO):
    detector_preset: str = Field(min_length=1, max_length=256)
    detector_family: str = Field(min_length=1, max_length=80)
    detector_level: str = Field(min_length=1, max_length=40)
    task: TaskType = TaskType.FAITHFULNESS
    model_id: str | None = Field(default=None, max_length=256)
    provider_label: str | None = Field(default=None, max_length=120)
    calibrated: bool = False
    threshold: float | None = None
    threshold_source: str | None = Field(default=None, max_length=160)
    score_semantics: ScoreSemantics = ScoreSemantics.UNAVAILABLE
    layer: int | None = Field(default=None, ge=0)

    @field_validator('threshold')
    @classmethod
    def finite_threshold(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError('threshold must be finite')
        return value


class Provenance(DTO):
    dataset: str | None = Field(default=None, max_length=160)
    split: str | None = Field(default=None, max_length=80)
    source_model: str | None = Field(default=None, max_length=256)
    representation_model: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=160)
    integrity_sha256: str | None = None
    disclosures: list[str] = Field(default_factory=list, max_length=12)
    source_run_id: str | None = None
    original_created_at: datetime | None = None

    @field_validator('integrity_sha256')
    @classmethod
    def valid_sha(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256.fullmatch(value):
            raise ValueError('invalid SHA-256')
        return value

    @field_validator('source_run_id')
    @classmethod
    def valid_source_id(cls, value: str | None) -> str | None:
        if value is not None:
            UUID(value)
        return value


class RunInputs(DTO):
    context: str = ''
    question: str = ''
    supplied_answer: str = ''
    prompt: str = ''
    example_id: str | None = Field(default=None, max_length=256)

    @model_validator(mode='after')
    def bounded_input(self) -> 'RunInputs':
        if sum(len(value) for value in (
            self.context, self.question, self.supplied_answer, self.prompt
        )) > MAX_DETECTOR_CHARS:
            raise ValueError(
                f'Context, question, and answer together exceed the '
                f'{MAX_DETECTOR_CHARS:,}-character limit. Trim the context and try again.'
            )
        return self


class RunRequest(RunInputs):
    task: TaskType = TaskType.FAITHFULNESS
    mode: RunMode = RunMode.GENERATE_AND_SCORE
    source_run_id: str | None = None

    @model_validator(mode='after')
    def compatible_mode(self) -> 'RunRequest':
        if self.task == TaskType.ANSWERABILITY and self.mode != RunMode.ANSWERABILITY:
            raise ValueError('answerability accepts context and question only')
        if self.mode == RunMode.ANSWERABILITY and self.task != TaskType.ANSWERABILITY:
            raise ValueError('answerability mode requires the answerability task')
        if self.mode in {RunMode.SCORE_SUPPLIED_ANSWER, RunMode.RECORDED_REPLAY}:
            if not self.supplied_answer:
                raise ValueError('this mode requires an answer')
        if self.mode == RunMode.QUICK_PROMPT and not self.prompt:
            raise ValueError('quick prompt mode requires a prompt')
        if self.mode != RunMode.QUICK_PROMPT and not self.question:
            raise ValueError('question is required')
        if self.source_run_id is not None:
            UUID(self.source_run_id)
        return self


class SafeTimings(DTO):
    total_seconds: float = Field(ge=0)
    generation_seconds: float | None = Field(default=None, ge=0)
    detection_seconds: float | None = Field(default=None, ge=0)

    @field_validator('total_seconds', 'generation_seconds', 'detection_seconds')
    @classmethod
    def finite_timing(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError('timing must be finite')
        return value


class RunRecord(DTO):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra='forbid',
        frozen=True,
    )

    id: str
    created_at: datetime
    completed_at: datetime | None = None
    status: RunStatus
    origin: RunOrigin
    setup_revision: int = Field(ge=0)
    setup_snapshot: SetupSnapshot
    inputs: RunInputs
    answer: str = ''
    analysis: AnalysisResult | None = None
    timings: SafeTimings | None = None
    provenance: Provenance = Field(default_factory=Provenance)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    error: PublicError | None = None
    request_digest: str

    @field_validator('id')
    @classmethod
    def valid_id(cls, value: str) -> str:
        UUID(value)
        return value

    @field_validator('request_digest')
    @classmethod
    def valid_digest(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError('invalid request digest')
        return value

    @model_validator(mode='after')
    def terminal_shape(self) -> 'RunRecord':
        if self.status == RunStatus.SUCCEEDED and self.analysis is None:
            raise ValueError('successful run requires analysis')
        if self.status == RunStatus.PARTIAL and not self.answer:
            raise ValueError('partial run requires a preserved answer')
        if self.status in TERMINAL_STATUSES and self.completed_at is None:
            raise ValueError('terminal run requires completion time')
        return self


class RunSummary(DTO):
    id: str
    created_at: datetime
    status: RunStatus
    origin: RunOrigin
    task: TaskType
    title: str
    verdict: bool | None = None
    score: float | None = None
    stale_setup: bool = False

    @classmethod
    def from_record(cls, run: RunRecord, current_setup_revision: int) -> 'RunSummary':
        title = run.inputs.question or run.inputs.prompt or 'Untitled run'
        return cls(
            id=run.id,
            created_at=run.created_at,
            status=run.status,
            origin=run.origin,
            task=run.setup_snapshot.task,
            title=title[:160],
            verdict=run.analysis.verdict if run.analysis else None,
            score=run.analysis.score if run.analysis else None,
            stale_setup=run.setup_revision != current_setup_revision,
        )


class ExampleSummary(DTO):
    id: str = Field(min_length=1, max_length=256)
    label: str = Field(min_length=1, max_length=160)
    dataset: str = Field(min_length=1, max_length=160)
    task: TaskType = TaskType.FAITHFULNESS
    context: str = ''
    question: str = ''
    prompt: str = ''
    recorded_answer: str
    why_notable: str | None = Field(default=None, max_length=500)
    provenance: Provenance


class Activity(DTO):
    run_id: str
    status: RunStatus
    label: str = Field(max_length=160)


class DiagnosticsSummary(DTO):
    runtime: str = Field(default='Python', max_length=120)
    device: str = Field(default='Loads on first run', max_length=120)
    model_loaded: bool = False
    active_model: str | None = Field(default=None, max_length=256)
    attention_available: bool = False
    message: str | None = Field(default=None, max_length=240)


class Notice(DTO):
    level: Literal['info', 'warning', 'error'] = 'info'
    message: str = Field(min_length=1, max_length=240)


class ActionReceipt(DTO):
    action_id: str
    sequence: int = Field(ge=1)
    status: ReceiptStatus
    payload_digest: str
    code: str | None = Field(default=None, max_length=64)
    message: str | None = Field(default=None, max_length=240)


class DownloadTransfer(DTO):
    file_name: str = Field(pattern=r'^[A-Za-z0-9_.-]+$', max_length=160)
    mime_type: Literal['application/json'] = 'application/json'
    content: str


def default_view_state() -> dict[str, Any]:
    return {
        'workspace': 'analyze',
        'appearance': {'theme': 'light', 'motion': 'subtle'},
    }


class WorkspacePayload(DTO):
    protocol_version: Literal[1] = PROTOCOL_VERSION
    server_instance_id: str
    setup_revision: int = Field(ge=0)
    runs_revision: int = Field(ge=0)
    capabilities: CapabilitySet
    setup: SetupSnapshot
    activity: Activity | None = None
    examples: list[ExampleSummary]
    runs: list[RunSummary]
    selected_run: RunRecord | None = None
    diagnostics: DiagnosticsSummary
    view_state: dict[str, Any] = Field(default_factory=default_view_state)
    notices: list[Notice] = Field(default_factory=list)
    action_receipt: ActionReceipt | None = None
    download: DownloadTransfer | None = None
    draft: dict[str, Any] | None = None


class ActionEnvelope(DTO):
    protocol_version: Literal[1] = PROTOCOL_VERSION
    client_instance_id: str
    sequence: int = Field(ge=1)
    action_id: str
    type: Literal[
        'submit', 'retryDetection', 'selectRun', 'deleteRun', 'clearRuns',
        'import', 'exportRun', 'exportBundle', 'prepareRerun', 'clearDownload',
        'refreshDiagnostics', 'unloadModels', 'openCachedAttention',
        'openLiveAttention'
    ]
    expected_setup_revision: int = Field(ge=0)
    expected_runs_revision: int = Field(ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator('client_instance_id', 'action_id')
    @classmethod
    def valid_uuid(cls, value: str) -> str:
        UUID(value)
        return value


class WorkspaceEvent(DTO):
    action: ActionEnvelope | None = None
