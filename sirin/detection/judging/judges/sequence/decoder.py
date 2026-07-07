from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from loguru import logger as lg
from transformers import EvalPrediction

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    format_dialogue_for_training,
    prepare_decoder_inputs_with_labels,
    build_prompt_messages,
)
from sirin.detection.judging.training import SequenceDecoderJudgeTrainer
from sirin.detection.utils.basic import calibrate_threshold
from sirin.inference.adapters import HfModelAdapter
from sirin.metrics.classification import calculate_classification_metrics
from sirin.models.detection import HfJudgeConfig
from sirin.utils.hf import get_assistant_prefix


class SequenceDecoderJudge(HfJudgeBase):
    """
    Decoder judge implementation for sequence-level hallucination detection.

    Uses generative decoder models (e.g., Llama, GPT) with next-token prediction.
    Predicts a class token (0, 1, etc.) for the entire sequence.
    """

    detection_level = DetectionLevel.SEQUENCE
    data_collator_type = DataCollatorType.TOKEN
    trainer = SequenceDecoderJudgeTrainer

    def __init__(self, config: HfJudgeConfig, model_adapter: HfModelAdapter):
        super().__init__(config=config, model_adapter=model_adapter)
        self.assistant_prefix = get_assistant_prefix(self.model_adapter._model_name)
        self.last_generations: list[str] | None = None  # generated text is not locally decoded here.

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Architecture: Uses generative decoder model (e.g., Llama, GPT).
        Differs from encoder judges by using next-token prediction instead of classification head.
        Predicts a class token (0, 1, etc.) as the first generated token.
        """
        samples, group_ids = self._split_context_samples(samples)

        self._check_truncation_warning(samples)

        formatted_input = build_prompt_messages(self.config, samples)

        preprocessed_input = self.model_adapter._preprocess_input(formatted_input)
        preprocessed_input = [
            f"{sample}{self.assistant_prefix}" for sample in preprocessed_input
        ]

        inputs = self.model_adapter.tokenizer(
            preprocessed_input,
            return_tensors=self.config.return_tensors,
            truncation=self.model_adapter.config.truncation,
            padding=self.model_adapter.config.padding,
        ).to(self.config.device)

        # Decoder approach: Generate next token and extract logits for class tokens
        with torch.no_grad():
            outputs = self.model_adapter.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                do_sample=False,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                pad_token_id=self.model_adapter.tokenizer.eos_token_id,
                eos_token_id=self.model_adapter.tokenizer.eos_token_id,
                return_dict_in_generate=True,
                output_scores=True,
            )

        # Extract logits for class tokens (e.g., "0", "1") from first generated position
        first_token_logits = outputs.scores[0]
        selected_logits = first_token_logits[:, self.class_token_ids]
        probs, preds = self._logits_to_probs_preds(selected_logits)

        probs = probs.tolist()
        preds = preds.tolist()

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels

    def _compute_metrics(self, eval_pred: EvalPrediction) -> Dict[str, Any]:
        """Compute metrics for sequence-level classification."""
        probs = eval_pred.predictions
        labels = eval_pred.label_ids

        if self.config.num_classification_heads == 2:
            self.threshold = calibrate_threshold(
                probs,
                labels,
                self.config.threshold_method,
                self.config.threshold_percentile,
                self.config.fixed_threshold,
            )
            preds = (probs > self.threshold).astype(int)
        else:
            self.threshold = None
            preds = np.argmax(probs, axis=1)

        metrics = calculate_classification_metrics(
            labels,
            probs,
            preds,
            metrics=self.metrics_to_compute,
        )
        lg.info(f"Evaluation metrics: {metrics}")
        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for sequence-level classification with decoder models."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        # Format dialogue samples with system/user/assistant roles
        formatted_messages = format_dialogue_for_training(
            inputs, targets, self.config, is_token_level=False
        )

        # Prepare tokenized inputs with proper label masking
        return prepare_decoder_inputs_with_labels(
            formatted_messages, self.model_adapter, self.config
        )
