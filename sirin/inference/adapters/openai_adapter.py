import asyncio
import hashlib
import json
import math
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import httpx
from loguru import logger as lg

from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.model_manager import manage_active_model
from sirin.models.inference import OpenAIConfig


def _extract_sequence_logprobs(token_logprobs) -> List[List[Tuple[str, float]]]:
    """Flatten an OpenAI ``logprobs.content`` payload to ``[[(token, logprob), ...], ...]``.

    One inner list per generated position, holding that position's top-k alternatives in
    descending-probability order (the API's own ordering).

    The token STRING is load-bearing and must not be dropped. A classifier judge needs to
    know *which* class a logprob belongs to; a bare float only says how confident the model
    was, which is identical for a confident "0" and a confident "1". Returning floats alone
    is what forced `SequenceOpenAIJudge`/`ClaimOpenAIJudge` into `prob = -logprob`, a
    class-blind score that yields chance-level AUROC.
    """
    sequence_logprobs = []
    for token_info in token_logprobs:
        if token_info.top_logprobs:
            alternatives = [(t.token, t.logprob) for t in token_info.top_logprobs]
        else:
            alternatives = [(token_info.token, token_info.logprob)]
        sequence_logprobs.append(alternatives)
    return sequence_logprobs


class OpenAIModelAdapter(ModelAdapterBase):
    """OpenAI API model implementation for inference."""

    def __init__(
        self,
        config: Optional[OpenAIConfig] = None,
        model: Any = None,
        tokenizer: Any = None,
    ):
        try:
            import openai

            self.openai = openai
        except ImportError:
            raise ImportError(
                'openai package is not available. Please install openai to use OpenAIModelAdapter.'
            )

        super().__init__(config, model, tokenizer)
        self._client = None
        self._async_client = None
        # Per-choice finish_reasons of the last n>1 sample() call: one inner list per input,
        # aligned 1:1 with that input's returned generations. None for n==1 calls.
        self.last_finish_reasons: Optional[List[List[Optional[str]]]] = None

    def load(self, model: Any = None, tokenizer: Any = None):
        """Load the OpenAI client."""
        if self._is_loaded:
            lg.warning('OpenAI client already loaded')
            return

        if model is not None:
            self._client = model
            # Async client will be created on demand
        else:
            client_kwargs = {
                'http_client': httpx.Client(
                    proxy=self.config.proxy_url, timeout=self.config.timeout
                ),
                'timeout': self.config.timeout,
            }
            # honor an explicit api_key (e.g. an OpenRouter key) but keep the
            # SDK's OPENAI_API_KEY env fallback when config.api_key is None.
            if self.config.api_key:
                client_kwargs['api_key'] = self.config.api_key

            if self.config.base_url:
                client_kwargs['base_url'] = self.config.base_url

            self._client = self.openai.OpenAI(**client_kwargs)
            
            # Create async client for parallel processing
            async_client_kwargs = client_kwargs.copy()
            async_client_kwargs['http_client'] = httpx.AsyncClient(
                proxy=self.config.proxy_url, timeout=self.config.timeout
            )
            self._async_client = self.openai.AsyncOpenAI(**async_client_kwargs)

        self._model_name = self.config.model_path
        self._is_loaded = True
        lg.info(f'Loaded OpenAI client for model: {self.config.model_path}')

    @staticmethod
    def _require_choices(response):
        """A response with no choices (observed on OpenRouter free routes under provider
        hiccups: HTTP 200 with an error body) must count as a failed attempt and retry."""
        if not getattr(response, 'choices', None):
            raise ValueError('OpenAI-compatible response returned no choices.')
        return response

    @staticmethod
    def _is_non_retryable(error: Exception) -> bool:
        """A 4xx (except 429 rate-limit) is a client error retrying can't fix -- fail fast
        so callers (e.g. the logprobs-unsupported judge fallback) react without burning the
        full backoff schedule."""
        status = getattr(error, 'status_code', None)
        return isinstance(status, int) and 400 <= status < 500 and status != 429

    async def _create_with_retry_async(self, messages: List[Dict], **create_kwargs):
        """One async chat completion with exponential-backoff retry."""
        if self.config.extra_body:
            create_kwargs.setdefault('extra_body', self.config.extra_body)
        for attempt in range(self.config.max_retries):
            try:
                return self._require_choices(
                    await self._async_client.chat.completions.create(
                        model=self.config.model_path, messages=messages, **create_kwargs
                    )
                )
            except Exception as e:
                lg.warning(f'Attempt {attempt + 1} failed: {e}')
                if self._is_non_retryable(e) or attempt == self.config.max_retries - 1:
                    raise e
                await asyncio.sleep(2**attempt)

    def _create_with_retry_sync(self, messages: List[Dict], **create_kwargs):
        """One synchronous chat completion with exponential-backoff retry."""
        if self.config.extra_body:
            create_kwargs.setdefault('extra_body', self.config.extra_body)
        for attempt in range(self.config.max_retries):
            try:
                return self._require_choices(
                    self._client.chat.completions.create(
                        model=self.config.model_path, messages=messages, **create_kwargs
                    )
                )
            except Exception as e:
                lg.warning(f'Attempt {attempt + 1} failed: {e}')
                if self._is_non_retryable(e) or attempt == self.config.max_retries - 1:
                    raise e
                time.sleep(2**attempt)

    @staticmethod
    def _texts_from_response(
        response, texts: List[str], finish_reasons: List[Optional[str]]
    ) -> None:
        if not response.choices:
            raise ValueError('OpenAI-compatible response returned no choices for n>1.')
        for choice in response.choices:
            texts.append(choice.message.content)
            finish_reasons.append(getattr(choice, 'finish_reason', None))

    async def _make_single_request_async(
        self,
        messages: List[Dict],
        return_logprobs: bool,
        **sampling_kwargs
    ) -> Union[str, List[str], Tuple[str, List]]:
        """One input -> str (n==1), (str, logprobs) (n==1 + logprobs), or (texts, finish_reasons) (n>1)."""
        n = sampling_kwargs.pop('n', 1)
        if n > 1:
            texts: List[str] = []
            finish_reasons: List[Optional[str]] = []
            per_call = n  # ask for all n first; top up singly when the provider returns fewer.
            while len(texts) < n:
                response = await self._create_with_retry_async(
                    messages, n=per_call, **sampling_kwargs
                )
                self._texts_from_response(response, texts, finish_reasons)
                per_call = 1
            return texts[:n], finish_reasons[:n]

        response = await self._create_with_retry_async(messages, **sampling_kwargs)
        generated_text = response.choices[0].message.content
        if (
            return_logprobs
            and getattr(response.choices[0], 'logprobs', None) is not None
        ):
            token_logprobs = response.choices[0].logprobs.content
            return generated_text, _extract_sequence_logprobs(token_logprobs or [])
        return (generated_text, []) if return_logprobs else generated_text

    def _make_single_request_sync(
        self,
        messages: List[Dict],
        return_logprobs: bool,
        **sampling_kwargs
    ) -> Union[str, List[str], Tuple[str, List]]:
        """One input -> str (n==1), (str, logprobs) (n==1 + logprobs), or (texts, finish_reasons) (n>1)."""
        n = sampling_kwargs.pop('n', 1)
        if n > 1:
            texts: List[str] = []
            finish_reasons: List[Optional[str]] = []
            per_call = n  # ask for all n first; top up singly when the provider returns fewer.
            while len(texts) < n:
                response = self._create_with_retry_sync(
                    messages, n=per_call, **sampling_kwargs
                )
                self._texts_from_response(response, texts, finish_reasons)
                per_call = 1
            return texts[:n], finish_reasons[:n]

        response = self._create_with_retry_sync(messages, **sampling_kwargs)
        generated_text = response.choices[0].message.content
        if (
            return_logprobs
            and getattr(response.choices[0], 'logprobs', None) is not None
        ):
            token_logprobs = response.choices[0].logprobs.content
            return generated_text, _extract_sequence_logprobs(token_logprobs or [])
        return (generated_text, []) if return_logprobs else generated_text

    async def _make_batch_async(
        self, 
        messages_batch: List[List[Dict]], 
        return_logprobs: bool, 
        max_concurrent: int = 10,
        **sampling_kwargs
    ):
        """Make batch requests asynchronously with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(messages):
            async with semaphore:
                return await self._make_single_request_async(messages, return_logprobs, **sampling_kwargs)
        
        results = await asyncio.gather(*[process_with_semaphore(msg) for msg in messages_batch])
        
        if return_logprobs:
            texts = [r[0] for r in results]
            logprobs = [r[1] for r in results]
            return texts, logprobs
        else:
            return results
    
    def _make_request(
        self, 
        messages_batch: List[List[Dict]], 
        return_logprobs: bool, 
        use_async: bool = True,
        max_concurrent: int = 10,
        **sampling_kwargs
    ):
        """Make batch requests to OpenAI API.
        
        Args:
            messages_batch: Batch of message lists to process
            return_logprobs: Whether to return logprobs
            use_async: Whether to use async processing for parallel requests
            max_concurrent: Maximum number of concurrent requests (for async mode)
            **sampling_kwargs: Additional sampling parameters
        """
        # Use async for better performance when processing multiple requests
        if use_async and len(messages_batch) > 1 and self._async_client is not None:
            lg.debug(f"Processing {len(messages_batch)} requests in parallel (async)")
            return asyncio.run(
                self._make_batch_async(
                    messages_batch, 
                    return_logprobs, 
                    max_concurrent=max_concurrent,
                    **sampling_kwargs
                )
            )
        else:
            # Sequential processing for single request or when async is disabled
            results = []
            logprobs_results = []
            
            for messages in messages_batch:
                result = self._make_single_request_sync(messages, return_logprobs, **sampling_kwargs)
                
                if return_logprobs:
                    results.append(result[0])
                    logprobs_results.append(result[1])
                else:
                    results.append(result)
            
            if return_logprobs:
                return results, logprobs_results
            else:
                return results

    @manage_active_model
    def sample(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
        return_logprobs: bool = False,
        top_logprobs: int = 1,
        num_return_sequences: int = 1,
        n: int = 1,
        use_async: bool = True,
        max_concurrent: int = 10,
        **kwargs: Any,
    ) -> Union[List[str], List[List[str]], Tuple[List[str], List[List[List[Tuple[str, float]]]]]]:
        """Generate text using OpenAI API with sampling parameters.

        Args:
            inputs: List of input strings or message lists
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p (nucleus) sampling parameter
            top_k: Top-k sampling parameter (not supported by OpenAI)
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: List of stop sequences
            return_logprobs: Whether to return logprobs (only valid with n==1)
            top_logprobs: Number of top logprobs to return
            num_return_sequences: Ignored by this adapter (HF-signature compatibility only);
                use ``n`` to request multiple generations per input.
            n: Generations per input. n==1 keeps the single-generation shape; n>1 requests
                multiple. Providers that ignore/return-fewer choices are topped up with n=1 calls.
            use_async: Whether to use async processing for parallel requests
            max_concurrent: Maximum number of concurrent requests (for async mode)
            **kwargs: Additional sampling parameters

        Returns:
            - n==1: ``list[str]`` (one text per input), or ``(list[str], list[logprobs])`` if
              ``return_logprobs``.
            - n>1: ``list[list[str]]`` (one inner list of n texts per input). ``return_logprobs``
              is NOT supported here and raises ``ValueError``.

        Side channel: ``self.last_finish_reasons`` is reset every call; after an n>1 call it holds
        one inner list per input, aligned 1:1 with that input's returned generations
        (e.g. 'length' marks a generation truncated by the token budget).
        """
        self.last_finish_reasons = None
        if return_logprobs and n > 1:
            raise ValueError('return_logprobs=True is not supported together with n>1.')
        if num_return_sequences > 1:
            lg.warning(
                'num_return_sequences is ignored by OpenAIModelAdapter; pass n=<k> to '
                'request multiple generations per input.'
            )

        messages_batch = []
        for input_item in inputs:
            if isinstance(input_item, list):
                messages = input_item
            else:
                messages = [{'role': 'user', 'content': input_item}]
            messages_batch.append(messages)

        sampling_kwargs = {
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
        }

        if stop_sequences:
            sampling_kwargs['stop'] = stop_sequences

        if top_k > 0:
            lg.warning('top_k parameter is not supported by OpenAI API, ignoring.')
        
        if return_logprobs:
            sampling_kwargs['logprobs'] = True
            sampling_kwargs['top_logprobs'] = top_logprobs

        # Remove our custom parameters before passing to OpenAI
        kwargs.pop('use_async', None)
        kwargs.pop('max_concurrent', None)
        sampling_kwargs.update(kwargs)

        # n is consumed per-request by _make_single_request_*; only forward it when >1 so the
        # n==1 request stays byte-identical to before (some providers reject an explicit n=1).
        if n > 1:
            sampling_kwargs['n'] = n

        if return_logprobs:
            results, logprobs_results = self._make_request(
                messages_batch, 
                return_logprobs=True, 
                use_async=use_async,
                max_concurrent=max_concurrent,
                **sampling_kwargs
            )
            return results, logprobs_results
        else:
            results = self._make_request(
                messages_batch,
                return_logprobs=False,
                use_async=use_async,
                max_concurrent=max_concurrent,
                **sampling_kwargs
            )
            if n > 1:
                # n>1 per-input results are (texts, finish_reasons) tuples; split the side
                # channel off so the public return shape stays list[list[str]].
                self.last_finish_reasons = [list(reasons) for _, reasons in results]
                return [list(texts) for texts, _ in results]
            return results

    @manage_active_model
    def stream(
        self,
        inputs: Union[List[str], List[List[Dict]]],
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = -1,
        stop_sequences: Optional[List[str]] = None,
        capture_token_uncertainty: bool = False,
        top_logprobs: int = 20,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream one OpenAI-compatible response and retain its exact token trace."""
        if len(inputs) != 1:
            raise ValueError('OpenAI-compatible streaming supports one input at a time.')
        input_item = inputs[0]
        messages = (
            input_item
            if isinstance(input_item, list)
            else [{'role': 'user', 'content': input_item}]
        )

        request: Dict[str, Any] = {
            'model': self.config.model_path,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'stream': True,
        }
        if stop_sequences:
            request['stop'] = stop_sequences
        if top_k > 0:
            lg.warning('top_k parameter is not supported by OpenAI APIs, ignoring.')
        if capture_token_uncertainty:
            request.update(logprobs=True, top_logprobs=top_logprobs)
            self.last_generation_trace = None
        config_extra_body = getattr(self.config, 'extra_body', None)
        extra_body = dict(config_extra_body) if config_extra_body else {}
        if 'qwen3.5' in self.config.model_path.lower():
            chat_template_kwargs = dict(extra_body.get('chat_template_kwargs') or {})
            chat_template_kwargs['enable_thinking'] = False
            extra_body['chat_template_kwargs'] = chat_template_kwargs
        if extra_body:
            request['extra_body'] = extra_body
        for key in ('seed', 'frequency_penalty', 'presence_penalty'):
            if key in kwargs:
                request[key] = kwargs[key]

        text = ''
        pieces: List[str] = []
        chosen_nll: List[float] = []
        token_entropy: List[float] = []
        response = self._client.chat.completions.create(**request)
        for event in response:
            if not event.choices:
                continue
            choice = event.choices[0]
            chunk = choice.delta.content or ''
            if not chunk:
                continue
            if capture_token_uncertainty:
                infos = list(getattr(choice.logprobs, 'content', None) or [])
                if not infos:
                    raise ValueError(
                        'OpenAI-compatible streamed content has no token logprobs.'
                    )
                scored_chunk = []
                reconstructed = ''
                for info in infos:
                    if reconstructed == chunk:
                        break  # vLLM may bundle the trailing stop token in this chunk.
                    piece = (
                        bytes(info.bytes).decode('utf-8')
                        if info.bytes
                        else info.token
                    )
                    if not chunk.startswith(reconstructed + piece):
                        break
                    reconstructed += piece
                    scored_chunk.append((piece, info))
                if reconstructed != chunk:
                    raise ValueError(
                        'OpenAI-compatible token trace does not reconstruct the '
                        'streamed answer exactly.'
                    )
                for piece, info in scored_chunk:
                    top = list(info.top_logprobs or [])
                    entropy = -sum(
                        math.exp(item.logprob) * item.logprob
                        for item in top
                        if math.isfinite(item.logprob)
                    )
                    pieces.append(piece)
                    chosen_nll.append(float(-info.logprob))
                    token_entropy.append(float(entropy))
            text += chunk
            yield chunk

        if capture_token_uncertainty:
            if not pieces or ''.join(pieces) != text:
                raise ValueError('OpenAI-compatible token trace is incomplete.')
            offsets = []
            cursor = 0
            for piece in pieces:
                offsets.append([cursor, cursor + len(piece)])
                cursor += len(piece)
            trace = {
                'text': text,
                'pieces': pieces,
                'offsets': offsets,
                'MaximumTokenProbability': chosen_nll,
                'TokenEntropy': token_entropy,
                'methods': ['MaximumTokenProbability', 'TokenEntropy'],
                'entropy_scope': f'top-{top_logprobs}',
                'temperature': float(temperature),
                'max_tokens': int(max_tokens),
                'input_sha256': hashlib.sha256(
                    json.dumps(
                        inputs, ensure_ascii=False, separators=(',', ':')
                    ).encode()
                ).hexdigest(),
            }
            trace['trace_sha256'] = hashlib.sha256(
                json.dumps(trace, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            self.last_generation_trace = trace

    def _convert_logprobs_to_tensor(self, token_logprobs):
        """Convert OpenAI logprobs to tensor format."""
        import torch

        if not token_logprobs:
            return torch.tensor([])

        logprob_values = []
        for token_info in token_logprobs:
            logprob_values.append(token_info.logprob)

        return torch.tensor(logprob_values)

    def unload(self):
        """Unload the OpenAI client."""
        if self._async_client is not None:
            # Close async client's http client if it exists
            if hasattr(self._async_client, '_client') and hasattr(self._async_client._client, 'aclose'):
                try:
                    asyncio.run(self._async_client._client.aclose())
                except Exception as e:
                    lg.warning(f"Failed to close async client: {e}")
        
        self._client = None
        self._async_client = None
        self._is_loaded = False
        lg.info('Unloaded OpenAI client')
