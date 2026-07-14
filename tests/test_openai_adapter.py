"""OpenAIModelAdapter single-request contract: string vs (text, logprobs) shapes."""
import types

from sirin.inference.adapters.openai_adapter import OpenAIModelAdapter
from sirin.models.inference import OpenAIConfig


def _response(text, with_logprobs=True):
    tops = [types.SimpleNamespace(token='0', logprob=-0.1),
            types.SimpleNamespace(token='1', logprob=-2.3)]
    logprobs = (types.SimpleNamespace(content=[types.SimpleNamespace(
        token='0', logprob=-0.1, top_logprobs=tops)]) if with_logprobs else None)
    choice = types.SimpleNamespace(
        message=types.SimpleNamespace(content=text), logprobs=logprobs)
    return types.SimpleNamespace(choices=[choice])


class _FakeClient:
    def __init__(self, text='0', with_logprobs=True):
        self._text, self._with_logprobs = text, with_logprobs
        create = lambda **kw: _response(self._text, self._with_logprobs)  # noqa: E731
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=create))


def _adapter(client):
    adapter = OpenAIModelAdapter(OpenAIConfig(model_path='m', max_retries=1))
    adapter.load(model=client)
    return adapter


def test_single_request_without_logprobs_returns_a_string_not_a_tuple():
    """`return text, [] if return_logprobs else text` bound as `(text, text)`.

    TokenOpenAIJudge is the only logprob-free caller, so it was the only victim: it fed
    the tuple into a regex and died with "expected string or bytes-like object".
    """
    adapter = _adapter(_FakeClient(text='hello'))
    out = adapter._make_single_request_sync([], return_logprobs=False)
    assert out == 'hello'
    assert isinstance(out, str)


def test_single_request_with_logprobs_returns_text_and_token_pairs():
    adapter = _adapter(_FakeClient(text='0'))
    text, logprobs = adapter._make_single_request_sync([], return_logprobs=True)
    assert text == '0'
    assert logprobs == [[('0', -0.1), ('1', -2.3)]]


def test_single_request_with_logprobs_requested_but_absent_returns_empty_list():
    adapter = _adapter(_FakeClient(text='0', with_logprobs=False))
    text, logprobs = adapter._make_single_request_sync([], return_logprobs=True)
    assert text == '0'
    assert logprobs == []


def test_empty_choices_response_is_retried_then_succeeds():
    """OpenRouter free routes can return HTTP 200 with no choices (observed live);
    that must count as a failed attempt and retry, not crash the caller."""
    responses = [types.SimpleNamespace(choices=None), _response('recovered')]

    class _FlakyClient:
        def __init__(self):
            create = lambda **kw: responses.pop(0)  # noqa: E731
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=create)
            )

    adapter = OpenAIModelAdapter(OpenAIConfig(model_path='m', max_retries=2))
    adapter.load(model=_FlakyClient())
    out = adapter._make_single_request_sync([], return_logprobs=False)
    assert out == 'recovered'


def test_sequential_batch_without_logprobs_yields_strings():
    adapter = _adapter(_FakeClient(text='x'))
    results = adapter._make_request([[], []], return_logprobs=False, use_async=False)
    assert results == ['x', 'x']


def test_sequential_batch_with_logprobs_yields_texts_and_logprobs():
    adapter = _adapter(_FakeClient(text='1'))
    texts, logprobs = adapter._make_request([[], []], return_logprobs=True, use_async=False)
    assert texts == ['1', '1']
    assert len(logprobs) == 2 and logprobs[0] == [[('0', -0.1), ('1', -2.3)]]
