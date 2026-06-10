from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import datasets


class LoggerBase(ABC):
    """Abstract base class for experiment loggers"""

    def __init__(self, experiment_name: str, **kwargs):
        self.experiment_name = experiment_name

    @abstractmethod
    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ''
    ):
        """Log scalar metrics"""
        pass

    @abstractmethod
    def log_hyperparameters(self, config: Any):
        """Log config params"""
        pass

    @abstractmethod
    def log_dataset_info(self, dataset_name: str, dataset: datasets.Dataset):
        """Log dataset info"""
        pass

    @abstractmethod
    def log_text(self, text: str):
        """Log text"""
        pass

    @abstractmethod
    def log_model(self, model_name: str, save_dir: str):
        """Log model"""
        pass

    @abstractmethod
    def finish(self):
        """Finishing"""
        pass
