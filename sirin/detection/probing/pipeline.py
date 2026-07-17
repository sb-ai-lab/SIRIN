from typing import Optional

import datasets
import numpy as np
import torch
from loguru import logger as lg
from torch.utils.data import DataLoader

from sirin.definitions import (
    INPUT_COL,
    OFFSETS_COL,
    TARGET_COL,
    DetectionLevel,
    DetectionTaskType,
    Phase,
)
from sirin.detection.approximators import TargetApproximatorBase
from sirin.detection.base import PipelineBase
from sirin.detection.probing.detectors.base import ProbingDetectorBase
from sirin.detection.utils.basic import flatten_array
from sirin.detection.utils.torch import FeaturesDataset, InputsDataset
from sirin.inference.adapters import ModelAdapterBase
from sirin.loggers.base import LoggerBase
from sirin.metrics import calculate_classification_metrics
from sirin.models.detection import DetectionResult, ProbingPipelineConfig
from sirin.utils.config_manager import validate_hydra_config
from sirin.utils.hf import add_or_replace_column


class ProbingPipeline(PipelineBase):
    @validate_hydra_config
    def __init__(
        self,
        config: ProbingPipelineConfig,
        detector: ProbingDetectorBase,
        train_dataset: datasets.Dataset,
        target_col: str = 'target',
        eval_dataset: Optional[datasets.Dataset] = None,
        task_type: str = DetectionTaskType.HALLUCINATION_DETECTION,
        generator_adapter: Optional[ModelAdapterBase] = None,
        target_approximator: Optional[TargetApproximatorBase] = None,
        experiment_logger: Optional[LoggerBase] = None,
    ):
        super().__init__(
            config=config,
            detector=detector,
            train_dataset=train_dataset,
            target_col=target_col,
            eval_dataset=eval_dataset,
            task_type=task_type,
            generator_adapter=generator_adapter,
            target_approximator=target_approximator,
            experiment_logger=experiment_logger,
        )
        if self.experiment_logger:
            self.experiment_logger.log_hyperparameters(config)

    def train(self) -> DetectionResult:
        lg.info("Starting training pipeline...")

        if self.experiment_logger:
            self.experiment_logger.log_text("Training started")

        if self.target_approximator is not None:
            new_targets = self.target_approximator(
                self.train_dataset[INPUT_COL], self.train_dataset[TARGET_COL]
            )
            self.train_dataset = add_or_replace_column(
                self.train_dataset, TARGET_COL, new_targets
            )

        batch_size = self.detector.config.batch_size

        train_data, _ = self._load_dataset(
            self.train_dataset,
            split='train',
        )
        if self.experiment_logger:
            self.experiment_logger.log_dataset_info(Phase.TRAIN, train_data)
        lg.info("Pre-processing training data...")
        train_loader = self._preprocess_dataset(
            train_data, batch_size=batch_size, shuffle=self.config.shuffle_train, phase=Phase.TRAIN
        )

        val_loader, val_data = None, None
        if isinstance(self.train_dataset, datasets.DatasetDict):
            val_name = 'val' if 'val' in self.train_dataset else 'validation'
            if val_name not in self.train_dataset:
                raise ValueError(
                    "The train dataset is a datasets.DatasetDict but does not contain 'validation' or 'val'"
                )

            val_data, _ = self._load_dataset(self.train_dataset, split=val_name)
            if self.experiment_logger:
                self.experiment_logger.log_dataset_info(Phase.VAL, val_data)
            lg.info("Pre-processing val data...")
            val_loader = self._preprocess_dataset(
                val_data,
                batch_size=batch_size,
                shuffle=False,
                phase=Phase.VAL,
            )

        group_ids = train_data.group_ids
        if val_data:
            group_ids = val_data.group_ids

        lg.info("Starting model training...")
        results = self.detector.train(
            self.config.train_args,
            train_loader,
            val_loader=val_loader,
            group_ids=group_ids,
            logger=self.experiment_logger,
        )

        self.detector.threshold = results.threshold

        if self.experiment_logger:
            try:
                self.experiment_logger.log_metrics(
                    results.metrics, prefix='final/train/'
                )
                self.experiment_logger.log_model(
                    'probing_detector', self.config.save_dir
                )

                self.experiment_logger.finish()

            except Exception as e:
                lg.warning(f"Failed to log final results to logger: {e}")

        lg.info("Training completed successfully")
        return results

    def eval(self) -> DetectionResult:
        if not self.eval_dataset:
            lg.warning("Empty evaluation dataset: you need to set `eval_dataset`")
            return DetectionResult()

        lg.info("Starting evaluation...")

        if self.experiment_logger:
            self.experiment_logger.log_text("Evaluation started")

        batch_size = self.detector.config.batch_size
        data, _ = self._load_dataset(self.eval_dataset)

        samples = data[INPUT_COL]
        target = data[TARGET_COL]

        all_probs = []
        all_preds = []
        all_labels = []

        for i in range(0, len(samples), batch_size):
            batch_samples, batch_target_spans = (
                samples[i : i + batch_size],
                target[i : i + batch_size],
            )
            batch_probs, batch_preds, batch_labels = self.detector.detect(
                batch_samples, batch_target_spans
            )
            all_probs.extend(batch_probs.tolist() if isinstance(batch_probs, np.ndarray) else batch_probs)
            all_preds.extend(batch_preds.tolist() if isinstance(batch_preds, np.ndarray) else batch_preds)
            all_labels.extend(batch_labels)

        # Decide whether to use per-sample or flattened metrics
        use_per_sample = (
            self.config.per_sample_metrics 
            and self.detector.detection_level == DetectionLevel.TOKEN
        )

        if use_per_sample:
            # Keep data structured per sample for per-sample metric calculation
            # all_probs, all_preds, all_labels are already lists of arrays (one per sample)
            if self.config.classification_metrics is not None:
                from sirin.metrics.classification import calculate_per_sample_metrics
                
                result_metrics = calculate_per_sample_metrics(
                    all_labels,
                    all_probs,
                    all_preds,
                    metrics=self.config.classification_metrics,
                    beta=self.config.f_beta,
                )
            else:
                result_metrics = None
            
            # For storage, flatten to maintain compatibility
            flat_probs = np.array(flatten_array(all_probs))
            flat_labels = np.array(flatten_array(all_labels))
        else:
            # Original behavior: flatten for TOKEN level
            if self.detector.detection_level == DetectionLevel.TOKEN:
                all_probs = flatten_array(all_probs)
                all_preds = flatten_array(all_preds)
                all_labels = flatten_array(all_labels)

            all_probs = np.array(all_probs)
            all_preds = np.array(all_preds)
            all_labels = np.array(all_labels)

            if self.config.classification_metrics is not None:
                result_metrics = calculate_classification_metrics(
                    all_labels,
                    all_probs,
                    all_preds,
                    metrics=self.config.classification_metrics,
                    beta=self.config.f_beta,
                )
            else:
                result_metrics = None
            
            flat_probs = all_probs
            flat_labels = all_labels

        results = DetectionResult(
            metrics=result_metrics,
            probs=flat_probs.tolist() if isinstance(flat_probs, np.ndarray) else flat_probs,
            labels=flat_labels.tolist() if isinstance(flat_labels, np.ndarray) else flat_labels,
            threshold=self.detector.threshold,
        )

        if self.experiment_logger:
            try:
                self.experiment_logger.log_metrics(result_metrics, prefix='eval/')

            except Exception as e:
                lg.warning(f"Failed to log evaluation results to logger: {e}")

        lg.info("Evaluation completed successfully")
        return results

    def _preprocess_dataset(
        self,
        dataset: InputsDataset,
        batch_size: int = 1,
        shuffle: bool = False,
        phase: Phase = Phase.TRAIN,
    ) -> DataLoader:
        total_samples = len(dataset)
        processed_features = []
        all_answer_indices = []

        for start_idx in range(0, total_samples, batch_size):
            end_idx = min(start_idx + batch_size, total_samples)

            features, answer_indices = self.detector.feature_processor(
                dataset[INPUT_COL][start_idx:end_idx]
            )

            if not processed_features:
                processed_features = [[] for _ in range(len(features))]
            for i, feature in enumerate(features):
                processed_features[i].extend(
                    feature.tolist() if isinstance(feature, torch.Tensor) else feature
                )
            all_answer_indices.extend(answer_indices)

        hasnan_mask = (
            torch.tensor(
                [
                    [torch.tensor(sample).isnan().sum() > 0 for sample in samples]
                    for samples in processed_features
                ]
            ).sum(dim=0)
            > 0
        ).bool() | torch.tensor([len(indices) == 0 for indices in all_answer_indices])
        for index, hasnan in enumerate(hasnan_mask):
            if hasnan:
                lg.error(f"Features of sample {index} in {phase.value} dataset contain NAN. Probably its out of context length. Sample will be ignored!")

        processed_features = [
            [sample for index, sample in enumerate(samples) if not hasnan_mask[index]]
            for samples in processed_features
        ]
        labels = [
            label
            for index, label in enumerate(dataset[TARGET_COL])
            if not hasnan_mask[index]
        ]
        all_answer_indices = [
            answer_indices
            for index, answer_indices in enumerate(all_answer_indices)
            if not hasnan_mask[index]
        ]

        offsets = None
        if self.detector.detection_level == DetectionLevel.TOKEN:
            features, masks, offsets, labels = self.detector._process_token_features(
                processed_features,
                [
                    sample
                    for index, sample in enumerate(dataset[INPUT_COL])
                    if not hasnan_mask[index]
                ],
                all_answer_indices,
                labels,
            )
        else:
            features, masks = self.detector._process_sequence_features(
                processed_features
            )

        offsets = [-1] * len(features[0]) if offsets is None else offsets

        data_dict = {
            **{f"hiddens{index}": features[index] for index in range(len(features))},
            **{f"attention_masks{index}": masks[index] for index in range(len(masks))},
            TARGET_COL: labels,
            OFFSETS_COL: offsets,
        }

        torch_dataset = FeaturesDataset(data_dict)
        torch_dataloader = DataLoader(
            torch_dataset,
            batch_size=self.config.train_args.train_batch_size
            if phase == Phase.TRAIN
            else self.config.train_args.val_batch_size,
            shuffle=shuffle,
            generator=torch.Generator().manual_seed(self.detector.config.seed),
        )

        return torch_dataloader
