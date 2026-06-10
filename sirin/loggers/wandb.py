from typing import Any, Dict, Optional

from loguru import logger as lg

from sirin.loggers import LoggerBase

try:
    import wandb
except ImportError:
    wandb = None


class WandbLogger(LoggerBase):
    def __init__(self, experiment_name: str, config: Any, **kwargs):
        if wandb is None:
            raise ImportError("wandb is not installed. Install with: pip install wandb")

        super().__init__(experiment_name=experiment_name)

        try:
            # Initialize wandb run
            self.run = wandb.init(name=experiment_name, config=config, **kwargs)
            lg.info("Weights & Biases logging initialized successfully")
        except Exception as e:
            lg.warning(f"Failed to initialize Weights & Biases: {e}")
            self.run = None

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ""
    ):
        """Log scalar metrics to Weights & Biases."""
        if not self.run:
            return

        try:
            wandb_metrics = {f"{prefix}{k}": v for k, v in metrics.items()}
            if step is not None:
                wandb_metrics["step"] = step
            self.run.log(wandb_metrics, step=step)
        except Exception as e:
            lg.warning(f"Failed to log metrics to Weights & Biases: {e}")

    def log_hyperparameters(self, config: Any):
        """Log configuration to Weights & Biases."""
        if not self.run:
            return

        try:
            if hasattr(config, "__dict__"):
                self.run.config.update(config.__dict__)
            elif isinstance(config, dict):
                self.run.config.update(config)
        except Exception as e:
            lg.warning(f"Failed to log config to Weights & Biases: {e}")

    def log_dataset_info(self, dataset_name: str, dataset):
        """Log dataset information to Weights & Biases."""
        if not self.run:
            return

        try:
            dataset_info = {
                f"{dataset_name}_size": len(dataset) if dataset else 0,
            }
            if hasattr(dataset, "features"):
                dataset_info[f"{dataset_name}_features"] = (
                    list(dataset.features.keys()) if dataset else []
                )

            self.run.config.update(dataset_info)
        except Exception as e:
            lg.warning(f"Failed to log dataset info to Weights & Biases: {e}")

    def log_text(self, text: str):
        """Log text to Weights & Biases."""
        if not self.run:
            return

        try:
            self.run.log({"text": text})
        except Exception as e:
            lg.warning(f"Failed to log text to Weights & Biases: {e}")

    def log_model(self, model_name: str, save_dir: str):
        """Log model to Weights & Biases."""
        if not self.run:
            return

        try:
            # Log model as artifact
            artifact = wandb.Artifact(model_name, type="model")
            artifact.add_dir(save_dir)
            self.run.log_artifact(artifact)
        except Exception as e:
            lg.warning(f"Failed to log model to Weights & Biases: {e}")

    def finish(self):
        """Finish the Weights & Biases run."""
        if self.run:
            try:
                self.run.finish()
            except Exception as e:
                lg.warning(f"Failed to finish Weights & Biases run: {e}")
