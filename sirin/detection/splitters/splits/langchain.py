from typing import Any, Dict, List, Optional

from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import SplitConfig


class LangChainSplitter(TextSplitterBase):
    """Wrapper for LangChain text splitters."""

    def __init__(self, config: SplitConfig):
        self.config = config
        try:
            from langchain_text_splitters import (
                CharacterTextSplitter,
                MarkdownTextSplitter,
                PythonCodeTextSplitter,
                RecursiveCharacterTextSplitter,
                TokenTextSplitter,
            )
        except ImportError:
            raise ImportError(
                'Please install langchain: `pip install langchain` to use LangChain splitters.'
            )

        self.splitter_type = config.langchain_splitter_type
        self.splitter_kwargs = config.langchain_splitter_kwargs or {}
        
        # Add chunk_overlap if not explicitly set and config.overlap is specified
        if 'chunk_overlap' not in self.splitter_kwargs and config.overlap > 0:
            self.splitter_kwargs['chunk_overlap'] = config.overlap

        splitter_map = {
            'RecursiveCharacterTextSplitter': RecursiveCharacterTextSplitter,
            'CharacterTextSplitter': CharacterTextSplitter,
            'TokenTextSplitter': TokenTextSplitter,
            'MarkdownTextSplitter': MarkdownTextSplitter,
            'PythonCodeTextSplitter': PythonCodeTextSplitter,
        }

        if self.splitter_type not in splitter_map:
            available_splitters = list(splitter_map.keys())
            raise ValueError(
                f"Unknown LangChain splitter type: {self.splitter_type}. "
                f"Available types: {available_splitters}"
            )

        self.splitter = splitter_map[self.splitter_type](**self.splitter_kwargs)

    def split(self, samples: List[str], model_adapter: Optional[ModelAdapterBase]) -> List[List[str]]:
        splitted_samples = []
        for sample in samples:
            chunks = self.splitter.split_text(sample)
            splitted_samples.append(chunks)
        
        return [self._apply_prefix(chunks) for chunks in splitted_samples]
