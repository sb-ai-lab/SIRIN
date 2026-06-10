import numpy as np
import joblib
from abc import ABC, abstractmethod

class FeatureScaler(ABC):
    """Abstract base class for feature scaling."""

    def __init__(self):
        self.is_fitted = False

    @abstractmethod
    def fit(self, X: np.ndarray, mask: np.ndarray) -> 'FeatureScaler':
        """Fit the scaler on the data."""
        pass

    @abstractmethod
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform the data using the fitted scaler."""
        pass

    @abstractmethod
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform the data."""
        pass

    def fit_transform(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Fit the scaler and transform the data."""
        return self.fit(X, mask).transform(X)

    @abstractmethod
    def save(self, filepath: str):
        """Save the scaler."""
        pass

    @classmethod
    def load(cls, filepath: str) -> 'FeatureScaler':
        """Load the scaler."""
        return joblib.load(filepath)
