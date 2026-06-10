from abc import ABC, abstractmethod
from typing import Any, Dict, List

from sirin.inference.adapters import ModelAdapterBase


class TargetApproximatorBase(ABC):
    def __init__(self, extractor: ModelAdapterBase):
        self.extractor = extractor

    @abstractmethod
    def __call__(self, samples: List[List[Dict]], **kwargs) -> Any:
        pass
