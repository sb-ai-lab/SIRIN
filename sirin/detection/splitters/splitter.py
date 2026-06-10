from typing import Any, Dict, List, Optional, Tuple, Union
from collections import defaultdict
from copy import deepcopy

import datasets
import numpy as np
from scipy import stats

from sirin.definitions import AggregationMethod, SplitStrategy, GROUP_ID_COL
from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.detection.splitters.splits import *
from sirin.models.detection import SplitConfig
from sirin.inference.adapters import ModelAdapterBase


class SplitManager:
    """Class to split dataset samples and aggregate predictions."""

    def __init__(self, config: SplitConfig, split_response: bool = True):
        self.config = config
        self.split_response = int(split_response)
        self.splitter = self._get_splitter()

    def _get_splitter(self) -> TextSplitterBase:
        """Get the appropriate splitter based on configuration."""
        if self.config.strategy == SplitStrategy.SENTENCE:
            return SentenceSplitter(self.config)
        elif self.config.strategy == SplitStrategy.PARAGRAPH:
            return ParagraphSplitter(self.config)
        elif self.config.strategy == SplitStrategy.CHARACTER:
            return CharacterSplitter(self.config)
        elif self.config.strategy == SplitStrategy.LANGCHAIN:
            if not self.config.langchain_splitter_type:
                raise ValueError(
                    "langchain_splitter_type must be specified when using LANGCHAIN strategy"
                )
            return LangChainSplitter(self.config)
        elif self.config.strategy == SplitStrategy.ATOMIC:
            return ClaimSplitter(self.config)
        else:
            raise ValueError(f"Unknown split strategy: {self.config.strategy}")

    def split_dataset(
        self,
        dataset: datasets.Dataset,
        model_adapter: Optional[ModelAdapterBase] = None,
    ) -> datasets.Dataset:
        """
        Split each sample in the dataset based on the input content.
        Each split will have the same group ID as the original sample.

        Args:
            dataset: Input dataset with "input" column containing list of dicts with "content"

        Returns:
            Dataset with split samples, each having a "group_id" to track original sample
        """
        all_split_samples = []
        split_sources = [
            sample["input"][self.split_response]["content"] for sample in dataset
        ]
        splits = self.split_samples(split_sources, model_adapter)

        for idx, (split_contents, sample) in enumerate(zip(splits, dataset)):
            for split_idx, content in enumerate(split_contents):
                new_sample = deepcopy(sample)

                new_sample["input"][self.split_response]["content"] = content
                new_sample[GROUP_ID_COL] = idx
                new_sample["split_idx"] = split_idx
                new_sample["total_splits"] = len(split_contents)

                all_split_samples.append(new_sample)

        if all_split_samples:
            split_dataset = datasets.Dataset.from_list(all_split_samples)
        else:
            split_dataset = dataset.select([])

        return split_dataset

    def split_inputs(
        self,
        inputs: List[Dict[str, Any]],
        model_adapter: Optional[ModelAdapterBase] = None,
    ) -> List[Dict[str, Any]]:
        contents = [sample[self.split_response]["content"] for sample in inputs]

        all_split_samples = self.split_samples(contents, model_adapter)
        new_inputs = []

        for input_, splits in zip(inputs, all_split_samples):
            inputs_with_splits = []
            for split in splits:
                new_input = deepcopy(input_)
                new_input[self.split_response]["content"] = split
                inputs_with_splits.append(new_input)
            new_inputs.append(inputs_with_splits)
        return new_inputs

    def split_samples(
        self, samples, model_adapter: Optional[ModelAdapterBase] = None
    ) -> List[List[str]]:
        all_split_samples = self.splitter.split(samples, model_adapter)

        return all_split_samples

    def aggregate_predictions(
        self,
        group_ids: List[int],
        preds: List[List[int]],
        probs: List[List[float]],
        labels: Optional[Any] = None,
        binary: bool = True,
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Aggregate predictions with specific strategies.

        Args:
            group_ids: Group IDs for each prediction
            preds: Predictions for each chunk (can be scalars or variable-length arrays)
            probs: Probabilities for each chunk (can be scalars or variable-length arrays)
            labels: Optional labels per chunk; when provided, one label per group is returned (first in group).
            binary: Whether this is binary classification (default: True)

        Returns:
            Tuple of (preds, probs) as numpy arrays, or (preds, probs, labels) when labels is provided.
            For variable-length predictions (token-level), returns object arrays.

        Strategies:
        - VOTE: Majority vote on labels. Probs = Mean of all chunks.
        - MEAN: Mean of probabilities. Pred = Argmax of mean probs.
        - MAX: Select chunk with HIGHEST confidence. Return its exact pred/prob.
        - MIN: Select chunk with LOWEST confidence. Return its exact pred/prob.
        """
        grouped_predictions = defaultdict(list)
        grouped_probs = defaultdict(list)

        for group_id, pred, prob in zip(group_ids, preds, probs):
            grouped_predictions[group_id].append(pred)
            grouped_probs[group_id].append(prob)

        final_preds, final_probs = [], []
        for key in sorted(grouped_probs.keys()):
            group_pred = np.array(grouped_predictions[key])
            group_prob = np.array(grouped_probs[key])

            if binary:
                group_prob[group_pred == 0] = 1 - group_prob[group_pred == 0]

            if self.config.aggregation_method in [
                AggregationMethod.MAX,
                AggregationMethod.MIN,
            ]:
                if self.config.aggregation_method == AggregationMethod.MAX:
                    selected_idx = np.argmax(group_prob, axis=0)
                else:
                    selected_idx = np.argmin(group_prob, axis=0)

                selected_idx_expanded = np.expand_dims(selected_idx, axis=0)
                best_pred = np.take_along_axis(
                    group_pred, selected_idx_expanded, axis=0
                ).squeeze(axis=0)
                best_prob = np.take_along_axis(
                    group_prob, selected_idx_expanded, axis=0
                ).squeeze(axis=0)

                final_preds.append(best_pred)
                final_probs.append(best_prob)

            elif self.config.aggregation_method == AggregationMethod.VOTE:
                mode_res = stats.mode(group_pred, axis=0, keepdims=True)

                final_preds.append(mode_res.mode.squeeze(axis=0))
                final_probs.append(np.mean(group_prob, axis=0))

            elif self.config.aggregation_method == AggregationMethod.MEAN:
                agg_prob = np.mean(group_prob, axis=0)
                final_probs.append(agg_prob)
                final_preds.append(np.argmax(agg_prob, axis=0))

        try:
            final_preds = np.array(final_preds)
            final_probs = np.array(final_probs)
    
            if binary and final_probs.dtype != object:
                final_probs = np.where(final_preds == 0, 1 - final_probs, final_probs)

        except (ValueError, TypeError):
            final_preds = np.array(final_preds, dtype=object)
            final_probs = np.array(final_probs, dtype=object)
            
            if binary:
                final_probs = np.array([
                    np.where(pred == 0, 1 - prob, prob)
                    for pred, prob in zip(final_preds, final_probs)
                ], dtype=object)

        if labels is not None:
            grouped_labels = defaultdict(list)
            for group_id, label in zip(group_ids, labels):
                grouped_labels[group_id].append(label)
            final_labels = np.array(
                [grouped_labels[key][0] for key in sorted(grouped_labels.keys())]
            )
            return final_preds, final_probs, final_labels
        
        return final_preds, final_probs
