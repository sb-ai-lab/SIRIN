from typing import Any, Dict
import re

from sirin.inference.cleaners.base import BaseCleaner


class CustomCleaner(BaseCleaner):
    """Cleaner that applies custom functions"""

    def __init__(self, params: Dict[str, Any]):
        self.functions = params.get('functions', [])
        self.function_map = {
            'lowercase': self._lowercase,
            'uppercase': self._uppercase,
            'remove_digits': self._remove_digits,
            'remove_punctuation': self._remove_punctuation,
        }

    def _lowercase(self, text: str) -> str:
        return text.lower()

    def _uppercase(self, text: str) -> str:
        return text.upper()

    def _remove_digits(self, text: str) -> str:
        return re.sub(r'\d+', '', text)

    def _remove_punctuation(self, text: str) -> str:
        return re.sub(r'[^\w\s]', '', text)

    def clean(self, text: str) -> str:
        result = text
        for func_name in self.functions:
            if func_name in self.function_map:
                result = self.function_map[func_name](result)
        return result
