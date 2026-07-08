from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from loguru import logger as lg
from torch.utils.data import DataLoader
from pathlib import Path
from sirin.classification import LinearClassifier
from sirin.definitions import DetectionLevel
from sirin.loggers import LoggerBase
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.probing.detectors.utils.detection import check_features_for_nan
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


class SequenceLinearProbingDetector(ProbingDetectorBase):
    """
    Linear probing detector for sequence-level classification.

    Architecture: Uses linear classifier with attention pooling over hidden states.
    Differs from tree-based models (CatBoost/TabPFN) which don't use attention.
    """

    detection_level = DetectionLevel.SEQUENCE

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
        samples: List[Dict[Any, str]],
        labels: Optional[np.ndarray] = None,
        **kwargs,
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect with proper scaling and compression handling."""
        samples, group_ids = self._split_context_samples(samples)

        features, _ = self.feature_processor(samples)
        check_features_for_nan(features, samples)

        features, masks = self._process_sequence_features(features)
        features = [feature.to(self.device) for feature in features]
        masks = [mask.to(self.device) for mask in masks]

        logits = self.model(features, masks)
        probs, preds = self._logits_to_probs_preds(logits)
        preds, probs = self._aggregate_context_predictions(
            group_ids, preds, probs, binary=(self.config.num_classification_heads <= 2)
        )

        return probs, preds, labels

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
                projection_hidden_dim=getattr(
                    self.config, 'projection_hidden_dim', None
                ),
                projection_num_layers=getattr(self.config, 'projection_num_layers', 2),
                use_projection_dropout=getattr(
                    self.config, 'use_projection_dropout', False
                ),
                projection_dropout=getattr(self.config, 'projection_dropout', 0.1),
            )
            self.model.to(self.device)
        self.threshold = self.config.threshold

    def _load_model(self, load_dir: Path) -> None:
        """Load the LinearClassifier model from directory."""
        model_path = load_dir / 'model.pt'

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
        model.classifier.load_state_dict(checkpoint['model_state_dict'])
        for i in range(len(model.layer_classifiers)):
            model.layer_classifiers[i].load_state_dict(
                checkpoint['layer_classifiers_dicts'][i]
            )

        self.model = model
        self.model.to(self.device)
        lg.info(f"Loaded LinearClassifier model from {model_path}")

    def _save_model(self, save_dir: Path) -> None:
        """Save the LinearClassifier model to directory."""
        model_path = save_dir / 'model.pt'

        model_state_dict = self.model.classifier.state_dict()
        layer_classifiers_dicts = [
            layer_classifier.state_dict()
            for layer_classifier in self.model.layer_classifiers
        ]

        torch.save(
            {
                'model_state_dict': model_state_dict,
                'layer_classifiers_dicts': layer_classifiers_dicts,
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
