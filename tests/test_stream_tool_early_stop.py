import json
import sys
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from helpers import extract_tools
from helpers import litellm_transport


@pytest.fixture(autouse=True)
def _clear_transport_capability_cache():
    litellm_transport.clear_transport_capability_cache()


def _chunk(content: str) -> dict:
    return {"choices": [{"delta": {"content": content}, "message": {}}]}


def _response_event(delta: str) -> dict:
    return {"type": "response.output_text.delta", "delta": delta}


class _AsyncChunkStream:
    def __init__(self, chunks: list[dict]):
        self._chunks = chunks
        self.index = 0
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self.index]
        self.index += 1
        return chunk

    async def aclose(self):
        self.closed = True


class _FailingAsyncChunkStream:
    def __init__(self, exc: Exception):
        self.exc = exc
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise self.exc

    async def aclose(self):
        self.closed = True


class _DumpOnly:
    def __init__(self, **data):
        self._data = data

    def model_dump(self):
        return dict(self._data)


def test_extract_json_root_string_returns_canonical_snapshot():
    text = (
        'prefix {"tool_name":"response","tool_args":{"text":"brace } inside"}} '
        "trailing noise"
    )

    root = extract_tools.extract_json_root_string(text)

    assert root == '{"tool_name":"response","tool_args":{"text":"brace } inside"}}'
    assert extract_tools.json_parse_dirty(root)["tool_args"]["text"] == "brace } inside"
    assert extract_tools.extract_json_root_string(
        '{"tool_name":"response","tool_args":{"text":"missing"'
    ) is None
    assert extract_tools.extract_json_root_string('[{"tool_name":"response"}]') is None


def test_json_parse_dirty_prefers_valid_tool_request_after_preamble_object():
    text = (
        'I will call the tool after this note {"note":"not the tool"}.\n'
        '{"tool_name":"response","tool_args":{"text":"ok"}} trailing text'
    )

    assert extract_tools.json_parse_dirty(text) == {
        "tool_name": "response",
        "tool_args": {"text": "ok"},
    }


def test_extract_json_root_string_prefers_valid_tool_request():
    text = (
        'I will call the tool after this note {"note":"not the tool"}.\n'
        '{"tool_name":"response","tool_args":{"text":"ok"}} trailing text'
    )

    assert extract_tools.extract_json_root_string(text) == (
        '{"tool_name":"response","tool_args":{"text":"ok"}}'
    )
    assert extract_tools.extract_json_root_string(
        'Only a note {"note":"not the tool"}'
    ) == '{"note":"not the tool"}'


def test_extract_json_root_string_waits_for_complete_parallel_parent():
    partial = (
        '{"tool_name":"parallel","tool_args":{"tool_calls":['
        '{"tool_name":"code_execution_tool","tool_args":{"code":"first"}}'
    )

    assert extract_tools.extract_json_root_string(partial) is None

    full = (
        partial
        + ',{"tool_name":"code_execution_tool","tool_args":{"code":"second"}}'
        '],"wait":true}} trailing text'
    )

    root = extract_tools.extract_json_root_string(full)
    assert root == (
        '{"tool_name":"parallel","tool_args":{"tool_calls":['
        '{"tool_name":"code_execution_tool","tool_args":{"code":"first"}},'
        '{"tool_name":"code_execution_tool","tool_args":{"code":"second"}}'
        '],"wait":true}}'
    )
    parsed = extract_tools.json_parse_dirty(root)
    assert parsed["tool_name"] == "parallel"
    assert len(parsed["tool_args"]["tool_calls"]) == 2


def test_litellm_global_kwargs_merge_defaults_and_config(monkeypatch):
    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {"litellm_global_kwargs": {}},
    )

    assert models._merge_litellm_call_kwargs({})["drop_params"] is True
    assert models._merge_litellm_call_kwargs({"temperature": 0}) == {
        "drop_params": True,
        "temperature": 0,
    }

    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {
            "litellm_global_kwargs": {
                "drop_params": "false",
                "timeout": "30",
                "additional_drop_params": ["response_format"],
            }
        },
    )

    assert models._merge_litellm_call_kwargs({}) == {
        "drop_params": False,
        "timeout": 30,
        "additional_drop_params": ["response_format"],
    }

    original_drop_params = getattr(models.litellm, "drop_params", None)
    had_timeout = hasattr(models.litellm, "timeout")
    original_timeout = getattr(models.litellm, "timeout", None)
    had_additional_drop_params = hasattr(models.litellm, "additional_drop_params")
    original_additional_drop_params = getattr(
        models.litellm, "additional_drop_params", None
    )
    try:
        assert models.set_litellm_params() == {
            "drop_params": False,
            "timeout": 30,
            "additional_drop_params": ["response_format"],
        }
        assert models.litellm.drop_params is False
        if had_timeout:
            assert models.litellm.timeout == original_timeout
        else:
            assert not hasattr(models.litellm, "timeout")
        if had_additional_drop_params:
            assert (
                models.litellm.additional_drop_params
                == original_additional_drop_params
            )
        else:
            assert not hasattr(models.litellm, "additional_drop_params")
    finally:
        setattr(models.litellm, "drop_params", original_drop_params)
        if had_timeout:
            setattr(models.litellm, "timeout", original_timeout)
        elif hasattr(models.litellm, "timeout"):
            delattr(models.litellm, "timeout")
        if had_additional_drop_params:
            setattr(
                models.litellm,
                "additional_drop_params",
                original_additional_drop_params,
            )
        elif hasattr(models.litellm, "additional_drop_params"):
            delattr(models.litellm, "additional_drop_params")


def test_provider_defaults_do_not_freeze_litellm_global_kwargs(monkeypatch):
    monkeypatch.setattr(models, "get_provider_config", lambda *args, **kwargs: None)
    monkeypatch.setattr(models, "get_api_key", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {"litellm_global_kwargs": {"drop_params": "true"}},
    )

    _, provider_kwargs = models._merge_provider_defaults("chat", "openai", {})

    assert "drop_params" not in provider_kwargs
    assert models._merge_litellm_call_kwargs(provider_kwargs)["drop_params"] is True

    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {"litellm_global_kwargs": {"drop_params": "false"}},
    )

    assert models._merge_litellm_call_kwargs(provider_kwargs)["drop_params"] is False


@pytest.mark.asyncio
async def test_unified_call_stops_after_canonical_root_snapshot(monkeypatch):
    stream = _AsyncChunkStream(
        [
            {"type": "response.created"},
            _response_event(
                '{"tool_name":"response","tool_args":{"text":"hello"}} trailing text'
            ),
            _response_event(" unreachable"),
        ]
    )

    async def fake_aresponses(*args, **kwargs):
        assert kwargs["stream"] is True
        assert kwargs["input"] == ""
        assert kwargs["store"] is True
        return stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)
    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {"litellm_global_kwargs": {}},
    )

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    seen: list[tuple[str, str]] = []

    async def response_callback(chunk: str, full: str):
        seen.append((chunk, full))
        snapshot = extract_tools.extract_json_root_string(full)
        if snapshot:
            return snapshot
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == '{"tool_name":"response","tool_args":{"text":"hello"}}'
    assert reasoning == ""
    assert stream.index == 2
    assert stream.closed is True
    assert len(seen) == 1
    assert seen[0][1] == '{"tool_name":"response","tool_args":{"text":"hello"}} trailing text'


@pytest.mark.asyncio
async def test_unified_call_stops_after_tool_root_with_incidental_json(monkeypatch):
    stream = _AsyncChunkStream(
        [
            {"type": "response.created"},
            _response_event('Preamble {"note":"not the tool"}.\n'),
            _response_event(
                '{"tool_name":"response","tool_args":{"text":"ok"}} trailing text'
            ),
            _response_event(" unreachable"),
        ]
    )

    async def fake_aresponses(*args, **kwargs):
        assert kwargs["stream"] is True
        assert kwargs["input"] == ""
        assert kwargs["store"] is True
        return stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)
    monkeypatch.setattr(
        models.settings,
        "get_settings",
        lambda: {"litellm_global_kwargs": {}},
    )

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    seen: list[tuple[str, str]] = []

    async def response_callback(chunk: str, full: str):
        seen.append((chunk, full))
        snapshot = extract_tools.extract_json_root_string(full)
        if not snapshot:
            return None
        parsed_snapshot = extract_tools.json_parse_dirty(snapshot)
        if parsed_snapshot is None:
            return None
        try:
            extract_tools.normalize_tool_request(parsed_snapshot)
        except ValueError:
            return None
        return snapshot

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == '{"tool_name":"response","tool_args":{"text":"ok"}}'
    assert reasoning == ""
    assert stream.index == 3
    assert stream.closed is True
    assert len(seen) == 2
    assert seen[0][1] == 'Preamble {"note":"not the tool"}.\n'
    assert (
        seen[1][1]
        == 'Preamble {"note":"not the tool"}.\n'
        '{"tool_name":"response","tool_args":{"text":"ok"}} trailing text'
    )


@pytest.mark.asyncio
async def test_unified_call_closes_responses_stream_when_callback_raises(monkeypatch):
    stream = _AsyncChunkStream([_response_event("interrupt me")])

    class ExpectedIntervention(Exception):
        pass

    async def fake_aresponses(*args, **kwargs):
        assert kwargs["stream"] is True
        return stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        raise ExpectedIntervention()

    with pytest.raises(ExpectedIntervention):
        await wrapper.unified_call(
            messages=[],
            response_callback=response_callback,
        )

    assert stream.closed is True


@pytest.mark.asyncio
async def test_chat_completions_escape_hatch_still_uses_acompletion(monkeypatch):
    stream = _AsyncChunkStream([_chunk("hello")])
    calls: list[str] = []

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert "a0_api_mode" not in kwargs
        return stream

    async def fake_aresponses(*args, **kwargs):
        raise AssertionError("Responses path should not be used")

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
        a0_api_mode="chat_completions",
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "hello"
    assert reasoning == ""
    assert calls == ["chat"]


@pytest.mark.asyncio
async def test_unified_call_retries_responses_with_high_reasoning(monkeypatch):
    validation_error = ValueError(
        "1 validation error for ResponseCreatedEvent\n"
        "response.reasoning.effort\n"
        "Input should be 'minimal', 'low', 'medium' or 'high' "
        "[type=literal_error, input_value='none', input_type=str]"
    )
    failing_stream = _FailingAsyncChunkStream(validation_error)
    working_stream = _AsyncChunkStream([_response_event("ok")])
    calls: list[dict] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return failing_stream
        return working_stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="gpt-5.4",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "ok"
    assert reasoning == ""
    assert failing_stream.closed is True
    assert len(calls) == 2
    assert "reasoning" not in calls[0]
    assert calls[1]["reasoning"] == {"effort": "high"}


@pytest.mark.asyncio
async def test_unified_call_falls_back_to_chat_when_responses_endpoint_missing(
    monkeypatch,
):
    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        raise RuntimeError(
            "Client error '404 Not Found' for url "
            "'https://llm.agent-zero.ai/v1/responses'"
        )

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert kwargs["drop_params"] is True
        assert "tool_choice" not in kwargs
        assert "parallel_tool_calls" not in kwargs
        return _AsyncChunkStream([_chunk("fallback")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="claude-opus-4.7",
        provider="openai",
        model_config=None,
        tool_choice="auto",
        parallel_tool_calls=True,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat"]

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat", "chat"]


@pytest.mark.asyncio
async def test_unified_call_falls_back_when_litellm_hides_responses_404_url(
    monkeypatch,
):
    class NotFoundError(Exception):
        status_code = 404

    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        raise NotFoundError(
            'litellm.NotFoundError: NotFoundError: OpenAIException - {"detail":"Not Found"}'
        )

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert kwargs["drop_params"] is True
        return _AsyncChunkStream([_chunk("fallback")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="claude-opus-4.7",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat"]


@pytest.mark.parametrize(
    "responses_error",
    [
        "litellm.exceptions.APIError: Path /api/v1/responses is not "
        "available through this proxy.",
        "MaskedHTTPStatusError: Server error '500 Internal Server Error' "
        "for url 'https://api.venice.ai/api/v1/responses'",
        "InternalServerError: OpenAIException - '<=' not supported between "
        "instances of 'str' and 'int' for url 'http://192.168.200.52:4000/responses'",
        "ImportError Missing dependency No module named 'fastapi'. "
        "Run `pip install 'litellm[proxy]'`",
    ],
)
@pytest.mark.asyncio
async def test_unified_call_falls_back_for_proxy_responses_failures(
    monkeypatch,
    responses_error,
):
    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        raise RuntimeError(responses_error)

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert kwargs["drop_params"] is True
        return _AsyncChunkStream([_chunk("fallback")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat"]


@pytest.mark.asyncio
async def test_unified_call_falls_back_when_responses_mock_reads_sse_as_json(
    monkeypatch,
):
    calls: list[str] = []
    sse_error = json.JSONDecodeError(
        "Expecting value",
        'event: response.output_text.delta\ndata: {"delta":"hello"}\n\n',
        0,
    )
    failing_stream = _FailingAsyncChunkStream(sse_error)

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        return failing_stream

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert kwargs["drop_params"] is True
        return _AsyncChunkStream([_chunk("fallback")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="omniroute/test-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat"]
    assert failing_stream.closed is True


@pytest.mark.asyncio
async def test_unified_call_falls_back_when_responses_bad_request_rejects_shape(
    monkeypatch,
):
    class BadRequestError(Exception):
        status_code = 400

    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        raise BadRequestError(
            'BadRequestError: Zod validation error: input_image Expected object, '
            'received string; Expected string, received array'
        )

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        assert kwargs["drop_params"] is True
        return _AsyncChunkStream([_chunk("fallback")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="venice-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[
            HumanMessage(
                content=[
                    {"type": "text", "text": "describe it"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.test/a.png"},
                    },
                ]
            )
        ],
        response_callback=response_callback,
    )

    assert response == "fallback"
    assert reasoning == ""
    assert calls == ["responses", "chat"]


@pytest.mark.asyncio
async def test_unified_call_raises_generic_responses_bad_request(monkeypatch):
    class BadRequestError(Exception):
        status_code = 400

    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append("responses")
        raise BadRequestError(
            "BadRequestError: validation error: invalid request: max_tokens is too high"
        )

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        raise AssertionError("generic 400 should not fallback to chat")

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    with pytest.raises(BadRequestError):
        await wrapper.unified_call(
            messages=[],
            response_callback=response_callback,
        )

    assert calls == ["responses"]


@pytest.mark.asyncio
async def test_unified_call_preserves_cache_control_with_chat_for_non_native_responses(
    monkeypatch,
):
    calls: list[str] = []

    async def fake_aresponses(*args, **kwargs):
        raise AssertionError("cache_control should keep Anthropic-family calls on chat")

    async def fake_acompletion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["stream"] is True
        messages = kwargs["messages"]
        assert "cache_control" not in messages[0]
        assert messages[0]["content"][-1]["cache_control"] == {
            "type": "ephemeral"
        }
        assert messages[1]["content"][-1]["cache_control"] == {
            "type": "ephemeral"
        }
        assert "cache_control" not in messages[2]
        assert messages[3]["content"][-1]["cache_control"] == {
            "type": "ephemeral"
        }
        return _AsyncChunkStream([_chunk("cached")])

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="claude-sonnet-4-5",
        provider="anthropic",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    response, reasoning = await wrapper.unified_call(
        messages=[
            SystemMessage(content="static instructions"),
            HumanMessage(content="question"),
            AIMessage(content="previous answer"),
            HumanMessage(content="follow up"),
        ],
        response_callback=response_callback,
        explicit_caching=True,
    )

    assert response == "cached"
    assert reasoning == ""
    assert calls == ["chat"]


def test_responses_request_translates_messages_and_params():
    messages = [
        {"role": "system", "content": "You are precise."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Inspect this."},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.test/a.png"},
                },
            ],
        },
        {
            "role": "assistant",
            "content": "empty",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "lookup", "arguments": '{"q":"a0"}'},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "done"},
    ]
    kwargs = {
        "max_tokens": 42,
        "reasoning_effort": "high",
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "answer",
                "schema": {"type": "object"},
                "strict": True,
            },
        },
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "lookup",
                    "description": "Search",
                    "parameters": {"type": "object"},
                    "strict": True,
                },
            }
        ],
    }

    request = litellm_transport.ResponsesTransport.from_chat(messages, kwargs)

    assert "instructions" not in request
    assert request["store"] is True
    assert request["max_output_tokens"] == 42
    assert request["reasoning"] == {"effort": "high"}
    assert request["text"] == {
        "format": {
            "type": "json_schema",
            "name": "answer",
            "schema": {"type": "object"},
            "strict": True,
        }
    }
    assert request["tools"] == [
        {
            "type": "function",
            "name": "lookup",
            "description": "Search",
            "parameters": {"type": "object", "properties": {}},
            "strict": True,
        }
    ]
    assert request["input"] == [
        {"role": "system", "content": "You are precise."},
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Inspect this."},
                {
                    "type": "input_image",
                    "image_url": "https://example.test/a.png",
                },
            ],
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "id": "call_1",
            "name": "lookup",
            "arguments": '{"q":"a0"}',
            "status": "completed",
        },
        {"type": "function_call_output", "call_id": "call_1", "output": "done"},
    ]


def test_responses_request_normalizes_reasoning_and_orphan_tool_choice():
    request = litellm_transport.ResponsesTransport.from_chat(
        [],
        {
            "reasoning_effort": "none",
            "tools": [],
            "tool_choice": "auto",
            "parallel_tool_calls": True,
        },
    )

    assert "reasoning" not in request
    assert "tools" not in request
    assert "tool_choice" not in request
    assert "parallel_tool_calls" not in request

    request = litellm_transport.ResponsesTransport.from_chat(
        [],
        {"reasoning": {"effort": "xhigh"}},
    )

    assert request["reasoning"] == {"effort": "high"}

    request = litellm_transport.ResponsesTransport.from_chat(
        [],
        {"reasoning_effort": "off"},
    )

    assert "reasoning" not in request


def test_responses_request_normalizes_function_tool_parameter_shapes():
    request = litellm_transport.ResponsesTransport.from_chat(
        [],
        {
            "functions": [
                {
                    "name": "legacy_noop",
                    "description": "Legacy function",
                    "parameters": {},
                }
            ],
        },
    )

    assert request["tools"] == [
        {
            "type": "function",
            "name": "legacy_noop",
            "description": "Legacy function",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
    ]

    request = litellm_transport.ResponsesTransport.from_chat(
        [],
        {
            "a0_responses_function_tools": [
                {
                    "type": "function",
                    "name": "native_noop",
                    "description": "Native function",
                    "parameters": {"type": "object"},
                }
            ],
            "responses_builtin_tools": [{"type": "web_search"}],
        },
    )

    assert request["tools"] == [
        {
            "type": "function",
            "name": "native_noop",
            "description": "Native function",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
        {"type": "web_search"},
    ]


def test_chat_completions_kwargs_omit_empty_tools():
    kwargs = litellm_transport.ChatCompletionsTransport.prepare_kwargs(
        {
            "tools": [],
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "max_tokens": 8,
        }
    )

    assert kwargs == {"max_tokens": 8}

    kwargs = litellm_transport.ChatCompletionsTransport.prepare_kwargs(
        {
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "lookup",
                        "parameters": {"type": "object"},
                    },
                }
            ],
            "tool_choice": "auto",
        }
    )

    assert kwargs["tools"][0]["function"]["name"] == "lookup"
    assert kwargs["tool_choice"] == "auto"


def test_complete_falls_back_to_chat_when_responses_shim_sends_empty_tools(
    monkeypatch,
):
    calls: list[str] = []

    def fake_responses(*args, **kwargs):
        calls.append("responses")
        raise RuntimeError(
            "Value error, `tools` must not be an empty array. "
            "Either provide at least one tool or omit the field entirely."
        )

    def fake_completion(*args, **kwargs):
        calls.append("chat")
        assert kwargs["drop_params"] is True
        assert "tools" not in kwargs
        assert "tool_choice" not in kwargs
        assert "parallel_tool_calls" not in kwargs
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(litellm_transport, "responses", fake_responses)
    monkeypatch.setattr(litellm_transport, "completion", fake_completion)

    transport = litellm_transport.LiteLLMTransport(
        model="hosted_vllm/qwen",
        messages=[{"role": "user", "content": "hi"}],
        kwargs={
            "tools": [],
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "max_tokens": 8,
        },
    )

    parsed = transport.complete()

    assert parsed["response_delta"] == "ok"
    assert calls == ["responses", "chat"]


def test_responses_request_adds_openai_prompt_cache_key_for_static_prefix():
    request = litellm_transport.ResponsesTransport.from_chat(
        [
            {"role": "system", "content": "stable system prompt"},
            {"role": "user", "content": "dynamic question"},
        ],
        {
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "lookup",
                        "description": "Search",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        },
        model="openai/gpt-5.4",
    )

    assert request["prompt_cache_key"].startswith("a0-")
    assert len(request["prompt_cache_key"]) == 35
    assert "stable system prompt" not in request["prompt_cache_key"]

    request_again = litellm_transport.ResponsesTransport.from_chat(
        [
            {"role": "system", "content": "stable system prompt"},
            {"role": "user", "content": "different dynamic question"},
        ],
        {
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "lookup",
                        "description": "Search",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        },
        model="openai/gpt-5.4",
    )

    assert request_again["prompt_cache_key"] == request["prompt_cache_key"]


def test_responses_request_respects_explicit_prompt_cache_and_retention():
    request = litellm_transport.ResponsesTransport.from_chat(
        [{"role": "system", "content": "stable system prompt"}],
        {
            "prompt_cache_key": "user-provided-key",
            "prompt_cache_retention": "24h",
            "extra_body": {"prompt_cache_retention": "in_memory"},
        },
        model="openai/gpt-5.4",
    )

    assert request["prompt_cache_key"] == "user-provided-key"
    assert "prompt_cache_retention" not in request
    assert request["extra_body"]["prompt_cache_retention"] == "in_memory"


def test_responses_request_adds_azure_prompt_cache_params():
    request = litellm_transport.ResponsesTransport.from_chat(
        [{"role": "system", "content": "stable system prompt"}],
        {"prompt_cache_retention": "24h"},
        model="azure/gpt-4.1",
    )

    assert request["prompt_cache_key"].startswith("a0-")
    assert "prompt_cache_retention" not in request
    assert request["extra_body"]["prompt_cache_retention"] == "24h"


def test_responses_request_does_not_add_openai_cache_key_to_custom_api_base():
    request = litellm_transport.ResponsesTransport.from_chat(
        [{"role": "system", "content": "stable system prompt"}],
        {"api_base": "https://llm.agent-zero.ai/v1"},
        model="openai/gpt-5.4",
    )

    assert "prompt_cache_key" not in request


def test_chat_kwargs_add_openai_prompt_cache_key_for_chat_completions():
    kwargs = litellm_transport.ChatCompletionsTransport.prepare_kwargs(
        {"max_tokens": 10},
        model="openai/gpt-5.4",
        messages=[
            {"role": "system", "content": "stable system prompt"},
            {"role": "user", "content": "dynamic question"},
        ],
    )

    assert kwargs["prompt_cache_key"].startswith("a0-")
    assert kwargs["max_tokens"] == 10


def test_chat_messages_strip_cache_control_for_openai_prompt_cache():
    messages = [
        {
            "role": "system",
            "cache_control": {"type": "ephemeral"},
            "content": [
                {
                    "type": "text",
                    "text": "stable system prompt",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        }
    ]

    prepared = litellm_transport.ChatCompletionsTransport.prepare_messages(
        messages,
        model="openai/gpt-5.4",
        kwargs={},
    )

    assert "cache_control" not in prepared[0]
    assert "cache_control" not in prepared[0]["content"][0]
    assert messages[0]["content"][0]["cache_control"] == {"type": "ephemeral"}


def test_chat_kwargs_mark_cached_tools_for_cache_control_providers():
    kwargs = litellm_transport.ChatCompletionsTransport.prepare_kwargs(
        {
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "lookup",
                        "description": "Search",
                        "parameters": {"type": "object"},
                    },
                }
            ],
        },
        model="anthropic/claude-sonnet-4-5",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "static instructions",
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
        explicit_prompt_caching=True,
    )

    assert kwargs["tools"][0]["function"]["cache_control"] == {
        "type": "ephemeral"
    }


def test_chat_kwargs_strip_orphan_tool_choice_and_enable_fallback_drop_params():
    kwargs = litellm_transport.ChatCompletionsTransport.prepare_kwargs(
        {
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "max_tokens": 10,
        },
        fallback_error=RuntimeError("This model does not support Responses API"),
    )

    assert kwargs["max_tokens"] == 10
    assert kwargs["drop_params"] is True
    assert "tool_choice" not in kwargs
    assert "parallel_tool_calls" not in kwargs


def test_cache_control_policy_keeps_native_responses_first():
    messages = [
        {
            "role": "system",
            "content": "static instructions",
            "cache_control": {"type": "ephemeral"},
        }
    ]

    openai_policy = litellm_transport.TransportPolicy.from_request(
        "openai/gpt-5.4",
        {},
        messages=messages,
    )
    anthropic_policy = litellm_transport.TransportPolicy.from_request(
        "anthropic/claude-sonnet-4-5",
        {},
        messages=messages,
    )

    assert openai_policy.mode is litellm_transport.TransportMode.RESPONSES
    assert anthropic_policy.mode is litellm_transport.TransportMode.CHAT_COMPLETIONS


def test_responses_fallback_does_not_mask_rate_limits():
    exc = RuntimeError(
        "RateLimitError: 429 Too Many Requests for url "
        "https://provider.example/v1/responses"
    )

    policy = litellm_transport.TransportPolicy(
        mode=litellm_transport.TransportMode.RESPONSES
    )

    assert (
        policy.recover(exc, got_any_chunk=False)
        is litellm_transport.TransportRecovery.RAISE
    )


def test_responses_response_parser_extracts_text_reasoning_and_function_calls():
    text_response = {
        "output": [
            {"type": "reasoning", "summary": [{"text": "because"}]},
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "answer"}],
            },
        ]
    }

    parsed = litellm_transport.ResponsesTransport.parse_response(text_response)

    assert parsed == {"response_delta": "answer", "reasoning_delta": "because"}

    tool_response = {
        "output": [
            {
                "type": "function_call",
                "name": "lookup",
                "arguments": '{"q":"a0"}',
            }
        ]
    }

    parsed_tool = litellm_transport.ResponsesTransport.parse_response(tool_response)

    assert extract_tools.json_parse_dirty(parsed_tool["response_delta"]) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }


def test_chat_completions_response_parser_extracts_tool_calls():
    parsed = litellm_transport.ChatCompletionsTransport.parse(
        {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "lookup",
                                    "arguments": '{"q":"a0"}',
                                },
                            }
                        ]
                    }
                }
            ]
        }
    )

    assert extract_tools.json_parse_dirty(parsed["response_delta"]) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }
    assert parsed["_output_items"][0]["name"] == "lookup"


def test_chat_completions_stream_parser_accumulates_tool_call_arguments():
    parser = litellm_transport.ChatCompletionsStreamParser()

    assert parser.parse(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "lookup",
                                    "arguments": '{"q":',
                                },
                            }
                        ]
                    }
                }
            ]
        }
    ) == {"reasoning_delta": "", "response_delta": ""}
    parsed = parser.parse(
        {
            "choices": [
                {
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "function": {"arguments": '"a0"}'},
                            }
                        ]
                    },
                    "finish_reason": "tool_calls",
                }
            ]
        }
    )

    assert extract_tools.json_parse_dirty(parsed["response_delta"]) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }
    assert parser.output_items()[0]["name"] == "lookup"
    assert parser.flush() == {"reasoning_delta": "", "response_delta": ""}


def test_chat_completions_stream_parser_reads_dumped_tool_calls():
    parser = litellm_transport.ChatCompletionsStreamParser()

    assert parser.parse(
        _DumpOnly(
            choices=[
                _DumpOnly(
                    delta=_DumpOnly(
                        tool_calls=[
                            {
                                "index": 0,
                                "id": "call_1",
                                "type": "function",
                                "function": _DumpOnly(
                                    name="lookup",
                                    arguments='{"q":"a0"}',
                                ),
                            }
                        ]
                    )
                )
            ]
        )
    ) == {"reasoning_delta": "", "response_delta": ""}

    parsed = parser.parse(
        _DumpOnly(choices=[_DumpOnly(delta=_DumpOnly(), finish_reason="tool_calls")])
    )

    assert extract_tools.json_parse_dirty(parsed["response_delta"]) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }


@pytest.mark.asyncio
async def test_unified_turn_preserves_chat_streaming_tool_calls(monkeypatch):
    async def fake_acompletion(*args, **kwargs):
        return _AsyncChunkStream(
            [
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "id": "call_1",
                                        "type": "function",
                                        "function": {
                                            "name": "lookup",
                                            "arguments": '{"q":',
                                        },
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "delta": {
                                "tool_calls": [
                                    {
                                        "index": 0,
                                        "function": {"arguments": '"a0"}'},
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls",
                        }
                    ]
                },
            ]
        )

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
    )

    async def response_callback(chunk: str, full: str):
        return None

    result = await wrapper.unified_turn(
        messages=[],
        response_callback=response_callback,
        a0_api_mode="chat",
    )

    assert extract_tools.json_parse_dirty(result.response) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }
    assert result.function_calls[0].name == "lookup"
    assert result.function_calls[0].arguments == {"q": "a0"}


def test_responses_stream_parser_accumulates_function_call_arguments():
    parser = litellm_transport.ResponsesEventParser()

    assert parser.parse(
        {
            "type": "response.output_item.added",
            "output_index": 0,
            "item": {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_1",
                "name": "lookup",
                "arguments": "",
            },
        }
    ) == {"reasoning_delta": "", "response_delta": ""}
    assert parser.parse(
        {
            "type": "response.function_call_arguments.delta",
            "item_id": "fc_1",
            "output_index": 0,
            "delta": '{"q":',
        }
    ) == {"reasoning_delta": "", "response_delta": ""}

    parsed = parser.parse(
        {
            "type": "response.function_call_arguments.done",
            "item_id": "fc_1",
            "output_index": 0,
            "name": "lookup",
            "arguments": '{"q":"a0"}',
        }
    )

    assert extract_tools.json_parse_dirty(parsed["response_delta"]) == {
        "tool_name": "lookup",
        "tool_args": {"q": "a0"},
    }
    assert parser.parse(
        {
            "type": "response.output_item.done",
            "output_index": 0,
            "item": {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_1",
                "name": "lookup",
                "arguments": '{"q":"a0"}',
            },
        }
    ) == {"reasoning_delta": "", "response_delta": ""}


def test_responses_stream_parser_uses_completed_response_when_no_deltas_arrive():
    parser = litellm_transport.ResponsesEventParser()

    parsed = parser.parse(
        {
            "type": "response.completed",
            "response": {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "done"}],
                    }
                ]
            },
        }
    )

    assert parsed == {"reasoning_delta": "", "response_delta": "done"}


def test_responses_stream_parser_handles_refusal_and_failed_events():
    parser = litellm_transport.ResponsesEventParser()

    assert parser.parse(
        {"type": "response.refusal.delta", "delta": "no"}
    ) == {"reasoning_delta": "", "response_delta": "no"}

    with pytest.raises(RuntimeError, match="policy"):
        parser.parse(
            {
                "type": "response.failed",
                "response": {"error": {"message": "policy"}},
            }
        )


def test_responses_response_parser_groups_parallel_function_calls():
    response = {
        "output": [
            {
                "type": "function_call",
                "name": "lookup",
                "arguments": '{"q":"a0"}',
            },
            {
                "type": "function_call",
                "name": "rank",
                "arguments": '{"limit":2}',
            },
        ]
    }

    parsed = litellm_transport.ResponsesTransport.parse_response(response)

    assert extract_tools.json_parse_dirty(parsed["response_delta"]) == {
        "tool_name": "parallel_tool_calls",
        "tool_args": {
            "calls": [
                {"tool_name": "lookup", "tool_args": {"q": "a0"}},
                {"tool_name": "rank", "tool_args": {"limit": 2}},
            ]
        },
    }
