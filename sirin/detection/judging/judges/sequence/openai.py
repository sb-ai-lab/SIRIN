import re
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from sirin.definitions import DataCollatorType, DetectionLevel
from sirin.detection.judging.judges.base import JudgeAnnotationError, OpenAIJudgeBase
from sirin.detection.judging.judges.utils import (
    build_prompt_messages,
    format_dialogue_samples,
    parse_binary_prediction,
    probability_of_positive_class,
)
from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import OpenAIJudgeConfig


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
                top_logprobs=self.config.top_logprobs,
                max_concurrent=self.config.max_concurrent,
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
        binary = num_classes <= 2
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
            # `probs` must be P(hallucinated), read off the class token's own logprob and
            # renormalized over the pair. Scoring by the top token's surprisal instead makes
            # a confident "0" and a confident "1" indistinguishable, which pins AUROC at
            # chance. When no class token appears in the top-k (or logprobs were rejected /
            # the task is multiclass): nan — no fabricated score, the verdict still holds.
            prob = probability_of_positive_class(logprob_result) if binary else None
            probs.append(float('nan') if prob is None else prob)

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels


# "1 87" / "0, 40" / "**1** (95%)" -- a digit, then the first integer after it.
_LABEL_CONFIDENCE = re.compile(r'([01])\D{0,8}?(\d{1,3})')


def parse_label_and_confidence(text: Optional[str]) -> Tuple[int, float]:
    """Read a verbalized ``"<label> <confidence 0-100>"`` answer into (pred, P(halluc.)).

    Confidence is stated *in the model's own label*, so it has to be flipped for the
    negative class: "0 90" means 90% sure it is grounded, i.e. P(hallucinated) = 0.10.
    An unparseable confidence degrades to the hard prediction (0.0 or 1.0) rather than a
    fabricated score.
    """
    if not text:
        return 0, 0.0

    match = _LABEL_CONFIDENCE.search(text.strip())
    if match is None:
        pred = parse_binary_prediction(text)
        return pred, float(pred)

    pred = int(match.group(1))
    confidence = min(100, max(0, int(match.group(2)))) / 100.0
    return pred, confidence if pred == 1 else 1.0 - confidence


class SequenceOpenAIVerbalizedJudge(OpenAIJudgeBase):
    """Sequence-level API judge for endpoints that expose no logprobs.

    Asks the model to state its own confidence alongside the label, so a threshold-free
    score (AUROC / AP) is still available. The score is coarser than a logprob -- models
    cluster their verbalized confidence on round numbers like 90 and 95 -- so prefer
    `SequenceOpenAIJudge` whenever the provider returns logprobs.
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
        samples, group_ids = self._split_context_samples(samples)
        formatted_samples = format_dialogue_samples(self.config, samples)
        formatted_input = [
            [
                {'role': 'system', 'content': self.config.confidence_system_prompt},
                {'role': 'user', 'content': self.config.confidence_user_prompt.format(sample=sample)},
            ]
            for sample in formatted_samples
        ]

        results = self.model_adapter.sample(
            inputs=formatted_input,
            max_tokens=self.config.verdict_max_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_concurrent=self.config.max_concurrent,
            **kwargs,
        )
        self.last_generations = list(results)

        parsed = [parse_label_and_confidence(text) for text in results]
        preds = [pred for pred, _ in parsed]
        probs = [prob for _, prob in parsed]

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels
