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

        def _sample(return_logprobs: bool):
            return self.model_adapter.sample(
                inputs=formatted_input,
                max_tokens=self.config.verdict_max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                return_logprobs=return_logprobs,
                top_logprobs=2,
                **kwargs
            )

        try:
            results, logprobs_results = _sample(return_logprobs=True)
        except Exception as exc:
            # Some providers reject logprobs outright (400): retry once without them and
            # keep the honest no-score verdict (nan). Anything else propagates unchanged.
            try:
                import openai
                logprobs_rejected = (
                    isinstance(exc, openai.BadRequestError)
                    and 'logprob' in str(exc).lower()
                )
            except ImportError:
                logprobs_rejected = False
            if not logprobs_rejected:
                raise
            results = _sample(return_logprobs=False)
            logprobs_results = [None] * len(results)
        self.last_generations = list(results)

        probs = []
        preds = []

        num_classes = max(self.config.num_classification_heads, 2)
        for idx, logprob_result in enumerate(logprobs_results):
            text = str(results[idx]).strip()
            # Reasoning models return prose in content; take the first valid class digit.
            digit = next(
                (int(c) for c in text if c.isdigit() and int(c) < num_classes), None
            )
            if digit is None:
                # Never fabricate a verdict when no valid class digit appears anywhere.
                raise JudgeAnnotationError(
                    f'The judge model did not answer with a bare class digit and no class '
                    f'digit appears anywhere in its answer (got {text!r}). Choose a judge '
                    'model that states the verdict digit, or raise verdict_max_tokens '
                    f'(currently {self.config.verdict_max_tokens}) so a reasoning model '
                    'can finish thinking before the digit.'
                )
            preds.append(digit)
            # The adapter's logprobs carry floats only (no token text), so the first-token
            # logprob is provably the digit's only when the whole answer IS the digit.
            # Some models also omit logprobs entirely. Either way: nan, verdict still holds.
            if logprob_result and logprob_result[0] and text == str(digit):
                probs.append(-1 * logprob_result[0][0])
            else:
                probs.append(float('nan'))

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels
