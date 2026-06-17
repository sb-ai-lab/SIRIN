from abc import ABC, abstractmethod

import joblib
import numpy as np


class FeatureCompressorBase(ABC):
    """Abstract base class for feature compression with layer-wise processing."""

    def __init__(self, n_components: int, random_state: int = 42):
        self.n_components = n_components
        self.random_state = random_state
        self.is_fitted = False
        self._compressors = []  # List of compressors for each layer
        self.n_features_in_ = None  # Number of input features per layer

    @abstractmethod
    def _create_compressor(self) -> object:
        """Create the compression model."""
        pass

    def fit(self, X: np.ndarray) -> "FeatureCompressorBase":
        if self._compressor is None:
            self._compressor = self._create_compressor()

        self._compressor.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted or self._compressor is None:
            raise ValueError("Compressor must be fitted before transform")
        return self._compressor.transform(X)

    def fit_layerwise(self, X: np.ndarray) -> "FeatureCompressorBase":
        """
        Fit compressor layer by layer.

        X shape: [batch_size, num_layers, num_tokens, emb_dim]
        """
        if len(X.shape) != 4:
            raise ValueError(
                f"Expected 4D input [batch_size, num_layers, num_tokens, emb_dim], got {X.shape}"
            )

        batch_size, num_layers, num_tokens, emb_dim = X.shape
        self.n_features_in_ = num_tokens * emb_dim

        # Create and fit compressor for each layer
        self._compressors = []
        for layer_idx in range(num_layers):
            layer_data = X[:, layer_idx, :, :]  # [batch_size, num_tokens, emb_dim]
            layer_reshaped = layer_data.reshape(
                batch_size, -1
            )  # [batch_size, num_tokens * emb_dim]

            compressor = self._create_compressor()
            compressor.fit(layer_reshaped)
            self._compressors.append(compressor)

        self.is_fitted = True
        return self

    def transform_layerwise(self, X: np.ndarray) -> np.ndarray:
        """
        Transform data layer by layer using fitted compressors.

        X shape: [batch_size, num_layers, num_tokens, emb_dim]
        Returns: [batch_size, num_layers, 1, compressed_dim]
        """
        if not self.is_fitted:
            raise ValueError("Compressor must be fitted before transform")

        if len(X.shape) != 4:
            raise ValueError(
                f"Expected 4D input [batch_size, num_layers, num_tokens, emb_dim], got {X.shape}"
            )

        batch_size, num_layers, num_tokens, emb_dim = X.shape

        if len(self._compressors) != num_layers:
            raise ValueError(
                f"Number of fitted compressors ({len(self._compressors)}) doesn't match number of layers ({num_layers})"
            )

        compressed_layers = []
        for layer_idx in range(num_layers):
            layer_data = X[:, layer_idx, :, :]  # [batch_size, num_tokens, emb_dim]
            layer_reshaped = layer_data.reshape(
                batch_size, -1
            )  # [batch_size, num_tokens * emb_dim]

            compressor = self._compressors[layer_idx]
            layer_compressed = compressor.transform(
                layer_reshaped
            )  # [batch_size, compressed_dim]

            # Reshape to [batch_size, 1, compressed_dim]
            layer_compressed = layer_compressed.reshape(batch_size, 1, -1)
            compressed_layers.append(layer_compressed)

        # Stack to [batch_size, num_layers, 1, compressed_dim]
        X_compressed = np.stack(compressed_layers, axis=1)
        return X_compressed

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit the compressor and transform the data."""
        return self.fit(X).transform(X)

    def save(self, filepath: str):
        """Save the fitted compressor."""
        if not self.is_fitted:
            raise ValueError("Compressor must be fitted before saving")

        compressors_data = []
        for compressor in self._compressors:
            compressor_data = {
                "compressor": compressor,
                "n_components": getattr(compressor, "n_components", self.n_components),
                "random_state": getattr(compressor, "random_state", self.random_state),
                "is_fitted": getattr(compressor, "is_fitted", True),
            }
            compressors_data.append(compressor_data)

        joblib.dump(
            {
                "compressors": compressors_data,
                "n_components": self.n_components,
                "random_state": self.random_state,
                "is_fitted": self.is_fitted,
                "n_features_in_": self.n_features_in_,
            },
            filepath,
        )

    @classmethod
    def load(cls, filepath: str) -> "FeatureCompressorBase":
        """Load a fitted compressor."""
        data = joblib.load(filepath)
        instance = cls(
            n_components=data["n_components"], random_state=data["random_state"]
        )

        # Load individual compressors
        instance._compressors = []
        for compressor_data in data["compressors"]:
            # Create compressor instance using the class method
            compressor_instance = instance._create_compressor()
            compressor_instance.__dict__.update(
                compressor_data["compressor"].__dict__
            )
            instance._compressors.append(compressor_instance)

        instance.is_fitted = data["is_fitted"]
        instance.n_features_in_ = data.get("n_features_in_", None)
        return instance
