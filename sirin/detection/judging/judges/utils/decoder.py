from typing import Any, Dict, List

from sirin.utils.hf import get_assistant_prefix


def prepare_decoder_inputs_with_labels(
    formatted_messages: List[List[Dict[str, str]]],
    model_adapter: Any,
    config: Any,
) -> Dict[str, Any]:
    """
    Prepare inputs for decoder models with proper label masking.
    
    Creates tokenized inputs where only the assistant response tokens are used for loss.
    Context tokens (system + user prompts) are masked with -100.
    
    Args:
        formatted_messages: Formatted message lists (system, user, assistant)
        model_adapter: Model adapter with tokenizer and preprocessing
        config: Judge configuration with tokenization settings
    
    Returns:
        Dict with 'input_ids', 'attention_mask', 'labels'
    """
    # Get assistant prefix (e.g., "assistant\n" for the model's format)
    assistant_prefix = get_assistant_prefix(model_adapter._model_name)
    
    # Preprocess messages without assistant response to find context length
    preprocessed_input_without_answer = [
        f'{sample}{assistant_prefix}'
        for sample in model_adapter._preprocess_input(
            [sample[:2] for sample in formatted_messages]  # Only system + user
        )
    ]
    
    # Preprocess full messages including assistant response
    preprocessed_input = model_adapter._preprocess_input(formatted_messages)
    
    # Tokenize without target (to find where assistant response starts)
    encoding_without_target = model_adapter.tokenizer(
        preprocessed_input_without_answer,
        truncation=model_adapter.config.truncation,
        padding=False,
        add_special_tokens=False,
    )
    
    # Tokenize with target
    encoding = model_adapter.tokenizer(
        preprocessed_input,
        truncation=model_adapter.config.truncation,
        padding=False,
        return_tensors=config.return_tensors,
        add_special_tokens=False,
    )
    
    # Create labels: copy input_ids but mask everything before assistant response
    labels = encoding['input_ids'].clone()
    for i, sample in enumerate(encoding_without_target['input_ids']):
        labels[i, :len(sample)] = -100  # Mask context tokens
    
    return {
        'input_ids': encoding['input_ids'],
        'attention_mask': encoding['attention_mask'],
        'labels': labels,
    }


