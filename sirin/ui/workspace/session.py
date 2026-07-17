"""Session reducer and strict portable run JSON format."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import timezone
from typing import Any, MutableMapping
from uuid import uuid4

from .contracts import (
    ActionEnvelope,
    ActionReceipt,
    DownloadTransfer,
    Provenance,
    ReceiptStatus,
    RunOrigin,
    RunRecord,
    RunRequest,
    RunStatus,
    TERMINAL_STATUSES,
    utc_now,
)


RUN_LIMIT = 50
RUN_BYTES = 5 * 1024 * 1024
BUNDLE_BYTES = 10 * 1024 * 1024
MAX_DEPTH = 40


class PortableFormatError(ValueError):
    pass


@dataclass
class _State:
    server_instance_id: str = field(default_factory=lambda: str(uuid4()))
    setup_revision: int = 0
    runs_revision: int = 0
    runs: list[RunRecord] = field(default_factory=list)
    selected_run_id: str | None = None
    high_water: dict[str, int] = field(default_factory=dict)
    receipts: list[ActionReceipt] = field(default_factory=list)
    download: DownloadTransfer | None = None
    pending_requests: dict[str, RunRequest] = field(default_factory=dict)
    seeded: bool = False
    setup_signatures: dict[int, str] = field(default_factory=dict)
    # Compare mode: the id/preset pair the compare view hydrates from, and (generate case only) the
    # map of a B run awaiting side A's answer -> the A run that produces it.
    compare: dict[str, str] | None = None
    compare_answer_source: dict[str, str] = field(default_factory=dict)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False
        ).encode('utf-8')
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PortableFormatError('Document contains unsupported values.') from exc


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _run_data(run: RunRecord) -> dict[str, Any]:
    return run.model_dump(mode='json', by_alias=True, exclude_none=True)


def export_run(run: RunRecord) -> str:
    body = {'format': 'sirin.run', 'version': 1, 'run': _run_data(run)}
    document = {**body, 'integrity': {'algorithm': 'sha256', 'sha256': _sha(body)}}
    encoded = _canonical(document)
    if len(encoded) > RUN_BYTES:
        raise PortableFormatError('Run exceeds the 5 MiB export limit.')
    return encoded.decode('utf-8')


def export_bundle(runs: list[RunRecord]) -> str:
    if len(runs) > RUN_LIMIT:
        raise PortableFormatError('Bundle exceeds the 50 run limit.')
    body = {'format': 'sirin.bundle', 'version': 1, 'runs': [_run_data(run) for run in runs]}
    document = {**body, 'integrity': {'algorithm': 'sha256', 'sha256': _sha(body)}}
    encoded = _canonical(document)
    if len(encoded) > BUNDLE_BYTES:
        raise PortableFormatError('Bundle exceeds the 10 MiB export limit.')
    return encoded.decode('utf-8')


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PortableFormatError('Duplicate JSON object key.')
        result[key] = value
    return result


def _validate_tree(value: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise PortableFormatError('Document is nested too deeply.')
    if isinstance(value, str):
        try:
            value.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise PortableFormatError('Document contains invalid Unicode.') from exc
    elif isinstance(value, dict):
        for key, child in value.items():
            _validate_tree(key, depth + 1)
            _validate_tree(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _validate_tree(child, depth + 1)


def import_portable_json(value: str | bytes) -> list[RunRecord]:
    raw = value.encode('utf-8') if isinstance(value, str) else value
    if len(raw) > BUNDLE_BYTES:
        raise PortableFormatError('Document exceeds the 10 MiB import limit.')
    try:
        text = raw.decode('utf-8')
        document = json.loads(
            text,
            object_pairs_hook=_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(
                PortableFormatError('Non-finite numbers are not supported.')
            ),
        )
    except PortableFormatError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PortableFormatError('Document is not valid UTF-8 JSON.') from exc
    _validate_tree(document)
    if not isinstance(document, dict):
        raise PortableFormatError('Document root must be an object.')

    kind = document.get('format')
    expected = {'format', 'version', 'integrity', 'run' if kind == 'sirin.run' else 'runs'}
    if set(document) != expected or document.get('version') != 1:
        raise PortableFormatError('Unknown portable document format or fields.')
    integrity = document['integrity']
    if (
        not isinstance(integrity, dict)
        or set(integrity) != {'algorithm', 'sha256'}
        or integrity.get('algorithm') != 'sha256'
    ):
        raise PortableFormatError('Invalid integrity metadata.')
    body = {key: child for key, child in document.items() if key != 'integrity'}
    if integrity.get('sha256') != _sha(body):
        raise PortableFormatError('SHA-256 integrity verification failed.')

    if kind == 'sirin.run':
        if len(raw) > RUN_BYTES:
            raise PortableFormatError('Run exceeds the 5 MiB import limit.')
        rows = [document['run']]
    elif kind == 'sirin.bundle':
        rows = document['runs']
        if not isinstance(rows, list) or len(rows) > RUN_LIMIT:
            raise PortableFormatError('Bundle exceeds the 50 run limit.')
    else:
        raise PortableFormatError('Unsupported portable document type.')
    try:
        return [RunRecord.model_validate(row) for row in rows]
    except Exception as exc:
        raise PortableFormatError('Run data does not match schema version 1.') from exc


class WorkspaceSession:
    def __init__(self, store: MutableMapping[str, Any], key: str = '_sirin_workspace') -> None:
        self._store = store
        self._key = key
        if not isinstance(store.get(key), _State):
            store[key] = _State()

    @property
    def state(self) -> _State:
        return self._store[self._key]

    def note_setup(self, signature: str) -> None:
        """Record the execution-compatibility signature for the current setup revision.

        The signature captures only what affects whether an in-flight action can still run
        (detector preset, model, task) — not appearance or generation knobs. It lets a stale
        setup revision be told apart from an incompatible one when an action arrives late.
        """
        self.state.setup_signatures[self.state.setup_revision] = signature

    def _setup_change_is_safe(self, expected_revision: int) -> bool:
        signatures = self.state.setup_signatures
        current = signatures.get(self.state.setup_revision)
        expected = signatures.get(expected_revision)
        return current is not None and expected is not None and current == expected

    def begin_action(self, action: ActionEnvelope) -> ActionReceipt:
        digest = _sha(action.model_dump(mode='json', by_alias=True))
        for previous in self.state.receipts:
            if previous.action_id == action.action_id:
                return previous.model_copy(update={'status': ReceiptStatus.DUPLICATE})
        if action.sequence <= self.state.high_water.get(action.client_instance_id, 0):
            return ActionReceipt(
                action_id=action.action_id, sequence=action.sequence,
                status=ReceiptStatus.DUPLICATE, payload_digest=digest,
                code='duplicate_sequence', message='This action was already handled.',
            )
        if (
            action.expected_setup_revision != self.state.setup_revision
            and not self._setup_change_is_safe(action.expected_setup_revision)
        ):
            # The setup changed AND the delta affects execution (different preset/model/task):
            # the queued inputs may no longer be valid, so make the person resubmit. A benign
            # delta (same preset/model) falls through and runs with the current setup snapshot.
            return self._record(action, digest, 'stale_setup', 'Setup changed; review and submit again.')
        # expected_runs_revision is deliberately NOT enforced. Every action either appends
        # runs (submit/import) or targets one by id (validated with "Run was not found"), so
        # a lagging runs revision never invalidates it semantically — while on slow hosts
        # (HF Space CPU) the browser's payload trails the server by a revision for seconds
        # and the gate produced spurious "Run history changed" rejections on honest clicks.
        self.state.high_water[action.client_instance_id] = action.sequence
        receipt = ActionReceipt(
            action_id=action.action_id, sequence=action.sequence,
            status=ReceiptStatus.ACCEPTED, payload_digest=digest,
        )
        self.state.receipts = [*self.state.receipts[-19:], receipt]
        return receipt

    def _record(self, action: ActionEnvelope, digest: str, code: str, message: str) -> ActionReceipt:
        receipt = ActionReceipt(
            action_id=action.action_id, sequence=action.sequence,
            status=ReceiptStatus.REJECTED, payload_digest=digest, code=code, message=message,
        )
        self.state.receipts = [*self.state.receipts[-19:], receipt]
        return receipt

    def replace_receipt(self, receipt: ActionReceipt) -> None:
        self.state.receipts = [
            receipt if item.action_id == receipt.action_id else item
            for item in self.state.receipts
        ]

    def add_run(self, run: RunRecord) -> None:
        self.state.runs.append(run)
        if run.status in TERMINAL_STATUSES:
            terminals = [item for item in self.state.runs if item.status in TERMINAL_STATUSES]
            keep = {item.id for item in terminals[-RUN_LIMIT:]}
            self.state.runs = [
                item for item in self.state.runs
                if item.status not in TERMINAL_STATUSES or item.id in keep
            ]
        self.state.selected_run_id = run.id
        self.state.runs_revision += 1

    def replace_run(self, run: RunRecord) -> None:
        self.state.runs = [run if item.id == run.id else item for item in self.state.runs]
        if run.status in TERMINAL_STATUSES:
            self.state.pending_requests.pop(run.id, None)
            terminals = [item for item in self.state.runs if item.status in TERMINAL_STATUSES]
            keep = {item.id for item in terminals[-RUN_LIMIT:]}
            self.state.runs = [
                item for item in self.state.runs
                if item.status not in TERMINAL_STATUSES or item.id in keep
            ]
        self.state.runs_revision += 1

    def selected(self) -> RunRecord | None:
        return next((run for run in self.state.runs if run.id == self.state.selected_run_id), None)

    def get(self, run_id: str) -> RunRecord | None:
        return next((run for run in self.state.runs if run.id == run_id), None)

    def import_runs(self, runs: list[RunRecord]) -> None:
        for source in runs:
            provenance = source.provenance.model_copy(update={
                'source_run_id': source.id,
                'original_created_at': source.created_at.astimezone(timezone.utc),
            })
            imported = source.model_copy(update={
                'id': str(uuid4()),
                'created_at': utc_now(),
                'origin': RunOrigin.IMPORTED,
                'provenance': provenance,
            })
            self.add_run(imported)

    def delete(self, run_id: str) -> bool:
        before = len(self.state.runs)
        self.state.runs = [run for run in self.state.runs if run.id != run_id]
        if len(self.state.runs) == before:
            return False
        if self.state.selected_run_id == run_id:
            self.state.selected_run_id = self.state.runs[-1].id if self.state.runs else None
        self.state.pending_requests.pop(run_id, None)
        self.state.runs_revision += 1
        return True

    def clear(self) -> None:
        self.state.runs.clear()
        self.state.selected_run_id = None
        self.state.pending_requests.clear()
        self.state.compare = None
        self.state.compare_answer_source.clear()
        self.state.runs_revision += 1

    def recover_interrupted(self) -> None:
        for run in list(self.state.runs):
            if run.status == RunStatus.RUNNING and run.id not in self.state.pending_requests:
                self.replace_run(run.model_copy(update={
                    'status': RunStatus.INTERRUPTED,
                    'completed_at': utc_now(),
                    'warnings': [*run.warnings, 'Execution was interrupted and was not repeated.'],
                }))
