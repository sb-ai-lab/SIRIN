"""Tests for uncertainty prompt splitting."""

from sirin.detection.processors.uncertainty import _split_prompt_and_answer


def test_two_message_format_is_noop():
    sample = [
        {'role': 'user', 'content': 'What is the capital of France?'},
        {'role': 'assistant', 'content': 'Paris.'},
    ]
    prompt, answer = _split_prompt_and_answer(sample)
    assert prompt == sample[0]['content']
    assert answer == sample[1]['content']


def test_system_user_assistant_merges_non_assistant():
    sample = [
        {'role': 'system', 'content': 'You are helpful.'},
        {'role': 'user', 'content': 'What is 2+2?'},
        {'role': 'assistant', 'content': '4'},
    ]
    prompt, answer = _split_prompt_and_answer(sample)
    assert 'You are helpful.' in prompt
    assert 'What is 2+2?' in prompt
    assert answer == '4'
