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


def test_multi_turn_scores_last_assistant_and_keeps_dialogue():
    sample = [
        {'role': 'user', 'content': 'Hi, my name is Sam.'},
        {'role': 'assistant', 'content': 'Nice to meet you, Sam.'},
        {'role': 'user', 'content': 'What is my name?'},
        {'role': 'assistant', 'content': 'Sam.'},
    ]
    prompt, answer = _split_prompt_and_answer(sample)
    # buggy version returned the FIRST assistant turn and dropped prior dialogue
    assert answer == 'Sam.'
    assert 'Nice to meet you, Sam.' in prompt
    assert 'What is my name?' in prompt
