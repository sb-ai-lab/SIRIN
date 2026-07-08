from typing import Optional

import datasets
import numpy as np
from loguru import logger as lg
from transformers import TrainingArguments

from sirin.definitions import INPUT_COL, TARGET_COL, DetectionLevel, DetectionTaskType
from sirin.detection.approximators import TargetApproximatorBase
from sirin.detection.base import PipelineBase
from sirin.detection.judging.judges.base import HfJudgeBase
from sirin.detection.utils.basic import flatten_array
from sirin.loggers import LoggerBase
from sirin.metrics import calculate_classification_metrics
from sirin.models.detection import *
from sirin.utils.config_manager import validate_hydra_config


class JudgePipeline(PipelineBase):
    """Judge pipeline implementation"""

    @validate_hydra_config
    def __init__(
        self,
        config: JudgePipelineConfig,
        judge: HfJudgeBase,
        train_dataset: datasets.Dataset,
        training_args: Optional[TrainingArguments] = None,
        target_col: str = TARGET_COL,
        eval_dataset: Optional[datasets.Dataset] = None,
        task_type: str = DetectionTaskType.HALLUCINATION_DETECTION,
        target_approximator: Optional[TargetApproximatorBase] = None,
        experiment_logger: Optional[LoggerBase] = None,
    ):
        super().__init__(
            config=config,
            detector=judge,
            train_dataset=train_dataset,
            target_col=target_col,
            eval_dataset=eval_dataset,
            task_type=task_type,
            target_approximator=target_approximator,
            experiment_logger=experiment_logger,
        )
        self.judge = judge
        self.training_args = training_args

        if (
            not hasattr(self.training_args, 'report_to')
            or self.training_args.report_to is None
        ):
            training_args_dict = (
                self.training_args.to_dict() if self.training_args else {}
            )
            training_args_dict['report_to'] = []
            self.training_args = TrainingArguments(**training_args_dict)

    def train(self, **kwargs) -> DetectionResult:
        """
        Train method that dispatches to either classification or decoder-based training.
        """
        assert self.training_args is not None, "Specify TrainingArguments"

        lg.info("Starting training pipeline...")

        if self.experiment_logger:
            self.experiment_logger.log_text("Training started")

        if isinstance(self.train_dataset, datasets.DatasetDict):
            train_data = self.train_dataset['train']
            val_data = self.train_dataset.get('validation') or self.train_dataset.get(
                'val'
            )
        else:
            train_data = self.train_dataset
            val_data = None

        train_data, _ = self._load_dataset(train_data)
        if self.experiment_logger:
            self.experiment_logger.log_dataset_info('train', train_data)
        if val_data:
            val_data, _ = self._load_dataset(val_data)
            if self.experiment_logger:
                self.experiment_logger.log_dataset_info('validation', val_data)

        if getattr(self.judge, 'class_token_ids', False):
            kwargs['class_token_ids'] = self.judge.class_token_ids

        lg.info("Starting model training...")
        results = self.judge.train(
            self.training_args,
            train_data,
            val_data=val_data,
            **kwargs,
        )

        self.judge.threshold = results.threshold

        if self.experiment_logger:
            try:
                self.experiment_logger.log_metrics(
                    results.metrics, prefix='final/train/'
                )
                self.experiment_logger.log_model(
                    'judge_detector', self.config.save_dir
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
            all_probs.extend(
                batch_probs.tolist()
                if isinstance(batch_probs, np.ndarray)
                else batch_probs
            )
            all_preds.extend(
                batch_preds.tolist()
                if isinstance(batch_preds, np.ndarray)
                else batch_preds
            )
            all_labels.extend(batch_labels)

        # Decide whether to use per-sample or flattened metrics
        use_per_sample = (
            self.config.per_sample_metrics
            and self.detector.detection_level == DetectionLevel.TOKEN
        )

        if use_per_sample:
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
