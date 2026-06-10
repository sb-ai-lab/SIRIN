import numpy as np
import joblib

from sirin.detection.probing.preprocessing.scalers.base import FeatureScaler


class IdScaler(FeatureScaler):
    """A scaler that does nothing - used when scaling method is NONE."""

    def __init__(self):
        super().__init__()
        self.is_fitted = True

    def fit(self, X: np.ndarray, mask: np.ndarray) -> 'IdScaler':
        """No operation - just return self."""
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Return the input unchanged."""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        return X

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Return the input unchanged."""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        return X

    def save(self, filepath: str):
        joblib.dump(self, filepath)
