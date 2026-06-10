import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from loguru import logger as lg

from sirin.inference.adapters import ModelAdapterBase
from sirin.inference.model_manager import manage_active_model
from sirin.models.inference import OpenAIConfig


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
                'http_client': httpx.Client(proxy=self.config.proxy_url),
                # 'api_key': self.config.api_key,
            }

            if self.config.base_url:
                client_kwargs['base_url'] = self.config.base_url

            self._client = self.openai.OpenAI(**client_kwargs)
            
            # Create async client for parallel processing
            async_client_kwargs = client_kwargs.copy()
            async_client_kwargs['http_client'] = httpx.AsyncClient(proxy=self.config.proxy_url)
            self._async_client = self.openai.AsyncOpenAI(**async_client_kwargs)

        self._model_name = self.config.model_path
        self._is_loaded = True
        lg.info(f'Loaded OpenAI client for model: {self.config.model_path}')

    
    async def _make_single_request_async(
        self, 
        messages: List[Dict], 
        return_logprobs: bool, 
        **sampling_kwargs
    ) -> Union[str, Tuple[str, List]]:
        """Make a single async request to OpenAI API with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                response = await self._async_client.chat.completions.create(
                    model=self.config.model_path, 
                    messages=messages, 
                    **sampling_kwargs
                )

                generated_text = response.choices[0].message.content
                
                if return_logprobs and hasattr(response.choices[0], 'logprobs') and response.choices[0].logprobs is not None:
                    token_logprobs = response.choices[0].logprobs.content
                    if token_logprobs:
                        sequence_logprobs = []
                        for token_info in token_logprobs:
                            top_logprobs = []
                            if token_info.top_logprobs:
                                for top_token in token_info.top_logprobs:
                                    top_logprobs.append(top_token.logprob)                                        
                            else:
                                top_logprobs.append(token_info.logprob)                                    
                            sequence_logprobs.append(top_logprobs)
                        return generated_text, sequence_logprobs
                    else:
                        return generated_text, []
                else:
                    return generated_text, [] if return_logprobs else generated_text
                
            except Exception as e:
                lg.warning(f'Attempt {attempt + 1} failed: {e}')
                if attempt == self.config.max_retries - 1:
                    raise e
                await asyncio.sleep(2**attempt)
    
    def _make_single_request_sync(
        self, 
        messages: List[Dict], 
        return_logprobs: bool, 
        **sampling_kwargs
    ) -> Union[str, Tuple[str, List]]:
        """Make a single synchronous request to OpenAI API with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model_path, 
                    messages=messages, 
                    **sampling_kwargs
                )

                generated_text = response.choices[0].message.content
                
                if return_logprobs and hasattr(response.choices[0], 'logprobs') and response.choices[0].logprobs is not None:
                    token_logprobs = response.choices[0].logprobs.content
                    if token_logprobs:
                        sequence_logprobs = []
                        for token_info in token_logprobs:
                            top_logprobs = []
                            if token_info.top_logprobs:
                                for top_token in token_info.top_logprobs:
                                    top_logprobs.append(top_token.logprob)                                        
                            else:
                                top_logprobs.append(token_info.logprob)                                    
                            sequence_logprobs.append(top_logprobs)
                        return generated_text, sequence_logprobs
                    else:
                        return generated_text, []
                else:
                    return generated_text, [] if return_logprobs else generated_text
                
            except Exception as e:
                lg.warning(f'Attempt {attempt + 1} failed: {e}')
                if attempt == self.config.max_retries - 1:
                    raise e
                time.sleep(2**attempt)
    
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
        use_async: bool = True,
        max_concurrent: int = 10,
        **kwargs: Any,
    ) -> Union[List[str], Tuple[List[str], List[List[List[Tuple[str, float]]]]]]:
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
            return_logprobs: Whether to return logprobs
            top_logprobs: Number of top logprobs to return
            num_return_sequences: Number of sequences to return (not supported by OpenAI)
            use_async: Whether to use async processing for parallel requests
            max_concurrent: Maximum number of concurrent requests (for async mode)
            **kwargs: Additional sampling parameters
            
        Returns:
            List of generated texts, or tuple of (texts, logprobs) if return_logprobs=True
        """
        if num_return_sequences > 1:
            lg.warning('num_return_sequences > 1 is not supported by OpenAI API, using n=1.')
        
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
            return results

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