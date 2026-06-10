from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import torch
from loguru import logger as lg
from tabpfn import TabPFNClassifier
from tabpfn.model.loading import load_model_criterion_config
from tabpfn.model_loading import load_fitted_tabpfn_model, save_fitted_tabpfn_model
from torch.utils.data import DataLoader

from sirin.detection.splitters import SplitManager
from sirin.definitions import DetectionLevel, Phase
from sirin.detection.base import (
    LoggerBase,
)
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.probing.detectors.utils.detection import (
    check_features_for_nan,
    handle_binary_multiclass_probs,
)
from sirin.detection.probing.detectors.utils.training import (
    calibrate_and_evaluate,
    preprocess_dataloader_to_numpy,
)
from sirin.detection.processors import FeatureProcessorBase

# from sirin.detection.tabpfn_wide.tabpfnwide.patches import fit
from sirin.models.detection import (
    ProbingDetectorConfig,
    DetectionResult,
    TrainingArgsConfig,
    SplitConfig,
)
from sirin.inference.adapters import ModelAdapterBase


class ClaimTabPFNProbingDetector(ProbingDetectorBase):
    """Enhanced TabPFN detector with robust scaling and compression functionality."""

    detection_level = DetectionLevel.CLAIM

    def __init__(
        self,
        config: ProbingDetectorConfig,
        feature_processor: FeatureProcessorBase,
        response_splitter_config: SplitConfig,
        split_model: Optional[ModelAdapterBase] = None,
    ):
        self.state = None
        super().__init__(config=config, feature_processor=feature_processor)
        self.response_splitter = SplitManager(config=response_splitter_config)
        self.split_model = split_model or feature_processor._extractor

    def detect(
        self, samples: List[str], labels: Optional[np.ndarray] = None, **kwargs
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Detect with proper scaling and compression handling."""
        original_samples = samples.copy()

        samples_fact_splits = self.response_splitter.split_inputs(
            samples, self.split_model
        )
        samples = samples_fact_splits.copy()
        response_group_ids = []
        for index, splits in enumerate(samples):
            response_group_ids.extend([index] * len(splits))
        flattened_samples = []
        for sample in samples:
            flattened_samples.extend(sample)
        samples = flattened_samples

        samples, group_ids = self._split_context_samples(samples)

        features, _ = self.feature_processor(samples)
        check_features_for_nan(features, samples)

        features, masks = self._process_sequence_features(features)

        features = [feature.reshape(feature.shape[0], -1) for feature in features]
        features = np.concatenate(features, axis=-1)

        probs = self.model.predict_proba(features)
        probs, preds = handle_binary_multiclass_probs(
            probs, self.threshold, is_binary=(self.config.num_classification_heads <= 2)
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
                for split, pred, prob in zip(
                    splitted_samples, sample_probs, sample_preds
                )
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

    def setup_model(self):
        if getattr(self.config, "model_load_path", None):
            self.load(self.config.model_load_path)
            return
        if (
            self.config.checkpoint_path
            and "TabPFN-Wide" in self.config.checkpoint_path
        ):
            self.state, _, _ = load_model_criterion_config(
                model_path=None,
                check_bar_distribution_criterion=False,
                cache_trainset_representation=False,
                which="classifier",
                version="v2",
                download=True,
            )
            self.state.features_per_group = 1
            checkpoint = torch.load(
                self.config.checkpoint_path,
                map_location=self.device,
                weights_only=False,
            )
            self.state.load_state_dict(checkpoint)
            self.model = TabPFNClassifier(
                n_estimators=1,
                device=self.device,
                ignore_pretraining_limits=True,
                random_state=self.config.seed,
                **self.config.kwargs,
            )
        else:
            self.model = TabPFNClassifier(
                model_path=self.config.checkpoint_path,
                random_state=self.config.seed,
            )

    def _save_model(self, save_dir: Path) -> None:
        """Save the TabPFN model to directory."""
        model_path = save_dir / "model.tabpfn_fit"
        save_fitted_tabpfn_model(self.model, model_path)
        lg.info(f"Saved TabPFN model to {model_path}")

    def _load_model(self, load_dir: Path) -> None:
        """Load the TabPFN model from directory."""
        model_path = load_dir / "model.tabpfn_fit"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        self.model = load_fitted_tabpfn_model(model_path, device="cpu")
        lg.info(f"Loaded TabPFN model from {model_path}")

    def _preprocess_data(
        self, data_loader: DataLoader
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract and preprocess features with TabPFN feature limit."""
        max_features_per_layer = max(1, int(8000 / len(self.config.embedding_dim)))
        return preprocess_dataloader_to_numpy(data_loader, max_features_per_layer)

    def _train_metamodel(
        self,
        cfg: TrainingArgsConfig,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        group_ids: Optional[List[int]] = None,
        logger: Optional[LoggerBase] = None,
        **kwargs,
    ) -> DetectionResult:
        """Train the metamodel with proper scaling and compression handling."""

        X_train_np, y_train_np = self._preprocess_data(train_loader)

        if self.state is not None:
            self.model.fit(X_train_np[:10000], y_train_np[:10000], model=self.state)
        else:
            self.model.fit(X_train_np[:10000], y_train_np[:10000])

        val_loader = val_loader or train_loader

        X_val_np, y_val_np = self._preprocess_data(val_loader)
        val_probs_full = self.model.predict_proba(X_val_np)

        val_probs, val_predictions, self.threshold, val_metrics = calibrate_and_evaluate(
            val_probs_full, y_val_np, self.config, cfg.metrics
        )

        if logger:
            logger.log_metrics(val_metrics, -1, prefix="/train")

        return DetectionResult(
            metrics=val_metrics,
            probs=val_probs,
            threshold=self.threshold,
        )
