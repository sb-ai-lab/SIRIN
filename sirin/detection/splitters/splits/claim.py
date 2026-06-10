import json
import re
from typing import List, Optional

from loguru import logger as lg

from sirin.detection.splitters.splits.base import TextSplitterBase
from sirin.inference.adapters.base import ModelAdapterBase
from sirin.inference.model_manager import ModelManager
from sirin.models.detection import SplitConfig


class ClaimSplitter(TextSplitterBase):
    def __init__(self, config: SplitConfig):
        self.config = config
        self.prompt = config.prompt
        self.batch_size = config.batch_size
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.stop_tokens = config.stop_tokens or ['}']
        self.enable_high_recall = config.enable_high_recall or True

    def split(
        self, samples: List[str], model_adapter: ModelAdapterBase
    ) -> List[List[str]]:
        model_adapter = ModelManager.load_model(model_adapter)
        batch_size = self.batch_size or len(samples)

        final_results: List[List[str]] = []

        for batch_idx in range(0, len(samples), batch_size):
            facts = []
            batch = samples[batch_idx : batch_idx + batch_size]

            prompts = [self.prompt.format(text=sample_text) for sample_text in batch]

            try:
                outputs = model_adapter.sample(
                    inputs=prompts,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    stop=self.stop_tokens,
                )

                facts = [self._extract_claims(output + '}') for output in outputs]
                for fact_idx in range(len(facts)):
                    if facts[fact_idx] is None or not facts[fact_idx]:
                        facts[fact_idx] = [batch[fact_idx]]
                        lg.warning(f'Facts not found for sample. Supposing sample is being the fact itself')

            except Exception as e:
                lg.error(f'Model call failed for batch #{batch_idx}-{batch_idx + batch_size}: {e}')

            final_results.extend(facts)

        return [self._apply_prefix(chunks) for chunks in final_results]

    @staticmethod
    def _find_json_between_fences(text: str) -> Optional[str]:
        patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
        ]
        for p in patterns:
            m = re.search(p, text, re.DOTALL | re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    @staticmethod
    def _find_first_brace_json(text: str) -> Optional[str]:
        stack = []
        start = None
        for i, ch in enumerate(text):
            if ch == '{':
                if start is None:
                    start = i
                stack.append('{')
            elif ch == '}' and stack:
                stack.pop()
                if not stack and start is not None:
                    return text[start : i + 1]
        return None

    @staticmethod
    def _repair_json(s: str) -> str:
        s = re.sub(r',\s*([}\]])', r'\1', s)
        if '"' not in s and s.count("'") > 0:
            s = s.replace("'", '"')
        return s

    @staticmethod
    def _extract_claims(text: str) -> Optional[List[str]]:
        candidates = []

        c = ClaimSplitter._find_json_between_fences(text)
        if c:
            candidates.append(c)

        c = ClaimSplitter._find_first_brace_json(text)
        if c:
            candidates.append(c)

        candidates.append(text)

        for c in candidates:
            try:
                repaired = ClaimSplitter._repair_json(c)
                parsed = json.loads(repaired)

                if isinstance(parsed, dict) and 'atomic_facts' in parsed:
                    if isinstance(parsed['atomic_facts'], list):
                        return parsed['atomic_facts']

                if isinstance(parsed, list):
                    return parsed

            except Exception:
                continue

        return None
