import numpy as np
from typing import Dict, List, Tuple, Union, Optional

from sirin.models.detection import OpenAIJudgeConfig
from sirin.detection.judging.judges.base import OpenAIJudgeBase
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

        probs = []
        preds = []
        
        for logprob_result in logprobs_results:
            most_likely_logprob = -1*logprob_result[0][0]
            probs.append(most_likely_logprob)
            
            pred = int(results[logprobs_results.index(logprob_result)]) if results[logprobs_results.index(logprob_result)].isdigit() else 0
            preds.append(pred)

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels
