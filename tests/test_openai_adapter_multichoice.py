"""OpenAIModelAdapter multi-generation (n>1) contract, with a fake client (no network).

The token judge asks for n generations per input; the adapter used to read only choices[0], so
consensus collapsed to a single generation. It must now collect every choice and top up with n=1
requests when a provider returns fewer than n choices.
"""
import types

import pytest

from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter
from sirin.models.inference import OpenAIConfig


def _choice(content, logprobs=None, finish_reason='stop'):
    return types.SimpleNamespace(
        message=types.SimpleNamespace(content=content),
        logprobs=logprobs,
        finish_reason=finish_reason,
    )


class _FakeCompletions:
    def __init__(self, responder):
        self._responder = responder
        self.calls = []

    def create(self, model, messages, **kwargs):
        response = self._responder(len(self.calls), kwargs)
        self.calls.append(kwargs)
        return response


class _FakeClient:
    def __init__(self, responder):
        self.completions = _FakeCompletions(responder)

    @property
    def chat(self):
        return self


def _adapter(responder):
    adapter = OpenAIModelAdapter(OpenAIConfig(model_path='m', max_retries=3))
    adapter._client = _FakeClient(responder)
    adapter._async_client = None  # 1 input -> sync path
    adapter._is_loaded = True
    adapter._model_name = 'm'
    return adapter


def test_n_choices_all_collected_in_one_call():
    # provider honors n and returns all 3 choices at once.
    responder = lambda idx, kw: types.SimpleNamespace(
        choices=[_choice(f't{i}') for i in range(kw['n'])]
    )
    adapter = _adapter(responder)

    out = adapter.sample([[{'role': 'user', 'content': 'x'}]], n=3, max_tokens=64)

    assert out == [['t0', 't1', 't2']]  # list[list[str]]: one inner list per input
    assert len(adapter._client.completions.calls) == 1
    assert adapter._client.completions.calls[0]['n'] == 3
    assert adapter._client.completions.calls[0]['max_tokens'] == 64


def test_top_up_when_provider_returns_one_choice_per_call():
    # OpenRouter/Anthropic-compat routes often ignore n and return a single choice.
    responder = lambda idx, kw: types.SimpleNamespace(choices=[_choice(f't{idx}')])
    adapter = _adapter(responder)

    out = adapter.sample([[{'role': 'user', 'content': 'x'}]], n=3)

    assert out == [['t0', 't1', 't2']]  # topped up to 3
    calls = adapter._client.completions.calls
    assert len(calls) == 3
    assert calls[0]['n'] == 3  # first asks for all n
    assert calls[1]['n'] == 1 and calls[2]['n'] == 1  # then tops up singly


def test_logprobs_with_n_gt_1_raises():
    adapter = _adapter(lambda idx, kw: types.SimpleNamespace(choices=[_choice('t')]))

    with pytest.raises(ValueError, match='return_logprobs'):
        adapter.sample([[{'role': 'user', 'content': 'x'}]], n=2, return_logprobs=True)


def test_n1_return_shape_unchanged():
    responder = lambda idx, kw: types.SimpleNamespace(choices=[_choice('only')])
    adapter = _adapter(responder)

    out = adapter.sample([[{'role': 'user', 'content': 'x'}]], max_tokens=32)

    assert out == ['only']  # n==1 stays a flat list[str]
    assert 'n' not in adapter._client.completions.calls[0]  # no explicit n=1 sent


def test_n1_logprobs_return_shape_unchanged():
    logprobs = types.SimpleNamespace(
        content=[
            types.SimpleNamespace(
                top_logprobs=[types.SimpleNamespace(logprob=-0.25)], logprob=-0.25
            )
        ]
    )
    responder = lambda idx, kw: types.SimpleNamespace(
        choices=[_choice('only', logprobs=logprobs)]
    )
    adapter = _adapter(responder)

    texts, lps = adapter.sample(
        [[{'role': 'user', 'content': 'x'}]], return_logprobs=True
    )

    assert texts == ['only']
    assert lps == [[[-0.25]]]


def test_finish_reasons_align_with_generations_across_top_up():
    # The 2nd of 3 topped-up generations overruns the budget: its slot (and only its slot)
    # must read 'length' in the side channel, 1:1 with the returned texts.
    reasons = ['stop', 'length', 'stop']
    responder = lambda idx, kw: types.SimpleNamespace(
        choices=[_choice(f't{idx}', finish_reason=reasons[idx])]
    )
    adapter = _adapter(responder)

    out = adapter.sample([[{'role': 'user', 'content': 'x'}]], n=3)

    assert out == [['t0', 't1', 't2']]  # public return shape unchanged
    assert adapter.last_finish_reasons == [['stop', 'length', 'stop']]


def test_finish_reasons_reset_to_none_on_n1_call():
    responder = lambda idx, kw: types.SimpleNamespace(choices=[_choice('t')])
    adapter = _adapter(responder)

    adapter.sample([[{'role': 'user', 'content': 'x'}]], n=2)
    assert adapter.last_finish_reasons == [['stop', 'stop']]

    adapter.sample([[{'role': 'user', 'content': 'x'}]])  # n==1 resets the side channel
    assert adapter.last_finish_reasons is None


def test_finish_reasons_missing_on_choice_become_none():
    # Providers/fakes without finish_reason must not crash the top-up path.
    choice = types.SimpleNamespace(message=types.SimpleNamespace(content='t'), logprobs=None)
    responder = lambda idx, kw: types.SimpleNamespace(choices=[choice])
    adapter = _adapter(responder)

    adapter.sample([[{'role': 'user', 'content': 'x'}]], n=2)

    assert adapter.last_finish_reasons == [[None, None]]
