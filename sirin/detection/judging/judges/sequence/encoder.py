from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from loguru import logger as lg
from transformers import EvalPrediction, Trainer

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    process_logits_to_probs,
    calibrate_and_compute_metrics,
)
from sirin.models.detection import HfJudgeConfig
from sirin.inference.adapters import HfModelAdapter


class SequenceEncoderJudge(HfJudgeBase):
    """
    Encoder judge implementation for sequence-level hallucination detection.

    Uses AutoModelForSequenceClassification with encoder embeddings + classification head.
    """

    detection_level = DetectionLevel.SEQUENCE
    data_collator_type = DataCollatorType.PADDING
    trainer = Trainer

    def __init__(self, config: HfJudgeConfig, model_adapter: HfModelAdapter):
        super().__init__(config=config, model_adapter=model_adapter)
        self.device = self.config.device
        if self.model_adapter.tokenizer.pad_token is None:
            self.model_adapter.tokenizer.pad_token = (
                self.model_adapter.tokenizer.eos_token
            )

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects hallucinations at sequence level using encoder embeddings.
        For binary: Returns 0 (no hallucination) or 1 (hallucination)
        For multiclass: Returns predicted class index

        Architecture: Uses encoder embeddings with classification head (AutoModelForSequenceClassification).
        This differs from decoder judges which use generative models with next-token prediction.
        """
        samples, group_ids = self._split_context_samples(samples)

        self._check_truncation_warning(samples)

        # Encoder approach: Get logits directly from classification head
        model_states = self.model_adapter.generate_hiddens(
            inputs=samples,
            return_hiddens=False,
            return_logits=True,
        )

        logits = model_states.logits

        probs, preds = self._logits_to_probs_preds(logits)

        probs = probs.tolist()
        preds = preds.tolist()

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels

    def _compute_metrics(self, eval_pred: EvalPrediction) -> Dict[str, Any]:
        """Compute metrics for sequence-level classification."""
        logits, labels = eval_pred

        # Convert logits to probabilities (handles binary/multiclass)
        probs, _ = process_logits_to_probs(logits, labels, filter_padding=False)

        # Calibrate threshold and compute metrics
        is_binary = logits.shape[-1] <= 2
        metrics, threshold = calibrate_and_compute_metrics(
            probs, labels, self.config, self.metrics_to_compute, is_binary
        )
        self.threshold = threshold

        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for sequence-level classification."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        processed_inputs = self.model_adapter._preprocess_input(inputs)

        tokenized = self.model_adapter.tokenizer(
            processed_inputs,
            padding=False,
            truncation=self.model_adapter.config.truncation,
            add_special_tokens=False,
        )

        tokenized["labels"] = targets

        return tokenized
