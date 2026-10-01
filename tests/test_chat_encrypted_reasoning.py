import pytest
import models
from helpers import litellm_transport
from helpers.litellm_transport import (
    ChatCompletionsStreamParser,
    ChatCompletionsTransport,
    ResponsesTransport,
)
from helpers.llm_result import LLMResult


MARKER = "__ENCRYPTED_REASONING__"


def test_chat_completion_excludes_sealed_reasoning_from_result_metadata():
    raw = {"choices": [{"message": {
        "content": "Answer",
        "reasoning_content": "Readable summary\n" + MARKER + "id=rs_test\nopaque",
    }}]}
    parsed = ChatCompletionsTransport.parse(raw)
    assert parsed == {"response_delta": "Answer", "reasoning_delta": "Readable summary\n"}
    result = LLMResult.from_chat(response=parsed["response_delta"], reasoning=parsed["reasoning_delta"])
    assert MARKER not in str(result.metadata())
    assert raw["choices"][0]["message"]["reasoning_content"].endswith("opaque")


def test_chat_stream_filters_every_marker_split_without_losing_content():
    reasoning = "Readable summary\n" + MARKER + "id=rs_test\nopaque"
    for split in range(len(reasoning) + 1):
        parser = ChatCompletionsStreamParser()
        chunks = [parser.parse({"choices": [{"delta": {
            "content": "Answer" if index == 1 else "",
            "reasoning_content": part,
        }}]}) for index, part in enumerate((reasoning[:split], reasoning[split:]))]
        chunks.append(parser.flush())
        assert "".join(c["reasoning_delta"] for c in chunks) == "Readable summary\n"
        assert "".join(c["response_delta"] for c in chunks) == "Answer"


def test_chat_stream_preserves_ordinary_reasoning_and_flushes_partial_prefix():
    for reasoning in ("Use __ underscores", "__ENCRYPTED_REASONING", "", "Normal reasoning"):
        parser = ChatCompletionsStreamParser()
        output = "".join(parser.parse({"choices": [{"delta": {
            "reasoning_content": char,
        }}]})["reasoning_delta"] for char in reasoning)
        assert output + parser.flush()["reasoning_delta"] == reasoning


def test_responses_sealed_reasoning_remains_an_opaque_output_item():
    raw = {"output": [{"type": "reasoning", "id": "rs_test",
                       "encrypted_content": "opaque", "summary": []}]}
    assert ResponsesTransport.parse_response(raw)["reasoning_delta"] == ""
    result = LLMResult.from_response(raw)
    assert result.output_items[0].data["encrypted_content"] == "opaque"


@pytest.mark.asyncio
async def test_chat_wrapper_never_emits_or_persists_encrypted_reasoning(monkeypatch):
    async def chunks():
        for part in ("Readable\n__ENCRYPTED_", "REASONING__id=rs_test", "opaque"):
            yield {"choices": [{"delta": {"reasoning_content": part}}]}
        yield {"choices": [{"delta": {"content": "Answer"}}]}

    async def completion(**kwargs):
        return chunks()

    async def no_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "acompletion", completion)
    monkeypatch.setattr(models, "apply_rate_limiter", no_limiter)
    emitted = []

    async def reasoning_callback(chunk, full):
        emitted.append(chunk)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model", provider="openai", model_config=None, a0_api_mode="chat",
    )
    result = await wrapper.unified_turn.__wrapped__(
        wrapper, messages=[], reasoning_callback=reasoning_callback,
    )
    assert "".join(emitted) == result.reasoning == "Readable\n"
    assert result.response == "Answer"
    assert MARKER not in str(result.metadata())
