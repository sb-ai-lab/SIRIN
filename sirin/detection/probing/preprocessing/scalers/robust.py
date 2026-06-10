from typing import Tuple

import numpy as np
import joblib

from sirin.detection.probing.preprocessing.scalers.base import FeatureScaler


class RobustScaler(FeatureScaler):
    def __init__(
        self,
        with_centering: bool = True,
        with_scaling: bool = True,
        quantile_range: Tuple[float, float] = (25.0, 75.0),
    ):
        super().__init__()
        self.with_centering = with_centering
        self.with_scaling = with_scaling
        self.quantile_range = quantile_range
        self.center_ = None
        self.scale_ = None

    def fit(self, X: np.ndarray, mask: np.ndarray) -> 'RobustScaler':
        """
        X shape: [batch_size, num_layers, num_tokens, emb_dim]
        mask shape: [batch_size, num_layers, num_tokens, emb_dim] (boolean or 0/1)
        Fit the scaler using quantiles across all dimensions except the first (batch_size)
        Only values where mask is True/1 are used for fitting
        """
        q_min, q_max = self.quantile_range

        # Create a masked array to ignore masked values
        X_masked = np.where(mask.astype(bool), X, np.nan)

        if self.with_centering:
            # Calculate median only for unmasked values using nanmedian
            self.center_ = np.nanmedian(
                X_masked, axis=(0, 2, 3), keepdims=True
            )  # Median
        else:
            self.center_ = np.zeros((1, X.shape[1], 1, X.shape[3]))

        if self.with_scaling:
            # Calculate quantiles only for unmasked values using nanpercentile
            q1 = np.nanpercentile(X_masked, q_min, axis=(0, 2, 3), keepdims=True)
            q3 = np.nanpercentile(X_masked, q_max, axis=(0, 2, 3), keepdims=True)

            self.scale_ = q3 - q1
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
        if self.center_ is None or self.scale_ is None:
            raise ValueError('Scaler has not been fitted yet')

        return (X - self.center_) / self.scale_

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """Inverse transform"""
        if not self.is_fitted:
            raise ValueError('Scaler has not been fitted yet')
        if self.center_ is None or self.scale_ is None:
            raise ValueError('Scaler has not been fitted yet')

        return X * self.scale_ + self.center_

    def save(self, filepath: str):
        joblib.dump(self, filepath)
