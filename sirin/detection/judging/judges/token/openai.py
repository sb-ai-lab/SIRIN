from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch

from sirin.definitions import DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import JudgeAnnotationError, OpenAIJudgeBase
from sirin.detection.judging.judges.utils import (
    build_prompt_messages,
    calculate_character_probabilities,
    extract_answer_from_generation,
    find_span_segments,
)
from sirin.detection.utils.token import convert_spans_to_labels
from sirin.inference.adapters import OpenAIModelAdapter
from sirin.models.detection import OpenAIJudgeConfig


class TokenOpenAIJudge(OpenAIJudgeBase):
    """
    OpenAI API judge implementation for token-level hallucination detection.

    Architecture: Uses OpenAI API with multiple generations to identify character-level spans.
    Similar to TokenDecoderJudge but uses API instead of local model.
    No training support - inference only via API calls.
    """
    detection_level = DetectionLevel.TOKEN

    def __init__(self, config: OpenAIJudgeConfig, model_adapter: OpenAIModelAdapter):
        super().__init__(config=config, model_adapter=model_adapter)
        self.class_token_ids = None
        self.last_generations: list[str] | None = None
        self.last_spans: list[list[tuple[int, int]]] | None = None
        self.last_consensus: list[dict] | None = None

    @staticmethod
    def _reference_answer(sample: Union[str, List[Dict]]) -> str:
        """The assistant answer the char scores must align to (matches format_dialogue_samples)."""
        if isinstance(sample, list) and len(sample) >= 2 and isinstance(sample[1], dict):
            return sample[1]['content']
        return sample

    @staticmethod
    def _echo_of(generation: Optional[str]) -> str:
        """A generation's answer with reasoning wrapper and span tags removed, for echo checking.

        A ``None``/empty generation (a provider may return empty content, e.g. when a reasoning
        budget is exhausted) is just an invalid vote: it returns '' and fails the echo check.
        """
        if not generation:
            return ''
        text = extract_answer_from_generation(generation)  # strips <think>… and outer whitespace
        return text.replace('[SPAN]', '').replace('[/SPAN]', '').strip()

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Uses OpenAI API for token-level classification with multiple generations.

        Each sample is annotated by ``num_beams`` independent generations. A generation only
        votes if it echoes the reference answer verbatim (after stripping any reasoning wrapper
        and the span tags); paraphrases/misaligned echoes are dropped. Each character's score is
        the fraction of VALID generations that flagged it, over the reference's characters. If no
        generation validates for a sample we raise instead of emitting a misleading all-clear.
        """
        samples, group_ids = self._split_context_samples(samples)
        references = [self._reference_answer(sample) for sample in samples]
        formatted_input = build_prompt_messages(self.config, samples)

        n = self.config.num_beams
        generated = self.model_adapter.sample(
            inputs=formatted_input,
            max_tokens=self.config.max_new_tokens,  # 100-token default truncates a real answer.
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            n=n,
            max_concurrent=self.config.max_concurrent,
        )
        # Adapter contract: n==1 -> list[str] (one per sample); n>1 -> list[list[str]] (n per sample).
        per_sample_gens = [[g] for g in generated] if n == 1 else generated
        # Adapter side channel (n>1): per-sample finish_reasons aligned 1:1 with the generations;
        # 'length' means the completion budget truncated that generation mid-reasoning.
        per_sample_reasons = getattr(self.model_adapter, 'last_finish_reasons', None) or []

        all_char_probs = []
        all_char_preds = []
        self.last_consensus = []
        for i, (reference, gens) in enumerate(zip(references, per_sample_gens)):
            reasons = list(per_sample_reasons[i]) if i < len(per_sample_reasons) else []
            reasons += [None] * (len(gens) - len(reasons))
            valid = []
            invalid = {'truncated': 0, 'empty': 0, 'not_verbatim': 0}
            for gen, reason in zip(gens, reasons):
                if self._echo_of(gen) == str(reference).strip():
                    valid.append(gen)
                elif reason == 'length':
                    invalid['truncated'] += 1
                elif not gen:
                    invalid['empty'] += 1
                else:
                    invalid['not_verbatim'] += 1
            entry = {
                'requested': n, 'valid': len(valid), 'temperature': self.config.temperature,
            }
            counts = {kind: count for kind, count in invalid.items() if count}
            if counts:
                entry['invalid'] = counts
            self.last_consensus.append(entry)
            if not valid:
                raise JudgeAnnotationError(
                    f'No judge generation echoed the answer verbatim '
                    f'({len(gens)} generation(s) all dropped); cannot annotate spans.'
                )
            sample_char_probs = torch.tensor(
                calculate_character_probabilities(valid, reference=reference)
            )
            all_char_probs.append(sample_char_probs)
            all_char_preds.append((sample_char_probs > self.threshold).long())

        # Expose sample 0's generations/spans for the UI (reads gens[0]/spans[0]).
        self.last_generations = list(per_sample_gens[0]) if per_sample_gens else []
        # `or ''`: a provider may return None content (e.g. exhausted reasoning budget) for one
        # generation while the sample still validates on the others.
        self.last_spans = [find_span_segments(g or '') for g in self.last_generations]

        char_probs = [prob.tolist() for prob in all_char_probs]
        char_preds = [pred.tolist() for pred in all_char_preds]

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids, char_preds, char_probs, binary=(self.config.num_classification_heads <= 2)
        )

        # Convert span annotations to character-level labels using shared utility
        char_labels = convert_spans_to_labels(labels, char_probs) if labels is not None else None

        return char_probs, char_preds, char_labels
