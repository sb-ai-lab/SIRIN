from contextlib import contextmanager
from types import SimpleNamespace
from uuid import uuid4

from sirin.inference.model_manager import ModelManager
from sirin.ui.workspace.contracts import (
    ActionEnvelope,
    DownloadTransfer,
    ReceiptStatus,
    RunMode,
    RunOrigin,
    RunRequest,
    RunStatus,
    SetupSnapshot,
    TaskType,
)
from sirin.ui.workspace.controller import WorkspaceController
from sirin.ui.workspace import run_engine as run_engine_module
from sirin.ui.workspace.run_engine import RunEngine
from sirin.ui.workspace.session import WorkspaceSession, export_run


_CLIENT_ID = '11111111-1111-1111-1111-111111111111'


def _setup():
    return SetupSnapshot(
        detector_preset='probe',
        detector_family='probing',
        detector_level='sequence',
        threshold=0.5,
    )


def _submit(session, question):
    return ActionEnvelope(
        client_instance_id=_CLIENT_ID,
        sequence=session.state.high_water.get(_CLIENT_ID, 0) + 1,
        action_id=str(uuid4()),
        type='submit',
        expected_setup_revision=session.state.setup_revision,
        expected_runs_revision=session.state.runs_revision,
        payload={'question': question},
    )


def test_controller_retains_partial_answer_and_terminal_failure(monkeypatch):
    logged = []
    monkeypatch.setattr(run_engine_module, 'lg', SimpleNamespace(exception=logged.append))

    def generate(request, _setup):
        if request.question == 'generation fails':
            raise OSError('private provider detail')
        return 'preserved answer'

    def detect(_answer, _request, _setup):
        raise RuntimeError('private detector detail')

    session = WorkspaceSession({})
    controller = WorkspaceController(
        session,
        RunEngine(generate=generate, detect=detect),
    )

    partial_receipt = controller.handle(_submit(session, 'detection fails'), setup=_setup())
    assert session.state.runs[-1].status is RunStatus.QUEUED
    assert controller.advance() is True
    assert session.state.runs[-1].status is RunStatus.RUNNING
    session.recover_interrupted()
    assert session.state.runs[-1].status is RunStatus.RUNNING
    assert controller.advance() is True
    assert session.state.runs[-1].status is RunStatus.PARTIAL

    failed_receipt = controller.handle(_submit(session, 'generation fails'), setup=_setup())
    assert session.state.runs[-1].status is RunStatus.QUEUED
    assert controller.advance() is True
    assert session.state.runs[-1].status is RunStatus.RUNNING
    assert controller.advance() is True

    assert partial_receipt.status is ReceiptStatus.ACCEPTED
    assert failed_receipt.status is ReceiptStatus.ACCEPTED
    assert [run.status for run in session.state.runs] == [
        RunStatus.PARTIAL,
        RunStatus.FAILED,
    ]
    partial, failed = session.state.runs
    assert partial.answer == 'preserved answer'
    assert partial.error.code == 'detection_failed'
    assert partial.error.correlation_id in logged[0]
    assert failed.error.code == 'operation_failed'
    assert 'private' not in partial.error.message + failed.error.message
    assert all(run.completed_at is not None for run in session.state.runs)

    orphan_request = RunRequest(question='orphaned')
    orphan = controller.engine.reserve(orphan_request, _setup(), 0).model_copy(
        update={'status': RunStatus.RUNNING}
    )
    session.add_run(orphan)
    session.recover_interrupted()
    assert session.get(orphan.id).status is RunStatus.INTERRUPTED


def test_controller_rejects_invalid_setup_before_queuing_run():
    session = WorkspaceSession({})
    controller = WorkspaceController(
        session,
        RunEngine(
            generate=lambda *_args: 'must not run',
            detect=lambda *_args: {'score': 0.1},
        ),
    )

    receipt = controller.handle(
        _submit(session, 'Question?'),
        setup=_setup(),
        submission_error='This preset needs a trained checkpoint directory.',
    )

    assert receipt.status is ReceiptStatus.REJECTED
    assert receipt.message == 'This preset needs a trained checkpoint directory.'
    assert session.state.runs == []


def test_answerability_never_calls_generator_and_uses_specific_label():
    generated = []
    engine = RunEngine(
        generate=lambda *_args: generated.append(True) or 'should not run',
        detect=lambda *_args: {'probability': 0.9, 'prediction': 1},
    )
    setup = _setup().model_copy(update={'task': TaskType.ANSWERABILITY})
    request = RunRequest(
        task=TaskType.ANSWERABILITY,
        mode=RunMode.ANSWERABILITY,
        context='Grounding context',
        question='Can this be answered?',
    )

    result = engine.execute(engine.reserve(request, setup, 0), request)

    assert generated == []
    assert result.status is RunStatus.SUCCEEDED
    assert result.analysis.label == 'Answerable'


def test_engine_maps_model_manager_contention_to_busy(monkeypatch):
    @contextmanager
    def busy():
        raise RuntimeError('locked')
        yield

    monkeypatch.setattr(ModelManager, 'exclusive_run', busy)
    engine = RunEngine(generate=lambda _request, _setup: 'answer', detect=lambda *_args: {})
    request = RunRequest(question='Question?')

    result = engine.execute(engine.reserve(request, _setup(), 0), request)

    assert result.status is RunStatus.FAILED
    assert result.error.code == 'busy'
    assert result.error.message == 'Another model operation is running.'


def test_submit_links_only_to_an_imported_snapshot():
    engine = RunEngine(
        generate=lambda *_args: 'answer',
        detect=lambda *_args: {'score': 0.1, 'verdict': False},
    )
    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine)
    request = RunRequest(question='Source question?')
    local = engine.execute(engine.reserve(request, _setup(), 0), request)
    session.add_run(local)

    rejected_action = _submit(session, 'Rerun?')
    rejected_action = rejected_action.model_copy(
        update={'payload': {'question': 'Rerun?', 'sourceRunId': local.id}}
    )
    assert controller.handle(rejected_action, setup=_setup()).status is ReceiptStatus.REJECTED

    session.import_runs([local])
    imported = session.state.runs[-1]
    accepted_action = _submit(session, 'Rerun?')
    accepted_action = accepted_action.model_copy(
        update={'payload': {'question': 'Rerun?', 'sourceRunId': imported.id}}
    )
    assert controller.handle(accepted_action, setup=_setup()).status is ReceiptStatus.ACCEPTED
    assert controller.advance() is True
    assert controller.advance() is True

    rerun = session.state.runs[-1]
    assert rerun.origin is RunOrigin.RERUN_IMPORTED
    assert rerun.provenance.source_run_id == imported.id


def test_consent_permission_surfaces_actionable_message_from_generation():
    from sirin.ui.workspace.run_engine import ConsentRequiredError

    def generate(_request, _setup):
        raise ConsentRequiredError(
            'External API calls need your consent. Turn on Allow external '
            'API calls in the sidebar, then run again.'
        )

    engine = RunEngine(generate=generate, detect=lambda *_args: {'score': 0.1})
    request = RunRequest(question='Question?')

    result = engine.execute(engine.reserve(request, _setup(), 0), request)

    assert result.status is RunStatus.FAILED
    assert result.error.code == 'consent_required'
    assert 'consent' in result.error.message.lower()
    assert result.error.message != 'The operation failed.'


def test_consent_permission_during_detection_is_not_masked_as_partial():
    from sirin.ui.workspace.run_engine import ConsentRequiredError

    def detect(*_args):
        raise ConsentRequiredError(
            'External API calls need your consent. Turn it on in the sidebar, then run again.'
        )

    engine = RunEngine(generate=lambda _request, _setup: 'A generated answer.', detect=detect)
    request = RunRequest(question='Question?')

    result = engine.execute(engine.reserve(request, _setup(), 0), request)

    assert result.status is RunStatus.FAILED
    assert result.error.code == 'consent_required'
    assert 'consent' in result.error.message.lower()


def test_a_stray_permission_error_stays_generic_and_leaks_nothing():
    def detect(*_args):
        raise PermissionError("[Errno 13] Permission denied: '/secret/checkpoint/model.pt'")

    engine = RunEngine(generate=lambda _request, _setup: 'preserved answer', detect=detect)
    request = RunRequest(question='Question?')

    result = engine.execute(engine.reserve(request, _setup(), 0), request)

    # A non-consent PermissionError must not surface its path; it falls through to the sanitized path.
    assert result.error.code != 'consent_required'
    assert '/secret/checkpoint' not in (result.error.message or '')


def test_oversize_combined_input_is_rejected_with_a_human_message():
    engine = RunEngine(generate=lambda *_args: 'must not run', detect=lambda *_args: {'score': 0.1})
    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine)

    action = _submit(session, 'Question?')
    action = action.model_copy(
        update={'payload': {'question': 'Question?', 'context': 'a' * 30_001}}
    )
    receipt = controller.handle(action, setup=_setup())

    assert receipt.status is ReceiptStatus.REJECTED
    assert '30,000-character limit' in receipt.message
    assert 'Trim the context' in receipt.message
    # The raw pydantic dump (and the offending input value) must not leak into the receipt.
    assert 'combined input exceeds' not in receipt.message
    assert 'validation error' not in receipt.message.lower()
    assert session.state.runs == []


def test_payload_view_state_and_portable_action_acknowledgments():
    engine = RunEngine(
        generate=lambda *_args: 'answer',
        detect=lambda *_args: {'score': 0.1, 'verdict': False},
    )
    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine)
    request = RunRequest(question='Portable question?')
    source = engine.execute(engine.reserve(request, _setup(), 0), request)
    import_action = ActionEnvelope(
        client_instance_id=_CLIENT_ID,
        sequence=1,
        action_id=str(uuid4()),
        type='import',
        expected_setup_revision=0,
        expected_runs_revision=0,
        payload={'json': export_run(source)},
    )

    assert controller.handle(import_action, setup=_setup()).status is ReceiptStatus.ACCEPTED
    assert session.state.runs[-1].origin is RunOrigin.IMPORTED

    session.state.download = DownloadTransfer(file_name='run.json', content='{}')
    clear_action = ActionEnvelope(
        client_instance_id=_CLIENT_ID,
        sequence=2,
        action_id=str(uuid4()),
        type='clearDownload',
        expected_setup_revision=0,
        expected_runs_revision=session.state.runs_revision,
        payload={},
    )
    assert controller.handle(clear_action, setup=_setup()).status is ReceiptStatus.ACCEPTED

    payload = controller.build_payload(setup=_setup()).model_dump(by_alias=True)
    assert payload['viewState'] == {
        'workspace': 'analyze',
        'appearance': {
            'theme': 'light',
            'motion': 'subtle',
        },
    }
    assert payload['download'] is None
    assert payload['actionReceipt']['actionId'] == clear_action.action_id
