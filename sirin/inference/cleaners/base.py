from abc import ABC, abstractmethod

class BaseCleaner(ABC):
    """Base class for all cleaners"""

    @abstractmethod
    def clean(self, text: str) -> str:
        """Clean the input text"""
        pass
