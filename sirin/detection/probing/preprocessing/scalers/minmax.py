from typing import Tuple

import numpy as np
import joblib

from sirin.detection.probing.preprocessing.scalers.base import FeatureScaler


class MinMaxScaler(FeatureScaler):
    def __init__(self, feature_range: Tuple[float, float] = (0, 1)):
        super().__init__()
        self.feature_range = feature_range
        self.min_ = None
        self.max_ = None
        self.scale_ = None
        self.min_range = feature_range[0]
        self.max_range = feature_range[1]

    def fit(self, X: np.ndarray, mask: np.ndarray) -> 'MinMaxScaler':
        """
        X shape: [batch_size, num_layers, num_tokens, emb_dim]
        mask shape: [batch_size, num_layers, num_tokens, emb_dim] (boolean or 0/1)
        Fit the scaler to compute min and max across all dimensions except the first (batch_size)
        Only values where mask is True/1 are used for fitting
        """
        # Create a masked array to ignore masked values
        X_masked = np.where(mask.astype(bool), X, np.nan)

        # Calculate min and max only for unmasked values
        self.min_ = np.nanmin(
            X_masked, axis=(0, 2, 3), keepdims=True
        )  # [1, num_layers, 1, emb_dim]
        self.max_ = np.nanmax(
            X_masked, axis=(0, 2, 3), keepdims=True
        )  # [1, num_layers, 1, emb_dim]

        # Handle case where min == max (constant features)
        range_ = self.max_ - self.min_
        range_ = np.where(range_ == 0, 1.0, range_)

        self.scale_ = (self.max_range - self.min_range) / range_

        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform the input array"""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        if self.min_ is None or self.max_ is None:
            raise ValueError('Scaler has not been fitted yet')

        X_scaled = (X - self.min_) * self.scale_ + self.min_range
        return X_scaled

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform"""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        if self.min_ is None or self.scale_ is None:
            raise ValueError('Scaler has not been fitted yet')

        X_inv = (X - self.min_range) / self.scale_ + self.min_
        return X_inv

    def save(self, filepath: str):
        joblib.dump(self, filepath)
