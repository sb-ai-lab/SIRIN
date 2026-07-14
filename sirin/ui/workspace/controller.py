"""Action reducer joining the component, session state, fixtures, and runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger as lg
from pydantic import ValidationError

from .contracts import (
    ActionEnvelope,
    ActionReceipt,
    Activity,
    CapabilitySet,
    DiagnosticsSummary,
    DownloadTransfer,
    Notice,
    ReceiptStatus,
    RunMode,
    RunOrigin,
    RunRequest,
    RunStatus,
    RunSummary,
    SetupSnapshot,
    TaskType,
    WorkspacePayload,
    default_view_state,
)
from .examples import ExampleRegistry, cached_example_registry
from .run_engine import RunEngine
from .seed import build_seed_runs, seed_draft
from .session import PortableFormatError, WorkspaceSession, export_bundle, export_run, import_portable_json


def _reject_message(exc: Exception) -> str:
    """Human, sanitized reject text for the action receipt.

    A raw ``str(ValidationError)`` is a multi-line pydantic dump that also echoes the offending input
    value, so we lift just the first validator message (dropping pydantic's ``Value error, `` prefix).
    Plain ``ValueError``/``PortableFormatError`` messages are already written for humans.
    """
    if isinstance(exc, ValidationError):
        errors = exc.errors()
        if errors:
            message = str(errors[0].get('msg') or '').removeprefix('Value error, ')
            return message[:240] or 'The request could not be accepted.'
        return 'The request could not be accepted.'
    return str(exc)[:240] or 'The action was rejected.'


class WorkspaceController:
    def __init__(
        self,
        session: WorkspaceSession,
        engine: RunEngine,
        examples: ExampleRegistry | None = None,
        diagnostic_actions: dict[str, Callable[[], None]] | None = None,
    ) -> None:
        self.session = session
        self.engine = engine
        self.examples = examples or cached_example_registry()
        self.diagnostic_actions = diagnostic_actions or {}

    def build_payload(
        self,
        *,
        setup: SetupSnapshot,
        capabilities: CapabilitySet | None = None,
        diagnostics: DiagnosticsSummary | None = None,
        view_state: dict[str, Any] | None = None,
        notices: list[Notice] | None = None,
    ) -> WorkspacePayload:
        state = self.session.state
        active = next(
            (run for run in reversed(state.runs) if run.status in {RunStatus.QUEUED, RunStatus.RUNNING}),
            None,
        )
        selected = self.session.selected()
        # A pristine landing (only recorded-result seed(s) exist, unselected by anyone) prefills the
        # census example so its editor and the primary Replay CTA are ready. The component consults this
        # only on first mount, so once the person interacts their own draft memory takes over. One or two
        # seeds (probe, and optionally the judge) both count as pristine.
        only_seeds = bool(state.runs) and all(
            run.origin == RunOrigin.RECORDED_RESULT for run in state.runs
        )
        draft = (
            seed_draft()
            if selected is not None
            and selected.origin == RunOrigin.RECORDED_RESULT
            and only_seeds
            else None
        )
        return WorkspacePayload(
            server_instance_id=state.server_instance_id,
            setup_revision=state.setup_revision,
            runs_revision=state.runs_revision,
            capabilities=capabilities or CapabilitySet(),
            setup=setup,
            activity=Activity(run_id=active.id, status=active.status, label='Analyzing') if active else None,
            examples=self.examples.summaries(),
            runs=[RunSummary.from_record(run, state.setup_revision) for run in reversed(state.runs)],
            selected_run=selected,
            diagnostics=diagnostics or DiagnosticsSummary(),
            view_state=view_state or default_view_state(),
            notices=notices or [],
            action_receipt=state.receipts[-1] if state.receipts else None,
            download=state.download,
            draft=draft,
        )

    def seed_landing(self, setup: SetupSnapshot) -> bool:
        """Seed the first-run recorded-result card exactly once per fresh session.

        Only a brand-new faithfulness session qualifies: never after the person has cleared,
        deleted, imported, or run anything (any of which advances ``runs_revision``), and never
        more than once. A broken asset is swallowed so the workspace still renders.
        """
        state = self.session.state
        if (
            state.seeded
            or state.runs
            or state.runs_revision != 0
            or setup.task != TaskType.FAITHFULNESS
        ):
            return False
        state.seeded = True
        try:
            for run in build_seed_runs(state.setup_revision):
                self.session.add_run(run)
        except Exception:
            lg.exception('First-run recorded-result seed could not be built')
            return False
        return True

    def handle(
        self,
        action: ActionEnvelope | dict[str, Any],
        *,
        setup: SetupSnapshot,
        submission_error: str | None = None,
    ) -> ActionReceipt:
        try:
            action = ActionEnvelope.model_validate(action)
        except ValidationError:
            raise ValueError('Invalid workspace action envelope.') from None
        receipt = self.session.begin_action(action)
        if receipt.status != ReceiptStatus.ACCEPTED:
            return receipt
        try:
            if action.type == 'submit':
                if submission_error:
                    raise ValueError(submission_error)
                self._submit(action, setup)
            elif action.type == 'retryDetection':
                self._retry(action, setup)
            elif action.type == 'selectRun':
                run_id = self._run_id(action.payload)
                if self.session.get(run_id) is None:
                    raise ValueError('Run was not found.')
                self.session.state.selected_run_id = run_id
            elif action.type == 'deleteRun':
                if not self.session.delete(self._run_id(action.payload)):
                    raise ValueError('Run was not found.')
            elif action.type == 'clearRuns':
                self._expect_keys(action.payload, set())
                self.session.clear()
            elif action.type == 'import':
                self._expect_keys(action.payload, {'json'})
                document = action.payload.get('json')
                if not isinstance(document, str):
                    raise ValueError('Import requires JSON text.')
                self.session.import_runs(import_portable_json(document))
            elif action.type == 'exportRun':
                run = self.session.get(self._run_id(action.payload))
                if run is None:
                    raise ValueError('Run was not found.')
                self.session.state.download = DownloadTransfer(
                    file_name=f'sirin-run-{run.id}.json', content=export_run(run)
                )
            elif action.type == 'exportBundle':
                self._expect_keys(action.payload, set())
                terminal = [run for run in self.session.state.runs if run.status not in {RunStatus.QUEUED, RunStatus.RUNNING}]
                self.session.state.download = DownloadTransfer(
                    file_name='sirin-session.json', content=export_bundle(terminal)
                )
            elif action.type == 'prepareRerun':
                run_id = self._run_id(action.payload)
                if self.session.get(run_id) is None:
                    raise ValueError('Run was not found.')
                self.session.state.selected_run_id = run_id
            elif action.type == 'clearDownload':
                self._expect_keys(action.payload, set())
                self.session.state.download = None
            elif action.type in {
                'refreshDiagnostics',
                'unloadModels',
                'openCachedAttention',
                'openLiveAttention',
            }:
                self._expect_keys(action.payload, set())
                callback = self.diagnostic_actions.get(action.type)
                if callback is None:
                    raise ValueError('This diagnostics action is unavailable.')
                callback()
        except (PortableFormatError, ValidationError, ValueError) as exc:
            receipt = receipt.model_copy(update={
                'status': ReceiptStatus.REJECTED,
                'code': 'invalid_action',
                'message': _reject_message(exc),
            })
            self.session.replace_receipt(receipt)
        return receipt

    def _submit(self, action: ActionEnvelope, setup: SetupSnapshot) -> None:
        provenance = None
        if action.payload.get('mode') == RunMode.RECORDED_REPLAY:
            example_id = action.payload.get('exampleId')
            if not isinstance(example_id, str) or not example_id:
                raise ValueError('Recorded replay requires a bundled example.')
            request, provenance = self.examples.resolve(example_id)
        else:
            request = RunRequest.model_validate(action.payload)
        if request.source_run_id:
            source = self.session.get(request.source_run_id)
            if source is None or source.origin != RunOrigin.IMPORTED:
                raise ValueError('Rerun linkage requires an imported run.')
        if request.task != setup.task:
            raise ValueError('The selected detector is not compatible with this task.')
        if (
            setup.detector_family == 'uncertainty'
            and request.mode in {RunMode.SCORE_SUPPLIED_ANSWER, RunMode.RECORDED_REPLAY}
        ):
            raise ValueError('This uncertainty detector cannot score a supplied answer.')
        queued = self.engine.reserve(request, setup, self.session.state.setup_revision, provenance)
        self.session.state.pending_requests[queued.id] = request
        self.session.add_run(queued)

    def _retry(self, action: ActionEnvelope, setup: SetupSnapshot) -> None:
        source = self.session.get(self._run_id(action.payload))
        if source is None or not source.answer:
            raise ValueError('No preserved answer is available for retry.')
        request = RunRequest(
            task=source.setup_snapshot.task,
            mode=RunMode.SCORE_SUPPLIED_ANSWER,
            context=source.inputs.context,
            question=source.inputs.question or source.inputs.prompt,
            prompt=source.inputs.prompt,
            supplied_answer=source.answer,
        )
        if request.task != setup.task or setup.detector_family == 'uncertainty':
            raise ValueError('The selected detector is not compatible with this retry.')
        provenance = source.provenance.model_copy(update={'source_run_id': source.id})
        queued = self.engine.reserve(request, setup, self.session.state.setup_revision, provenance)
        self.session.state.pending_requests[queued.id] = request
        self.session.add_run(queued)

    def advance(self) -> bool:
        """Advance one queued/running stage after its current state has been mounted."""
        self.session.recover_interrupted()
        active = next(
            (
                run for run in reversed(self.session.state.runs)
                if run.status in {RunStatus.QUEUED, RunStatus.RUNNING}
            ),
            None,
        )
        if active is None:
            return False
        request = self.session.state.pending_requests.get(active.id)
        if request is None:
            return False
        if active.status == RunStatus.QUEUED:
            self.session.replace_run(active.model_copy(update={'status': RunStatus.RUNNING}))
            return True
        self.session.state.pending_requests.pop(active.id, None)
        self.session.replace_run(self.engine.execute(active, request))
        return True

    @staticmethod
    def _expect_keys(payload: dict[str, Any], expected: set[str]) -> None:
        if set(payload) != expected:
            raise ValueError('Action payload has unknown or missing fields.')

    @classmethod
    def _run_id(cls, payload: dict[str, Any]) -> str:
        cls._expect_keys(payload, {'runId'})
        run_id = payload.get('runId')
        if not isinstance(run_id, str):
            raise ValueError('Run ID is required.')
        return run_id
