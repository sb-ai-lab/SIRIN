"""Hosted profile (SIRIN_UI_HOSTED=1): API-judge-only presets, OpenRouter-first backends, CPU."""

import pytest

from sirin.ui import presets
from sirin.ui import streamlit_app as ui
from test_streamlit_ui import _SidebarHarness

CENSUS_PRESET = 'Probing — Token Linear · PsiloQA/Qwen3-4B'
QWEN35_PRESET = 'Probing — Token Linear · PsiloQA/Qwen3.5-4B'


@pytest.fixture
def hosted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.setenv('SIRIN_UI_HOSTED', '1')


@pytest.fixture
def not_hosted(monkeypatch):
    monkeypatch.delenv('SIRIN_UI_TRUSTED_LOCAL', raising=False)
    monkeypatch.delenv('SIRIN_UI_HOSTED', raising=False)


def test_hosted_visible_presets_are_judges_plus_every_recorded_replay_preset(hosted):
    visible = presets.visible_presets()

    assert visible
    # Live scoring = judges; every other entry is a replay-only preset with a bundled
    # recorded result (probes, uncertainty, the LongMemEval sequence TabPFN).
    non_judge = [p.name for p in visible if p.family != 'judge']
    assert non_judge == list(presets.HOSTED_REPLAY_PRESETS)
    assert QWEN35_PRESET in non_judge
    assert sum(1 for p in visible if p.family == 'judge') == 5


def test_visible_presets_equal_list_presets_when_not_hosted(not_hosted):
    assert presets.visible_presets() == presets.list_presets()


def test_hosted_shows_the_verbalized_judge_preset(hosted):
    names = [p.name for p in presets.visible_presets()]

    assert 'Judge — API Sequence (verbalized confidence)' in names
    # The hosted default stays the span judge.
    assert names[0] != 'Judge — API Sequence (verbalized confidence)'


def test_hosted_offers_non_judge_presets_as_replay_only(hosted):
    assert presets.hosted_replay_only('probing') is True
    assert presets.hosted_replay_only('uncertainty') is True
    assert presets.hosted_replay_only('judge') is False


def test_replay_only_gate_is_hosted_only(not_hosted):
    assert presets.hosted_replay_only('probing') is False


def _hosted_submit_envelope(payload):
    from uuid import uuid4

    from sirin.ui.workspace.contracts import ActionEnvelope

    return ActionEnvelope(
        client_instance_id=str(uuid4()),
        sequence=1,
        action_id=str(uuid4()),
        type='submit',
        expected_setup_revision=0,
        expected_runs_revision=0,
        payload=payload,
    )


def test_hosted_probe_replay_serves_the_recorded_seed(hosted):
    from sirin.ui.workspace.contracts import RunOrigin
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.seed import build_second_probe_seed_run
    from sirin.ui.workspace.session import WorkspaceSession

    seed = build_second_probe_seed_run()
    assert seed is not None
    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)

    receipt = controller.handle(
        _hosted_submit_envelope(
            {'mode': 'recordedReplay', 'exampleId': seed.inputs.example_id}
        ),
        setup=seed.setup_snapshot,
    )

    assert receipt.status.value == 'accepted'
    run = session.state.runs[-1]
    assert run.origin is RunOrigin.RECORDED_RESULT
    assert run.setup_snapshot.detector_preset == QWEN35_PRESET
    assert run.analysis == seed.analysis  # byte-identical recorded derivation
    assert run.id != seed.id  # a fresh run, not the landing card itself


def test_hosted_replay_serves_each_presets_own_recording_of_the_same_example(hosted):
    # Several presets record the SAME landing example; the active preset must get its
    # own result, never another detector's.
    from sirin.ui.demo_cases import load_psiloqa_span_seed_qwen35
    from sirin.ui.workspace.seed import build_recorded_replay

    example_id = load_psiloqa_span_seed_qwen35()['example_id']
    token = build_recorded_replay(example_id, preset='Uncertainty — Token (zero-shot)')
    sequence = build_recorded_replay(example_id, preset='Uncertainty — Sequence (zero-shot)')

    assert token is not None and sequence is not None
    assert token.setup_snapshot.detector_preset == 'Uncertainty — Token (zero-shot)'
    assert sequence.setup_snapshot.detector_preset == 'Uncertainty — Sequence (zero-shot)'
    assert build_recorded_replay(example_id, preset='No Such Preset') is None


def test_hosted_uncertainty_replay_appends_the_recorded_run(hosted):
    from sirin.ui.workspace.contracts import RunOrigin, SetupSnapshot
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession
    from sirin.ui.demo_cases import load_psiloqa_span_seed_qwen35

    example_id = load_psiloqa_span_seed_qwen35()['example_id']
    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = SetupSnapshot(
        detector_preset='Uncertainty — Token (zero-shot)',
        detector_family='uncertainty',
        detector_level='token',
    )

    receipt = controller.handle(
        _hosted_submit_envelope({'mode': 'recordedReplay', 'exampleId': example_id}),
        setup=setup,
    )

    assert receipt.status.value == 'accepted'
    run = session.state.runs[-1]
    assert run.origin is RunOrigin.RECORDED_RESULT
    assert run.setup_snapshot.detector_preset == 'Uncertainty — Token (zero-shot)'


def test_hosted_probe_live_scoring_is_rejected_with_actionable_copy(hosted):
    from sirin.ui.workspace.contracts import SetupSnapshot
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession

    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = SetupSnapshot(
        detector_preset=QWEN35_PRESET,
        detector_family='probing',
        detector_level='token',
    )

    receipt = controller.handle(
        _hosted_submit_envelope(
            {
                'task': 'faithfulness',
                'mode': 'scoreSuppliedAnswer',
                'question': 'q',
                'suppliedAnswer': 'a',
            }
        ),
        setup=setup,
    )

    assert receipt.status.value == 'rejected'
    assert 'Judge — API' in receipt.message
    assert session.state.runs == []


def test_hosted_sidebar_defaults_to_judge_span_and_api_backends(hosted):
    harness = _SidebarHarness()

    cfg = ui._sidebar(harness)

    assert cfg['preset_name'] == presets.JUDGE_SPAN_PRESET
    preset_options = dict(harness.selectbox_calls)['Preset']
    assert preset_options[0] == presets.JUDGE_SPAN_PRESET
    assert preset_options.count(presets.JUDGE_SPAN_PRESET) == 1
    backend_options = dict(harness.selectbox_calls)['Backend']
    assert backend_options == ['OpenRouter', 'OpenAI', 'Anthropic']
    assert cfg['backend'] == 'OpenRouter'
    assert cfg['device'] == 'cpu'


def test_hosted_seed_runs_carry_one_recorded_card_per_replay_preset(hosted):
    from sirin.ui.workspace.contracts import RunOrigin
    from sirin.ui.workspace.seed import build_seed_runs

    runs = build_seed_runs()

    # Every replay-only preset lands with its own recorded card — this is also the pin
    # that HOSTED_REPLAY_PRESETS never promises a preset without a bundled recording.
    card_presets = {r.setup_snapshot.detector_preset for r in runs}
    assert set(presets.HOSTED_REPLAY_PRESETS) <= card_presets
    assert any(r.setup_snapshot.detector_family == 'judge' for r in runs)
    # The hero card stays the Qwen3.5-4B probe, and every card is honestly recorded.
    assert runs[-1].setup_snapshot.detector_preset == QWEN35_PRESET
    assert all(r.origin is RunOrigin.RECORDED_RESULT for r in runs)
    assert len({r.id for r in runs}) == len(runs)


def test_non_hosted_seed_runs_keep_the_census_hero(not_hosted):
    from sirin.ui.workspace.seed import build_seed_runs

    runs = build_seed_runs()

    assert runs[-1].setup_snapshot.detector_preset == CENSUS_PRESET
    assert any(r.setup_snapshot.detector_preset == QWEN35_PRESET for r in runs)


def _judge_span_setup():
    from sirin.ui.workspace.contracts import SetupSnapshot

    return SetupSnapshot(
        detector_preset=presets.JUDGE_SPAN_PRESET,
        detector_family='judge',
        detector_level='span',
    )


def test_hosted_payload_flags_hosted_and_keeps_recorded_seeding(hosted):
    from sirin.ui.workspace.contracts import RunOrigin
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession

    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = _judge_span_setup()

    assert controller.seed_landing(setup) is True
    payload = controller.build_payload(setup=setup)

    # The hosted profile is advertised to the client, which gates its Custom-first UX on it.
    assert payload.hosted is True
    # Recorded-run seeding is untouched — the Runs panel still lands with its verified cards.
    assert session.state.runs
    assert all(r.origin is RunOrigin.RECORDED_RESULT for r in session.state.runs)


def test_hosted_lands_on_empty_custom_draft(hosted):
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession

    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = _judge_span_setup()
    controller.seed_landing(setup)

    payload = controller.build_payload(setup=setup)
    # Hosted defaults to the Custom card: no prefilled example draft, so the client's empty DEFAULT_DRAFT
    # (exampleId=None) takes over. Contrast test_seed_prefills_the_census_draft_only_while_pristine (local).
    assert payload.draft is None


def test_not_hosted_still_prefills_the_example_draft(not_hosted):
    from sirin.ui.workspace.contracts import SetupSnapshot, TaskType
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession

    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = SetupSnapshot(
        detector_preset=CENSUS_PRESET,
        detector_family='probing',
        detector_level='token',
        task=TaskType.FAITHFULNESS,
    )
    controller.seed_landing(setup)

    payload = controller.build_payload(setup=setup)
    # Local landing is unchanged: the census example is still prefilled while pristine.
    assert payload.draft is not None
    assert payload.hosted is False


def test_curated_examples_name_the_answer_source_model(hosted):
    from sirin.ui.workspace.examples import cached_example_registry

    summaries = cached_example_registry().summaries()
    # Each curated example replays its ORIGINAL recorded answer, so provenance must name the model that
    # produced it — the honest note the gallery card and result provenance surface.
    assert summaries
    assert all(s.provenance.source_model for s in summaries)


def test_shared_env_key_serves_only_the_configured_default_model(monkeypatch):
    import pytest

    from sirin.ui.providers import OPENROUTER_PROVIDER, require_shared_key_model

    monkeypatch.setenv('SIRIN_UI_HOSTED', '1')
    monkeypatch.setenv(
        'SIRIN_OPENROUTER_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free'
    )
    # Shared env key + the configured default: allowed (the demo path).
    require_shared_key_model(
        OPENROUTER_PROVIDER, 'nvidia/nemotron-3-super-120b-a12b:free', None
    )
    # Any other model — even another free one — is blocked with actionable copy.
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', None)
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(
            OPENROUTER_PROVIDER, 'qwen/qwen3-8b:free', None
        )
    # A pasted key is the visitor's own: no restriction.
    require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', 'sk-user')


def test_shared_env_key_fails_closed_on_paid_or_unset_default(monkeypatch):
    """H1: the shared key must fund a :free route only. A misconfigured (paid) or unset
    default disables the shared key entirely rather than silently billing a paid model,
    and OpenAI/Anthropic env keys never ride the shared key without a pasted key."""
    import pytest

    from sirin.ui.providers import (
        ANTHROPIC_PROVIDER,
        OPENAI_PROVIDER,
        OPENROUTER_PROVIDER,
        require_shared_key_model,
    )

    monkeypatch.setenv('SIRIN_UI_HOSTED', '1')

    # Paid default → even that exact model is refused (fail closed, no billing).
    monkeypatch.setenv('SIRIN_OPENROUTER_MODEL', 'openai/gpt-4.1-mini')
    with pytest.raises(ValueError, match='free OpenRouter'):
        require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', None)

    # A funded OpenAI/Anthropic env key (if ever present) is never spent by a visitor
    # without a pasted key, whatever the model.
    monkeypatch.setenv('SIRIN_OPENROUTER_MODEL', 'qwen/qwen3-8b:free')
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(OPENAI_PROVIDER, 'gpt-4.1-mini', None)
    with pytest.raises(ValueError, match='paste your own'):
        require_shared_key_model(ANTHROPIC_PROVIDER, 'claude-sonnet-4-6', None)
    # ...but their own pasted key is unrestricted.
    require_shared_key_model(OPENAI_PROVIDER, 'gpt-4.1-mini', 'sk-user')


def test_generator_adapter_applies_openrouter_reasoning_policy(monkeypatch):
    # Without this the demo generator lets a reasoning model overrun the budget and
    # OpenRouter mirrors the truncated chain-of-thought into content — the "answer" the
    # judge then fails to echo is thinking text (user-reported on the Space).
    from sirin.ui.providers import openrouter_reasoning_extra_body
    from sirin.ui.streamlit_app import _new_generator_adapter

    monkeypatch.setenv('OPENROUTER_API_KEY', 'or-key')
    monkeypatch.setenv(
        'SIRIN_OPENROUTER_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free'
    )
    default = _new_generator_adapter(
        'OpenRouter', 'nvidia/nemotron-3-super-120b-a12b:free', 'cpu', '', ''
    )
    # The verified demo model generates with reasoning off entirely.
    assert default.config.extra_body == {'reasoning': {'enabled': False}}
    assert openrouter_reasoning_extra_body('anything/else') == {
        'reasoning': {'max_tokens': 1024}
    }


def test_shared_key_guard_is_hosted_only(monkeypatch):
    from sirin.ui.providers import OPENROUTER_PROVIDER, require_shared_key_model

    monkeypatch.delenv('SIRIN_UI_HOSTED', raising=False)
    # Local/campaign use keeps full env-key freedom.
    require_shared_key_model(OPENROUTER_PROVIDER, 'openai/gpt-4.1-mini', None)


def test_external_consent_defaults_to_checked():
    import sirin.ui.streamlit_app as ui

    captured = {}

    class _Sidebar:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _St:
        sidebar = _Sidebar()

        @staticmethod
        def checkbox(label, value=None, **kwargs):
            captured['value'] = value
            return value

    confirmed = ui._external_confirmed(
        _St, {'preset_name': 'Judge — API Span (zero-shot)', 'backend': 'OpenRouter'}
    )
    assert captured['value'] is True
    assert confirmed is True


def test_hosted_replay_target_resolves_every_replay_preset(hosted):
    # The payload carries the one recorded case each replay-only preset serves; its presence
    # is the client's replay-only signal. Judge presets score live -> no target.
    from sirin.ui.workspace.contracts import SetupSnapshot
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.seed import replay_record_for_preset
    from sirin.ui.workspace.session import WorkspaceSession

    controller = WorkspaceController(WorkspaceSession({}), engine=None)
    for name in presets.HOSTED_REPLAY_PRESETS:
        setup = SetupSnapshot(
            detector_preset=name,
            detector_family=presets.PRESETS[name].family,
            detector_level='sequence',
        )
        target = controller._replay_target(setup)
        assert target is not None, name
        assert target.preset == name
        assert target.answer
        assert target.example_id == replay_record_for_preset(name).inputs.example_id

    judge_setup = SetupSnapshot(
        detector_preset=presets.JUDGE_SPAN_PRESET,
        detector_family='judge',
        detector_level='token',
    )
    assert controller._replay_target(judge_setup) is None


def test_replay_target_is_none_when_not_hosted(not_hosted):
    from sirin.ui.workspace.contracts import SetupSnapshot
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.session import WorkspaceSession

    controller = WorkspaceController(WorkspaceSession({}), engine=None)
    setup = SetupSnapshot(
        detector_preset='Uncertainty — Token (zero-shot)',
        detector_family='uncertainty',
        detector_level='token',
    )
    assert controller._replay_target(setup) is None


@pytest.mark.parametrize(
    'preset',
    ['Probing — Sequence TabPFN (checkpoint)', CENSUS_PRESET],
)
def test_hosted_editor_replay_serves_preset_recording_even_with_stale_example(hosted, preset):
    # The hosted editor defaults to the Qwen3.5-4B example; TabPFN and Qwen3-4B record a
    # DIFFERENT case. A replay submitted under those presets with the stale default example
    # must still serve the preset's own recording (preset-only fallback), never reject.
    from sirin.ui.demo_cases import load_psiloqa_span_seed_qwen35
    from sirin.ui.workspace.contracts import RunOrigin, SetupSnapshot
    from sirin.ui.workspace.controller import WorkspaceController
    from sirin.ui.workspace.seed import replay_record_for_preset
    from sirin.ui.workspace.session import WorkspaceSession

    stale_example = load_psiloqa_span_seed_qwen35()['example_id']
    assert replay_record_for_preset(preset).inputs.example_id != stale_example  # genuinely stale

    session = WorkspaceSession({})
    controller = WorkspaceController(session, engine=None)
    setup = SetupSnapshot(
        detector_preset=preset,
        detector_family=presets.PRESETS[preset].family,
        detector_level='sequence',
    )

    receipt = controller.handle(
        _hosted_submit_envelope({'mode': 'recordedReplay', 'exampleId': stale_example}),
        setup=setup,
    )

    assert receipt.status.value == 'accepted', receipt.message
    run = session.state.runs[-1]
    assert run.origin is RunOrigin.RECORDED_RESULT
    assert run.setup_snapshot.detector_preset == preset
    assert run.inputs.example_id == replay_record_for_preset(preset).inputs.example_id


def test_hosted_verbalized_sequence_judge_precedes_plain(hosted):
    # On the free route the plain sequence judge often shows no score; lead the pair with the
    # verbalized judge so a visitor reaching for a sequence judge lands on one that scores.
    names = [p.name for p in presets.visible_presets()]
    assert names.index(presets.JUDGE_SEQUENCE_VERBALIZED_PRESET) < names.index(
        presets.JUDGE_SEQUENCE_PRESET
    )
