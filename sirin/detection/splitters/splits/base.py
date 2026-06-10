from abc import ABC, abstractmethod

from typing import List, Optional

from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import SplitConfig


class TextSplitterBase(ABC):
    """Abstract base class for different text splitting strategies."""
    
    def __init__(self, config: SplitConfig):
        self.config = config
    
    def _apply_prefix(self, chunks: List[str]) -> List[str]:
        if self.config.prefix is None or not self.config.prefix:
            return chunks
        
        return [f"{self.config.prefix}{chunk}" for chunk in chunks]
    
    @abstractmethod
    def split(self, samples: List[str], model_adapter: Optional[ModelAdapterBase]) -> List[List[str]]:
        pass