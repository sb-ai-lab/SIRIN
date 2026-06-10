from typing import Any, Dict, List, Optional

import datasets

from sirin.loggers import LoggerBase


class MultipleLoggers(LoggerBase):
    """Abstract base class for experiment loggers"""

    def __init__(self, experiment_name: str, loggers: List[LoggerBase], **kwargs):
        self.experiment_name = experiment_name
        self.loggers = loggers

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ''
    ):
        for logger in self.loggers:
            logger.log_metrics(metrics, step, prefix)

    def log_hyperparameters(self, config: Any):
        for logger in self.loggers:
            logger.log_hyperparameters(config)

    def log_dataset_info(self, dataset_name: str, dataset: datasets.Dataset):
        for logger in self.loggers:
            logger.log_dataset_info(dataset_name, dataset)

    def log_text(self, text: str):
        for logger in self.loggers:
            logger.log_text(text)

    def log_model(self, model_name: str, save_dir: str):
        for logger in self.loggers:
            logger.log_model(model_name, save_dir)

    def finish(self):
        for logger in self.loggers:
            logger.finish()