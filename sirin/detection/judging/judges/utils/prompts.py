from typing import Any, Dict, List


def format_dialogue_samples(config: Any, samples: List[Any]) -> List[Any]:
    """
    Format dialogue samples using the configured dialogue format.
    
    Args:
        config: Judge configuration with dialogue_format
        samples: List of samples (either strings or list of message dicts)
    
    Returns:
        List of formatted dialogue strings
    """
    if not samples:
        return []

    first = samples[0]
    if isinstance(first, list) and len(first) >= 2:
        return [
            config.dialogue_format.format(
                **{'question': sample[0]['content'], 'answer': sample[1]['content']}
            )
            for sample in samples
        ]

    return samples


def build_prompt_messages(config: Any, samples: List[Any]) -> List[List[Dict[str, str]]]:
    """
    Build full prompt messages with system and user roles.
    
    Used by API-based judges (OpenAI) to create message lists for API calls.
    
    Args:
        config: Judge configuration with system_prompt, user_prompt, dialogue_format
        samples: List of samples to format
    
    Returns:
        List of message lists, each containing system and user messages
    """
    formatted_samples = format_dialogue_samples(config, samples)

    return [
        [
            {'role': 'system', 'content': config.system_prompt},
            {'role': 'user', 'content': config.user_prompt.format(**{'sample': sample})},
        ]
        for sample in formatted_samples
    ]


def format_dialogue_for_training(
    inputs: List[List[Dict[str, str]]],
    targets: List[Any],
    config: Any,
    is_token_level: bool = False,
) -> List[List[Dict[str, str]]]:
    """
    Format dialogue samples with system/user/assistant roles for training.
    
    Used by decoder judges (both sequence and token-level) for preprocessing.
    
    Args:
        inputs: List of dialogue samples (each is list of messages)
        targets: List of target labels (int for sequence, List[Tuple] for token)
        config: Judge configuration with dialogue_format, system_prompt, user_prompt
        is_token_level: Whether this is token-level (uses span wrapping) or sequence-level
    
    Returns:
        List of formatted message lists ready for tokenization
    """
    from sirin.detection.judging.judges.utils.token_level import wrap_spans
    
    # Format dialogues using the config's dialogue format
    formatted_input = [
        config.dialogue_format.format(
            **{'question': sample[0]['content'], 'answer': sample[1]['content']}
        )
        for sample in inputs
    ]
    
    # Build full message lists with system/user/assistant roles
    formatted_messages = []
    for i, sample_text in enumerate(formatted_input):
        # For token-level, wrap spans in the assistant content
        if is_token_level:
            dialogue_sample = inputs[i]
            spans = targets[i]
            assistant_content = wrap_spans(dialogue_sample[1]['content'], spans)
        else:
            # For sequence-level, use the label directly
            assistant_content = str(targets[i])
        
        formatted_messages.append([
            {'role': 'system', 'content': config.system_prompt},
            {'role': 'user', 'content': config.user_prompt.format(**{'sample': sample_text})},
            {'role': 'assistant', 'content': assistant_content},
        ])
    
    return formatted_messages
