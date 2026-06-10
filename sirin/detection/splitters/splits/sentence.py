from typing import List, Optional
import re

from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.inference.adapters import ModelAdapterBase
from sirin.models.detection import SplitConfig


class SentenceSplitter(TextSplitterBase):
    """Split text by sentences using common sentence delimiters."""
    
    def __init__(self, config: SplitConfig):
        self.config = config
        self.sentence_delimiters = config.sentence_delimiters or [
            r'\. +', r'! +', r'\? +', r'\.+\n', r'!+\n', r'\?+\n'
        ]
        self.num_sentences = config.num_sentences
        self.overlap = min(config.overlap, max(0, self.num_sentences - 1))
    
    def split(self, samples: List[str], model_adapter: Optional[ModelAdapterBase]) -> List[List[str]]:
        splitted_samples = []
        for sample in samples:
            sentences = [sample]
            
            for delimiter in self.sentence_delimiters:
                new_sentences = []
                for sentence in sentences:
                    parts = re.split(f'({delimiter})', sentence)
                    temp_sentences = []
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            temp_sentences.append(parts[i] + parts[i + 1])
                        else:
                            temp_sentences.append(parts[i])
                    new_sentences.extend(temp_sentences)
                sentences = [s.strip() for s in new_sentences if s.strip()]
            
            sentences = [s for s in sentences if len(s.strip()) > 0]

            step = max(1, self.num_sentences - self.overlap)
            chunks = [''.join(sentences[i:i+self.num_sentences]) for i in range(0, len(sentences), step)]
            
            # Ensure at least one chunk is returned
            if not chunks and sentences:
                chunks = [''.join(sentences)]
            
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            chunks_with_prefix = self._apply_prefix(chunks)
            splitted_samples.append(chunks_with_prefix)

        return splitted_samples