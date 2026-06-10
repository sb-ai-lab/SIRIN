import numpy as np
import joblib

from sirin.detection.probing.preprocessing.scalers.base import FeatureScaler


class StandardScaler(FeatureScaler):
    def __init__(self, with_mean: bool = True, with_std: bool = True):
        super().__init__()
        self.with_mean = with_mean
        self.with_std = with_std
        self.mean_ = None
        self.scale_ = None

    def fit(self, X: np.ndarray, mask: np.ndarray) -> 'StandardScaler':
        """
        X shape: [batch_size, num_layers, num_tokens, emb_dim]
        mask shape: [batch_size, num_layers, num_tokens, emb_dim] (boolean or 0/1)
        Fit the scaler to compute mean and std across all dimensions except the first (batch_size)
        Only values where mask is True/1 are used for fitting
        """
        # Create a masked array to ignore masked values
        X_masked = np.where(mask.astype(bool), X, np.nan)

        if self.with_mean:
            self.mean_ = np.nanmean(
                X_masked, axis=(0, 2, 3), keepdims=True
            )  # [1, num_layers, 1, emb_dim]
        else:
            self.mean_ = np.zeros((1, X.shape[1], 1, X.shape[3]))

        if self.with_std:
            self.scale_ = np.nanstd(
                X_masked, axis=(0, 2, 3), keepdims=True
            )  # [1, num_layers, 1, emb_dim]
            # Avoid division by zero
            self.scale_ = np.where(self.scale_ == 0, 1.0, self.scale_)
        else:
            self.scale_ = np.ones((1, X.shape[1], 1, X.shape[3]))

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform the input array"""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        if self.mean_ is None or self.scale_ is None:
            raise ValueError('Scaler has not been fitted yet')

        return (X - self.mean_) / self.scale_

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform"""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        if self.mean_ is None or self.scale_ is None:
            raise ValueError('Scaler has not been fitted yet')

        return X * self.scale_ + self.mean_

    def save(self, filepath: str):
        joblib.dump(self, filepath)
