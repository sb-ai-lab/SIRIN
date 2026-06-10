import os
from typing import Any, Dict, Optional

from loguru import logger as lg

from sirin.loggers import LoggerBase

try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    SummaryWriter = None


class TensorBoardLogger(LoggerBase):
    def __init__(self, experiment_name: str, log_dir: str = 'runs', **kwargs):
        if SummaryWriter is None:
            raise ImportError(
                'Tensorboard is not installed. Install with: pip install tensorboard'
            )

        super().__init__(experiment_name=experiment_name)

        try:
            full_log_dir = os.path.join(log_dir, experiment_name)
            self.writer = SummaryWriter(log_dir=full_log_dir, **kwargs)
            self.log_dir = full_log_dir
            lg.info(
                f"TensorBoard logging initialized successfully. Logs saved to: {full_log_dir}"
            )
        except Exception as e:
            lg.warning(f"Failed to initialize TensorBoard: {e}")
            self.writer = None

    def log_metrics(
        self, metrics: Dict[str, float], step: Optional[int] = None, prefix: str = ''
    ):
        """Log scalar metrics to TensorBoard."""
        if not self.writer:
            return

        try:
            for key, val in metrics.items():
                full_key = f'{prefix}{key}' if prefix else key
                self.writer.add_scalar(full_key, val, step or 0)

        except Exception as e:
            lg.warning(f"Failed to log metrics to TensorBoard: {e}")

    def log_hyperparameters(self, config: Any):
        """Log configuration to TensorBoard."""
        if not self.writer:
            return

        try:
            # Log config as text
            if hasattr(config, '__dict__'):
                config_str = str(config.__dict__)
            elif isinstance(config, dict):
                config_str = str(config)
            else:
                config_str = str(config)

            self.writer.add_text('config', config_str, 0)
        except Exception as e:
            lg.warning(f"Failed to log config to TensorBoard: {e}")

    def log_dataset_info(self, dataset_name: str, dataset):
        """Log dataset information to TensorBoard."""
        if not self.writer:
            return

        try:
            info_text = f'Dataset: {dataset_name}\n'
            info_text += f'Size: {len(dataset) if dataset else 0}\n'
            if hasattr(dataset, 'features'):
                info_text += (
                    f'Features: {list(dataset.features.keys()) if dataset else []}\n'
                )

            self.writer.add_text(f'dataset/{dataset_name}', info_text, 0)
        except Exception as e:
            lg.warning(f"Failed to log dataset info to TensorBoard: {e}")

    def log_text(self, text: str):
        """Log text to TensorBoard."""
        if not self.writer:
            return

        try:
            self.writer.add_text('logs', text, 0)
        except Exception as e:
            lg.warning(f"Failed to log text to TensorBoard: {e}")

    def log_model(self, model_name: str, save_dir: str):
        """Log model to TensorBoard (as text info)."""
        if not self.writer:
            return

        try:
            self.writer.add_text(model_name, f'Model saved to: {save_dir}', 0)
        except Exception as e:
            lg.warning(f"Failed to log model info to TensorBoard: {e}")

    def finish(self):
        """Close the TensorBoard writer."""
        if self.writer:
            try:
                self.writer.close()
            except Exception as e:
                lg.warning(f"Failed to close TensorBoard writer: {e}")
