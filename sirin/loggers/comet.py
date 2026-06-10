from typing import Any, Dict, Optional

import datasets
from loguru import logger as lg

from sirin.loggers import LoggerBase

try:
    from comet_ml import Experiment
except ImportError:
    Experiment = None


class CometLogger(LoggerBase):
    def __init__(self, experiment_name: str, project_name: str = "default", **kwargs):
        if Experiment is None:
            raise ImportError(
                "CometML is not installed. Install with: pip install comet-ml"
            )

        super().__init__(experiment_name=experiment_name)
        """Initialize Comet ML logging."""
        try:
            self.comet_experiment = Experiment(project_name=project_name, **kwargs)

            if self.experiment_name:
                self.comet_experiment.set_name(self.experiment_name)

            lg.info("Comet ML logging initialized successfully")

        except Exception as e:
            lg.warning(f"Failed to initialize Comet ML: {e}")
            self.comet_experiment = None
            self.use_comet = False

    def log_hyperparameters(self, config: Any):
        """Log pipeline configuration to Comet ML."""
        if not self.comet_experiment:
            return

        try:
            # Log main config
            if hasattr(config, "__dict__"):
                self.comet_experiment.log_parameters(config.__dict__)

        except Exception as e:
            lg.warning(f"Failed to log config to Comet ML: {e}")

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ""
    ):
        """Log metrics to Comet ML."""
        if not self.comet_experiment:
            return

        try:
            comet_metrics = {f"{prefix}{k}": v for k, v in metrics.items()}
            self.comet_experiment.log_metrics(comet_metrics, step=step)
        except Exception as e:
            lg.warning(f"Failed to log metrics to Comet ML: {e}")

    def log_dataset_info(self, dataset_name: str, dataset: datasets.Dataset):
        """Log dataset information to Comet ML."""
        if not self.comet_experiment:
            return

        try:
            dataset_info = {
                f"{dataset_name}_size": len(dataset) if dataset else 0,
                f"{dataset_name}_features": list(dataset.features.keys())
                if dataset
                else [],
            }
            self.comet_experiment.log_parameters(dataset_info)
        except Exception as e:
            lg.warning(f"Failed to log dataset info to Comet ML: {e}")

    def log_text(self, text: str):
        self.comet_experiment.log_text(text)

    def log_model(self, model_name: str, save_dir: str):
        self.comet_experiment.log_model(model_name, save_dir)

    def finish(self):
        self.comet_experiment.end()
