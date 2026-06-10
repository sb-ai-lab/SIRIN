from typing import Any, Dict, List
import threading

import torch
from loguru import logger as lg

from sirin.models.inference import ModelManagerConfig
from sirin.inference.adapters import ModelAdapterBase
from sirin.utils.config_manager import validate_hydra_config


class ModelManager:
    """Manager class for loading and managing different model types."""

    _active_models: Dict[str, ModelAdapterBase] = {}
    _lock = threading.RLock()
    config = ModelManagerConfig()

    @classmethod
    @validate_hydra_config
    def setup_config(cls, config: ModelManagerConfig) -> None:
        """Initialize the model manager with given configuration."""
        cls.config = config

    @classmethod
    def load_model(
        cls,
        adapter: Any = None,
    ) -> ModelAdapterBase:
        """Create a model instance.
        Args:
            adapter: Adapter to load

        Returns:
            Model instance
        """
        model_id = id(adapter)
        with cls._lock:
            if model_id in cls._active_models:
                lg.debug(
                    f"{type(adapter)} model with ID {model_id} is already in use."
                )
            else:
                if cls.config.max_active_models <= len(cls._active_models):
                    cls._unload_least_recently_used_model()
                adapter.load()
                cls._active_models[model_id] = adapter
                lg.info(f"Created {type(adapter)} model with ID: {model_id}")

                if cls.config.auto_unload and cls._is_gpu_memory_high():
                    lg.warning(
                        "GPU memory usage above threshold; unloading least recently used model."
                    )
                    cls._unload_least_recently_used_model()

        return adapter

    @classmethod
    def _unload_least_recently_used_model(cls) -> None:
        """Unload the least recently used model to free resources."""
        with cls._lock:
            if not cls._active_models:
                lg.warning("No active models to unload.")
                return

            oldest_model_id = next(iter(cls._active_models))
            cls.unload_model(oldest_model_id)

    @classmethod
    def _is_gpu_memory_high(cls) -> bool:
        """Check if GPU memory usage exceeds threshold.
        
        For multi-device models, checks all GPUs and returns True if any GPU
        exceeds the threshold.
        """
        if not torch.cuda.is_available():
            return False

        num_gpus = torch.cuda.device_count()
        max_usage = 0.0
        
        for device_id in range(num_gpus):
            used = torch.cuda.memory_allocated(device_id)  # bytes
            total = torch.cuda.get_device_properties(device_id).total_memory  # bytes
            usage = used / total if total > 0 else 0.0
            max_usage = max(max_usage, usage)
            lg.debug(f"GPU {device_id} memory usage: {usage:.2%}")
        
        return max_usage > cls.config.memory_threshold

    @classmethod
    def unload_model(cls, model_id: str) -> None:
        """Unload a model by ID.

        Args:
            model_id: Model identifier
        """
        with cls._lock:
            if model_id in cls._active_models:
                cls._active_models[model_id].unload()
                del cls._active_models[model_id]
                lg.info(f"Unloaded model: {model_id}")
            else:
                lg.warning(f"Model '{model_id}' not found for unloading")

    @classmethod
    def unload_all_models(cls) -> None:
        """Unload all active models."""
        with cls._lock:
            # Create a copy of keys to avoid dictionary changing during iteration
            model_ids = list(cls._active_models.keys())
            for model_id in model_ids:
                cls.unload_model(model_id)
        lg.info("Unloaded all models")

    @classmethod
    def list_active_models(cls) -> List[str]:
        """List all active model IDs.

        Returns:
            List of active model IDs
        """
        with cls._lock:
            return list(cls._active_models.keys())


def manage_active_model(func):
    def wrapper(self, *args, **kwargs):
        self = ModelManager.load_model(self)
        return func(self, *args, **kwargs)

    return wrapper
