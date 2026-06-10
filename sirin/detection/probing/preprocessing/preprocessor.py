import warnings
from typing import List, Optional, Union

import joblib
import numpy as np

from sirin.detection.probing.preprocessing.compressors import (
    FeatureCompressorBase,
    PCACompressor,
    UMAPCompressor
)
from sirin.detection.probing.preprocessing.scalers import (  # You'll need to create this module
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
    IdScaler,
    FeatureScaler
)
from sirin.detection.probing.preprocessing.compressors import PCACompressor
from sirin.detection.probing.preprocessing.compressors import UMAPCompressor
from sirin.definitions import CompressionMethod, ScalingMethod


class FeaturePreprocessor:
    """Adaptive feature compressor with scaling and compression for multiple features independently."""

    def __init__(
        self,
        method: Union[str, CompressionMethod] = CompressionMethod.PCA,
        scaling_method: Union[str, ScalingMethod] = ScalingMethod.STANDARD,
        compression_threshold: int = 500,
        target_dimensions: int = 300,
        random_state: int = 42,
        **compressor_kwargs,
    ):
        if isinstance(method, str):
            method = CompressionMethod(method.lower())
        if isinstance(scaling_method, str):
            scaling_method = ScalingMethod(scaling_method.lower())

        self.method = method
        self.scaling_method = scaling_method
        self.compression_threshold = compression_threshold
        self.target_dimensions = target_dimensions
        self.random_state = random_state
        self.compressor_kwargs = compressor_kwargs

        # Initialize components - one per feature
        self.scalers = []  # List of scalers for each feature
        self._compressors = []  # List of compressors for each feature
        self.is_fitted = False
        self.feature_shapes = []  # Store shapes for each feature
        self.feature_n_features = []  # Store number of features for each feature
        self._scaling_stats_list = []  # Store stats for each feature
        self.all_features_sum = 0

    def _create_scaler(self) -> FeatureScaler:
        """Create the appropriate scaler based on the scaling method."""
        if self.scaling_method == ScalingMethod.STANDARD:
            return StandardScaler()
        elif self.scaling_method == ScalingMethod.MINMAX:
            return MinMaxScaler()
        elif self.scaling_method == ScalingMethod.ROBUST:
            return RobustScaler()
        elif self.scaling_method == ScalingMethod.NONE:
            return IdScaler()
        else:
            raise ValueError(f"Unsupported scaling method: {self.scaling_method}")

    def _create_compressor(self, i: int) -> Optional[FeatureCompressorBase]:
        """Create the appropriate compressor based on method."""
        if self.method == CompressionMethod.NONE:
            return None

        batch_size, num_layers, num_tokens, emb_dim = self.feature_shapes[i]

        # Calculate target dimensions proportionally to the feature's size
        feature_ratio = num_layers*num_tokens*emb_dim / sum(self.feature_n_features)
        target_dims = max(1, int(self.target_dimensions * feature_ratio / num_layers))  # Ensure at least 1

        if self.method == CompressionMethod.PCA:
            return PCACompressor(
                n_components=target_dims, random_state=self.random_state
            )
        elif self.method == CompressionMethod.UMAP:
            return UMAPCompressor(
                n_components=target_dims,
                random_state=self.random_state,
                **self.compressor_kwargs,
            )
        else:
            raise ValueError(f"Unsupported compression method: {self.method}")

    def _validate_data(self, X: np.ndarray) -> np.ndarray:
        """Validate and prepare data for processing."""
        if len(X.shape) != 4:
            raise ValueError(
                f"Expected 4D input [batch_size, num_layers, num_tokens, emb_dim], got {X.shape}"
            )

        # Check for NaN or infinite values
        if np.isnan(X).any():
            warnings.warn('Data contains NaN values. Consider cleaning the data first.')
        if np.isinf(X).any():
            warnings.warn(
                'Data contains infinite values. Consider cleaning the data first.'
            )

        return X

    def fit(self, X_list: List[np.ndarray], mask_list: List[np.ndarray]) -> 'FeaturePreprocessor':
        """Fit the scaler and compressor for each feature independently."""
        if not X_list:
            raise ValueError("X_list cannot be empty")

        # Validate all features and calculate feature dimensions
        self.feature_shapes = []
        self.feature_n_features = []

        for i, X in enumerate(X_list):
            X = self._validate_data(X)
            self.feature_shapes.append(X.shape)
            batch_size, num_layers, num_tokens, emb_dim = X.shape
            self.feature_n_features.append(num_tokens * emb_dim * num_layers)

        self._needs_compression = sum(self.feature_n_features) > self.compression_threshold

        # Create and fit scaler/compressor for each feature independently
        self.scalers = []
        self._compressors = []

        for i, (X, mask) in enumerate(zip(X_list, mask_list)):
            # Create and fit scaler for this feature
            scaler = self._create_scaler()
            if self.scaling_method != ScalingMethod.NONE:
                scaler.fit(X, mask)
            else:
                scaler.is_fitted = True
            self.scalers.append(scaler)

            # Store statistics for this feature
            self._scaling_stats_list.append(
                {
                    'original_mean': np.mean(X, axis=(0, 2, 3)),
                    'original_std': np.std(X, axis=(0, 2, 3)),
                    'original_min': np.min(X, axis=(0, 2, 3)),
                    'original_max': np.max(X, axis=(0, 2, 3)),
                }
            )

            # Create and fit compressor for this feature if needed
            if self._needs_compression:
                compressor = self._create_compressor(i)
                if compressor is not None:
                    compressor.fit_layerwise(X)
                self._compressors.append(compressor)
            else:
                self._compressors.append(None)

        self.is_fitted = True
        return self

    def transform(self, X_list: List[np.ndarray]) -> List[np.ndarray]:
        """Transform multiple features using independently fitted scalers and compressors."""
        if not self.is_fitted:
            raise ValueError("Compressor must be fitted before transform")

        if len(X_list) != len(self.feature_shapes):
            raise ValueError(
                f"Number of features in X_list ({len(X_list)}) doesn't match fitted features ({len(self.feature_shapes)})"
            )

        if len(X_list) != len(self.scalers):
            raise ValueError(
                f"Number of features in X_list ({len(X_list)}) doesn't match number of scalers ({len(self.scalers)})"
            )

        # Validate all features
        for i, X in enumerate(X_list):
            X = self._validate_data(X)
            if X.shape[1:] != self.feature_shapes[i][1:]:
                raise ValueError(
                    f"Feature {i} shape mismatch: expected {self.feature_shapes[i][1:]}, got {X.shape[1:]}"
                )

        # Transform each feature independently
        transformed_features = []
        for i, X in enumerate(X_list):
            # Apply scaling
            X_scaled = self.scalers[i].transform(X)

            # Apply compression if fitted and needed
            if self._compressors[i] is not None and self._needs_compression:
                X_compressed = self._compressors[i].transform_layerwise(X_scaled)
                transformed_features.append(X_compressed)
            else:
                transformed_features.append(X_scaled)

        return transformed_features

    def fit_transform(self, X_list: List[np.ndarray], mask_list: List[np.ndarray]) -> List[np.ndarray]:
        """Fit and transform in one step."""
        return self.fit(X_list, mask_list).transform(X_list)

    def save(self, filepath: str):
        """Save the adaptive compressor state."""
        if not self.is_fitted:
            raise ValueError("Compressor must be fitted before saving")

        save_data = {
            'method': self.method.value,
            'scaling_method': self.scaling_method.value,
            'compression_threshold': self.compression_threshold,
            'target_dimensions': self.target_dimensions,
            'random_state': self.random_state,
            'compressor_kwargs': self.compressor_kwargs,
            'is_fitted': self.is_fitted,
            'feature_shapes': self.feature_shapes,
            'feature_n_features': self.feature_n_features,
            'scaling_stats_list': self._scaling_stats_list,
            'num_features': len(self.scalers),
        }

        # Save main config
        joblib.dump(save_data, f'{filepath}_config.joblib')

        # Save each scaler
        for i, scaler in enumerate(self.scalers):
            scaler.save(f'{filepath}_scaler_{i}.joblib')

        # Save each compressor
        for i, compressor in enumerate(self._compressors):
            if compressor is not None:
                compressor.save(f'{filepath}_compressor_{i}.joblib')

    @classmethod
    def load(cls, filepath: str) -> 'FeaturePreprocessor':
        """Load a fitted adaptive compressor."""
        # Load config
        config = joblib.load(f'{filepath}_config.joblib')

        # Create instance
        instance = cls(
            method=config['method'],
            scaling_method=config['scaling_method'],
            compression_threshold=config['compression_threshold'],
            target_dimensions=config['target_dimensions'],
            random_state=config['random_state'],
            **config['compressor_kwargs'],
        )

        instance.is_fitted = config['is_fitted']
        instance.feature_shapes = config['feature_shapes']
        instance.feature_n_features = config['feature_n_features']
        instance._scaling_stats_list = config.get('scaling_stats_list', [])

        # Load scalers
        instance.scalers = []
        for i in range(config['num_features']):
            # You'll need to load the correct scaler type based on the saved method
            # This requires knowing which scaler type was saved
            scaler = FeatureScaler.load(f'{filepath}_scaler_{i}.joblib')
            instance.scalers.append(scaler)

        # Load compressors
        instance._compressors = []
        for i in range(config['num_features']):
            compressor = None
            if instance.method == CompressionMethod.NONE:
                instance._compressors.append(None)
                continue
            try:
                if instance.method == CompressionMethod.PCA:
                    compressor = PCACompressor.load(f'{filepath}_compressor_{i}.joblib')
                elif instance.method == CompressionMethod.UMAP:
                    compressor = UMAPCompressor.load(
                        f'{filepath}_compressor_{i}.joblib'
                    )
                instance._compressors.append(compressor)
            except FileNotFoundError:
                # No compressor was saved for this feature (compression not needed)
                instance._compressors.append(None)

        return instance

    @property
    def compression_info(self) -> dict:
        """Get detailed information about the compression pipeline."""
        info = {
            'scaling_method': self.scaling_method.value,
            'compression_method': self.method.value,
            'total_features': sum(self.feature_n_features),
            'compression_threshold': self.compression_threshold,
            'target_dimensions': self.target_dimensions,
            'is_scaled': all(scaler.is_fitted for scaler in self.scalers),
            'is_compressed': any(comp is not None for comp in self._compressors),
            'num_features': len(self.feature_shapes),
            'feature_shapes': self.feature_shapes,
            'feature_n_features': self.feature_n_features,
        }

        # Add info for each feature
        feature_info = []
        for i in range(len(self.feature_shapes)):
            feat_info = {
                'feature_index': i,
                'original_shape': self.feature_shapes[i],
                'original_features': self.feature_n_features[i],
                'is_compressed': self._compressors[i] is not None,
                'scaling_stats': self._scaling_stats_list[i],
            }
            if self._compressors[i] is not None:
                feat_info.update(
                    {
                        'compressed_dimensions': self._compressors[i].n_components,
                        'compression_ratio': self._compressors[i].n_components
                        / self.feature_n_features[i],
                    }
                )
            feature_info.append(feat_info)

        info['features'] = feature_info
        return info