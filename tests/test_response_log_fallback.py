from types import SimpleNamespace

import pytest

from extensions.python.monologue_end._85_ensure_response_log import EnsureResponseLog


class _LoopData:
    def __init__(self, **kwargs):
        self.params_temporary = kwargs.get("params_temporary", {})


class FakeLog:
    def __init__(self):
        self.entries = []

    def log(self, **kwargs):
        self.entries.append(kwargs)
        return SimpleNamespace(id=kwargs.get("id"))


def _agent_with_last_message(content, *, ai=True):
    return _agent_with_messages([SimpleNamespace(ai=ai, content=content)])


def _agent_with_messages(messages):
    log = FakeLog()
    agent = SimpleNamespace(
        agent_name="A0",
        context=SimpleNamespace(log=log),
        history=SimpleNamespace(
            current=SimpleNamespace(messages=messages),
        ),
    )
    return agent, log


@pytest.mark.asyncio
async def test_monologue_end_logs_plain_text_ai_response_from_history():
    agent, log = _agent_with_last_message("Plain text final answer.")
    loop_data = _LoopData(
        params_temporary={
            "log_item_generating": SimpleNamespace(id="stream-log-id"),
        }
    )

    await EnsureResponseLog(agent=agent).execute(loop_data=loop_data)

    assert log.entries == [
        {
            "type": "response",
            "heading": "icon://chat A0: Responding",
            "content": "Plain text final answer.",
            "id": "stream-log-id",
        }
    ]


@pytest.mark.asyncio
async def test_monologue_end_logs_latest_ai_response_when_warning_follows_it():
    agent, log = _agent_with_messages(
        [
            SimpleNamespace(ai=True, content="Plain text final answer."),
            SimpleNamespace(
                ai=False,
                content="You have misformatted your message. Follow system prompt instructions.",
            ),
        ]
    )
    loop_data = _LoopData(
        params_temporary={
            "log_item_generating": SimpleNamespace(id="stream-log-id"),
        }
    )

    await EnsureResponseLog(agent=agent).execute(loop_data=loop_data)

    assert log.entries == [
        {
            "type": "response",
            "heading": "icon://chat A0: Responding",
            "content": "Plain text final answer.",
            "id": "stream-log-id",
        }
    ]


@pytest.mark.asyncio
async def test_monologue_end_skips_when_live_response_already_logged():
    agent, log = _agent_with_last_message("Already logged.")
    loop_data = _LoopData(
        params_temporary={
            "log_item_generating": SimpleNamespace(id="stream-log-id"),
            "log_item_response": SimpleNamespace(id="response-log-id"),
        }
    )

    await EnsureResponseLog(agent=agent).execute(loop_data=loop_data)

    assert log.entries == []


@pytest.mark.asyncio
async def test_monologue_end_does_not_log_non_response_tool_request():
    agent, log = _agent_with_last_message(
        '{"tool_name":"search_engine","tool_args":{"query":"Agent Zero"}}'
    )
    loop_data = _LoopData(
        params_temporary={
            "log_item_generating": SimpleNamespace(id="stream-log-id"),
        }
    )

    await EnsureResponseLog(agent=agent).execute(loop_data=loop_data)

    assert log.entries == []
