from typing import List, Optional

from sirin.inference.adapters import ModelAdapterBase
from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.models.detection import SplitConfig


class CharacterSplitter(TextSplitterBase):
    """Split text by custom chunk size with optional overlap."""
    
    def __init__(self, config: SplitConfig):
        self.config = config
        self.chunk_size = config.chunk_size
        self.overlap = min(config.overlap, max(0, self.chunk_size - 1))
    
    def split(self, samples: List[str], model_adapter: Optional[ModelAdapterBase]) -> List[List[str]]:
        splitted_samples = []
        for sample in samples:
            if len(sample) <= self.chunk_size:
                chunks = [sample]
                chunks_with_prefix = self._apply_prefix(chunks)
                splitted_samples.append(chunks_with_prefix)
                continue
            
            chunks = []
            start = 0
            step = max(1, self.chunk_size - self.overlap)
            
            while start < len(sample):
                end = min(start + self.chunk_size, len(sample))
                chunk = sample[start:end]
                chunks.append(chunk)
                start += step
            
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            chunks_with_prefix = self._apply_prefix(chunks)
            splitted_samples.append(chunks_with_prefix)
        
        return splitted_samples
