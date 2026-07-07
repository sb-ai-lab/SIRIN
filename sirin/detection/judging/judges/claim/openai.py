from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
from loguru import logger as lg

from sirin.definitions import DetectionLevel
from sirin.detection.judging.judges.base import OpenAIJudgeBase
from sirin.detection.judging.judges.utils import build_prompt_messages
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

        results, logprobs_results = self.model_adapter.sample(
            inputs=formatted_input,
            max_tokens=1,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            return_logprobs=True,
            top_logprobs=2,
            **kwargs,
        )

        probs = []
        preds = []

        for idx, logprob_result in enumerate(logprobs_results):
            # models that omit logprobs get a nan score (not a crash); the verdict still holds.
            if logprob_result and logprob_result[0]:
                probs.append(-1 * logprob_result[0][0])
            else:
                probs.append(float('nan'))

            text = str(results[idx]).strip()
            preds.append(int(text) if text.isdigit() else 0)

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
                for split, pred, prob in zip(splitted_samples, sample_probs, sample_preds)
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
