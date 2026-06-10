from sklearn.decomposition import PCA

from sirin.detection.probing.preprocessing.compressors.base import (
    FeatureCompressorBase,
)


class PCACompressor(FeatureCompressorBase):
    """PCA-based feature compression."""

    def _create_compressor(self) -> PCA:
        return PCA(
            n_components=self.n_components,
            random_state=self.random_state,
            svd_solver="auto",
        )
