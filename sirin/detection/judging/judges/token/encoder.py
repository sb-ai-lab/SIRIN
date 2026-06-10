from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from loguru import logger as lg
from transformers import EvalPrediction, Trainer

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    process_logits_to_probs,
    calibrate_and_compute_metrics,
    rearrange_token_predictions_with_indices,
    repeat_labels_with_offsets,
)
from sirin.detection.utils.token import get_token_labels, get_answer_offsets
from sirin.models.detection import HfJudgeConfig
from sirin.inference.adapters import HfModelAdapter


class TokenEncoderJudge(HfJudgeBase):
    """
    Encoder judge implementation for token-level hallucination detection.
    
    Uses AutoModelForTokenClassification with encoder embeddings + token classification head.
    Handles per-token predictions with offset mapping for character-level spans.
    """

    detection_level = DetectionLevel.TOKEN
    data_collator_type = DataCollatorType.TOKEN
    trainer = Trainer

    def __init__(self, config: HfJudgeConfig, model_adapter: HfModelAdapter):
        super().__init__(config=config, model_adapter=model_adapter)
        self.device = self.config.device
        if self.model_adapter.tokenizer.pad_token is None:
            self.model_adapter.tokenizer.pad_token = self.model_adapter.tokenizer.eos_token

    def detect(
        self,
        samples: List[str],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects hallucinations at token level using encoder embeddings.
        For binary: Returns 0 (no hallucination) or 1 (hallucination)

        Architecture: Uses encoder embeddings with token classification head (AutoModelForTokenClassification).
        Differs from sequence-level which returns one prediction per sample.
        This approach requires offset mapping to align token predictions with character spans.
        """
        samples, group_ids = self._split_context_samples(samples)

        self._check_truncation_warning(samples)

        # Token-level approach: Get character offsets for each token in answer
        offsets, _, answer_indices = get_answer_offsets(samples, self.model_adapter)

        if labels is not None:
            labels = get_token_labels(offsets, labels)

        # Get per-token logits from token classification head
        model_states = self.model_adapter.generate_hiddens(
            inputs=samples,
            return_hiddens=False,
            return_logits=True,
            **kwargs,
        )

        logits = model_states.logits

        probs, preds = self._logits_to_probs_preds(logits)
        probs = probs.cpu()
        preds = preds.cpu()

        offsets = [torch.tensor(offset).long() for offset in offsets]

        # Rearrange token predictions to character-level using shared utility
        char_probs, char_preds = rearrange_token_predictions_with_indices(
            probs, preds, offsets, answer_indices
        )

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids, char_preds, char_probs, binary=(self.config.num_classification_heads <= 2)
        )

        if labels is not None:
            repeats = [offset[:, 1] - offset[:, 0] for offset in offsets]
            char_labels = repeat_labels_with_offsets(labels, repeats)
        else:
            char_labels = None

        return char_probs, char_preds, char_labels

    def _compute_metrics(self, eval_pred: EvalPrediction) -> Dict[str, Any]:
        """
        Compute metrics for token-level classification.
        
        Filters out padding tokens (-100) before computing metrics.
        """
        logits, labels = eval_pred
        
        # Convert logits to probabilities, filtering padding tokens
        probs, active_labels = process_logits_to_probs(logits, labels, filter_padding=True)
        
        # Token-level is always binary classification
        metrics, threshold = calibrate_and_compute_metrics(
            probs, active_labels, self.config, self.metrics_to_compute, is_binary=True
        )
        self.threshold = threshold
        
        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for token-level classification."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        answer_offsets, tokenized, _ = get_answer_offsets(inputs, self.model_adapter)
        labels_raw = get_token_labels(answer_offsets=answer_offsets, target_spans=targets)

        labels = [[-100] * len(sample) for sample in tokenized['input_ids']]
        for i in range(len(labels)):
            labels[i][-len(labels_raw[i]):] = labels_raw[i]

        tokenized['labels'] = labels

        return tokenized
