import json
import sys
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from agent import Agent, AgentConfig, AgentContextType, LoopData
from helpers import extension, extract_tools, history, litellm_transport
from helpers.log import Log
from helpers.llm_result import LLMResult, result_from_metadata
from helpers.persist_chat import _collect_response_ids
from helpers.tool import Response


@pytest.fixture(autouse=True)
def _clear_transport_capability_cache():
    litellm_transport.clear_transport_capability_cache()


class _AsyncEventStream:
    def __init__(self, events: list[dict]):
        self.events = events
        self.index = 0
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.events):
            raise StopAsyncIteration
        event = self.events[self.index]
        self.index += 1
        return event

    async def aclose(self):
        self.closed = True


def test_responses_function_call_text_preserves_non_ascii_tool_args():
    result = LLMResult.from_response(
        {
            "output": [
                {
                    "type": "function_call",
                    "name": "response",
                    "arguments": '{"text":"привет"}',
                }
            ]
        }
    )

    assert result.function_calls_text() == '{"tool_name": "response", "tool_args": {"text": "привет"}}'


@pytest.mark.parametrize("mode", ["", "chat_completions", "responses", "custom"])
def test_llm_result_round_trip_preserves_explicit_mode(mode):
    result = LLMResult.non_llm() if not mode else LLMResult(
        mode=mode, response_id="resp_1", previous_response_id="resp_0",
        usage={"input_tokens": 10},
    )
    assert LLMResult.from_dict(result.to_dict()) == result
    assert result_from_metadata(result.metadata()).metadata() == result.metadata()


@pytest.mark.parametrize("data", [None, {}, {"mode": None}])
def test_llm_result_missing_mode_keeps_legacy_default(data):
    assert LLMResult.from_dict(data).mode == "responses"


@pytest.mark.parametrize("call_form", [
    "message", "legacy_id", "keyword_id", "result", "result_id", "keywords", "native",
])
def test_history_response_call_compatibility_preserves_state(monkeypatch, call_form):
    monkeypatch.setattr(extension, "call_extensions_sync", lambda *args, **kwargs: None)
    agent = object.__new__(Agent)
    agent.data = {}
    agent.loop_data = LoopData()
    agent.history = history.History(agent)
    agent.parse_prompt = lambda template, **kwargs: kwargs["message"]
    agent.hist_add_message = agent.history.add_message
    remembered = []

    def remember(result, message):
        remembered.append(result)
        Agent._remember_llm_result_state(agent, result, message)

    agent._remember_llm_result_state = remember
    result = LLMResult(response_id="resp_1", provider_model_key="test/model")
    if call_form == "native":
        result = LLMResult.from_response({
            "id": "resp_1", "output_text": "hello",
            "output": [{"type": "function_call", "name": "lookup", "call_id": "call_1", "arguments": '{"q":"a0"}'}],
        }, provider_model_key="test/model")
    args, kwargs = {
        "message": ((), {}),
        "legacy_id": (("message_id",), {}),
        "keyword_id": ((), {"id": "message_id"}),
        "result": ((result,), {}),
        "result_id": ((result, "message_id"), {}),
        "keywords": ((), {"llm_result": result, "id": "message_id"}),
        "native": ((), {"llm_result": result, "id": "message_id"}),
    }[call_form]
    message = agent.hist_add_ai_response("hello", *args, **kwargs)
    expected = result if call_form in {"result", "result_id", "keywords", "native"} else LLMResult.non_llm()
    assert remembered == [expected]
    assert result_from_metadata(message.metadata).metadata() == expected.metadata()
    assert agent.history.all_messages() == [message]
    assert message.content == (expected.function_calls_text() or "hello")
    assert agent.loop_data.last_response == message.content
    if call_form == "native":
        assert result.response == "hello"
    if call_form not in {"message", "result"}:
        assert message.id == "message_id"
    state = agent.get_data(Agent.DATA_NAME_RESPONSES_STATE)
    if expected.response_id:
        assert state["response_ids"] == ["resp_1"]
        assert state["history_counter"] == message.sequence
    else:
        assert state is None

    with pytest.raises(TypeError, match="ID supplied twice"):
        agent.hist_add_ai_response("invalid", "first", id="second")
    assert agent.history.all_messages() == [message]


def test_llm_result_persists_only_durable_responses_metadata():
    result = LLMResult.from_response(
        {
            "id": "resp_123",
            "usage": {"input_tokens": 10},
            "output": [
                {"type": "reasoning", "summary": [{"text": "because"}]},
                {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "call_1",
                    "name": "lookup",
                    "arguments": '{"q":"a0"}',
                },
                {
                    "type": "web_search_call",
                    "id": "ws_1",
                    "status": "completed",
                },
            ],
        },
        input_items=[{"role": "user", "content": "question"}],
        previous_response_id="resp_prev",
        provider_model_key="openai/gpt-5.4",
    )

    metadata = result.metadata()
    persisted = metadata["responses"]
    assert "response" not in persisted
    assert "reasoning" not in persisted
    assert "input_items" not in persisted
    assert "raw" not in persisted

    loaded = result_from_metadata(metadata)

    assert loaded is not None
    assert loaded.response_id == "resp_123"
    assert loaded.previous_response_id == "resp_prev"
    assert loaded.function_calls[0].name == "lookup"
    assert loaded.function_calls[0].arguments == {"q": "a0"}
    assert loaded.builtin_items[0].type == "web_search_call"


def test_history_migrates_legacy_ai_metadata_and_preserves_tool_inputs():
    class DummyAgent:
        pass

    hist = history.History(DummyAgent())
    result = LLMResult.from_response(
        {"id": "resp_1", "output": [{"type": "message", "content": [{"type": "output_text", "text": "ok"}]}]},
        input_items=[{"role": "user", "content": "question"}],
        provider_model_key="openai/gpt-5.4",
    )

    message = hist.add_message(True, "ok", metadata=result.metadata())
    tool_item = {"type": "function_call_output", "call_id": "call_1", "output": "done"}
    hist.add_message(
        False,
        "done",
        metadata={"responses": {"input_items": [tool_item]}},
    )
    serialized = hist.serialize()
    assert '"input_items":[{"type":"function_call_output"' in serialized
    restored = history.deserialize_history(serialized, DummyAgent())

    restored_message = restored.all_messages()[0]
    assert restored_message.sequence == message.sequence
    assert result_from_metadata(restored_message.metadata).response_id == "resp_1"
    assert restored.all_messages()[1].metadata["responses"]["input_items"] == [tool_item]

    migrated = history.Message.from_dict(
        {
            "_cls": "Message",
            "ai": True,
            "content": "old",
            "metadata": {"custom": "keep", "responses": result.to_dict()},
        },
        restored,
    )
    assert "input_items" not in migrated.metadata["responses"]
    assert migrated.metadata["custom"] == "keep"

    old = history.Message.from_dict({"_cls": "Message", "ai": False, "content": "old"}, restored)
    assert old.metadata == {}
    assert old.sequence == 0


@pytest.mark.asyncio
async def test_chat_completion_transport_preserves_reported_usage(monkeypatch):
    async def fake_acompletion(**kwargs):
        return {
            "choices": [{"message": {"content": "done"}}],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 8,
                "total_tokens": 128,
            },
            "_hidden_params": {"response_cost": 0.0042},
        }

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    transport = litellm_transport.LiteLLMTransport(
        model="custom/model",
        messages=[{"role": "user", "content": "question"}],
        kwargs={"a0_api_mode": "chat_completions"},
    )

    await transport.acomplete()

    assert transport.last_result is not None
    assert transport.last_result.usage == {
        "prompt_tokens": 120,
        "completion_tokens": 8,
        "total_tokens": 128,
        "cost": 0.0042,
    }


@pytest.mark.asyncio
async def test_chat_stream_requests_and_records_terminal_usage(monkeypatch):
    calls: list[dict] = []

    async def fake_acompletion(**kwargs):
        calls.append(kwargs)

        async def stream():
            yield {"choices": [{"delta": {"content": "done"}}]}
            yield {
                "choices": [],
                "usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 8,
                    "total_tokens": 128,
                },
            }

        return stream()

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    transport = litellm_transport.LiteLLMTransport(
        model="custom/model",
        messages=[{"role": "user", "content": "question"}],
        kwargs={"a0_api_mode": "chat_completions"},
    )

    async for _chunk in transport.astream():
        pass

    assert calls[0]["stream"] is True
    assert calls[0]["stream_options"] == {"include_usage": True}
    assert transport.last_result is not None
    assert transport.last_result.usage == {
        "prompt_tokens": 120,
        "completion_tokens": 8,
        "total_tokens": 128,
    }


@pytest.mark.asyncio
async def test_chat_stream_retries_without_usage_when_stream_options_rejected(
    monkeypatch,
):
    calls: list[dict] = []

    class BadRequestError(Exception):
        pass

    async def fake_acompletion(**kwargs):
        calls.append(kwargs)
        if kwargs.get("stream_options", {}).get("include_usage"):
            raise BadRequestError("Unknown parameter: 'stream_options'.")

        async def stream():
            yield {"choices": [{"delta": {"content": "done"}}]}

        return stream()

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    transport = litellm_transport.LiteLLMTransport(
        model="custom/model",
        messages=[{"role": "user", "content": "question"}],
        kwargs={
            "a0_api_mode": "chat_completions",
            "stream_options": {"include_usage": True, "custom": "keep"},
        },
    )

    async for _chunk in transport.astream():
        pass

    assert calls[0]["stream_options"] == {
        "include_usage": True,
        "custom": "keep",
    }
    assert calls[1]["stream_options"] == {"custom": "keep"}
    assert len(calls) == 2

    next_transport = litellm_transport.LiteLLMTransport(
        model="custom/model",
        messages=[{"role": "user", "content": "again"}],
        kwargs={
            "a0_api_mode": "chat_completions",
            "stream_options": {"include_usage": True, "custom": "keep"},
        },
    )
    request = next_transport._chat_request(stream=True)
    assert request["stream_options"] == {"custom": "keep"}


def test_responses_provider_state_uses_previous_response_and_new_items():
    new_items = [{"type": "function_call_output", "call_id": "call_1", "output": "done"}]
    local_items = [{"role": "user", "content": "full replay"}]

    request = litellm_transport.ResponsesTransport.from_chat(
        [{"role": "user", "content": "ignored while continuing provider state"}],
        {
            "previous_response_id": "resp_1",
            "responses_input_items": new_items,
            "responses_local_input_items": local_items,
        },
        model="openai/gpt-5.4",
    )

    assert request["store"] is True
    assert request["previous_response_id"] == "resp_1"
    assert request["input"] == new_items

    local_request = litellm_transport.ResponsesTransport.from_chat(
        [{"role": "user", "content": "ignored"}],
        {
            "responses_state": "local",
            "previous_response_id": "resp_1",
            "responses_input_items": new_items,
            "responses_local_input_items": local_items,
        },
        model="openai/gpt-5.4",
    )

    assert local_request["store"] is False
    assert "previous_response_id" not in local_request
    assert local_request["input"] == local_items


@pytest.mark.asyncio
async def test_transport_retries_provider_state_as_local_replay(monkeypatch):
    calls: list[dict] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("previous_response_id is not supported by this provider")
        return {
            "id": "resp_local",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "ok"}],
                }
            ],
        }

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)

    transport = litellm_transport.LiteLLMTransport(
        model="openai/gpt-5.4",
        messages=[{"role": "user", "content": "new"}],
        kwargs={
            "a0_api_mode": "responses",
            "previous_response_id": "resp_1",
            "responses_input_items": [{"role": "user", "content": "new"}],
            "responses_local_input_items": [{"role": "user", "content": "full"}],
        },
    )

    parsed = await transport.acomplete()

    assert parsed["response_delta"] == "ok"
    assert calls[0]["store"] is True
    assert calls[0]["previous_response_id"] == "resp_1"
    assert calls[1]["store"] is False
    assert "previous_response_id" not in calls[1]
    assert calls[1]["input"] == [{"role": "user", "content": "full"}]
    assert transport.last_result.response_id == "resp_local"


@pytest.mark.asyncio
async def test_transport_downgrades_unsupported_builtin_tools(monkeypatch):
    calls: list[dict] = []

    async def fake_aresponses(*args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("unsupported tool type: web_search")
        return {
            "id": "resp_no_builtin",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "ok"}],
                }
            ],
        }

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)

    transport = litellm_transport.LiteLLMTransport(
        model="openai/gpt-5.4",
        messages=[{"role": "user", "content": "new"}],
        kwargs={
            "a0_api_mode": "responses",
            "responses_builtin_tools": [{"type": "web_search"}],
        },
    )

    parsed = await transport.acomplete()

    assert parsed["response_delta"] == "ok"
    assert calls[0]["tools"] == [{"type": "web_search"}]
    assert "tools" not in calls[1]
    assert transport.last_result.capability["builtin_tool_downgrades"] == [
        "web_search"
    ]

    next_transport = litellm_transport.LiteLLMTransport(
        model="openai/gpt-5.4",
        messages=[{"role": "user", "content": "again"}],
        kwargs={
            "a0_api_mode": "responses",
            "responses_builtin_tools": [{"type": "web_search"}],
        },
    )
    request = next_transport._responses_request(stream=False)
    assert "tools" not in request


@pytest.mark.asyncio
async def test_unified_turn_keeps_streamed_call_when_completion_omits_output(
    monkeypatch,
):
    stream = _AsyncEventStream(
        [
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
            },
            {
                "type": "response.function_call_arguments.done",
                "item_id": "fc_1",
                "output_index": 0,
                "name": "lookup",
                "arguments": '{"q":"a0"}',
            },
            {
                "type": "response.completed",
                "response": {
                    "id": "resp_1",
                    "output": [],
                },
            },
        ]
    )

    async def fake_aresponses(*args, **kwargs):
        return stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
        a0_api_mode="responses",
    )

    async def response_callback(chunk: str, full: str):
        return None

    result = await wrapper.unified_turn(
        messages=[HumanMessage(content="hi")],
        response_callback=response_callback,
    )

    assert stream.index == 3
    assert stream.closed is False
    assert result.response_id == "resp_1"
    assert result.function_calls[0].call_id == "call_1"
    assert result.function_calls[0].arguments == {"q": "a0"}


@pytest.mark.asyncio
async def test_unified_turn_waits_for_completed_native_responses_calls(monkeypatch):
    calls = [
        {
            "type": "function_call",
            "id": "fc_1",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": '{"q":"a0"}',
        },
        {
            "type": "function_call",
            "id": "fc_2",
            "call_id": "call_2",
            "name": "summarize",
            "arguments": '{"style":"short"}',
        },
    ]
    stream = _AsyncEventStream(
        [
            {
                "type": "response.output_item.added",
                "output_index": 0,
                "item": {**calls[0], "arguments": ""},
            },
            {
                "type": "response.function_call_arguments.done",
                "item_id": "fc_1",
                "output_index": 0,
                "name": "lookup",
                "arguments": calls[0]["arguments"],
            },
            {
                "type": "response.output_item.added",
                "output_index": 1,
                "item": {**calls[1], "arguments": ""},
            },
            {
                "type": "response.function_call_arguments.done",
                "item_id": "fc_2",
                "output_index": 1,
                "name": "summarize",
                "arguments": calls[1]["arguments"],
            },
            {
                "type": "response.completed",
                "response": {
                    "id": "resp_parallel",
                    "output": calls,
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                    "_hidden_params": {"response_cost": 0.0012},
                },
            },
        ]
    )

    async def fake_aresponses(*args, **kwargs):
        return stream

    async def fake_rate_limiter(*args, **kwargs):
        return None

    monkeypatch.setattr(litellm_transport, "aresponses", fake_aresponses)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)

    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openai",
        model_config=None,
        a0_api_mode="responses",
    )

    async def response_callback(chunk: str, full: str):
        return full if extract_tools.extract_tool_request(full) else None

    result = await wrapper.unified_turn(
        messages=[HumanMessage(content="hi")],
        response_callback=response_callback,
    )

    assert stream.index == 5
    assert stream.closed is False
    assert result.mode == "responses"
    assert result.response_id == "resp_parallel"
    assert result.usage == {
        "input_tokens": 10,
        "output_tokens": 5,
        "cost": 0.0012,
    }
    assert [call.name for call in result.function_calls] == ["lookup", "summarize"]
    assert json.loads(result.response) == {
        "tool_name": "parallel_tool_calls",
        "tool_args": {
            "calls": [
                {"tool_name": "lookup", "tool_args": {"q": "a0"}},
                {"tool_name": "summarize", "tool_args": {"style": "short"}},
            ]
        },
    }


def test_collect_response_ids_from_agent_state_and_history_metadata():
    payload = {
        "agents": [
            {
                "data": {
                    "responses_state": {
                        "response_id": "resp_latest",
                        "response_ids": ["resp_old", "resp_latest"],
                    }
                },
                "history": '{"current":{"messages":[{"metadata":{"responses":{"response_id":"resp_history"}}}]}}',
            }
        ]
    }

    assert _collect_response_ids(payload) == [
        "resp_latest",
        "resp_old",
        "resp_history",
    ]


@pytest.mark.asyncio
async def test_agent_executes_native_responses_function_call_and_records_output():
    class DummyContext:
        paused = False
        log = Log()
        type = AgentContextType.USER

        def get_data(self, key, recursive=True):
            return None

    class DummyTool:
        name = "lookup"
        progress = ""

        def __init__(self, agent):
            self.agent = agent

        async def before_execution(self, **kwargs):
            self.args = kwargs

        async def execute(self, **kwargs):
            return Response(message=f"done:{kwargs['q']}", break_loop=False)

        async def after_execution(self, response):
            self.agent.hist_add_tool_result(
                self.name,
                response.message,
                **(response.additional or {}),
            )

    agent = object.__new__(Agent)
    agent.data = {Agent.DATA_NAME_RESPONSES_TOOL_NAME_MAP: {}}
    agent.context = DummyContext()
    agent.config = AgentConfig(mcp_servers="")
    agent.loop_data = LoopData()
    agent.history = history.History(agent)
    agent.intervention = None
    agent.agent_name = "A0"
    agent.number = 0

    def get_tool(**kwargs):
        return DummyTool(agent)

    agent.get_tool = get_tool

    result = LLMResult.from_response(
        {
            "id": "resp_1",
            "output": [
                {
                    "type": "function_call",
                    "id": "fc_1",
                    "call_id": "call_1",
                    "name": "lookup",
                    "arguments": '{"q":"a0"}',
                }
            ],
        },
        provider_model_key="openai/gpt-5.4",
    )

    assert await Agent.process_llm_result_tools(agent, result) is None

    recorded = agent.history.all_messages()[0]
    metadata = result_from_metadata(recorded.metadata)
    assert recorded.content["tool_result"] == "done:a0"
    assert metadata.input_items == [
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "done:a0",
        }
    ]


@pytest.mark.asyncio
async def test_agent_routes_chat_retries_and_native_responses_text() -> None:
    agent = object.__new__(Agent)
    processed: list[str] = []
    executed: list[dict] = []

    async def log_builtin_items(result):
        return None

    async def process_tools(message):
        processed.append(message)
        return None

    async def execute_tool_request(**kwargs):
        executed.append(kwargs)
        return None

    agent._log_response_builtin_items = log_builtin_items
    agent.process_tools = process_tools
    agent._execute_tool_request = execute_tool_request

    tool_request = '{"type":"function","name":"response","parameters":{"text":"ok"}}'
    chat_messages = (
        "Plain final answer.",
        '{"status":"planning"}',
        f"Example tool JSON: {tool_request}",
        f"∂\n{tool_request}",
        (
            '{"thoughts":["Done"],"headline":"Done","tool_args":'
            '{"text":"ok","tool_name":"response"}'
        ),
    )
    for message in chat_messages:
        assert await Agent.process_llm_result_tools(
            agent, LLMResult.from_chat(response=message)
        ) is None
    assert processed == list(chat_messages)

    processed.clear()
    responses_messages = (
        "Plain final answer.",
        '{"status":"planning"}',
        f"Example tool JSON: {tool_request}",
    )
    for message in responses_messages:
        assert await Agent.process_llm_result_tools(
            agent, LLMResult(response=message)
        ) is None
    assert processed == []
    assert executed == [
        {
            "tool_name": "response",
            "tool_args": {"text": message},
            "message": message,
        }
        for message in responses_messages
    ]

    processed.clear()
    executed.clear()
    assert await Agent.process_llm_result_tools(
        agent, LLMResult.from_chat(response=tool_request)
    ) is None
    assert processed == [tool_request]

    processed.clear()
    assert await Agent.process_llm_result_tools(
        agent, LLMResult(response="", reasoning=tool_request)
    ) is None
    assert processed == [tool_request]

    processed.clear()
    assert await Agent.process_llm_result_tools(
        agent, LLMResult(response="", reasoning='{"status":"planning"}')
    ) is None
    assert processed == [""]


@pytest.mark.asyncio
async def test_agent_routes_misformatted_tool_intent_to_repair() -> None:
    agent = object.__new__(Agent)
    processed: list[str] = []

    async def log_builtin_items(result):
        return None

    async def process_tools(message):
        processed.append(message)
        return None

    agent._log_response_builtin_items = log_builtin_items
    agent.process_tools = process_tools

    malformed = (
        '{"thoughts":["Plan the work", "Run the tools", '
        '"headline":"Save results", "tool_name":"parallel", '
        '"tool_args":{"tool_calls":[{"tool_name":"memory_save",'
        '"tool_args":{"text":"ok"}}],"wait":true}}'
    )

    assert await Agent.process_llm_result_tools(
        agent, LLMResult.from_chat(response=malformed)
    ) is None
    assert processed == [malformed]

    processed.clear()
    assert await Agent.process_llm_result_tools(
        agent, LLMResult(response="", reasoning=malformed)
    ) is None
    assert processed == [malformed]

    fenced = (
        "I will call the tool.\n\n```json\n"
        '{"tool_name":"response","tool_args":{"text":"ok"}}\n```'
    )
    processed.clear()
    assert await Agent.process_llm_result_tools(
        agent, LLMResult.from_chat(response=fenced)
    ) is None
    assert processed == [fenced]


@pytest.mark.asyncio
async def test_text_tool_execution_uses_normalized_tool_args(monkeypatch) -> None:
    class DummyMCPConfig:
        def get_tool(self, agent, tool_name):
            return None

    class DummyTool:
        def __init__(self):
            self.args = {}

        async def before_execution(self, **kwargs):
            assert self.args == {"text": "ok"}

        async def execute(self, **kwargs):
            assert kwargs == {"text": "ok"}
            return Response(message=self.args["text"], break_loop=True)

        async def after_execution(self, response):
            return None

    async def no_extension(*args, **kwargs):
        return None

    async def no_intervention(*args, **kwargs):
        return None

    import agent as agent_module
    from helpers import mcp_handler

    monkeypatch.setattr(
        mcp_handler.MCPConfig, "get_instance", lambda: DummyMCPConfig()
    )
    monkeypatch.setattr(agent_module.extension, "call_extensions_async", no_extension)

    tool = DummyTool()
    agent = object.__new__(Agent)
    agent.data = {}
    agent.loop_data = LoopData()
    agent.handle_intervention = no_intervention
    agent.get_tool = lambda **kwargs: tool

    assert await Agent.process_tools(
        agent, '{"actions":[{"tool_name":"response","tool_args":{"text":"ok"}}]}'
    ) == "ok"
