from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from sirin.models.inference import ModelAdapterBaseConfig


class ModelAdapterBase(ABC):
    """Abstract base class for all model implementations."""

    def __init__(
        self,
        config: Optional[ModelAdapterBaseConfig] = None,
        model: Any = None,
        tokenizer: Any = None,
    ):
        """Initialize the base model.

        Args:
            config: Model configuration from hydra config
        """
        self.device = config.device or "cpu"
        self.config = config
        self._is_loaded = False
        self.model = model
        self._model_name = None
        self.tokenizer = tokenizer

    @abstractmethod
    def load(self, model: Any = None, tokenizer: Any = None):
        """Load the model and tokenizer."""
        pass

    @abstractmethod
    def sample(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Generate text using sampling parameters.

        Args:
            prompts: List of input prompts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p (nucleus) sampling parameter
            top_k: Top-k sampling parameter
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: List of stop sequences
            **kwargs: Additional sampling parameters

        Returns:
            List of generated texts
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    @property
    def name(self) -> str:
        """Get model's name."""
        return self._model_name

    def unload(self):
        """Unload the model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self._is_loaded = False
