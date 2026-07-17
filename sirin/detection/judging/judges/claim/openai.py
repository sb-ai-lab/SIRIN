from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from loguru import logger as lg

from sirin.definitions import DetectionLevel
from sirin.detection.judging.judges.base import OpenAIJudgeBase
from sirin.detection.judging.judges.utils import (
    build_prompt_messages,
    probability_of_positive_class,
    sample_with_logprobs_fallback,
)
from sirin.detection.splitters import SplitManager
from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import OpenAIJudgeConfig, SplitConfig


class ClaimOpenAIJudge(OpenAIJudgeBase):
    """
    OpenAI API judge implementation for claim-level hallucination detection.

    Decomposes each response into atomic claims via SplitManager, classifies
    each claim independently via the OpenAI API, then re-aggregates per-claim
    predictions back to response level. No training support.
    """

    detection_level = DetectionLevel.CLAIM

    def __init__(
        self,
        config: OpenAIJudgeConfig,
        model_adapter: ModelAdapterBase,
        response_splitter_config: SplitConfig,
        split_model: Optional[ModelAdapterBase] = None,
    ):
        super().__init__(config=config, model_adapter=model_adapter)
        self.response_splitter_config = response_splitter_config
        self.response_splitter = SplitManager(config=response_splitter_config)
        self.split_model = split_model or model_adapter

    def detect(
        self,
        samples: Union[List[str], List[List[Dict]]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Detects hallucinations at claim level using the OpenAI API.

        Each response is split into atomic claims, classified independently
        via API logprobs, then predictions are re-aggregated to response level.
        """
        original_samples = list(samples)

        samples_fact_splits = self.response_splitter.split_inputs(
            samples, self.split_model
        )
        response_group_ids = []
        for index, splits in enumerate(samples_fact_splits):
            response_group_ids.extend([index] * len(splits))
        samples = [split for splits in samples_fact_splits for split in splits]

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
                **kwargs,
            )

        results, logprobs_results = sample_with_logprobs_fallback(_sample)

        probs = []
        preds = []

        num_classes = max(self.config.num_classification_heads, 2)
        binary = num_classes <= 2
        for idx, logprob_result in enumerate(logprobs_results):
            # See `SequenceOpenAIJudge.detect`: the score has to be P(hallucinated) read
            # off the class token, not the top token's surprisal. No class token in the
            # top-k / logprobs omitted / multiclass -> nan; the verdict still holds.
            prob = probability_of_positive_class(logprob_result) if binary else None
            probs.append(float('nan') if prob is None else prob)

            text = str(results[idx]).strip()
            # First valid class digit anywhere in the answer; decorated answers ("1.",
            # "**0**") no longer collapse to the negative class. Claims default to 0
            # rather than raising: one unreadable claim should not sink the response.
            preds.append(
                next((int(c) for c in text if c.isdigit() and int(c) < num_classes), 0)
            )

        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        overall_preds, overall_probs = self.response_splitter.aggregate_predictions(
            response_group_ids,
            preds,
            probs,
            binary=(self.config.num_classification_heads <= 2),
        )

        results = []
        for sample_idx, sample in enumerate(original_samples):
            sample_mask = [
                i for i, gid in enumerate(response_group_ids) if gid == sample_idx
            ]
            splitted_samples = samples_fact_splits[sample_idx]
            sample_probs = [probs[i] for i in sample_mask]
            sample_preds = [preds[i] for i in sample_mask]
            facts = [
                {"fact": split[1]["content"], "pred": pred, "prob": prob}
                for split, pred, prob in zip(splitted_samples, sample_preds, sample_probs)
            ]
            results.append(
                {
                    "sample": sample,
                    "overall_pred": overall_preds[sample_idx],
                    "overall_prob": overall_probs[sample_idx],
                    "facts": facts,
                }
            )
        self.claim_results = results

        return overall_probs, overall_preds, labels

    def _save_config(self, save_dir: Path):
        super()._save_config(save_dir)
        joblib.dump(self.response_splitter_config, save_dir / "splitter_config.joblib")
        lg.info(f"Saved splitter config to {save_dir / 'splitter_config.joblib'}")

    def _load_config(self, load_dir: Path):
        super()._load_config(load_dir)
        splitter_config_path = load_dir / "splitter_config.joblib"
        if splitter_config_path.exists():
            self.response_splitter_config = joblib.load(splitter_config_path)
            self.response_splitter = SplitManager(config=self.response_splitter_config)
            lg.info(f"Loaded splitter config from {splitter_config_path}")
