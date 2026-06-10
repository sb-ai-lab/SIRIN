import re
from typing import Any, Dict

from sirin.inference.cleaners.base import BaseCleaner


class CodeCleaner(BaseCleaner):
    """Cleaner for code-related cleaning"""

    def __init__(self, params: Dict[str, Any]):
        self.remove_comments = params.get('remove_comments', False)
        self.normalize_indentation = params.get('normalize_indentation', False)
        self.remove_code_blocks = params.get('remove_code_blocks', False)
        self.code_block_patterns = params.get(
            'code_block_patterns', [r'```.*?```', r'`.*?`']
        )

    def clean(self, text: str) -> str:
        result = text

        if self.remove_code_blocks:
            for pattern in self.code_block_patterns:
                result = re.sub(pattern, '', result, flags=re.DOTALL)

        if self.remove_comments:
            # Simple comment removal (can be extended for different languages)
            result = re.sub(r'#.*$', '', result, flags=re.MULTILINE)
            result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)

        return result
