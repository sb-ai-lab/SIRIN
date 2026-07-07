from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch

from sirin.definitions import DetectionLevel, DataCollatorType
from sirin.detection.judging.judges.base import OpenAIJudgeBase
from sirin.detection.judging.judges.utils import (
    build_prompt_messages,
    calculate_character_probabilities,
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

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Uses OpenAI API for token-level classification with multiple generations.
        Calculates character probabilities from span tag consistency across generations.
        """
        samples, group_ids = self._split_context_samples(samples)
        formatted_input = build_prompt_messages(self.config, samples)

        all_generated_sequences = []
        generated_texts = self.model_adapter.sample(
            inputs=formatted_input,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            n=self.config.num_beams,
        )
        self.last_generations = list(generated_texts)
        self.last_spans = [find_span_segments(text) for text in generated_texts]
        sample_sequences = []
        for _ in range(self.config.num_beams):
            sample_sequences.append(generated_texts[0])
        all_generated_sequences.append(sample_sequences)

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
