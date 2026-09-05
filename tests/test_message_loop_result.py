from types import SimpleNamespace

from extensions.python.message_loop_result import _20_empty_response as empty_response
from extensions.python.message_loop_result._20_empty_response import EmptyResponse
from extensions.python.message_loop_result._30_repeat_response import RepeatResponse
from extensions.python._functions.agent.Agent.hist_add_warning.end import (
    _90_stop_unusable_response_loop as response_loop,
)


class FakeAgent:
    def __init__(self, response: str, reasoning: str = "", last_response: str = ""):
        self.loop_data = SimpleNamespace(
            last_response=last_response,
            params_temporary={},
            params_persistent={},
            iteration=0,
        )
        self.logs = []
        self.context = SimpleNamespace(
            log=SimpleNamespace(log=lambda **entry: self.logs.append(entry))
        )
        self.agent_name = "A0"
        self.response = response
        self.reasoning = reasoning
        self.warnings = []
        self.history = []

    def read_prompt(self, name, **kwargs):
        if name == "fw.msg_unusable_response_limit.md":
            return f"stopped at {kwargs['limit']}"
        return {
            "fw.msg_misformat.md": "misformatted",
            "fw.msg_empty_response.md": "empty",
            "fw.msg_repeat.md": "repeat",
            "fw.msg_repeat_response.md": "Repeated response detected. Retrying.",
            "fw.msg_reasoning_only.md": "reasoning only",
            "fw.msg_reasoning_only_response.md": "Reasoning-only response detected. Retrying.",
        }[name]

    def hist_add_ai_response(self, response, **kwargs):
        self.history.append(response)
        return SimpleNamespace(id="assistant")

    def _remember_llm_result_state(self, *args):
        pass

    def hist_add_warning(self, message):
        self.warnings.append(message)
        return SimpleNamespace(id="warning")


def _run(agent):
    result_data = {
        "llm_result": SimpleNamespace(response=agent.response, reasoning=agent.reasoning)
    }
    EmptyResponse(agent).execute(result_data)
    RepeatResponse(agent).execute(result_data)
    return result_data


def test_empty_result_skips_default_processing():
    agent = FakeAgent("")

    assert _run(agent)["skip_default_processing"] is True
    assert agent.history == []
    assert agent.warnings == []
    assert agent.logs == [{"type": "warning", "content": "A0: empty"}]


def test_empty_result_counts_toward_unusable_response_limit(monkeypatch):
    monkeypatch.setattr(
        empty_response,
        "get_settings",
        lambda: {"max_consecutive_unusable_responses": 2},
    )
    agent = FakeAgent("")

    assert _run(agent)["skip_default_processing"] is True

    agent.loop_data.iteration = 1
    try:
        _run(agent)
    except response_loop.HandledException as error:
        assert str(error) == "stopped at 2"
    else:
        raise AssertionError("empty response should stop at the configured limit")

    assert agent.loop_data.params_persistent[response_loop.STATE_KEY]["count"] == 2


def test_later_handlers_skip_a_result_already_handled_by_an_extension():
    response = '{"tool_name":"response"}'
    agent = FakeAgent(response, last_response=response)
    result_data = {
        "llm_result": SimpleNamespace(response=response, reasoning=""),
        "skip_default_processing": True,
    }

    EmptyResponse(agent).execute(result_data)
    RepeatResponse(agent).execute(result_data)

    assert agent.history == []
    assert agent.warnings == []


def test_repeat_skips_default_processing():
    agent = FakeAgent('{"tool_name":"response"}', last_response='{"tool_name":"response"}')

    assert _run(agent)["skip_default_processing"] is True
    assert agent.warnings == ["repeat"]
    assert agent.logs == [
        {
            "type": "warning",
            "content": "A0: Repeated response detected. Retrying.",
            "id": "warning",
        }
    ]


def test_repeat_ignores_reasoning():
    response = '{"tool_name":"response"}'
    agent = FakeAgent(response, reasoning="thinking", last_response=response)

    assert _run(agent)["skip_default_processing"] is True
    assert agent.warnings == ["repeat"]


def test_reasoning_only_retries_with_agent_warning():
    agent = FakeAgent("", reasoning="thinking", last_response="previous")

    result = _run(agent)

    assert result["skip_default_processing"] is True
    assert agent.warnings == ["reasoning only"]
    assert agent.logs == [
        {
            "type": "warning",
            "content": "A0: Reasoning-only response detected. Retrying.",
            "id": "warning",
        }
    ]
