from typing import Any, Dict
import re

from sirin.inference.cleaners.base import BaseCleaner


class HTMLCleaner(BaseCleaner):
    """Cleaner that removes HTML tags"""

    def __init__(self, params: Dict[str, Any]):
        self.remove_tags = params.get('remove_tags', True)
        self.decode_entities = params.get('decode_entities', True)

    def clean(self, text: str) -> str:
        import html

        result = text

        if self.remove_tags:
            # Remove HTML tags
            result = re.sub(r'<[^>]+>', '', result)

        if self.decode_entities:
            # Decode HTML entities
            result = html.unescape(result)

        return result
