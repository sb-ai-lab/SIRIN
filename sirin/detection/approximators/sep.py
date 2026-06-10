from typing import Dict, List, Optional

import numpy as np
import torch
from loguru import logger as lg

from sirin.detection.utils.math import binarize_entropy
from sirin.inference.adapters import ModelAdapterBase
from sirin.detection.approximators import TargetApproximatorBase
from sirin.metrics.classification import calculate_classification_metrics
from sirin.definitions import ClassificationMetric


class SEPTargetApproximator(TargetApproximatorBase):
    def __init__(self, extractor: ModelAdapterBase):
        super().__init__(extractor=extractor)
        from lm_polygraph.utils.deberta import Deberta

        self.nli_model = Deberta(batch_size=8)
        self.stats = {}

    def fit(
        self, samples: List[List[Dict]], labels: Optional[List[int]] = None
    ) -> List[int]:
        from lm_polygraph.estimators import SemanticEntropy
        from lm_polygraph.stat_calculators import (
            SemanticClassesCalculator,
            SemanticMatrixCalculator,
        )

        responses, logits = self.extractor.generate_with_logprobs(samples)

        new_stats = self.stats
        if 'sample_texts' not in new_stats:
            new_stats['sample_texts'] = []
            new_stats['sample_log_probs'] = []
        new_stats['sample_texts'].extend(
            [[sample for sample in gen] for gen in responses]
        )
        new_stats['sample_log_probs'].extend(
            [
                [np.array([token[0] for token in sample]).sum() for sample in gen]
                for gen in logits
            ]
        )

        semantic_matrix_calculator = SemanticMatrixCalculator(nli_model=self.nli_model)
        semantic_matrix = semantic_matrix_calculator(new_stats, samples)
        new_stats.update(semantic_matrix)

        semantic_classes_calculator = SemanticClassesCalculator()
        semantic_classes = semantic_classes_calculator(new_stats)
        new_stats.update(semantic_classes)

        semantic_entropy_calculator = SemanticEntropy()
        semantic_entropy = semantic_entropy_calculator(new_stats)

        new_labels, split = binarize_entropy(torch.tensor(semantic_entropy))
        self.split = split

        if labels is not None:
            try:
                lg.info(
                    f"ROC_AUC_SCORE {calculate_classification_metrics(labels, semantic_entropy, metrics=[ClassificationMetric.ROC_AUC])} #"
                )
            except ValueError:
                pass

        return new_labels.tolist()

    def __call__(
        self, samples: List[List[Dict]], labels: Optional[List[int]] = None
    ) -> List[int]:
        """
        Compute semantic entropy labels for each sample in the dataset.

        Args:
            samples: A list of dictionaries representing input data. Each dictionary
                     should have keys like "chat_in", "target", etc.

        Returns:
            List of binary labels derived from semantic entropy.
        """
        from lm_polygraph.estimators import SemanticEntropy
        from lm_polygraph.stat_calculators import (
            SemanticClassesCalculator,
            SemanticMatrixCalculator,
        )

        responses, logits = self.extractor.generate_with_logprobs(samples)

        self.stats.update(
            {
                'sample_texts': [[sample for sample in gen] for gen in responses],
                'sample_log_probs': [
                    [np.array([token[0] for token in sample]).sum() for sample in gen]
                    for gen in logits
                ],
            }
        )

        semantic_matrix_calculator = SemanticMatrixCalculator(nli_model=self.nli_model)
        semantic_matrix = semantic_matrix_calculator(self.stats, samples)
        self.stats.update(semantic_matrix)

        semantic_classes_calculator = SemanticClassesCalculator()
        semantic_classes = semantic_classes_calculator(self.stats)
        self.stats.update(semantic_classes)

        semantic_entropy_calculator = SemanticEntropy()
        semantic_entropy = semantic_entropy_calculator(self.stats)

        new_labels, split = binarize_entropy(torch.tensor(semantic_entropy))
        self.split = split

        if labels is not None:
            try:
                lg.info(
                    f"ROC_AUC_SCORE {calculate_classification_metrics(labels, semantic_entropy, metrics=[ClassificationMetric.ROC_AUC])} #"
                )
            except ValueError:
                pass

        return new_labels.tolist()
