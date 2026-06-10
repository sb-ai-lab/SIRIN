from typing import Optional

from loguru import logger as lg

from sirin.loggers import LoggerBase


class CatBoostLoggerCallback:
    """Forward per-iteration CatBoost eval metrics to a :class:`LoggerBase` logger.

    CatBoost's ``callbacks`` parameter accepts objects that implement
    ``after_iteration(info)``.  ``info.metrics`` is a nested dict::

        {
            "learn": {"Logloss": [value], ...},
            "validation": {"Logloss": [value], ...},
        }

    This callback flattens those series and forwards them at every iteration
    so that W&B / TensorBoard / etc. receive a proper learning curve.
    """

    def __init__(self, experiment_logger: Optional[LoggerBase] = None, prefix: str = "/catboost"):
        self.experiment_logger = experiment_logger
        self.prefix = prefix

    def after_iteration(self, info) -> bool:
        """Called by CatBoost after each boosting iteration.

        Returns ``True`` to continue training (``False`` would stop early).
        """
        if self.experiment_logger is None:
            return True

        step = info.iteration
        flat: dict = {}
        for split_name, metric_dict in (info.metrics or {}).items():
            for metric_name, values in metric_dict.items():
                if values:
                    flat[f"{split_name}/{metric_name}"] = float(values[-1])

        if flat:
            try:
                self.experiment_logger.log_metrics(flat, step=step, prefix=self.prefix)
            except Exception as exc:
                lg.warning(f"CatBoostLoggerCallback: failed to log metrics at step {step}: {exc}")

        return True
