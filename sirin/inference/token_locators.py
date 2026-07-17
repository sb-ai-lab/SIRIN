from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from loguru import logger as lg
from transformers import PreTrainedTokenizerBase

from sirin.definitions import TokenLocation
from sirin.models.inference import TokenLocatorConfig
from sirin.utils.config_manager import validate_hydra_config


class TokenLocatorBase(ABC):
    """Base class for token locators."""

    tokens_to_locate: Optional[Set[int]] = None

    @abstractmethod
    def locate(
        self,
        tokens: List[int],
        tokenizer: Callable,
        answer_text: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Dict[str, Union[int, List[int]]], List[int]]:
        """Locate tokens based on implementation-specific logic."""
        pass

    @abstractmethod
    def _setup_tokens_to_locate(self) -> Set[str]:
        pass


class HfTokenLocator(TokenLocatorBase):
    """Token locator for question answering tasks."""

    @validate_hydra_config
    def __init__(self, config: TokenLocatorConfig):
        self.config = config

        self.n_to_answer_end_overlap_question = config.n_to_answer_end_overlap_question
        self.case_sensitive = config.case_sensitive
        self.first_substring = config.first_substring
        self._setup_tokens_to_locate()

    def _setup_tokens_to_locate(self) -> Set[str]:
        tokens_to_locate = set()

        if self.config.locate_eos:
            tokens_to_locate.add(TokenLocation.EOS.value)

        if (
            self.config.locate_answer_start
            or self.config.locate_answer_middle
            or self.config.locate_answer_end
            or self.config.n_to_answer_start > 0
            or self.config.n_to_answer_end > 0
        ):
            if self.config.locate_answer_end:
                tokens_to_locate.add(TokenLocation.ANS_END.value)

            if self.config.locate_answer_start:
                tokens_to_locate.add(TokenLocation.ANS_START.value)

            if self.config.locate_answer_middle:
                tokens_to_locate.add(TokenLocation.ANS_MID.value)

        for n_to_ in range(1, self.config.n_to_answer_end + 1):
            tokens_to_locate.add(f'{TokenLocation.N_TO_ANS_END.value}_{n_to_}')

        for n_to_ in range(1, self.config.n_to_answer_start + 1):
            tokens_to_locate.add(f'{TokenLocation.N_TO_ANS_START.value}_{n_to_}')

        if self.config.locate_substring:
            for index, search_substring in enumerate(self.config.substrings):
                tokens_to_locate.add(f'{TokenLocation.SUBSTRING.value}_{index}')

        self.tokens_to_locate = tokens_to_locate

    def _find_substring_locations(
        self,
        tokenizer: PreTrainedTokenizerBase,
        input_string: str,
        target_substring: str,
    ) -> Optional[List[int]]:
        """
        Find locations of tokens where a sequence of next tokens contains the substring.

        Args:
            tokenizer: The tokenizer to decode tokens
            input_string: The source string
            target_substring: The substring to search for

        Returns:
            List of token indices where the substring match starts or None if not found
        """
        if not target_substring:
            return []

        # Normalize target substring for comparison
        search_target = (
            target_substring if self.case_sensitive else target_substring.lower()
        )
        compare_string = input_string if self.case_sensitive else input_string.lower()

        substring_start = (
            compare_string.find(search_target)
            if self.first_substring
            else compare_string.rfind(search_target)
        )
        if substring_start == -1:
            return None

        substring_end = substring_start + len(search_target)
        encoding = tokenizer(input_string, return_offsets_mapping=True)

        overlapping_tokens = []
        for i, (start, end) in enumerate(encoding['offset_mapping']):
            if start < substring_end and end > substring_start:
                overlapping_tokens.append(i)

        return overlapping_tokens

    def locate(
        self,
        tokens: List[int],
        tokenizer: PreTrainedTokenizerBase,
        answer_text: Optional[str] = None,
    ) -> Dict[str, Union[int, List[int]]]:
        """
        Locate tokens based on various criteria.

        Args:
            tokens: List of token IDs
            tokenizer: Tokenizer to use for decoding
            answer_text: Optional answer text to locate

        Returns:
            Dictionary mapping output types to token positions
        """
        dout: Dict[str, Union[int, List[int]]] = {}

        lt = len(tokens)
        tokenizer = tokenizer.func if hasattr(tokenizer, 'func') else tokenizer

        if tokens[-1] == tokenizer.eos_token_id:
            eos_idx = lt - 1
            answer_last_idx = lt - 2
        else:
            eos_idx = None
            answer_last_idx = lt - 1

        if eos_idx is not None and self.config.locate_eos:
            dout[TokenLocation.EOS.value] = eos_idx

        n_to_answer_start = self.config.n_to_answer_start
        n_to_answer_end = self.config.n_to_answer_end

        # Original answer location logic
        if (
            self.config.locate_answer_start
            or self.config.locate_answer_middle
            or self.config.locate_answer_end
            or n_to_answer_start > 0
            or n_to_answer_end > 0
        ):
            if answer_text is None:
                raise ValueError(
                    f'Options requiring answer positions need `answer_text` to be provided.'
                )

            input_string = tokenizer.decode(tokens, skip_special_tokens=False)
            answer_start_char = input_string.rfind(answer_text)
            if answer_start_char < 0:
                raise ValueError('Answer text was not found in the rendered model input.')
            answer_end_char = answer_start_char + len(answer_text)
            full_offsets = tokenizer(
                input_string,
                return_offsets_mapping=True,
                add_special_tokens=False,
            )['offset_mapping']
            if len(full_offsets) != len(tokens):
                raise ValueError(
                    'Rendered input token alignment mismatch: '
                    f'{len(tokens)} token ids but {len(full_offsets)} offsets.'
                )
            answer_token_indices = [
                index
                for index, (start, end) in enumerate(full_offsets)
                if (start, end) != (0, 0)
                and end > answer_start_char
                and start < answer_end_char
            ]
            if not answer_token_indices:
                raise ValueError('Answer text overlaps no tokens in the rendered model input.')
            answer_start_idx = answer_token_indices[0]
            answer_last_idx = answer_token_indices[-1]

            if self.config.locate_answer_end:
                dout[TokenLocation.ANS_END.value] = answer_last_idx

            if self.config.locate_answer_start:
                dout[TokenLocation.ANS_START.value] = answer_start_idx

            if self.config.locate_answer_middle:
                if len(answer_token_indices) > 2:
                    dout[TokenLocation.ANS_MID.value] = answer_token_indices[
                        len(answer_token_indices) // 2
                    ]
                else:
                    dout[TokenLocation.ANS_MID.value] = answer_start_idx

        # Handle `n` tokens before `answer_last_idx`
        if n_to_answer_end > 0:
            n_to_ = 1
            current_idx_ = answer_last_idx - 1
            while current_idx_ >= 0 and n_to_ <= n_to_answer_end:
                if (
                    not self.n_to_answer_end_overlap_question
                    and current_idx_ < answer_start_idx
                ):
                    break

                dout[f'{TokenLocation.N_TO_ANS_END.value}_{n_to_}'] = current_idx_
                n_to_ += 1
                current_idx_ -= 1
            # To correctly process trimming
            while n_to_ <= n_to_answer_end:
                dout[f'{TokenLocation.N_TO_ANS_END.value}_{n_to_}'] = None
                n_to_ += 1

        elif n_to_answer_end != 0:
            raise ValueError(
                f'Unexpected value for `{TokenLocation.N_TO_ANS_END.value}`: '
                f'{n_to_answer_end}'
            )

        # Handle `n` tokens before `answer_start_idx`
        if n_to_answer_start > 0:
            n_to_ = 1
            current_idx_ = answer_start_idx - 1
            while current_idx_ >= 0 and n_to_ <= n_to_answer_start:
                dout[f'{TokenLocation.N_TO_ANS_START.value}_{n_to_}'] = current_idx_
                n_to_ += 1
                current_idx_ -= 1
            # To correctly process trimming
            while n_to_ <= n_to_answer_start:
                dout[f'{TokenLocation.N_TO_ANS_START.value}_{n_to_}'] = None
                n_to_ += 1

        elif n_to_answer_start != 0:
            raise ValueError(
                f'Unexpected value for `{TokenLocation.N_TO_ANS_START.value}`: '
                f'{n_to_answer_start}'
            )

        # Substring search functionality
        if self.config.locate_substring:
            for index, search_substring in enumerate(self.config.substrings):
                try:
                    # Decode token sequences and search for substring
                    substring_locations = self._find_substring_locations(
                        tokenizer=tokenizer,
                        input_string=tokenizer.decode(tokens),
                        target_substring=search_substring,
                    )
                    # Store all found locations
                    if substring_locations:
                        dout[f'{TokenLocation.SUBSTRING.value}_{index}'] = (
                            substring_locations
                        )
                        lg.debug(
                            f"Found substring '{search_substring}' at positions: {substring_locations}"
                        )
                    else:
                        lg.debug(f"Substring '{search_substring}' not found in tokens")
                except Exception as e:
                    lg.warning(f'Error in substring search: {e}')

        return dout
