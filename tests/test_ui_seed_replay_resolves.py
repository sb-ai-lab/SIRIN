"""The landing seed cards' "Run it live" replays must resolve after gallery re-curation.

The census hero and judge seed carry their own example_id, but those cases are no longer curated
gallery chips. The registry registers them as resolve-only replay sources so recordedReplay works
without surfacing a hidden example in the picker.
"""

from sirin.ui.demo_cases import load_judge_span_seed, load_psiloqa_span_seed
from sirin.ui.workspace.contracts import RunMode, TaskType
from sirin.ui.workspace.examples import ExampleRegistry


def test_census_hero_seed_resolves_to_recorded_replay():
    case = load_psiloqa_span_seed()
    registry = ExampleRegistry()

    request, provenance = registry.resolve(case['example_id'])

    assert request.mode == RunMode.RECORDED_REPLAY
    assert request.task == TaskType.FAITHFULNESS
    assert request.example_id == case['example_id']
    assert request.supplied_answer == case['answer']  # replays the verified answer
    assert request.context == case['passage']
    assert provenance.dataset == case['dataset']


def test_seed_replay_id_is_hidden_from_the_curated_gallery():
    case = load_psiloqa_span_seed()
    registry = ExampleRegistry()

    visible = {summary.id for summary in registry.summaries()}
    assert case['example_id'] not in visible  # resolvable, but not a gallery chip
    registry.resolve(case['example_id'])  # still resolves


def test_judge_seed_run_it_live_resolves_when_asset_present():
    case = load_judge_span_seed()
    if case is None:  # asset is optional; absence is silent by design
        return
    registry = ExampleRegistry()

    request, _ = registry.resolve(case['example_id'])

    assert request.mode == RunMode.RECORDED_REPLAY
    assert request.supplied_answer == case['answer']
    assert case['example_id'] not in {s.id for s in registry.summaries()}
