"""Registry backed only by the verified examples already shipped with SIRIN."""

from __future__ import annotations

from functools import lru_cache

from .contracts import ExampleSummary, Provenance, RunMode, RunRequest, TaskType
from sirin.ui.demo_cases import (
    load_demo_cases,
    load_judge_span_seed,
    load_psiloqa_demo_cases,
    load_psiloqa_span_seed,
    load_psiloqa_span_seed_qwen35,
    load_ragtruth_demo_cases,
)


class ExampleRegistry:
    def __init__(self) -> None:
        self._summaries: dict[str, ExampleSummary] = {}
        self._requests: dict[str, RunRequest] = {}
        # Resolve-only replay sources (landing seeds); never surfaced in summaries().
        self._hidden: dict[str, tuple[RunRequest, Provenance]] = {}
        self._load_psiloqa()
        self._load_ragtruth()
        self._load_recorded_cases()
        self._load_seed_examples()

    def _load_psiloqa(self) -> None:
        for case in load_psiloqa_demo_cases():
            provenance = Provenance(
                dataset=case['dataset'],
                split=case['split'],
                source_model=case['source_answer_model'],
                representation_model=case['representation_model'],
                integrity_sha256=case['messages_sha256'],
                disclosures=[
                    case['representation_disclosure'],
                    case['selection_disclosure'],
                    case['annotation_disclosure'],
                    f"License: {case['license']}",
                ],
            )
            summary = ExampleSummary(
                id=case['case_id'],
                label=case['label'],
                dataset=case['dataset'],
                context=case['passage'],
                question=case['question'],
                prompt=case['messages'][0]['content'],
                recorded_answer=case['answer'],
                why_notable=case['why_notable'],
                provenance=provenance,
            )
            self._summaries[summary.id] = summary
            self._requests[summary.id] = RunRequest(
                task=TaskType.FAITHFULNESS,
                mode=RunMode.RECORDED_REPLAY,
                context=summary.context,
                question=summary.question,
                prompt=summary.prompt,
                supplied_answer=summary.recorded_answer,
                example_id=summary.id,
            )

    def _load_ragtruth(self) -> None:
        for case in load_ragtruth_demo_cases():
            provenance = Provenance(
                dataset=case['dataset'],
                split=case['split'],
                source_model=case['source_answer_model'],
                integrity_sha256=case['messages_sha256'],
                disclosures=[
                    case['selection_disclosure'],
                    case['annotation_disclosure'],
                    case['source_disclosure'],
                    f"License: {case['license']}",
                ],
            )
            summary = ExampleSummary(
                id=case['case_id'],
                label=case['label'],
                dataset=case['dataset'],
                context=case['context'],
                question=case['question'],
                prompt=case['messages'][0]['content'],
                recorded_answer=case['answer'],
                why_notable=case['why_notable'],
                provenance=provenance,
            )
            self._summaries[summary.id] = summary
            self._requests[summary.id] = RunRequest(
                task=TaskType.FAITHFULNESS,
                mode=RunMode.RECORDED_REPLAY,
                context=summary.context,
                question=summary.question,
                prompt=summary.prompt,
                supplied_answer=summary.recorded_answer,
                example_id=summary.id,
            )

    def _load_recorded_cases(self) -> None:
        for case in load_demo_cases().values():
            provenance_data = case['provenance']
            provenance = Provenance(
                dataset=provenance_data.get('dataset'),
                source_model=provenance_data.get('model'),
                integrity_sha256=case['messages_sha256'],
                disclosures=[
                    'Recorded answer replayed from the verified bundled artifact; detection runs live.'
                ],
            )
            summary = ExampleSummary(
                id=case['sample_id'],
                label=case['title'],
                dataset=provenance_data.get('dataset') or 'LongMemEval',
                prompt=case['answer_prompt'],
                question=case['title'],
                recorded_answer=case['prediction'],
                provenance=provenance,
            )
            self._summaries[summary.id] = summary
            self._requests[summary.id] = RunRequest.model_construct(
                task=TaskType.FAITHFULNESS,
                mode=RunMode.RECORDED_REPLAY,
                question=summary.question,
                prompt=summary.prompt,
                supplied_answer=summary.recorded_answer,
                example_id=summary.id,
            )

    def _load_seed_examples(self) -> None:
        """Register the landing span seeds as resolve-only replay sources.

        The hero/judge/second-probe seed cards each expose "Run it live" — a recordedReplay of the
        seed's own example_id. The re-curated gallery no longer contains these cases, so resolve()
        would fail and the button would no-op. Registering the verified seed assets here (resolvable,
        but never surfaced in summaries()) restores Run-it-live without adding a hidden gallery chip. A
        seed whose example_id is already a curated visible case is skipped so it never shadows it.
        """
        for load in (
            load_psiloqa_span_seed,
            load_psiloqa_span_seed_qwen35,
            load_judge_span_seed,
        ):
            try:
                case = load()
            except FileNotFoundError:
                continue
            if not case:
                continue
            example_id = case['example_id']
            if example_id in self._summaries or example_id in self._hidden:
                continue
            self._hidden[example_id] = (
                _seed_request(case),
                _seed_provenance(case),
            )

    def summaries(self) -> list[ExampleSummary]:
        return list(self._summaries.values())

    def resolve(self, example_id: str) -> tuple[RunRequest, Provenance]:
        hidden = self._hidden.get(example_id)
        if hidden is not None:
            request, provenance = hidden
            return request.model_copy(deep=True), provenance.model_copy(deep=True)
        try:
            summary = self._summaries[example_id]
            request = self._requests[example_id]
        except KeyError as exc:
            raise ValueError('unknown example') from exc
        return request.model_copy(deep=True), summary.provenance.model_copy(deep=True)


def _seed_request(case: dict) -> RunRequest:
    """RECORDED_REPLAY request from a verified span-seed case (replays the answer through live
    detection). Mirrors _load_psiloqa's mapping: context=passage, prompt=user message, answer=answer."""
    return RunRequest(
        task=TaskType.FAITHFULNESS,
        mode=RunMode.RECORDED_REPLAY,
        context=case['passage'],
        question=case['question'],
        prompt=case['messages'][0]['content'],
        supplied_answer=case['answer'],
        example_id=case['example_id'],
    )


def _seed_provenance(case: dict) -> Provenance:
    """Provenance from a span-seed case, tolerating the leaner judge-seed schema (no representation
    model / disclosure fields)."""
    disclosures = [
        case[key]
        for key in (
            'representation_disclosure',
            'selection_disclosure',
            'annotation_disclosure',
        )
        if case.get(key)
    ]
    disclosures.append(f"License: {case['license']}")
    return Provenance(
        dataset=case.get('dataset'),
        split=case.get('split'),
        source_model=case.get('source_answer_model'),
        representation_model=case.get('representation_model'),
        integrity_sha256=case.get('messages_sha256'),
        disclosures=disclosures,
    )


@lru_cache(maxsize=1)
def cached_example_registry() -> ExampleRegistry:
    """Process-wide registry singleton.

    The bundled examples are immutable per process, so their JSON parsing and SHA-256 verification
    should happen once, not on every Streamlit rerun. ``resolve`` hands out deep copies, so sharing
    this instance is safe. Callers needing a fresh build can still construct ``ExampleRegistry()``.
    """
    return ExampleRegistry()
