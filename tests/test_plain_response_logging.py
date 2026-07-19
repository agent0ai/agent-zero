from types import SimpleNamespace

from helpers.log import Log
from extensions.python._functions.agent.Agent.hist_add_ai_response.end._10_log_plain_responses import (
    LogPlainResponses,
)


def _agent_with_generating_log():
    log = Log()
    item = log.log(type="agent", heading="A0: Calling LLM...", id="msg-1")
    agent = SimpleNamespace(
        loop_data=SimpleNamespace(params_temporary={"log_item_generating": item})
    )
    return agent, item


def test_responses_plain_text_completion_finishes_generating_log_as_response():
    agent, item = _agent_with_generating_log()
    data = {
        "args": (agent, "Plain final answer."),
        "kwargs": {"id": "msg-1", "llm_result": SimpleNamespace(mode="responses")},
    }

    LogPlainResponses(agent=agent).execute(data=data)

    assert item.type == "response"
    assert item.heading == ""
    assert item.content == "Plain final answer."
    assert item.update_progress == "none"
    assert item.kvps["finished"] is True
    assert agent.loop_data.params_temporary["log_item_response"] is item


def test_responses_tool_json_keeps_generating_log_as_agent_step():
    agent, item = _agent_with_generating_log()
    data = {
        "args": (
            agent,
            '{"tool_name":"search_engine","tool_args":{"query":"today news"}}',
        ),
        "kwargs": {"id": "msg-1", "llm_result": SimpleNamespace(mode="responses")},
    }

    LogPlainResponses(agent=agent).execute(data=data)

    assert item.type == "agent"
    assert item.heading == "A0: Calling LLM..."
    assert item.content == ""
    assert "log_item_response" not in agent.loop_data.params_temporary


def test_responses_plain_text_completion_does_not_replace_live_response_log():
    agent, item = _agent_with_generating_log()
    live_response = Log().log(type="response", content="Already live")
    agent.loop_data.params_temporary["log_item_response"] = live_response
    data = {
        "args": (agent, "Plain final answer."),
        "kwargs": {"id": "msg-1", "llm_result": SimpleNamespace(mode="responses")},
    }

    LogPlainResponses(agent=agent).execute(data=data)

    assert item.type == "agent"
    assert item.content == ""
    assert agent.loop_data.params_temporary["log_item_response"] is live_response
