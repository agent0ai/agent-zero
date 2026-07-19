import sys
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from agent import Agent, AgentConfig, AgentContextType, LoopData
from helpers import history, litellm_transport
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
async def test_unified_turn_keeps_stream_open_to_capture_response_id(monkeypatch):
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
        return full

    result = await wrapper.unified_turn(
        messages=[HumanMessage(content="hi")],
        response_callback=response_callback,
    )

    assert stream.index == 3
    assert stream.closed is False
    assert result.response_id == "resp_1"
    assert result.function_calls[0].call_id == "call_1"


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
