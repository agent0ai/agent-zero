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
from helpers import extract_tools, history, litellm_transport
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
    restored = history.deserialize_history(hist.serialize(), DummyAgent())

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
        kwargs={"responses_builtin_tools": [{"type": "web_search"}]},
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
        kwargs={"responses_builtin_tools": [{"type": "web_search"}]},
    )
    request = next_transport._responses_request(stream=False)
    assert "tools" not in request


@pytest.mark.asyncio
async def test_unified_turn_captures_response_id_without_stop_request(monkeypatch):
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
    assert result.usage == {"input_tokens": 10, "output_tokens": 5}
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

    async def process_tools(message, **kwargs):
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

    async def process_tools(message, **kwargs):
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
