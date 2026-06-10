from typing import Any, Dict, Optional

import datasets
from loguru import logger as lg

from sirin.loggers import LoggerBase

try:
    from clearml import Task
except ImportError:
    Task = None


class ClearMLLogger(LoggerBase):
    def __init__(self, experiment_name: str, project_name: str = "default", **kwargs):
        if Task is None:
            raise ImportError(
                "ClearML is not installed. Install with: pip install clearml"
            )

        super().__init__(experiment_name=experiment_name)

        try:
            # Initialize ClearML task
            self.task = Task.init(
                project_name=project_name, task_name=experiment_name, **kwargs
            )
            self.logger = self.task.get_logger()

            lg.info("ClearML logging initialized successfully")
        except Exception as e:
            lg.warning(f"Failed to initialize ClearML: {e}")
            self.task = None
            self.logger = None

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ""
    ):
        """Log scalar metrics to ClearML."""
        if not self.logger:
            return

        try:
            for key, value in metrics.items():
                full_key = f"{prefix}{key}" if prefix else key
                self.logger.report_scalar(
                    "metrics", full_key, value, iteration=step or 0
                )
        except Exception as e:
            lg.warning(f"Failed to log metrics to ClearML: {e}")

    def log_hyperparameters(self, config: Any):
        """Log configuration to ClearML."""
        if not self.task:
            return

        try:
            if hasattr(config, "__dict__"):
                self.task.connect_configuration(config.__dict__)
            elif isinstance(config, dict):
                self.task.connect_configuration(config)
        except Exception as e:
            lg.warning(f"Failed to log config to ClearML: {e}")

    def log_dataset_info(self, dataset_name: str, dataset: datasets.Dataset):
        """Log dataset information to ClearML."""
        if not self.task:
            return

        try:
            dataset_info = {
                f"{dataset_name}_size": len(dataset) if dataset else 0,
            }
            if hasattr(dataset, "features"):
                dataset_info[f"{dataset_name}_features"] = (
                    list(dataset.features.keys()) if dataset else []
                )

            self.task.connect_configuration(dataset_info)
        except Exception as e:
            lg.warning(f"Failed to log dataset info to ClearML: {e}")

    def log_text(self, text: str):
        """Log text to ClearML."""
        if not self.logger:
            return

        try:
            self.logger.report_text(text)
        except Exception as e:
            lg.warning(f"Failed to log text to ClearML: {e}")

    def log_model(self, model_name: str, save_dir: str):
        """Log model to ClearML."""
        if not self.task:
            return

        try:
            # Upload model as output model
            self.task.upload_artifact(name=model_name, artifact_object=save_dir)
        except Exception as e:
            lg.warning(f"Failed to log model to ClearML: {e}")

    def finish(self):
        """Close the ClearML task."""
        if self.task:
            try:
                self.task.close()
            except Exception as e:
                lg.warning(f"Failed to close ClearML task: {e}")
