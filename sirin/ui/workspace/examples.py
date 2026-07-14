"""Registry backed only by the verified examples already shipped with SIRIN."""

from __future__ import annotations

from functools import lru_cache

from .contracts import ExampleSummary, Provenance, RunMode, RunRequest, TaskType
from sirin.ui.demo_cases import load_demo_cases, load_psiloqa_demo_cases


class ExampleRegistry:
    def __init__(self) -> None:
        self._summaries: dict[str, ExampleSummary] = {}
        self._requests: dict[str, RunRequest] = {}
        self._load_psiloqa()
        self._load_recorded_cases()

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

    def summaries(self) -> list[ExampleSummary]:
        return list(self._summaries.values())

    def resolve(self, example_id: str) -> tuple[RunRequest, Provenance]:
        try:
            summary = self._summaries[example_id]
            request = self._requests[example_id]
        except KeyError as exc:
            raise ValueError('unknown example') from exc
        return request.model_copy(deep=True), summary.provenance.model_copy(deep=True)


@lru_cache(maxsize=1)
def cached_example_registry() -> ExampleRegistry:
    """Process-wide registry singleton.

    The bundled examples are immutable per process, so their JSON parsing and SHA-256 verification
    should happen once, not on every Streamlit rerun. ``resolve`` hands out deep copies, so sharing
    this instance is safe. Callers needing a fresh build can still construct ``ExampleRegistry()``.
    """
    return ExampleRegistry()
