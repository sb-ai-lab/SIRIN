import numpy as np
from typing import Dict, List, Tuple, Union, Optional

from sirin.models.detection import OpenAIJudgeConfig
from sirin.detection.judging.judges.base import JudgeAnnotationError, OpenAIJudgeBase
from sirin.detection.judging.judges.utils import build_prompt_messages
from sirin.definitions import DetectionLevel, DataCollatorType
from sirin.inference.adapters import ModelAdapterBase


class SequenceOpenAIJudge(OpenAIJudgeBase):
    """
    OpenAI API judge implementation for sequence-level hallucination detection.

    Architecture: Uses OpenAI API (e.g., GPT-4) instead of local HuggingFace models.
    No training support - inference only via API calls.
    """
    detection_level = DetectionLevel.SEQUENCE

    def __init__(self, config: OpenAIJudgeConfig, model_adapter: ModelAdapterBase):
        super().__init__(config=config, model_adapter=model_adapter)
        self.last_generations: list[str] | None = None

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Uses OpenAI API for sequence-level classification.
        Returns logprobs from API instead of running local model inference.
        """
        samples, group_ids = self._split_context_samples(samples)
        formatted_input = build_prompt_messages(self.config, samples)

        results, logprobs_results = self.model_adapter.sample(
            inputs=formatted_input,
            max_tokens=1,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            return_logprobs=True,
            top_logprobs=2,
            **kwargs
        )
        self.last_generations = list(results)

        probs = []
        preds = []

        num_classes = max(self.config.num_classification_heads, 2)
        for idx, logprob_result in enumerate(logprobs_results):
            # Some models omit logprobs: score becomes nan (not a crash); the verdict still holds.
            if logprob_result and logprob_result[0]:
                probs.append(-1 * logprob_result[0][0])
            else:
                probs.append(float('nan'))

            text = str(results[idx]).strip()
            if not (text.isdigit() and int(text) < num_classes):
                # Never fabricate a verdict: reasoning models spend the one-token budget on
                # thinking, so the first token is not the digit the prompt demands.
                raise JudgeAnnotationError(
                    f'The judge model did not answer with a bare class digit (got {text!r}). '
                    'Choose a judge model that returns the verdict as its first token; '
                    'reasoning models spend the one-token budget on thinking.'
                )
            preds.append(int(text))

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels
