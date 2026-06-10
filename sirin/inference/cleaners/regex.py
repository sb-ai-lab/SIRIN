from typing import Dict, Any
import re

from sirin.inference.cleaners.base import BaseCleaner


class RegexCleaner(BaseCleaner):
    """Cleaner that applies regex patterns"""

    def __init__(self, params: Dict[str, Any]):
        self.patterns = params.get('patterns', [])
        self.replacements = params.get('replacements', [])

        # Validate that patterns and replacements have same length
        if len(self.patterns) != len(self.replacements):
            raise ValueError('Number of patterns must match number of replacements')

    def clean(self, text: str) -> str:
        result = text
        for pattern, replacement in zip(self.patterns, self.replacements):
            result = re.sub(pattern, replacement, result)
        return result
