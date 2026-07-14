"""Action reducer joining the component, session state, fixtures, and runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger as lg
from pydantic import ValidationError

from uuid import uuid4

from .compare import build_compare_payload
from .contracts import (
    ActionEnvelope,
    ActionReceipt,
    Activity,
    CapabilitySet,
    DiagnosticsSummary,
    DownloadTransfer,
    Notice,
    Provenance,
    PublicError,
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
    utc_now,
)
from .examples import ExampleRegistry, cached_example_registry
from .recipes import detector_recipes
from .run_engine import RunEngine
from .seed import build_recorded_replay, build_seed_runs, seed_draft
from .session import PortableFormatError, WorkspaceSession, export_bundle, export_run, import_portable_json


CompareSetup = Callable[[str, SetupSnapshot], SetupSnapshot]


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
        compare_setup: CompareSetup | None = None,
    ) -> None:
        self.session = session
        self.engine = engine
        self.examples = examples or cached_example_registry()
        self.diagnostic_actions = diagnostic_actions or {}
        # Resolves a side-B preset name (+ side-A setup for task-compat) into its own SetupSnapshot.
        # Streamlit owns preset->setup mapping (it builds side A the same way), so the controller
        # stays detector-agnostic; None (e.g. in bare tests) disables compare.
        self.compare_setup = compare_setup

    def build_payload(
        self,
        *,
        setup: SetupSnapshot,
        capabilities: CapabilitySet | None = None,
        diagnostics: DiagnosticsSummary | None = None,
        view_state: dict[str, Any] | None = None,
        notices: list[Notice] | None = None,
        available_presets: list[str] | None = None,
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
            compare=self._compare_payload(),
            available_presets=available_presets or [],
            recipes=detector_recipes(),
        )

    def _compare_payload(self):
        compare = self.session.state.compare
        if not compare:
            return None
        run_a = self.session.get(compare.get('run_a_id', ''))
        run_b = self.session.get(compare.get('run_b_id', ''))
        if run_a is None and run_b is None:
            return None
        return build_compare_payload(
            run_a, run_b, compare.get('preset_a'), compare.get('preset_b')
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
            elif action.type == 'runCompare':
                if submission_error:
                    raise ValueError(submission_error)
                self._run_compare(action, setup)
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
        from sirin.ui.presets import hosted_replay_only

        provenance = None
        replay_only = hosted_replay_only(setup.detector_family)
        if action.payload.get('mode') == RunMode.RECORDED_REPLAY:
            example_id = action.payload.get('exampleId')
            if not isinstance(example_id, str) or not example_id:
                raise ValueError('Recorded replay requires a bundled example.')
            if replay_only:
                # The hosted Space ships no probe checkpoints and no GPU: replays under a
                # non-judge preset serve the verified recorded seed result, rebuilt from
                # the bundled asset (never live scoring, never mutable history).
                record = build_recorded_replay(
                    example_id, self.session.state.setup_revision
                )
                if (
                    record is None
                    or record.setup_snapshot.detector_preset != setup.detector_preset
                ):
                    raise ValueError(
                        'On the hosted demo this preset serves its recorded result only, '
                        'and this example has no recorded result for it. Pick a '
                        'Judge — API preset for live scoring.'
                    )
                self.session.add_run(record)
                return
            request, provenance = self.examples.resolve(example_id)
        else:
            if replay_only:
                raise ValueError(
                    'On the hosted demo this preset replays its recorded result only — '
                    'pick a Judge — API preset for live scoring.'
                )
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

    def _run_compare(self, action: ActionEnvelope, setup: SetupSnapshot) -> None:
        self._expect_keys(action.payload, {'inputs', 'presetB'})
        preset_b = action.payload.get('presetB')
        if not isinstance(preset_b, str) or not preset_b:
            raise ValueError('Compare requires a second detector preset.')
        raw_inputs = action.payload.get('inputs')
        if not isinstance(raw_inputs, dict):
            raise ValueError('Compare requires run inputs.')
        if self.compare_setup is None:
            raise ValueError('Detector comparison is unavailable in this environment.')
        # May raise ValueError (unknown preset / same as A / task-incompatible) — caught by handle.
        setup_b = self.compare_setup(preset_b, setup)
        supplied = bool(raw_inputs.get('suppliedAnswer'))
        mode_a = RunMode.SCORE_SUPPLIED_ANSWER if supplied else RunMode.GENERATE_AND_SCORE
        request_a = RunRequest.model_validate({**raw_inputs, 'mode': mode_a.value})
        if request_a.task != setup.task:
            raise ValueError('The active detector is not compatible with this task.')
        prov_a = Provenance(
            disclosures=[f'Compared with the {setup_b.detector_preset} detector.']
        )
        queued_a = self.engine.reserve(
            request_a, setup, self.session.state.setup_revision, prov_a
        )
        # Side B always scores the SAME answer as A — never a second generation. When A supplied the
        # answer, B scores it directly; when A generates, B's answer is injected in advance() once A
        # completes (see compare_answer_source below), so B's request starts answer-less here.
        if supplied:
            request_b = RunRequest.model_validate(
                {**raw_inputs, 'mode': RunMode.SCORE_SUPPLIED_ANSWER.value}
            )
        else:
            request_b = RunRequest.model_construct(
                task=request_a.task,
                mode=RunMode.SCORE_SUPPLIED_ANSWER,
                context=request_a.context,
                question=request_a.question,
                prompt=request_a.prompt,
                supplied_answer='',
                example_id=request_a.example_id,
                source_run_id=None,
            )
        prov_b = Provenance(
            source_run_id=queued_a.id,
            disclosures=[
                f'Scored the same answer as run {queued_a.id} ({setup.detector_preset}).'
            ],
        )
        queued_b = self.engine.reserve(
            request_b, setup_b, self.session.state.setup_revision, prov_b
        )
        # Add B before A so advance() (which scans runs in reverse for the active one) drives A→B, and
        # B scores exactly the answer A produced/received.
        self.session.state.pending_requests[queued_b.id] = request_b
        self.session.state.pending_requests[queued_a.id] = request_a
        self.session.add_run(queued_b)
        self.session.add_run(queued_a)
        if not supplied:
            self.session.state.compare_answer_source[queued_b.id] = queued_a.id
        self.session.state.compare = {
            'run_a_id': queued_a.id,
            'run_b_id': queued_b.id,
            'preset_a': setup.detector_preset,
            'preset_b': setup_b.detector_preset,
        }

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
        source_id = self.session.state.compare_answer_source.pop(active.id, None)
        if source_id is not None:
            # This is the compare B side of a generate run: score exactly the answer A produced.
            source = self.session.get(source_id)
            answer = source.answer if source else ''
            if not answer:
                self.session.replace_run(active.model_copy(update={
                    'status': RunStatus.FAILED,
                    'completed_at': utc_now(),
                    'error': PublicError(
                        code='compare_no_answer',
                        message='The compared answer was not produced, so this side could not score it.',
                        correlation_id=str(uuid4()),
                    ),
                }))
                return True
            request = request.model_copy(update={'supplied_answer': answer})
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
