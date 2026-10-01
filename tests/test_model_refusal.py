import pytest
from litellm import ContentPolicyViolationError

import models
from helpers import litellm_transport
from helpers.litellm_transport import ChatCompletionsStreamParser, ChatCompletionsTransport


@pytest.mark.parametrize("reason", ["content_filter", "refusal"])
def test_refusals_fail_before_partial_tool_calls_can_be_returned(reason):
    raw = {"model": "test", "choices": [{"finish_reason": reason, "message": {
        "content": "partial", "tool_calls": [{"type": "function", "function": {
            "name": "response", "arguments": '{"text":"partial"}',
        }}],
    }}]}
    for parse in (ChatCompletionsTransport.parse, ChatCompletionsStreamParser().parse):
        with pytest.raises(ContentPolicyViolationError, match=f"finish_reason={reason}"):
            parse(raw)
    assert ChatCompletionsTransport.parse({"choices": [{"finish_reason": "stop"}]}) == {
        "response_delta": "", "reasoning_delta": "",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_refusal_stops_model_call_without_retry_and_closes_stream(monkeypatch, stream):
    calls = 0
    closed = False
    raw = {"model": "test", "choices": [{"finish_reason": "content_filter", "delta": {}}]}

    async def chunks():
        nonlocal closed
        try:
            yield raw
        finally:
            closed = True

    async def completion(**kwargs):
        nonlocal calls
        calls += 1
        return chunks() if kwargs["stream"] else raw

    async def callback(*args):
        raise AssertionError("Refused output must not reach callbacks")

    monkeypatch.setattr(litellm_transport, "acompletion", completion)
    wrapper = models.LiteLLMChatWrapper(model="test", provider="openai")
    with pytest.raises(ContentPolicyViolationError, match="Model provider refused"):
        await wrapper.unified_turn.__wrapped__(
            wrapper, messages=[], response_callback=callback if stream else None,
        )
    assert calls == 1
    assert closed == stream
