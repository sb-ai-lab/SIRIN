import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from sirin.ui.workspace.contracts import (
    ActionEnvelope,
    AnalysisKind,
    AnalysisResult,
    ReceiptStatus,
    RunInputs,
    RunOrigin,
    RunRecord,
    RunStatus,
    ScoreSemantics,
    SetupSnapshot,
)
from sirin.ui.workspace import session as session_module
from sirin.ui.workspace.session import (
    PortableFormatError,
    WorkspaceSession,
    export_bundle,
    export_run,
    import_portable_json,
)


def _run(*, run_id=None, answer='answer'):
    now = datetime(2026, 7, 13, tzinfo=timezone.utc)
    return RunRecord(
        id=run_id or str(uuid4()),
        created_at=now,
        completed_at=now,
        status=RunStatus.SUCCEEDED,
        origin=RunOrigin.SUPPLIED_ANSWER,
        setup_revision=0,
        setup_snapshot=SetupSnapshot(
            detector_preset='probe',
            detector_family='probing',
            detector_level='sequence',
            score_semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE,
        ),
        inputs=RunInputs(question='Question?', supplied_answer=answer),
        answer=answer,
        analysis=AnalysisResult(
            kind=AnalysisKind.SEQUENCE,
            score_semantics=ScoreSemantics.THRESHOLDED_RAW_SCORE,
            label='Supported',
            verdict=False,
            score=0.1,
        ),
        request_digest='a' * 64,
    )


def _action(sequence, *, setup_revision=0, runs_revision=0, action_id=None):
    return ActionEnvelope(
        client_instance_id='11111111-1111-1111-1111-111111111111',
        sequence=sequence,
        action_id=action_id or str(uuid4()),
        type='clearRuns',
        expected_setup_revision=setup_revision,
        expected_runs_revision=runs_revision,
    )


def test_single_and_bundle_json_verify_integrity_and_enforce_size(monkeypatch):
    first = _run(answer='one')
    second = _run(answer='two')

    single = export_run(first)
    bundle = export_bundle([first, second])

    assert import_portable_json(single) == [first]
    assert import_portable_json(bundle) == [first, second]
    tampered = json.loads(single)
    tampered['run']['answer'] = 'changed'
    with pytest.raises(PortableFormatError, match='integrity verification failed'):
        import_portable_json(json.dumps(tampered))

    monkeypatch.setattr(session_module, 'RUN_BYTES', 1)
    with pytest.raises(PortableFormatError, match='5 MiB export limit'):
        export_run(first)
    monkeypatch.setattr(session_module, 'RUN_BYTES', 5 * 1024 * 1024)
    monkeypatch.setattr(session_module, 'BUNDLE_BYTES', 1)
    with pytest.raises(PortableFormatError, match='10 MiB export limit'):
        export_bundle([first])


def test_import_creates_an_immutable_local_snapshot_with_source_provenance():
    source = _run()
    session = WorkspaceSession({})

    session.import_runs(import_portable_json(export_run(source)))

    imported = session.state.runs[0]
    assert imported.id != source.id
    assert imported.origin is RunOrigin.IMPORTED
    assert imported.provenance.source_run_id == source.id
    assert imported.provenance.original_created_at == source.created_at
    with pytest.raises(ValidationError, match='frozen'):
        imported.answer = 'changed'


def test_actions_are_deduplicated_and_stale_revisions_are_rejected():
    session = WorkspaceSession({})
    first = _action(1)

    assert session.begin_action(first).status is ReceiptStatus.ACCEPTED
    assert session.begin_action(first).status is ReceiptStatus.DUPLICATE
    assert session.begin_action(_action(1)).code == 'duplicate_sequence'

    session.state.setup_revision = 1
    stale_setup = session.begin_action(_action(2))
    assert (stale_setup.status, stale_setup.code) == (
        ReceiptStatus.REJECTED,
        'stale_setup',
    )

    session.state.runs_revision = 1
    stale_runs = session.begin_action(_action(3, setup_revision=1))
    assert (stale_runs.status, stale_runs.code) == (
        ReceiptStatus.REJECTED,
        'stale_runs',
    )


def test_stale_setup_with_a_benign_delta_auto_accepts_with_current_setup():
    session = WorkspaceSession({})
    session.note_setup('preset-and-model')
    session.state.setup_revision = 1
    session.note_setup('preset-and-model')

    receipt = session.begin_action(_action(1, setup_revision=0))

    assert receipt.status is ReceiptStatus.ACCEPTED


def test_stale_setup_with_an_incompatible_delta_is_rejected():
    session = WorkspaceSession({})
    session.note_setup('preset-a')
    session.state.setup_revision = 1
    session.note_setup('preset-b')

    receipt = session.begin_action(_action(1, setup_revision=0))

    assert (receipt.status, receipt.code) == (ReceiptStatus.REJECTED, 'stale_setup')


def test_direct_and_imported_history_keep_only_the_latest_50_runs():
    direct = WorkspaceSession({})
    direct_runs = [_run() for _ in range(51)]
    for run in direct_runs:
        direct.add_run(run)

    imported = WorkspaceSession({})
    imported_runs = [_run() for _ in range(51)]
    imported.import_runs(imported_runs)

    assert len(direct.state.runs) == 50
    assert direct_runs[0].id not in {run.id for run in direct.state.runs}
    assert len(imported.state.runs) == 50
    assert imported.state.runs[0].provenance.source_run_id == imported_runs[1].id
