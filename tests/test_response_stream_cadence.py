from types import SimpleNamespace

import pytest

import agent as agent_module
from agent import Agent
from helpers import extension
from helpers.llm_result import LLMResult


async def _run_monologue(monkeypatch, chunks, clock, *, advance=0.0):
    agent = object.__new__(Agent)
    agent.context = SimpleNamespace(streaming_agent=None, task=None)
    agent.last_user_message = None
    events = []
    provider_callbacks = 0

    async def call_extensions(name, _agent=None, **kwargs):
        events.append(("extension", name))
        if name == "response_stream_chunk":
            stream_data = kwargs["stream_data"]
            stream_data["full"] = "masked:" + stream_data["full"]

    async def call_model(*, response_callback, **_kwargs):
        nonlocal provider_callbacks
        full = ""
        for chunk in chunks:
            provider_callbacks += 1
            clock.now += advance
            full += chunk
            stopped = await response_callback(chunk, full)
            if stopped:
                return LLMResult(response=stopped)
        return LLMResult(response=full)

    async def handle_response_stream(full):
        events.append(("handle", full))

    async def done(_result):
        return "done"

    async def no_intervention(*_args):
        return None

    async def no_prompt(**_kwargs):
        return []

    monkeypatch.setattr(extension, "call_extensions_async", call_extensions)
    monkeypatch.setattr(agent_module.time, "monotonic", lambda: clock.now)
    agent.prepare_prompt = no_prompt
    agent.handle_intervention = no_intervention
    agent.call_chat_model_turn = call_model
    agent.handle_response_stream = handle_response_stream
    agent.hist_add_ai_response = lambda *_args, **_kwargs: SimpleNamespace(id="")
    agent._remember_llm_result_state = lambda *_args: None
    agent.process_llm_result_tools = done

    result = await Agent.monologue.__wrapped__(agent)
    return result, events, provider_callbacks


@pytest.mark.asyncio
async def test_response_stream_coalesces_fast_fragments_and_flushes_final(monkeypatch):
    clock = SimpleNamespace(now=0.0)
    result, events, provider_callbacks = await _run_monologue(
        monkeypatch, list("x" * 130), clock
    )

    handled = [value for kind, value in events if kind == "handle"]
    chunk_hooks = [
        event
        for event in events
        if event == ("extension", "response_stream_chunk")
    ]

    assert result == "done"
    assert provider_callbacks == len(chunk_hooks) == 130
    assert handled == ["masked:" + "x" * size for size in (128, 130)]
    assert events.index(("handle", handled[-1])) < events.index(
        ("extension", "response_stream_end")
    )
    assert events.index(("extension", "response_stream_end")) < events.index(
        ("extension", "message_loop_result")
    )


@pytest.mark.asyncio
async def test_response_stream_time_bound_keeps_slow_fragments_live(monkeypatch):
    clock = SimpleNamespace(now=0.0)
    _, events, _ = await _run_monologue(
        monkeypatch, ["a" * 10] * 3, clock, advance=0.03
    )

    handled = [value for kind, value in events if kind == "handle"]
    assert handled == ["masked:" + "a" * size for size in (20, 30)]


@pytest.mark.asyncio
async def test_response_stream_still_stops_on_exact_canonical_root(monkeypatch):
    clock = SimpleNamespace(now=0.0)
    message = '{"tool_name":"response","tool_args":{"text":"ok"}}'
    result, events, provider_callbacks = await _run_monologue(
        monkeypatch, [message[:-1], message[-1], " unreachable"], clock
    )

    assert result == "done"
    assert provider_callbacks == 2
    assert [value for kind, value in events if kind == "handle"] == ["masked:" + message]
    assert events.count(("extension", "response_stream_chunk")) == 2
