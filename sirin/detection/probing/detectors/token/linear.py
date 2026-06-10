from typing import List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader
from loguru import logger as lg
from pathlib import Path

from sirin.classification import LinearClassifier
from sirin.definitions import DetectionLevel
from sirin.detection.base import LoggerBase
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.probing.detectors.utils.detection import (
    check_features_for_nan_with_indices,
    compute_token_cumulative_lengths,
    rearrange_token_predictions,
)
from sirin.detection.utils.token import convert_spans_to_labels
from sirin.detection.probing.detectors.utils.training import setup_linear_model_config
from sirin.detection.probing.training.trainers import (
    BinaryHiddenStatesClassifierTrainer,
    MultiClassHiddenStatesClassifierTrainer,
)
from sirin.detection.processors.base import FeatureProcessorBase
from sirin.models.detection import (
    ProbingDetectorConfig,
    DetectionResult,
    TrainingArgsConfig,
)


class TokenLinearProbingDetector(ProbingDetectorBase):
    """Pooling probing detector"""

    detection_level = DetectionLevel.TOKEN

    def __init__(
        self, config: ProbingDetectorConfig, feature_processor: FeatureProcessorBase
    ):
        super().__init__(config=config, feature_processor=feature_processor)
        if config.num_classification_heads <= 2:
            self.trainer = BinaryHiddenStatesClassifierTrainer(self._context_splitter)
        else:
            self.trainer = MultiClassHiddenStatesClassifierTrainer(
                self._context_splitter
            )

    def detect(
        self,
        samples: List[str],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect with proper scaling and compression handling."""
        samples, group_ids = self._split_context_samples(samples)

        features, answer_indices = self.feature_processor(samples)
        check_features_for_nan_with_indices(features, samples, answer_indices)

        # Compute cumulative token lengths for slicing
        all_lengths = compute_token_cumulative_lengths(features)

        features, masks, offsets, _ = self._process_token_features(
            features, samples, answer_indices, labels
        )

        features = [feature.to(self.device) for feature in features]
        masks = [mask.to(self.device) for mask in masks]

        logits = self.model(features, masks)

        token_probs, token_preds = self._logits_to_probs_preds(logits)

        # Rearrange token predictions to character-level per sample
        char_probs, char_preds = rearrange_token_predictions(
            token_probs, token_preds, offsets, all_lengths
        )

        char_preds, char_probs = self._aggregate_context_predictions(
            group_ids, char_preds, char_probs,
            binary=(self.config.num_classification_heads <= 2)
        )

        # Convert hallucination spans to character-level labels (no token-level conversion)
        if labels is not None:
            char_labels = convert_spans_to_labels(labels, char_probs)
        else:
            char_labels = None

        return char_probs, char_preds, char_labels

    def setup_model(self):
        if self.config.model_load_path:
            self.model = self.load(self.config.model_load_path)
        else:
            attention_pooling, ensemble = setup_linear_model_config(self.config)
            self.config.attention_pooling = attention_pooling
            self.config.ensemble = ensemble

            self.model = LinearClassifier(
                embedding_dim=self.config.embedding_dim,
                num_features=self.config.num_features,
                attention_pooling=self.config.attention_pooling,
                ensemble=self.config.ensemble,
                num_classes=self.config.num_classification_heads,
                use_contrastive=self.config.use_contrastive,
                projection_dim=self.config.projection_dim,
                contrastive_layers=self.config.contrastive_layers,
            )
            self.model.to(self.device)
        self.threshold = self.config.threshold

    def _load_model(self, load_dir: Path) -> None:
        """Load the LinearClassifier model from directory."""
        model_path = load_dir / "model.pt"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        checkpoint = torch.load(
            model_path, map_location=self.device, weights_only=False
        )

        # Create model with loaded config
        model = LinearClassifier(
            embedding_dim=self.config.embedding_dim,
            num_features=self.config.num_features,
            attention_pooling=self.config.attention_pooling,
            ensemble=self.config.ensemble,
            num_classes=self.config.num_classification_heads,
            use_contrastive=self.config.use_contrastive,
            projection_dim=self.config.projection_dim,
            contrastive_layers=self.config.contrastive_layers,
        )

        # Load model state dict
        model.classifier.load_state_dict(checkpoint["model_state_dict"])
        for i in range(len(model.layer_classifiers)):
            model.layer_classifiers[i].load_state_dict(
                checkpoint["layer_classifiers_dicts"][i]
            )

        self.model = model
        self.model.to(self.device)
        lg.info(f"Loaded LinearClassifier model from {model_path}")

    def _save_model(self, save_dir: Path) -> None:
        """Save the LinearClassifier model to directory."""
        model_path = save_dir / "model.pt"

        model_state_dict = self.model.classifier.state_dict()
        layer_classifiers_dicts = [
            layer_classifier.state_dict()
            for layer_classifier in self.model.layer_classifiers
        ]

        torch.save(
            {
                "model_state_dict": model_state_dict,
                "layer_classifiers_dicts": layer_classifiers_dicts,
            },
            model_path,
        )
        lg.info(f"Saved LinearClassifier model to {model_path}")

    def _train_metamodel(
        self,
        cfg: TrainingArgsConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        group_ids: Optional[List[int]] = None,
        logger: Optional[LoggerBase] = None,
        **kwargs,
    ) -> DetectionResult:
        return self.trainer.train(
            detector=self,
            train_data=train_loader,
            cfg=cfg,
            val_data=val_loader,
            group_ids=group_ids,
            logger=logger,
        )
