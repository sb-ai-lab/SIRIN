import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar, Union

import torch
from loguru import logger as lg


T = TypeVar('T')


def _safe_cat_tensors(
    tensors: List[torch.Tensor], 
    dim: int = 0,
    validate_shapes: bool = True,
) -> Optional[torch.Tensor]:
    """Safely concatenate tensors, handling different shapes.
    
    Args:
        tensors: List of tensors to concatenate
        dim: Dimension along which to concatenate
        validate_shapes: Whether to validate tensor shapes before concatenation
        
    Returns:
        Concatenated tensor or None if failed
    """
    if not tensors:
        return None
    
    if len(tensors) == 1:
        return tensors[0]
    
    try:
        # Validate shapes if requested
        if validate_shapes and len(tensors) > 1:
            first_shape = list(tensors[0].shape)
            for i, tensor in enumerate(tensors[1:], 1):
                shape = list(tensor.shape)
                # Check all dimensions except the concat dimension
                for d in range(len(first_shape)):
                    if d != dim and first_shape[d] != shape[d]:
                        lg.warning(
                            f"Shape mismatch in tensor {i}: dimension {d} has size {shape[d]} "
                            f"but expected {first_shape[d]}. Skipping validation."
                        )
                        validate_shapes = False
                        break
        
        return torch.cat(tensors, dim=dim)
    except RuntimeError as e:
        lg.error(f"Failed to concatenate tensors: {e}")
        return None


def merge_model_states(batch_results: List[Any]) -> Any:
    """Merge multiple ModelStates objects into a single one.
    
    Args:
        batch_results: List of ModelStates objects from different batches
        
    Returns:
        Merged ModelStates object or None if failed
    """
    from sirin.models.detection import ModelStates
    
    if not batch_results:
        return None
    
    if not isinstance(batch_results[0], ModelStates):
        # Not ModelStates, return as is
        return batch_results
    
    # Merge all fields
    all_hiddens = []
    all_attentions = []
    all_locations = []
    all_sublayers = []
    all_token_hallucinations = []
    all_masks = []
    all_logits = []
    all_logprobs = []
    
    for batch_result in batch_results:
        if batch_result.hiddens is not None:
            all_hiddens.extend(batch_result.hiddens)
        if batch_result.attentions is not None:
            all_attentions.extend(batch_result.attentions)
        if batch_result.locations is not None:
            if len(batch_result.locations) and isinstance(batch_result.locations[0], list):
                if len(all_locations):
                    for i, locations in enumerate(batch_result.locations):
                        all_locations[i].extend(locations)
                else:
                    all_locations = batch_result.locations
            else:
                all_locations.extend(batch_result.locations)
        if batch_result.sublayers is not None:
            all_sublayers.extend(batch_result.sublayers)
        if batch_result.token_hallucinations is not None:
            all_token_hallucinations.extend(batch_result.token_hallucinations)
        if batch_result.masks is not None:
            all_masks.append(batch_result.masks)
        if batch_result.logits is not None:
            all_logits.append(batch_result.logits)
        if batch_result.logprobs is not None:
            all_logprobs.append(batch_result.logprobs)
    
    # Safely concatenate tensors
    merged_masks = _safe_cat_tensors(all_masks, dim=0)
    merged_logits = _safe_cat_tensors(all_logits, dim=0)
    merged_logprobs = _safe_cat_tensors(all_logprobs, dim=0)
    
    return ModelStates(
        hiddens=all_hiddens if all_hiddens else None,
        attentions=all_attentions if all_attentions else None,
        locations=all_locations if all_locations else None,
        logits=merged_logits,
        sublayers=all_sublayers if all_sublayers else None,
        token_hallucinations=all_token_hallucinations if all_token_hallucinations else None,
        logprobs=merged_logprobs,
        masks=merged_masks,
    )


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
        
    Raises:
        ValueError: If chunk_size <= 0
    """
    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be positive, got {chunk_size}")
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def batch_processor(
    batch_size: Optional[int] = None,
    flatten_results: bool = True,
    log_progress: bool = True,
    continue_on_error: bool = False,
):
    """Decorator for automatic batch processing of inputs.
    
    This decorator automatically splits large input batches into smaller chunks
    and processes them sequentially. It's useful for managing memory usage
    and preventing OOM errors.
    
    Args:
        batch_size: Maximum size of each batch. If None, uses adapter's config.
        flatten_results: Whether to flatten results from multiple batches into a single list.
        log_progress: Whether to log batch processing progress.
        continue_on_error: Whether to continue processing if a batch fails.
        
    Example:
        @batch_processor(batch_size=32)
        def sample(self, inputs: List[str], **kwargs) -> List[str]:
            # This will be called with at most 32 inputs at a time
            return self.model.generate(inputs, **kwargs)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, inputs: Union[List[str], List[List[dict]]], *args, **kwargs):
            # Determine batch size
            effective_batch_size = batch_size
            if effective_batch_size is None:
                # Try to get from config
                if hasattr(self, 'config') and hasattr(self.config, 'batch_size'):
                    effective_batch_size = self.config.batch_size
                else:
                    # No batch size limit, process all at once
                    lg.debug("No batch_size configured, processing all inputs at once")
                    return func(self, inputs, *args, **kwargs)
            
            # FIX: Add None check before comparison
            if effective_batch_size is None or len(inputs) <= effective_batch_size:
                return func(self, inputs, *args, **kwargs)
            
            # Split into batches
            try:
                batches = chunk_list(inputs, effective_batch_size)
            except ValueError as e:
                lg.error(f"Failed to split inputs into batches: {e}")
                raise
            
            if log_progress:
                lg.info(
                    f"Processing {len(inputs)} inputs in {len(batches)} batches "
                    f"of size {effective_batch_size}"
                )
            
            # Process each batch
            all_results = []
            failed_batches = []
            
            for i, batch in enumerate(batches):
                if log_progress and len(batches) > 1:
                    lg.debug(f"Processing batch {i + 1}/{len(batches)}")
                
                try:
                    batch_result = func(self, batch, *args, **kwargs)
                    all_results.append(batch_result)
                except Exception as e:
                    lg.error(f"Failed to process batch {i + 1}/{len(batches)}: {e}")
                    failed_batches.append(i)
                    
                    if not continue_on_error:
                        raise
                    
                    # Append None placeholder for failed batch
                    all_results.append(None)
            
            if failed_batches and log_progress:
                lg.warning(
                    f"Failed to process {len(failed_batches)} batches: {failed_batches}. "
                    f"Results may contain None values."
                )
            
            # Return batches without flattening if requested
            if not flatten_results:
                return all_results
            
            # Check if we're dealing with ModelStates
            from sirin.models.detection import ModelStates
            if all_results and isinstance(all_results[0], ModelStates):
                return merge_model_states(all_results)
            
            # Handle different return types for non-ModelStates results
            final_results = []
            expected_tuple_length = None
            
            for i, batch_result in enumerate(all_results):
                if batch_result is None:
                    # Skip failed batches
                    continue
                    
                if isinstance(batch_result, tuple):
                    # Multiple return values (e.g., texts and logprobs)
                    if not final_results:
                        # Initialize structure for first batch
                        expected_tuple_length = len(batch_result)
                        final_results = [[] for _ in range(expected_tuple_length)]
                    elif len(batch_result) != expected_tuple_length:
                        # FIX: Validate tuple length consistency
                        raise ValueError(
                            f"Inconsistent tuple length in batch {i}: "
                            f"expected {expected_tuple_length}, got {len(batch_result)}"
                        )
                    
                    for j, result_part in enumerate(batch_result):
                        if isinstance(result_part, list):
                            final_results[j].extend(result_part)
                        else:
                            final_results[j].append(result_part)
                else:
                    # Single return value
                    if isinstance(batch_result, list):
                        final_results.extend(batch_result)
                    else:
                        final_results.append(batch_result)
            
            # Return in the same format as original function
            if isinstance(final_results, list) and final_results and isinstance(final_results[0], list):
                # Multiple return values case
                return tuple(final_results)
            else:
                return final_results
        
        return wrapper
    return decorator


async def async_batch_processor(
    items: List[Any],
    process_func: Callable,
    max_concurrent: int = 5,
    show_progress: bool = True,
) -> List[Any]:
    """Process items asynchronously with concurrency control.
    
    Args:
        items: List of items to process
        process_func: Async function to process each item
        max_concurrent: Maximum number of concurrent tasks
        show_progress: Whether to show progress logs
        
    Returns:
        List of results in the same order as input items
    """
    if not items:
        return []
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(item, index):
        async with semaphore:
            if show_progress and index % 10 == 0:
                lg.debug(f"Processing item {index + 1}/{len(items)}")
            return await process_func(item)
    
    tasks = [process_with_semaphore(item, i) for i, item in enumerate(items)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for exceptions
    failed_indices = [i for i, r in enumerate(results) if isinstance(r, Exception)]
    if failed_indices:
        lg.warning(f"Failed to process {len(failed_indices)} items: {failed_indices}")
    
    return results


def parallel_batch_processor(
    items: List[Any],
    process_func: Callable,
    max_workers: int = 5,
    show_progress: bool = True,
) -> List[Any]:
    """Process items in parallel using ThreadPoolExecutor.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        max_workers: Maximum number of worker threads
        show_progress: Whether to show progress logs
        
    Returns:
        List of results in the same order as input items
    """
    if not items:
        return []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, item in enumerate(items):
            future = executor.submit(process_func, item)
            futures.append(future)
        
        results = []
        for i, future in enumerate(futures):
            if show_progress and i % 10 == 0:
                lg.debug(f"Completed item {i + 1}/{len(items)}")
            
            try:
                results.append(future.result())
            except Exception as e:
                lg.error(f"Failed to process item {i}: {e}")
                results.append(None)
        
        return results
