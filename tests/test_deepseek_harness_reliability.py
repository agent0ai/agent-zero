"""Regression tests for DeepSeek V4 Flash harness reliability.

Covers the failure modes observed with deepseek/deepseek-v4-flash:
- planning prose before an otherwise valid JSON tool envelope
- provider-truncated output (finish_reason=length) being indistinguishable
  from a malformed response
- concurrent memory post-processing jobs racing on the background loop
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.extract_tools import (
    explain_tool_request_failure,
    extract_tool_request,
    recover_embedded_tool_request,
)
from helpers.litellm_transport import (
    ChatCompletionsStreamParser,
    ChatCompletionsTransport,
)
from helpers.llm_result import LLMResult
from plugins._memory.helpers.memorize_lock import get_memorize_lock


TOOL_REQUEST = (
    '{"thoughts":["check state"],"headline":"Checking state",'
    '"tool_name":"code_execution_tool","tool_args":{"code":"ls"}}'
)


# --- embedded tool-request recovery -----------------------------------------


def test_recover_embedded_tool_request_accepts_prose_before_json() -> None:
    content = (
        "I'll first verify the current state, then apply the fix.\n\n"
        + TOOL_REQUEST
    )

    assert extract_tool_request(content) is None  # strict path stays strict
    recovered = recover_embedded_tool_request(content)
    assert recovered is not None
    assert recovered["tool_name"] == "code_execution_tool"
    assert recovered["tool_args"] == {"code": "ls"}


def test_recover_embedded_tool_request_accepts_prose_after_json() -> None:
    content = TOOL_REQUEST + "\n\nThat will show the current files."

    recovered = recover_embedded_tool_request(content)
    assert recovered is not None
    assert recovered["tool_name"] == "code_execution_tool"


def test_recover_embedded_tool_request_rejects_multiple_distinct_requests() -> None:
    other = (
        '{"thoughts":["reply"],"headline":"Reply",'
        '"tool_name":"response","tool_args":{"text":"hi"}}'
    )
    content = f"First option:\n{TOOL_REQUEST}\nSecond option:\n{other}"

    assert recover_embedded_tool_request(content) is None


def test_recover_embedded_tool_request_dedupes_repeated_identical_request() -> None:
    content = f"As planned:\n{TOOL_REQUEST}\nRepeating for clarity:\n{TOOL_REQUEST}"

    recovered = recover_embedded_tool_request(content)
    assert recovered is not None
    assert recovered["tool_name"] == "code_execution_tool"


def test_recover_embedded_tool_request_rejects_plain_prose() -> None:
    assert recover_embedded_tool_request("I need to think about this first.") is None
    assert recover_embedded_tool_request("") is None


def test_recover_embedded_tool_request_rejects_non_tool_json() -> None:
    assert recover_embedded_tool_request('Here is the status: {"status":"ok"}') is None


# --- failure diagnostics -----------------------------------------------------


def test_explain_tool_request_failure_flags_truncated_envelope() -> None:
    truncated = (
        '{"thoughts":["apply the patch"],"headline":"Applying patch",'
        '"tool_name":"code_execution_tool","tool_args":{"code":"echo'
    )

    reason = explain_tool_request_failure(truncated)
    assert "truncated" in reason.lower()
    assert str(len(truncated)) in reason


def test_explain_tool_request_failure_flags_plain_prose() -> None:
    reason = explain_tool_request_failure("Let me plan the next steps first.")

    assert "no json" in reason.lower() or "prose" in reason.lower()


def test_explain_tool_request_failure_flags_empty_response() -> None:
    assert "empty" in explain_tool_request_failure("").lower()
    assert "empty" in explain_tool_request_failure("   \n  ").lower()


def test_explain_tool_request_failure_flags_non_tool_json() -> None:
    reason = explain_tool_request_failure('{"status":"planning"}')

    assert "tool_name" in reason or "tool_args" in reason


# --- finish_reason propagation -----------------------------------------------


def test_chat_completions_parse_captures_finish_reason() -> None:
    chunk = {
        "choices": [
            {"message": {"content": "partial"}, "finish_reason": "length"}
        ]
    }

    parsed = ChatCompletionsTransport.parse(chunk)

    assert parsed["response_delta"] == "partial"
    assert parsed["finish_reason"] == "length"


def test_chat_completions_stream_parser_remembers_finish_reason() -> None:
    parser = ChatCompletionsStreamParser()
    parser.parse(
        {"choices": [{"delta": {"content": "part"}, "finish_reason": None}]}
    )
    parser.parse({"choices": [{"delta": {}, "finish_reason": "length"}]})

    assert parser.finish_reason == "length"


def test_llm_result_from_chat_carries_finish_reason_roundtrip() -> None:
    result = LLMResult.from_chat(response="text", finish_reason="length")

    assert result.finish_reason == "length"
    assert result.metadata()["responses"]["finish_reason"] == "length"

    restored = LLMResult.from_dict(result.to_dict())
    assert restored.finish_reason == "length"


def test_llm_result_finish_reason_defaults_empty() -> None:
    assert LLMResult.from_chat(response="text").finish_reason == ""
    assert LLMResult.from_dict({}).finish_reason == ""


# --- memory job serialization --------------------------------------------------


def test_memorize_lock_is_shared_and_serializes_jobs() -> None:
    assert get_memorize_lock() is get_memorize_lock()

    events: list[str] = []

    async def job(name: str) -> None:
        async with get_memorize_lock():
            events.append(f"start:{name}")
            await asyncio.sleep(0.01)
            events.append(f"end:{name}")

    async def main() -> None:
        await asyncio.gather(job("fragments"), job("solutions"))

    asyncio.run(main())

    # no interleaving: each job must fully finish before the next starts
    assert events in (
        ["start:fragments", "end:fragments", "start:solutions", "end:solutions"],
        ["start:solutions", "end:solutions", "start:fragments", "end:fragments"],
    )


# --- agent-level wiring --------------------------------------------------------


@pytest.mark.asyncio
async def test_process_tools_recovers_embedded_tool_request(monkeypatch) -> None:
    import agent as agent_module
    from agent import Agent, LoopData
    from helpers import mcp_handler
    from helpers.tool import Response

    class DummyMCPConfig:
        def get_tool(self, agent, tool_name):
            return None

    class DummyTool:
        def __init__(self):
            self.args = {}

        async def before_execution(self, **kwargs):
            return None

        async def execute(self, **kwargs):
            return Response(message=f"ran:{self.args['code']}", break_loop=True)

        async def after_execution(self, response):
            return None

    async def no_extension(*args, **kwargs):
        return None

    async def no_intervention(*args, **kwargs):
        return None

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

    content = (
        "I'll first verify whether the patch helper survived, then apply the fix.\n\n"
        + TOOL_REQUEST
    )

    assert await Agent.process_tools(agent, content) == "ran:ls"
    assert tool.args == {"code": "ls"}


@pytest.mark.asyncio
async def test_process_llm_result_tools_forwards_finish_reason(monkeypatch) -> None:
    from agent import Agent

    agent = object.__new__(Agent)
    captured: list[dict] = []

    async def log_builtin_items(result):
        return None

    async def process_tools(message, **kwargs):
        captured.append({"message": message, **kwargs})
        return None

    agent._log_response_builtin_items = log_builtin_items
    agent.process_tools = process_tools

    truncated = '{"thoughts":["apply patch"],"tool_name":"code_execution'
    result = LLMResult.from_chat(response=truncated, finish_reason="length")

    assert await Agent.process_llm_result_tools(agent, result) is None
    assert captured == [{"message": truncated, "finish_reason": "length"}]


@pytest.mark.asyncio
async def test_process_tools_logs_sanitized_failure_reason(monkeypatch) -> None:
    from types import SimpleNamespace

    import agent as agent_module
    from agent import Agent, LoopData

    async def no_extension(*args, **kwargs):
        return None

    async def no_intervention(*args, **kwargs):
        return None

    monkeypatch.setattr(agent_module.extension, "call_extensions_async", no_extension)

    logged: list[dict] = []
    agent = object.__new__(Agent)
    agent.data = {}
    agent.loop_data = LoopData()
    agent.agent_name = "A0"
    agent.handle_intervention = no_intervention
    agent.read_prompt = lambda name, **kw: "misformatted"
    agent.hist_add_warning = lambda msg: SimpleNamespace(id=None)
    agent.context = SimpleNamespace(
        log=SimpleNamespace(log=lambda **entry: logged.append(entry))
    )

    truncated = (
        '{"thoughts":["apply the patch"],"headline":"Applying patch",'
        '"tool_name":"code_execution_tool","tool_args":{"code":"echo'
    )

    await Agent.process_tools(agent, truncated, finish_reason="length")

    warnings = [e for e in logged if e.get("type") == "warning"]
    assert warnings, "expected a misformat warning log entry"
    content = warnings[-1]["content"]
    assert "misformat" in content.lower()
    assert "truncated" in content.lower()
    assert "finish_reason=length" in content


# --- stream integrity: provider-dropped connections ----------------------------


class _FakeAsyncStream:
    def __init__(self, chunks):
        self._chunks = chunks
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


def _chat_transport():
    from helpers import litellm_transport as lt

    return lt.LiteLLMTransport(
        model="deepseek/deepseek-v4-flash",
        messages=[{"role": "user", "content": "hi"}],
        kwargs={"a0_api_mode": "chat"},
    )


@pytest.mark.asyncio
async def test_transport_records_finish_reason_when_stream_completes(monkeypatch) -> None:
    from helpers import litellm_transport as lt

    chunks = [
        {"choices": [{"delta": {"content": '{"tool_name":"response"}'}}]},
        {"choices": [{"delta": {}, "finish_reason": "stop"}]},
    ]

    async def fake_acompletion(**kwargs):
        return _FakeAsyncStream(chunks)

    monkeypatch.setattr(lt, "acompletion", fake_acompletion)
    transport = _chat_transport()
    async for _ in transport.astream():
        pass

    assert transport.last_finish_reason == "stop"


@pytest.mark.asyncio
async def test_transport_records_missing_finish_reason_when_stream_drops(monkeypatch) -> None:
    """DeepSeek intermittently closes the connection mid-stream; LiteLLM ends
    the iterator without an error, so no terminal finish_reason ever arrives."""
    from helpers import litellm_transport as lt

    chunks = [
        {"choices": [{"delta": {"content": '{"thoughts":["partial"], "tool_na'}}]},
    ]

    async def fake_acompletion(**kwargs):
        return _FakeAsyncStream(chunks)

    monkeypatch.setattr(lt, "acompletion", fake_acompletion)
    transport = _chat_transport()
    async for _ in transport.astream():
        pass

    assert transport.last_finish_reason == ""


def test_should_retry_truncated_stream_flags_dropped_deepseek_stream() -> None:
    from types import SimpleNamespace

    from models import _should_retry_truncated_stream

    transport = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="deepseek/deepseek-v4-flash",
        last_finish_reason="",
    )
    assert _should_retry_truncated_stream(transport, stream=True, stopped_early=False) is True


def test_should_retry_truncated_stream_accepts_clean_stop() -> None:
    from types import SimpleNamespace

    from models import _should_retry_truncated_stream

    for reason in ("stop", "length", "tool_calls"):
        transport = SimpleNamespace(
            policy=SimpleNamespace(using_responses=False),
            model="deepseek/deepseek-v4-flash",
            last_finish_reason=reason,
        )
        assert _should_retry_truncated_stream(transport, stream=True, stopped_early=False) is False


def test_should_retry_truncated_stream_exempts_early_stop_and_non_deepseek() -> None:
    from types import SimpleNamespace

    from models import _should_retry_truncated_stream

    dropped = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="deepseek/deepseek-v4-flash",
        last_finish_reason="",
    )
    # agent's own early-stop breaks the stream before finish_reason arrives
    assert _should_retry_truncated_stream(dropped, stream=True, stopped_early=True) is False
    # non-stream calls always carry a terminal state from the provider
    assert _should_retry_truncated_stream(dropped, stream=False, stopped_early=False) is False
    # other providers may legitimately omit finish_reason; do not change behavior
    other = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="openai/gpt-5.4",
        last_finish_reason="",
    )
    assert _should_retry_truncated_stream(other, stream=True, stopped_early=False) is False
    # responses-api transport has its own completion semantics
    responses_transport = SimpleNamespace(
        policy=SimpleNamespace(using_responses=True),
        model="deepseek/deepseek-v4-flash",
        last_finish_reason="",
    )
    assert _should_retry_truncated_stream(responses_transport, stream=True, stopped_early=False) is False


@pytest.mark.asyncio
async def test_unified_turn_retries_dropped_deepseek_stream(monkeypatch) -> None:
    """End-to-end: first stream dies mid-JSON (no finish_reason), the retry
    delivers the complete envelope; the partial output must be discarded."""
    import models
    from helpers import litellm_transport as lt

    partial = [
        {"choices": [{"delta": {"content": '{"thoughts":["apply patch"], "tool_na'}}]},
    ]
    complete = [
        {"choices": [{"delta": {"content": '{"tool_name":"response",'}}]},
        {"choices": [{"delta": {"content": '"tool_args":{"text":"ok"}}'}}]},
        {"choices": [{"delta": {}, "finish_reason": "stop"}]},
    ]
    streams = [_FakeAsyncStream(partial), _FakeAsyncStream(complete)]
    calls = 0

    async def fake_acompletion(**kwargs):
        nonlocal calls
        stream = streams[min(calls, len(streams) - 1)]
        calls += 1
        return stream

    monkeypatch.setattr(lt, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "configure_litellm", lambda: None)

    model = models.LiteLLMChatWrapper(
        model="deepseek-v4-flash", provider="deepseek",
        a0_api_mode="chat", a0_retry_delay_seconds=0,
    )

    streamed: list[str] = []

    async def on_chunk(chunk: str, full: str):
        streamed.append(chunk)
        return None

    result = await model.unified_turn(
        user_message="hi", response_callback=on_chunk,
    )

    assert calls == 2, "dropped stream must trigger exactly one retry"
    assert result.response == '{"tool_name":"response","tool_args":{"text":"ok"}}'
    assert result.finish_reason == "stop"
    # the partial first attempt must not leak into the final response
    assert "apply patch" not in result.response


@pytest.mark.asyncio
async def test_unified_turn_accepts_partial_after_retries_exhausted(monkeypatch) -> None:
    """If every attempt is dropped, fall back to the last partial response
    (previous behavior) rather than failing the turn."""
    import models
    from helpers import litellm_transport as lt

    partial = [
        {"choices": [{"delta": {"content": '{"thoughts":["still cut"], "tool_na'}}]},
    ]

    async def fake_acompletion(**kwargs):
        return _FakeAsyncStream(partial)

    monkeypatch.setattr(lt, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "configure_litellm", lambda: None)

    model = models.LiteLLMChatWrapper(
        model="deepseek-v4-flash", provider="deepseek",
        a0_api_mode="chat", a0_retry_delay_seconds=0,
    )

    async def on_chunk(chunk: str, full: str):
        return None

    result = await model.unified_turn(user_message="hi", response_callback=on_chunk)

    assert result.response == '{"thoughts":["still cut"], "tool_na'
    assert result.finish_reason == ""


def test_truncated_json_body_is_classified_transient_despite_http_200() -> None:
    """DeepSeek sometimes closes a non-streaming response mid-body; LiteLLM
    raises 'Unable to get json response' with the original 200 status code,
    which must still count as transient so the call is retried."""
    from models import _is_transient_litellm_error

    class FakeProviderError(Exception):
        def __init__(self):
            super().__init__(
                "litellm.APIError: APIError: DeepseekException - "
                "Unable to get json response - Unterminated string starting "
                "at: line 1 column 2001 (char 2000), Original Response: {..."
            )
            self.message = str(self)
            self.status_code = 200

    assert _is_transient_litellm_error(FakeProviderError()) is True


# --- empty completions (DeepSeek JSON/thinking mode) ---------------------------


def test_should_retry_empty_completion_flags_whitespace_stop() -> None:
    """Reproduces seq 1082: full reasoning stream, finish_reason=stop, and a
    message body of 45 spaces — the provider completed but returned nothing."""
    from types import SimpleNamespace

    from models import _should_retry_empty_completion

    transport = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="deepseek/deepseek-v4-flash",
    )
    assert _should_retry_empty_completion(transport, " " * 45, stopped_early=False) is True
    assert _should_retry_empty_completion(transport, "", stopped_early=False) is True


def test_should_retry_empty_completion_accepts_real_content() -> None:
    from types import SimpleNamespace

    from models import _should_retry_empty_completion

    transport = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="deepseek/deepseek-v4-flash",
    )
    assert _should_retry_empty_completion(transport, '{"tool_name":"x"}', stopped_early=False) is False
    assert _should_retry_empty_completion(transport, "", stopped_early=True) is False

    other = SimpleNamespace(
        policy=SimpleNamespace(using_responses=False),
        model="openai/gpt-5.4",
    )
    assert _should_retry_empty_completion(other, "", stopped_early=False) is False

    responses_transport = SimpleNamespace(
        policy=SimpleNamespace(using_responses=True),
        model="deepseek/deepseek-v4-flash",
    )
    assert _should_retry_empty_completion(responses_transport, "", stopped_early=False) is False


@pytest.mark.asyncio
async def test_unified_turn_retries_empty_completion_with_reasoning(monkeypatch) -> None:
    """Mirror of the production failure: reasoning streams fully, content is
    whitespace, finish_reason=stop; the retry must deliver the real envelope."""
    import models
    from helpers import litellm_transport as lt

    empty_completion = [
        {"choices": [{"delta": {"reasoning_content": "Let me plan the patch carefully."}}]},
        {"choices": [{"delta": {"content": " " * 45}}]},
        {"choices": [{"delta": {}, "finish_reason": "stop"}]},
    ]
    complete = [
        {"choices": [{"delta": {"content": '{"tool_name":"response","tool_args":{"text":"ok"}}'}}]},
        {"choices": [{"delta": {}, "finish_reason": "stop"}]},
    ]
    streams = [_FakeAsyncStream(empty_completion), _FakeAsyncStream(complete)]
    calls = 0

    async def fake_acompletion(**kwargs):
        nonlocal calls
        stream = streams[min(calls, len(streams) - 1)]
        calls += 1
        return stream

    monkeypatch.setattr(lt, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "configure_litellm", lambda: None)

    model = models.LiteLLMChatWrapper(
        model="deepseek-v4-flash", provider="deepseek",
        a0_api_mode="chat", a0_retry_delay_seconds=0,
    )

    async def on_chunk(chunk: str, full: str):
        return None

    result = await model.unified_turn(user_message="hi", response_callback=on_chunk)

    assert calls == 2, "whitespace-only completion must trigger exactly one retry"
    assert result.response == '{"tool_name":"response","tool_args":{"text":"ok"}}'
    assert result.finish_reason == "stop"
