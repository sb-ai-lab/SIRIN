from typing import List, Optional

from sirin.inference.adapters import ModelAdapterBase
from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.models.detection import SplitConfig


class ParagraphSplitter(TextSplitterBase):
    """Split text by paragraphs using newline delimiters."""
    
    def __init__(self, config: SplitConfig):
        self.config = config
        self.paragraph_delimiters = config.paragraph_delimiters or ['\n\n', '\r\n\r\n']
        self.num_paragraphs = getattr(config, 'num_paragraphs', 1)
        self.overlap = min(config.overlap, max(0, self.num_paragraphs - 1))
    
    def split(self, samples: List[str], model_adapter: Optional[ModelAdapterBase]) -> List[List[str]]:
        splitted_samples = []
        for sample in samples:
            paragraphs = [sample]
            
            for delimiter in self.paragraph_delimiters:
                new_paragraphs = []
                for para in paragraphs:
                    new_paragraphs.extend(para.split(delimiter))
                paragraphs = new_paragraphs
            
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            if self.num_paragraphs == 1 and self.overlap == 0:
                chunks = paragraphs
            else:
                step = max(1, self.num_paragraphs - self.overlap)
                chunks = ['\n\n'.join(paragraphs[i:i+self.num_paragraphs]) for i in range(0, len(paragraphs), step)]
                
                # Ensure at least one chunk is returned
                if not chunks and paragraphs:
                    chunks = ['\n\n'.join(paragraphs)]
                
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            
            chunks_with_prefix = self._apply_prefix(chunks)
            splitted_samples.append(chunks_with_prefix)
        
        return splitted_samples