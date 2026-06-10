from sirin.detection.probing.preprocessing.compressors.base import (
    FeatureCompressorBase,
)

try:
    import umap
except ImportError:
    umap = None


class UMAPCompressor(FeatureCompressorBase):
    """UMAP-based feature compression."""

    def __init__(
        self,
        n_components: int,
        random_state: int = 42,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        metric: str = "euclidean",
        **kwargs,
    ):
        if umap is None:
            raise ImportError(
                "UMAP is not installed. Install with: pip install umap-learn"
            )

        super().__init__(n_components, random_state)
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.metric = metric
        self.kwargs = kwargs

    def _create_compressor(self) -> object:
        return umap.UMAP(
            n_components=self.n_components,
            random_state=self.random_state,
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            metric=self.metric,
            verbose=False,
            **self.kwargs,
        )
