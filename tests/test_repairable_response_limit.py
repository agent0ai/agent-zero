"""Bound tool self-repair through the real agent loop without a live provider."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from agent import Agent
from extensions.python._functions.agent.Agent.handle_exception.end import (
    _40_handle_intervention_exception as intervention_handler,
)
from extensions.python._functions.agent.Agent.handle_exception.end import (
    _50_handle_repairable_exception as repair_handler,
)
from extensions.python._functions.agent.Agent.handle_exception.end import (
    _90_handle_critical_exception as critical_handler,
)
from extensions.python._functions.agent.Agent.hist_add_warning.end import (
    _90_stop_unusable_response_loop as response_loop,
)
from extensions.python.message_loop_result._30_repeat_response import RepeatResponse
from helpers import extension, history, mcp_handler
from helpers.errors import HandledException, InterventionException, RepairableException
from helpers.files import read_prompt_file
from helpers.llm_result import LLMResult, ResponseItem
from helpers.log import Log
from helpers.tool import Response, Tool
from tools.response import ResponseTool


class ProbeBudgetExceeded(BaseException):
    """Stop a faulty loop without making a real request or relying on timeouts."""


class ContinuingTool(Tool):
    async def execute(self, **kwargs):
        if self.args.get("warning"):
            self.agent.hist_add_warning(self.args["warning"])
        return Response(message="continued", break_loop=False)


class RepairableTool(Tool):
    async def execute(self, **kwargs):
        if self.args.get("warning"):
            self.agent.hist_add_warning(self.agent.read_prompt("fw.msg_misformat.md"))
        raise RepairableException(self.args["error"])


def _request(name="response", **args):
    return json.dumps({"tool_name": name, "tool_args": args})


def _nested_response(turn):
    return _request(text={"user_message": f"answer {turn}"})


def _agent(monkeypatch, output, limit=3):
    agent = object.__new__(Agent)
    agent.agent_name = "A0"
    agent.data = {}
    agent.last_user_message = None
    agent.history = history.History(agent)
    agent.hist_add_message = agent.history.add_message
    agent.parse_prompt = lambda name, **kwargs: kwargs["message"]
    agent.read_prompt = lambda name, **kwargs: read_prompt_file(
        name, ["plugins/_context_doctor/prompts", "prompts"], **kwargs
    )
    agent.context = SimpleNamespace(log=Log(), streaming_agent=None, task=None)
    tool_types = {
        "response": ResponseTool,
        "continue": ContinuingTool,
        "repairable": RepairableTool,
    }
    agent.get_tool = lambda **kwargs: tool_types[kwargs["name"]](agent=agent, **kwargs)
    calls: list[str | LLMResult] = []

    async def no_op(*args, **kwargs):
        return []

    async def call_model(**kwargs):
        if len(calls) >= 12:
            raise ProbeBudgetExceeded(
                f"12 model turns exceeded configured limit {limit}; "
                f"breaker state={agent.loop_data.params_persistent!r}"
            )
        text = output(len(calls))
        calls.append(text)
        if isinstance(text, LLMResult):
            return text
        return LLMResult(response=text, mode="chat_completions")

    hook_classes = {
        "_functions/agent/Agent/handle_exception/end": [
            intervention_handler.HandleInterventionException,
            repair_handler.HandleRepairableException,
            critical_handler.HandleCriticalException,
        ],
        "_functions/agent/Agent/hist_add_warning/end": [
            response_loop.StopUnusableResponseLoop,
        ],
        "message_loop_result": [RepeatResponse],
    }
    # Retain actual dispatch, decorators, handler, breaker and tool execution;
    # isolate unrelated plugins/persistence and replace only the model boundary.
    monkeypatch.setattr(
        extension,
        "_get_extension_classes",
        lambda point, **kwargs: hook_classes.get(point, []),
    )
    for module in (response_loop, repair_handler):
        monkeypatch.setattr(
            module,
            "get_settings",
            lambda: {"max_consecutive_unusable_responses": limit},
            raising=False,
        )
    monkeypatch.setattr(
        mcp_handler.MCPConfig,
        "get_instance",
        lambda: SimpleNamespace(get_tool=lambda *args: None),
    )
    agent.prepare_prompt = no_op
    agent.handle_intervention = no_op
    agent.call_chat_model_turn = call_model
    return agent, calls


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [1, 3, 5])
async def test_nested_response_arguments_stop_at_configured_limit(monkeypatch, limit):
    agent, calls = _agent(monkeypatch, _nested_response, limit=limit)
    with pytest.raises(HandledException, match=f"after {limit} consecutive"):
        await agent.monologue()
    assert len(calls) == limit
    assert agent.loop_data.params_persistent[response_loop.STATE_KEY]["count"] == limit


@pytest.mark.asyncio
async def test_native_response_call_uses_the_same_repair_limit(monkeypatch):
    def output(turn):
        return LLMResult(
            response=f"answer {turn}",
            mode="responses",
            output_items=[
                ResponseItem.from_any(
                    {
                        "type": "function_call",
                        "name": "response",
                        "call_id": f"call_{turn}",
                        "arguments": {"text": {"user_message": f"answer {turn}"}},
                    }
                )
            ],
        )

    agent, calls = _agent(monkeypatch, output)
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_malformed_json_still_stops_at_configured_limit(monkeypatch):
    agent, calls = _agent(monkeypatch, lambda turn: f"no tool request {turn}")
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_valid_response_still_completes(monkeypatch):
    agent, calls = _agent(
        monkeypatch,
        lambda turn: '{"tool_name":"response","tool_args":{"text":"done"}}',
    )
    assert await agent.monologue() == "done"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_corrected_response_can_finish_before_the_limit(monkeypatch):
    outputs = [_nested_response(0), _request(text=""), _request(text="done")]
    agent, calls = _agent(monkeypatch, outputs.__getitem__)
    assert await agent.monologue() == "done"
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_new_monologue_has_a_fresh_repair_budget(monkeypatch):
    outputs = [
        _nested_response(0),
        _nested_response(1),
        _request(text="first"),
        _nested_response(3),
        _nested_response(4),
        _request(text="second"),
    ]
    agent, calls = _agent(monkeypatch, outputs.__getitem__)
    assert await agent.monologue() == "first"
    assert await agent.monologue() == "second"
    assert len(calls) == 6


@pytest.mark.asyncio
@pytest.mark.parametrize("failures_after_success", [2, 3])
async def test_successful_tool_starts_a_new_repair_window(
    monkeypatch,
    failures_after_success,
):
    outputs = [_nested_response(0), _nested_response(1), _request("continue")]
    outputs += [_nested_response(turn + 3) for turn in range(failures_after_success)]
    outputs.append(_request(text="done"))
    agent, calls = _agent(monkeypatch, outputs.__getitem__)
    if failures_after_success == 3:
        with pytest.raises(HandledException, match="after 3 consecutive"):
            await agent.monologue()
    else:
        assert await agent.monologue() == "done"
    assert len(calls) == 6
    assert agent.loop_data.params_persistent[response_loop.STATE_KEY]["count"] == (
        failures_after_success
    )


@pytest.mark.asyncio
async def test_different_repairable_error_messages_cannot_escape_the_limit(monkeypatch):
    errors = ["missing field", "unsupported argument", "invalid value"]
    agent, calls = _agent(
        monkeypatch,
        lambda turn: _request("repairable", error=errors[turn]),
    )
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_mixed_malformed_and_repairable_responses_share_the_limit(monkeypatch):
    outputs = ["no tool request", _nested_response(1), "still no tool request"]
    agent, calls = _agent(monkeypatch, outputs.__getitem__)
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()
    assert len(calls) == 3


@pytest.mark.asyncio
async def test_warning_and_repairable_error_count_once_per_iteration(monkeypatch):
    agent, calls = _agent(
        monkeypatch,
        lambda turn: _request("repairable", error=f"bad argument {turn}", warning=True),
    )
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()
    assert len(calls) == 3


def test_exhausted_iteration_stays_stopped_without_duplicate_count_or_log(monkeypatch):
    agent, _ = _agent(monkeypatch, _nested_response)
    agent.loop_data = SimpleNamespace(iteration=1, params_persistent={})
    entries: list[dict] = []
    agent.context.log = SimpleNamespace(log=lambda **entry: entries.append(entry))
    record = response_loop.response_recovery.record_unusable_response

    first = record(agent, 1)
    second = record(agent, 1)

    assert isinstance(first, HandledException)
    assert isinstance(second, HandledException)
    assert str(first) == str(second)
    assert agent.loop_data.params_persistent[response_loop.STATE_KEY] == {
        "iteration": 1,
        "count": 1,
    }
    assert entries == [{"type": "warning", "content": str(first)}]


@pytest.mark.asyncio
async def test_error_warning_stop_propagates_before_the_repair_handler_can_clear_it(
    monkeypatch,
):
    agent, calls = _agent(monkeypatch, _nested_response)

    class FormatAsMisformat(extension.Extension):
        def execute(self, msg, **kwargs):
            msg["message"] = agent.read_prompt("fw.msg_misformat.md")

    original_classes = extension._get_extension_classes
    monkeypatch.setattr(
        extension,
        "_get_extension_classes",
        lambda point, **kwargs: (
            [FormatAsMisformat]
            if point == "error_format"
            else original_classes(point, **kwargs)
        ),
    )
    recorded_iterations: list[int] = []
    original_record = repair_handler.record_unusable_response

    def record(agent, limit):
        recorded_iterations.append(agent.loop_data.iteration)
        return original_record(agent, limit)

    monkeypatch.setattr(repair_handler, "record_unusable_response", record)
    with pytest.raises(HandledException, match="after 3 consecutive"):
        await agent.monologue()

    assert len(calls) == 3
    assert recorded_iterations == [0, 1]
    assert agent.loop_data.params_persistent[response_loop.STATE_KEY]["count"] == 3


@pytest.mark.asyncio
async def test_ordinary_tool_warnings_do_not_consume_the_repair_budget(monkeypatch):
    agent, calls = _agent(
        monkeypatch,
        lambda turn: (
            _request("continue", warning=f"ordinary warning {turn}")
            if turn < 5
            else _request(text="done")
        ),
    )
    assert await agent.monologue() == "done"
    assert len(calls) == 6
    assert response_loop.STATE_KEY not in agent.loop_data.params_persistent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception",
    [
        None,
        RuntimeError("critical"),
        HandledException("stop"),
        InterventionException("intervene"),
        asyncio.CancelledError(),
    ],
)
async def test_handler_does_not_count_other_exception_types(monkeypatch, exception):
    agent, _ = _agent(monkeypatch, _nested_response)
    prior_state = (
        {response_loop.STATE_KEY: {"iteration": 1, "count": 3}}
        if isinstance(exception, HandledException)
        else {}
    )
    agent.loop_data = SimpleNamespace(iteration=1, params_persistent=prior_state.copy())
    data = {"exception": exception}
    await repair_handler.HandleRepairableException(agent=agent).execute(data)
    assert data["exception"] is exception
    assert agent.loop_data.params_persistent == prior_state


@pytest.mark.asyncio
async def test_repairable_error_formatting_still_precedes_history_and_logging(
    monkeypatch,
):
    warnings = []
    logs = []

    def hist_add_warning(message):
        warnings.append(message)
        return SimpleNamespace(id="w")

    agent = SimpleNamespace(
        loop_data=SimpleNamespace(iteration=1, params_persistent={}),
        hist_add_warning=hist_add_warning,
        context=SimpleNamespace(
            log=SimpleNamespace(log=lambda **entry: logs.append(entry))
        ),
    )

    async def mask_error(point, **kwargs):
        assert point == "error_format"
        kwargs["msg"]["message"] = "masked repairable error"

    monkeypatch.setattr(extension, "call_extensions_async", mask_error)
    monkeypatch.setattr(
        repair_handler,
        "get_settings",
        lambda: {"max_consecutive_unusable_responses": 3},
        raising=False,
    )
    data = {"exception": RepairableException("sensitive test value")}
    await repair_handler.HandleRepairableException(agent=agent).execute(data)
    assert data["exception"] is None
    assert warnings == ["masked repairable error"]
    assert logs == [{"type": "warning", "content": warnings[0], "id": "w"}]
    assert agent.loop_data.params_persistent[response_loop.STATE_KEY]["count"] == 1


@pytest.mark.asyncio
async def test_repairable_error_without_loop_state_remains_repairable(monkeypatch):
    agent, _ = _agent(monkeypatch, _nested_response)
    data = {"exception": RepairableException("invalid tool argument")}
    await repair_handler.HandleRepairableException(agent=agent).execute(data)
    assert data["exception"] is None
