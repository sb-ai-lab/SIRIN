from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from transformers import Trainer

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.judging.judges.utils import (
    format_dialogue_for_training,
    prepare_decoder_inputs_with_labels,
    build_prompt_messages,
    calibrate_and_compute_metrics,
    calculate_character_probabilities,
    create_char_binary_vector,
)
from sirin.detection.utils.token import convert_spans_to_labels
from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import HfJudgeConfig
from sirin.utils.hf import get_assistant_prefix


class TokenDecoderJudge(HfJudgeBase):
    """
    Decoder judge implementation for token-level hallucination detection.
    
    Uses generative decoder models with multiple beam samples to identify
    hallucinated character spans based on generation consistency.
    """
    
    detection_level = DetectionLevel.TOKEN
    data_collator_type = DataCollatorType.TOKEN
    trainer = Trainer

    def __init__(self, config: HfJudgeConfig, model_adapter: ModelAdapterBase):
        super().__init__(config=config, model_adapter=model_adapter)
        self.model_adapter.tokenizer.add_tokens(['[SPAN]', '[/SPAN]'], special_tokens=True)
        self.model_adapter.model.resize_token_embeddings(len(self.model_adapter.tokenizer))
        self.assistant_prefix = get_assistant_prefix(self.model_adapter._model_name)

    def detect(
        self, samples: Union[List[str], List[List[Dict]]], labels: Optional[np.ndarray] = None, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Architecture: Uses generative decoder model with multiple beam samples.
        Differs from sequence decoder by identifying character-level hallucination spans.
        Uses generation consistency across beams: characters wrapped in [SPAN] tags
        by multiple generations are marked as hallucinated.
        """
        samples, group_ids = self._split_context_samples(samples)

        self._check_truncation_warning(samples)

        formatted_input = build_prompt_messages(self.config, samples)

        preprocessed_input = self.model_adapter._preprocess_input(formatted_input)
        preprocessed_input = [
            f'{sample}{self.assistant_prefix}' for sample in preprocessed_input
        ]

        # Generate multiple sequences per sample for consistency checking
        generated_texts = self.model_adapter.sample(
            inputs=preprocessed_input,
            max_tokens=self.config.max_new_tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            num_return_sequences=self.config.num_beams,
            do_sample=True,
            pad_token_id=self.model_adapter.tokenizer.eos_token_id,
            eos_token_id=self.model_adapter.tokenizer.eos_token_id,
            **kwargs
        )

        # Group generated sequences by input sample
        all_generated_sequences = []
        num_beams = self.config.num_beams
        
        for i in range(len(samples)):
            start_idx = i * num_beams
            sample_sequences = generated_texts[start_idx:start_idx + num_beams]
            all_generated_sequences.append(sample_sequences)

        # Calculate character-level probabilities from span tag consistency
        all_char_probs = []
        all_char_preds = []

        for generated_texts in all_generated_sequences:
            sample_char_probs = calculate_character_probabilities(generated_texts)
            sample_char_probs = torch.tensor(sample_char_probs)
            all_char_probs.append(sample_char_probs)
            all_char_preds.append((sample_char_probs > self.threshold).long())

        char_probs = [prob.tolist() for prob in all_char_probs]
        char_preds = [pred.tolist() for pred in all_char_preds]

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids, char_preds, char_probs, binary=(self.config.num_classification_heads <= 2)
        )

        # Convert span annotations to character-level labels using shared utility
        char_labels = convert_spans_to_labels(labels, char_probs) if labels is not None else None

        return char_probs, char_preds, char_labels
        
    def _compute_metrics(self, eval_pred: Any) -> Dict[str, Any]:
        """
        Compute metrics for token-level decoder judge.
        
        Converts token-level logits into predicted span-tagged text (teacher-forced),
        then derives character-level binary vectors for metric computation.
        """
        logits = getattr(eval_pred, "predictions", eval_pred[0])
        labels = getattr(eval_pred, "label_ids", eval_pred[1])

        if isinstance(logits, (tuple, list)):
            logits = logits[0]

        pred_ids = np.argmax(logits, axis=-1)

        probs_list = []
        labels_list = []

        tokenizer = self.model_adapter.tokenizer
        for pred_ids_sample, labels_sample in zip(pred_ids, labels):
            active_mask = labels_sample != -100
            if not np.any(active_mask):
                continue

            label_ids = labels_sample[active_mask]
            pred_ids_active = pred_ids_sample[active_mask]

            label_text = tokenizer.decode(label_ids, skip_special_tokens=False)
            pred_text = tokenizer.decode(pred_ids_active, skip_special_tokens=False)

            label_vector = create_char_binary_vector(label_text)
            pred_vector = create_char_binary_vector(pred_text)

            if not label_vector or not pred_vector:
                continue

            min_len = min(len(label_vector), len(pred_vector))
            if min_len == 0:
                continue

            labels_list.append(np.array(label_vector[:min_len]))
            probs_list.append(np.array(pred_vector[:min_len], dtype=float))

        if not labels_list:
            return {}

        labels_flat = np.concatenate(labels_list)
        probs_flat = np.concatenate(probs_list)

        metrics, threshold = calibrate_and_compute_metrics(
            probs_flat,
            labels_flat,
            self.config,
            self.metrics_to_compute,
            is_binary=True,
        )
        self.threshold = threshold

        return metrics

    def _preprocess(self, samples: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess samples for token-level classification with decoder models."""
        inputs = samples[INPUT_COL]
        targets = samples[TARGET_COL]

        self._check_truncation_warning(inputs)

        # Format dialogue samples with system/user/assistant roles (with span wrapping)
        formatted_messages = format_dialogue_for_training(
            inputs, targets, self.config, is_token_level=True
        )

        # Prepare tokenized inputs with proper label masking
        return prepare_decoder_inputs_with_labels(
            formatted_messages, self.model_adapter, self.config
        )