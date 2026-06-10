import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import datasets
import numpy as np
import torch
import torch.multiprocessing as mp
import transformers
from loguru import logger as lg

from sirin.definitions import (
    DSET_KEY,
    INPUT_COL,
    INPUT_PROC_COL,
    REFERENCE_COL,
    TARGET_COL,
    GROUP_ID_COL,
    DetectionTaskType,
    LmMetric,
)
from sirin.detection.approximators import TargetApproximatorBase
from sirin.detection.utils.torch import InputsDataset
from sirin.utils.hf import get_dataset_identifier
from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.cleaners import (
    BaseCleaner,
    CodeCleaner,
    CustomCleaner,
    HTMLCleaner,
    RegexCleaner,
)
from sirin.detection.splitters import SplitManager
from sirin.detection.utils.logits import logits_to_probs_preds
from sirin.loggers import LoggerBase
from sirin.metrics import calculate_lm_metrics
from sirin.models.detection import (
    BertScoreConfig,
    DetectionResult,
    DetectorBaseConfig,
    PipelineBaseConfig,
    TrainingArgsConfig,
)
from sirin.models.inference import CleanerConfig
from sirin.utils.savers import DatasetSaver


class DetectorBase(ABC):
    """Abstract base class for different detection methods."""

    model: Any

    def __init__(
        self,
        config: DetectorBaseConfig,
    ):
        self.threshold = 0.5
        self.config = config
        self.device = self.config.device
        self.num_cpus = max(1, min(self.config.num_cpus, mp.cpu_count() - 2))
        self.set_all_seeds(self.config.seed)
        self._context_splitter = (
            SplitManager(
                config=config.context_split_config,
                split_response=getattr(
                    config.context_split_config, "split_response", False
                ),
            )
            if config.context_split_config is not None
            else None
        )

    @classmethod
    def set_all_seeds(cls, seed: int):
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # for multi-GPU
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        transformers.set_seed(seed)

    @abstractmethod
    def setup_model(self, model: Optional[ModelAdapterBase] = None):
        pass

    @abstractmethod
    def detect(self, sample: Any, **kwargs) -> Dict[str, Any]:
        pass

    def _validate_and_create_save_dir(self, filepath: Optional[str]) -> Path:
        if filepath is None:
            raise ValueError("Filepath must be provided for saving.")

        save_dir = Path(filepath)

        # Ensure we're saving to a directory, not a file
        if save_dir.suffix:
            raise ValueError(
                "Please provide a directory path (folder name) for saving, "
                "not a file path with extension."
            )

        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    def _split_context_samples(
        self, samples: List[Any]
    ) -> Tuple[List[Any], Optional[List[int]]]:
        if not self._context_splitter:
            return samples, None

        split_samples = self._context_splitter.split_inputs(samples)
        group_ids = []
        flattened_samples = []
        for index, splits in enumerate(split_samples):
            group_ids.extend([index] * len(splits))
            flattened_samples.extend(splits)

        return flattened_samples, group_ids

    def _aggregate_context_predictions(
        self,
        group_ids: Optional[List[int]],
        preds: Any,
        probs: Any,
        binary: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray]:
        if not self._context_splitter or group_ids is None:
            return preds, probs

        return self._context_splitter.aggregate_predictions(
            group_ids, preds, probs, binary=binary
        )

    def _logits_to_probs_preds(
        self, logits: torch.Tensor, threshold: Optional[float] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        threshold = self.threshold if threshold is None else threshold
        return logits_to_probs_preds(logits, threshold)

    @abstractmethod
    def _save_config(self, save_dir: Path) -> None:
        pass

    @abstractmethod
    def _load_config(self, load_dir: Path) -> None:
        pass

    def save(self, filepath: Optional[str] = None):
        # Use model_save_path from config if filepath not provided
        if filepath is None:
            filepath = getattr(self.config, "model_save_path", None)

        save_dir = self._validate_and_create_save_dir(filepath)

        # Save config (required, implemented by subclass)
        self._save_config(save_dir)

        # Save additional components if implemented
        if hasattr(self, "_save_additional_components"):
            self._save_additional_components(save_dir)

        lg.info(f"Successfully saved to {save_dir}")

    def load(self, filepath: str):
        load_dir = Path(filepath)

        if not load_dir.exists():
            raise FileNotFoundError(f"Load directory not found: {load_dir}")

        if not load_dir.is_dir():
            raise ValueError(f"Expected directory path, got file: {load_dir}")

        # Load config (required, implemented by subclass)
        self._load_config(load_dir)

        # Load additional components if implemented
        if hasattr(self, "_load_additional_components"):
            self._load_additional_components(load_dir)

        lg.info(f"Successfully loaded from {load_dir}")

    @abstractmethod
    def train(
        self,
        cfg: TrainingArgsConfig,
        train_data: InputsDataset,
        val_data: Optional[InputsDataset],
        logger: Any = None,
    ) -> DetectionResult:
        pass


class PipelineBase(ABC):
    """Abstract base class for different trainers of detectors."""

    def __init__(
        self,
        config: PipelineBaseConfig,
        detector: DetectorBase,
        train_dataset: datasets.Dataset,
        target_col: str = TARGET_COL,
        eval_dataset: Optional[datasets.Dataset] = None,
        task_type: str = DetectionTaskType.HALLUCINATION_DETECTION,
        generator_adapter: Optional[ModelAdapterBase] = None,
        target_approximator: Optional[TargetApproximatorBase] = None,
        experiment_logger: Optional[LoggerBase] = None,
    ):
        self.config = config
        self.detector = detector
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset
        self.task_type = task_type
        self.target_col = target_col

        self._generator_adapter = generator_adapter
        self.target_approximator = target_approximator
        self.experiment_logger = experiment_logger

    @abstractmethod
    def train(self) -> DetectionResult:
        pass

    @abstractmethod
    def eval(self) -> DetectionResult:
        pass

    def _load_dataset(
        self,
        dataset: datasets.Dataset | datasets.DatasetDict,
        split: Optional[str] = None,
    ) -> Tuple[InputsDataset, DatasetSaver]:
        """Load and process dataset through the pipeline."""
        split_name = split or ""
        dataset_name = get_dataset_identifier(dataset)
        if split and hasattr(dataset, "keys") and split in dataset:
            dataset = dataset[split]
        if self._generator_adapter and self._generator_adapter.name:
            model_name = self._generator_adapter.name.split("/")[-1].replace(".", "")
        else:
            model_name = ""

        assert self.target_col in dataset.column_names, (
            f"Target column '{self.target_col}' not found in dataset."
        )
        assert INPUT_COL in dataset.column_names, (
            f"Input column '{INPUT_COL}' not found in dataset."
        )

        dataset_saver = DatasetSaver(
            dataset_name,
            save_dir=self.config.save_dir,
            file_type_alias=DSET_KEY,
        )
        stages = [
            ("generation", self._generate_answers, {}),
            ("cleaning", self._clean_generation_outputs, {}),
            ("metrics", self._compute_lm_metrics, {}),
        ]

        # Current logic implies that training dataset already contains labeled chunks
        # if split == 'train':
        #     stages.append(('splitting', self._split_context, {}))

        for stage_name, processor, kwargs in stages:
            lg.info(f"Starting stage: {stage_name}")
            dataset = processor(dataset, **kwargs)

            if dataset_saver is not None:
                dataset_saver.save(
                    dataset,
                    label="/".join([model_name, stage_name, split_name]).strip("/"),
                    description=f"Dataset {dataset_name} (split={split_name}, model={model_name}) after {stage_name} stage.",
                )

        dataset = InputsDataset(
            dataset[INPUT_COL],
            dataset[self.target_col],
            dataset[GROUP_ID_COL] if GROUP_ID_COL in dataset.column_names else None,
        )

        return dataset, dataset_saver

    def _split_context(self, dataset: datasets.Dataset) -> datasets.Dataset:
        if self.detector._context_splitter:
            return self.detector._context_splitter.split_dataset(dataset)
        lg.info("No context splitting specified.")
        return dataset

    def _load_lm_metrics(self) -> Dict[LmMetric, Any]:
        """Extract metrics to calculate from config with their configurations."""
        metrics = self.config.lm_metrics
        metrics_config = {}

        if metrics.rouge:
            for metric in LmMetric.get_rouge_metrics():
                metrics_config[metric] = None

        if metrics.bleu:
            metrics_config[LmMetric.BLEU] = None

        if metrics.meteor:
            metrics_config[LmMetric.METEOR] = None

        if metrics.ter:
            metrics_config[LmMetric.TER] = None

        if metrics.bert_score:
            bert_config = BertScoreConfig(
                model_path=metrics.bert_score.model_path,
                batch_size=metrics.bert_score.batch_size,
                nthreads=metrics.bert_score.nthreads,
                device=metrics.bert_score.device
                if hasattr(metrics.bert_score, "device")
                else None,
                lang=metrics.bert_score.lang
                if hasattr(metrics.bert_score, "lang")
                else "en",
            )

            for metric in LmMetric.get_bert_metrics():
                metrics_config[metric] = bert_config

        return metrics_config

    def _generate_answers(
        self,
        dataset: datasets.Dataset,
    ) -> datasets.Dataset:
        if self.task_type == DetectionTaskType.QUERY_ANSWERABILITY:
            return dataset

        generation_idxs = []
        generation_inputs = []
        for idx, example in enumerate(dataset):
            input_val = example[INPUT_COL]
            if input_val and input_val[-1]["role"] != "assistant":
                generation_idxs.append(idx)
                generation_inputs.append(input_val)

        if generation_idxs:
            generator_model = self._load_generator()
            generated_answers = []
            batch_size = self.config.get("batch_size") or 1
            for i in range(0, len(generation_inputs), batch_size):
                batch_inputs = generation_inputs[i : i + batch_size]
                batch_answers = generator_model.sample(
                    batch_inputs, **self.config.sampling
                )
                generated_answers.extend(batch_answers)

            generated_dict = dict(zip(generation_idxs, generated_answers))

            def add_generation(example, idx):
                if idx in generated_dict:
                    example[INPUT_COL].append(
                        {
                            "role": "assistant",
                            "content": generated_dict[idx],
                        }
                    )
                return example

            dataset = dataset.map(
                add_generation,
                with_indices=True,
                load_from_cache_file=False,
                desc="Updating with generated answers",
                batched=False,
                num_proc=self.num_cpus if self.config.use_multiprocessing else None,
            )
        else:
            lg.info("There are no missing LLM answers. No need to generate answers.")

        return dataset

    def _compute_lm_metrics(
        self,
        dataset: datasets.Dataset,
    ) -> datasets.Dataset:
        if self.config.lm_metrics is not None:
            metrics_to_calculate = self._load_lm_metrics()
            existing_columns = set(dataset.column_names)

            missing_metrics = {}
            for metric, config in metrics_to_calculate.items():
                if metric.value not in existing_columns:
                    missing_metrics[metric] = config

            if not missing_metrics:
                lg.info("All requested metrics already present in dataset.")
                return dataset

            lg.info(
                f"Calculating missing metrics: {[m.value for m in missing_metrics.keys()]}"
            )

            # Prefer cleaned inputs if available.
            source_col = (
                INPUT_PROC_COL if INPUT_PROC_COL in dataset.column_names else INPUT_COL
            )
            generations = []
            for item in dataset[source_col]:
                if isinstance(item, list):
                    if not item:
                        generations.append("")
                        continue
                    last_item = item[-1]
                    if isinstance(last_item, dict):
                        generations.append(last_item.get("content", ""))
                    else:
                        generations.append(str(last_item))
                elif isinstance(item, dict):
                    generations.append(item.get("content", ""))
                else:
                    generations.append(item)

            scores_dict = calculate_lm_metrics(
                missing_metrics,
                generations,
                dataset[REFERENCE_COL],
            )

            for metric_name, metric_values in scores_dict.items():
                dataset = dataset.add_column(metric_name, metric_values)
        else:
            lg.info("Metrics calculation is disabled.")

        return dataset

    def _clean_generation_outputs(
        self,
        dataset: datasets.Dataset,
    ) -> datasets.Dataset:
        if self.config.cleaner_configs:

            def clean_example(example: List[Dict[str, str]], cleaner):
                example[-1]["content"] = cleaner.clean(example[-1]["content"])
                return example

            def _create_cleaner(config: CleanerConfig) -> BaseCleaner:
                """Factory method to create the appropriate cleaner based on config"""
                cleaner_map = {
                    "regex": RegexCleaner,
                    "html": HTMLCleaner,
                    "code": CodeCleaner,
                    "custom": CustomCleaner,
                }

                cleaner_class = cleaner_map.get(config.type)
                if not cleaner_class:
                    raise ValueError(f"Unknown cleaner type: {config.type}")

                return cleaner_class(config.params or {})

            for cleaner_config in self.config.cleaner_configs:
                cleaner = _create_cleaner(config=cleaner_config)
                dataset = dataset.map(
                    lambda x: {INPUT_PROC_COL: clean_example(x[INPUT_COL], cleaner)},
                    batched=False,
                    num_proc=self.detector.num_cpus
                    if self.detector.config.use_multiprocessing
                    else None,
                    desc=f"Using cleaner: {cleaner_config.name}",
                )
        else:
            lg.info("No cleaning specified.")
            dataset = dataset.add_column(INPUT_PROC_COL, dataset[INPUT_COL])

        return dataset

    def __del__(self):
        if self.experiment_logger:
            try:
                self.experiment_logger.finish()
            except:
                pass
