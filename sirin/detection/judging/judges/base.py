from abc import abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

import joblib
from datasets import Dataset
from loguru import logger as lg
from peft import get_peft_model
from transformers import (
    DataCollatorForTokenClassification,
    DataCollatorWithPadding,
    TrainingArguments,
)
from sirin.utils.config_manager import validate_hydra_config

from sirin.models.detection import DetectionResult, JudgeBaseConfig
from sirin.utils.config_serialization import (
    deserialize_judge_config,
    serialize_judge_config,
)
from sirin.inference.adapters import ModelAdapterBase, HfModelAdapter, OpenAIModelAdapter
from sirin.inference.model_manager import ModelManager
from sirin.detection.base import DetectorBase
from sirin.definitions import (
    INPUT_COL,
    TARGET_COL,
    ClassificationMetric,
    BASIC_METRICS,
    DetectionLevel,
    DataCollatorType,
)


class JudgeAnnotationError(Exception):
    """Raised when a judge cannot produce a usable annotation for a sample.

    E.g. every sampled generation failed the reference-echo check, so there is no honest
    per-character consensus to emit. Callers must surface this rather than let an empty
    annotation render as "all clear".
    """


class JudgeBase(DetectorBase):
    """Base class for all judge implementations with shared configuration logic."""
    detection_level: DetectionLevel

    @validate_hydra_config
    def __init__(self, config: JudgeBaseConfig, model_adapter: ModelAdapterBase):
        super().__init__(config)
        self.model_adapter = ModelManager.load_model(model_adapter)
        if self.config.model_load_path:
            self.load(self.config.model_load_path)
        self.setup_model()

    @abstractmethod
    def setup_model(self):
        pass

    @abstractmethod
    def _compute_metrics(self, eval_pred: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _preprocess(self, samples: Dataset) -> Dict[str, Any]:
        pass

    def _save_config(self, save_dir: Path):
        """
        Save judge configuration to directory.
        
        Args:
            save_dir: Directory where to save the config
        """
        model_path = str(save_dir / 'model') if hasattr(self, '_save_model') else None
        config_dict = serialize_judge_config(
            config=self.config,
            threshold=self.threshold,
            model_adapter=self.model_adapter.config,
            model_path=model_path,
        )
        joblib.dump(config_dict, save_dir / 'config.joblib')
        lg.info(f'Saved config to {save_dir / "config.joblib"}')

    def _load_config(self, load_dir: Path):
        config_path = load_dir / 'config.joblib'
        if not config_path.exists():
            raise FileNotFoundError(f'Config file not found at: {config_path}')
        
        loaded_objects = joblib.load(config_path)
        config, threshold, adapter_config, model_path = deserialize_judge_config(loaded_objects)
        
        # Update config attributes
        for key, value in config.__dict__.items():
            if key not in ['model_load_path', 'model_save_path']:
                setattr(self.config, key, value)
        
        self.threshold = threshold
        lg.info(f'Loaded config from {config_path}')
        
        # Store adapter config for subclass use
        self._loaded_adapter_config = adapter_config
        self._loaded_model_path = model_path


class HfJudgeBase(JudgeBase):
    """Base class for HuggingFace model-based judges with training support."""
    
    # Override in subclasses to specify data collator type
    data_collator_type: DataCollatorType = DataCollatorType.PADDING  # Default for sequence encoder judges

    def __init__(self, config: JudgeBaseConfig, model_adapter: ModelAdapterBase):
        super().__init__(config, model_adapter)

    def setup_model(self):
        if self.config.peft_config is not None:
            self.model_adapter.model = get_peft_model(self.model_adapter.model, self.config.peft_config)
            lg.info(self.model_adapter.model.print_trainable_parameters())
        else:
            lg.info("Training without peft")

        self.class_token_ids = [
            self.model_adapter.tokenizer.convert_tokens_to_ids(str(i))
            for i in range(self.config.num_classification_heads)
        ]

    def _save_model(self, save_dir: Path):
        model_path = save_dir / 'model'
        model_path.mkdir(exist_ok=True)
        
        # Save model
        if hasattr(self.model_adapter, 'model'):
            self.model_adapter.model.save_pretrained(str(model_path))
            lg.info(f'Saved model to {model_path}')
        
        # Save tokenizer
        if hasattr(self.model_adapter, 'tokenizer'):
            self.model_adapter.tokenizer.save_pretrained(str(model_path))
            lg.info(f'Saved tokenizer to {model_path}')

    def _load_model(self, load_dir: Path):
        model_path = load_dir / 'model'
        
        if not model_path.exists():
            raise FileNotFoundError(f'Model directory not found at: {model_path}')
        
        # Load model using adapter config from _load_config
        adapter_config = getattr(self, '_loaded_adapter_config', None)
        if adapter_config is None:
            raise ValueError('Config must be loaded before model. Call _load_config() first.')
        
        # Update model path to point to saved model
        adapter_config.model_path = str(model_path)
        
        model_manager = ModelManager()
        self.model_adapter = model_manager.load(
            HfModelAdapter(config=adapter_config, model=str(model_path))
        )
        lg.info(f'Loaded model from {model_path}')

    def _save_additional_components(self, save_dir: Path):
        self._save_model(save_dir)

    def _load_additional_components(self, load_dir: Path):
        self._load_model(load_dir)

    def _check_truncation_warning(self, samples: List[Dict[str, Any]]):
        if not self.model_adapter.tokenizer:
            return
        
        preprocessed_samples = self.model_adapter._preprocess_input(samples)

        if self.model_adapter.config.truncation:
            for i, sample in enumerate(preprocessed_samples):
                tokens = self.model_adapter.tokenizer.encode(
                    sample, 
                    add_special_tokens=True,
                    truncation=False,
                )
                
                max_length = self.model_adapter.tokenizer.model_max_length
                if len(tokens) > max_length:
                    lg.warning(
                        f"Sample {i} exceeds model's max length ({len(tokens)} > {max_length}). "
                        f"Truncation will be applied. Consider reducing input length."
                    )

    def train(
        self,
        training_args: TrainingArguments,
        train_data: Dataset,
        val_data: Optional[Dataset],
        metrics: Optional[List[ClassificationMetric]] = None,
        **kwargs,
    ) -> DetectionResult:
        self.metrics_to_compute = metrics or BASIC_METRICS

        train_data_tokenized = train_data.batch_process(
            lambda x: self._preprocess(x),
            batch_size=self.config.batch_size,
            remove_columns=[INPUT_COL, TARGET_COL],
        )
        train_data_tokenized = Dataset.from_dict(train_data_tokenized)

        val_data_tokenized = None
        if val_data is not None:
            val_data_tokenized = val_data.batch_process(
                lambda x: self._preprocess(x),
                batch_size=self.config.batch_size,
                remove_columns=[INPUT_COL, TARGET_COL],
            )
            val_data_tokenized = Dataset.from_dict(val_data_tokenized)

        # Select data collator based on judge type (specified by subclass)
        if self.data_collator_type == DataCollatorType.TOKEN:
            data_collator = DataCollatorForTokenClassification(
                tokenizer=self.model_adapter.tokenizer,
                padding=self.model_adapter.config.padding,
                label_pad_token_id=-100,
            )
        elif self.data_collator_type == DataCollatorType.PADDING:
            data_collator = DataCollatorWithPadding(
                tokenizer=self.model_adapter.tokenizer,
                padding=self.model_adapter.config.padding,
            )
        else:
            raise ValueError(f'Invalid data_collator_type: {self.data_collator_type}')
        
        trainer = self.trainer(
            model=self.model_adapter.model,
            data_collator=data_collator,
            args=training_args,
            train_dataset=train_data_tokenized,
            eval_dataset=val_data_tokenized,
            processing_class=self.model_adapter.tokenizer,
            compute_metrics=self._compute_metrics if val_data_tokenized else None,
            **kwargs,
        )

        train_result = trainer.train()  
        self.model_adapter.model = trainer.model

        if training_args.output_dir:
            trainer.save_model()
            self.model_adapter.tokenizer.save_pretrained(training_args.output_dir)

        return DetectionResult(
            metrics=train_result.metrics,
            probs=None,
            threshold=self.threshold,
        )
    

class OpenAIJudgeBase(JudgeBase):
    """Base class for OpenAI API-based judges (no training support)."""

    def __init__(self, config: JudgeBaseConfig, model_adapter: ModelAdapterBase):
        super().__init__(config, model_adapter)
            
    def setup_model(self):
        pass

    def _load_config(self, load_dir: Path):
        """Override to reload OpenAI model adapter after config load."""
        super()._load_config(load_dir)
        
        # Reload model adapter with saved config
        model_manager = ModelManager()
        self.model_adapter = model_manager.load(
            OpenAIModelAdapter(
                config=self._loaded_adapter_config, 
                model=self._loaded_adapter_config.model_path or self._loaded_model_path
            )
        )
        lg.info('Reloaded OpenAI model adapter')

    def train(
        self,
        training_args: TrainingArguments,
        train_data: Dataset,
        val_data: Optional[Dataset],
        metrics: Optional[List[ClassificationMetric]] = None,
        **kwargs,
    ) -> DetectionResult:
        lg.info("There is no training for API judges")
        return DetectionResult()

    def _preprocess(self, samples: Dataset) -> Dataset:
        return samples

    def _compute_metrics(self, eval_pred: Any) -> Dict[str, Any]:
        lg.info("There is no metrics compution during training for API judges")
        return {}
