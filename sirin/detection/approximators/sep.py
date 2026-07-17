import inspect
from typing import Dict, List, Optional

import numpy as np
import torch
from loguru import logger as lg

import sirin.detection._lm_polygraph_compat  # noqa: F401 — must be before lm-polygraph imports
from sirin.detection.utils.math import binarize_entropy
from sirin.inference.adapters import ModelAdapterBase
from sirin.detection.approximators import TargetApproximatorBase
from sirin.metrics.classification import calculate_classification_metrics
from sirin.definitions import ClassificationMetric


def _log_roc_auc(labels: List[int], scores) -> None:
    try:
        lg.info(
            f"ROC_AUC_SCORE {calculate_classification_metrics(labels, scores, metrics=[ClassificationMetric.ROC_AUC])} #"
        )
    except ValueError as e:
        lg.debug(f"ROC-AUC logging skipped: {e}")


class SEPTargetApproximator(TargetApproximatorBase):
    def __init__(
        self,
        extractor: ModelAdapterBase,
        num_return_sequences: int = 5,
        sampling_kwargs: Optional[Dict] = None,
    ):
        super().__init__(extractor=extractor)
        from lm_polygraph.utils.deberta import Deberta

        self.nli_model = Deberta(batch_size=8)
        self.stats = {}
        self.num_return_sequences = num_return_sequences
        self.sampling_kwargs = sampling_kwargs or {}

    def _ensure_logprob_support(self) -> None:
        params = inspect.signature(self.extractor.sample).parameters
        supports_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in params.values()
        )
        if 'return_logprobs' not in params and not supports_kwargs:
            raise NotImplementedError(
                f"SEP requires an adapter with return_logprobs support; got {type(self.extractor).__name__}"
            )

    def _sample_with_logprobs(self, samples: List[List[Dict]]):
        self._ensure_logprob_support()
        return self.extractor.sample(
            samples,
            return_logprobs=True,
            num_return_sequences=self.num_return_sequences,
            max_tokens=100,
            temperature=1.0,
            **getattr(self, 'sampling_kwargs', {}),
        )

    @staticmethod
    def _is_token_logprob(token_logprob) -> bool:
        if isinstance(token_logprob, (int, float, np.floating)):
            return True
        if not isinstance(token_logprob, (tuple, list)) or len(token_logprob) == 0:
            return False
        first = token_logprob[0]
        return isinstance(first, (str, int, float, np.floating))

    @staticmethod
    def _is_sequence_logprobs(value) -> bool:
        return isinstance(value, list) and (
            len(value) == 0 or SEPTargetApproximator._is_token_logprob(value[0])
        )

    @staticmethod
    def _primary_logprob(token_logprob) -> float:
        if isinstance(token_logprob, (int, float, np.floating)):
            return float(token_logprob)
        if len(token_logprob) >= 2 and isinstance(token_logprob[0], str):
            return float(token_logprob[1])
        return float(token_logprob[0])

    def _normalize_sample_outputs(self, responses, logits, sample_count: int):
        if responses and isinstance(responses[0], str):
            if (
                self.num_return_sequences > 1
                and len(responses) == sample_count * self.num_return_sequences
            ):
                sample_texts = [
                    responses[i : i + self.num_return_sequences]
                    for i in range(0, len(responses), self.num_return_sequences)
                ]
            else:
                sample_texts = [[response] for response in responses]
        else:
            sample_texts = responses

        if (
            logits
            and self.num_return_sequences > 1
            and len(logits) == sample_count * self.num_return_sequences
            and all(self._is_sequence_logprobs(logits_for_sample) for logits_for_sample in logits)
        ):
            sample_logits = [
                logits[i : i + self.num_return_sequences]
                for i in range(0, len(logits), self.num_return_sequences)
            ]
        else:
            sample_logits = []
            for logits_for_sample in logits:
                if self._is_sequence_logprobs(logits_for_sample):
                    sample_logits.append([logits_for_sample])
                else:
                    sample_logits.append(logits_for_sample)

        return sample_texts, self._reshape_logprobs(sample_logits)

    @staticmethod
    def _reshape_logprobs(logits) -> List[List[float]]:
        """Convert adapter logprob output to per-sequence token logprob sums."""
        result = []
        for gen in logits:
            seq_scores = []
            for sample in gen:
                if not sample:
                    seq_scores.append(0.0)
                    continue
                seq_scores.append(
                    float(
                        np.array(
                            [
                                SEPTargetApproximator._primary_logprob(token)
                                for token in sample
                            ]
                        ).sum()
                    )
                )
            result.append(seq_scores)
        return result

    @staticmethod
    def _call_stat_calculator(calculator, *args):
        signature = inspect.signature(calculator.__call__)
        if any(
            param.kind == inspect.Parameter.VAR_POSITIONAL
            for param in signature.parameters.values()
        ):
            return calculator(*args)

        positional_count = len(
            [
                param
                for param in signature.parameters.values()
                if param.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
        )
        return calculator(*args[:positional_count])

    def _compute_semantic_entropy(
        self, samples: List[List[Dict]], labels: Optional[List[int]] = None
    ) -> List[int]:
        from lm_polygraph.estimators import SemanticEntropy
        from lm_polygraph.stat_calculators import (
            SemanticClassesCalculator,
            SemanticMatrixCalculator,
        )

        responses, logits = self._sample_with_logprobs(samples)
        sample_texts, logprob_sums = self._normalize_sample_outputs(
            responses,
            logits,
            sample_count=len(samples),
        )

        new_stats = {
            'sample_texts': sample_texts,
            'sample_log_probs': logprob_sums,
        }
        self.stats.update(new_stats)

        semantic_matrix_calculator = SemanticMatrixCalculator(nli_model=self.nli_model)
        semantic_matrix = self._call_stat_calculator(
            semantic_matrix_calculator,
            self.stats,
            samples,
            self.extractor,
        )
        self.stats.update(semantic_matrix)

        semantic_classes_calculator = SemanticClassesCalculator()
        semantic_classes = self._call_stat_calculator(
            semantic_classes_calculator,
            self.stats,
            samples,
            self.extractor,
        )
        self.stats.update(semantic_classes)

        semantic_entropy_calculator = SemanticEntropy()
        semantic_entropy = semantic_entropy_calculator(self.stats)

        new_labels, split = binarize_entropy(torch.tensor(semantic_entropy))
        self.split = split

        if labels is not None:
            _log_roc_auc(labels, semantic_entropy)

        return new_labels.tolist()

    def fit(
        self, samples: List[List[Dict]], labels: Optional[List[int]] = None
    ) -> List[int]:
        return self._compute_semantic_entropy(samples, labels)

    def __call__(
        self, samples: List[List[Dict]], labels: Optional[List[int]] = None
    ) -> List[int]:
        return self._compute_semantic_entropy(samples, labels)
