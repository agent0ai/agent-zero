import asyncio

from plugins._telegram_integration.extensions.python._functions.agent.Agent.handle_exception.end import (
    _85_telegram_error,
)
from plugins._telegram_integration.helpers import error_ui
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_ERROR_SENT,
    CTX_TG_REPLY_TO,
    CTX_TG_TYPING_STOP,
)


class FakeContext:
    def __init__(self):
        self.data = {
            CTX_TG_BOT: "main",
            CTX_TG_REPLY_TO: 456,
        }


class FakeAgent:
    number = 0

    def __init__(self):
        self.context = FakeContext()


def test_friendly_error_message_for_missing_api_key():
    message = error_ui.friendly_error_message(
        RuntimeError("OPENAI_API_KEY is missing or invalid")
    )

    assert "provider setup issue" in message
    assert "API key" in message
    assert "OPENAI_API_KEY is missing or invalid" in message


def test_friendly_error_message_for_rate_limit():
    message = error_ui.friendly_error_message(
        RuntimeError("Rate limit exceeded: too many requests")
    )

    assert "rate limited" in message
    assert "too many requests" in message


def test_telegram_exception_hook_sends_once_and_cleans_stream_state(monkeypatch):
    sends = []
    cleared = []
    typing_stopped = []

    async def fake_send(context, text, attachments=None, keyboard=None):
        sends.append(
            {
                "text": text,
                "reply_to": context.data.get(CTX_TG_REPLY_TO),
                "attachments": attachments,
                "keyboard": keyboard,
            }
        )
        return None

    def fake_clear(context):
        cleared.append(True)

    class FakeStop:
        def set(self):
            typing_stopped.append(True)

    agent = FakeAgent()
    agent.context.data[CTX_TG_TYPING_STOP] = FakeStop()

    monkeypatch.setattr(
        "plugins._telegram_integration.helpers.handler.send_telegram_reply",
        fake_send,
    )
    monkeypatch.setattr(
        "plugins._telegram_integration.helpers.draft_stream.clear",
        fake_clear,
    )

    extension = _85_telegram_error.TelegramFriendlyError(agent=agent)
    data = {"exception": RuntimeError("provider returned 503 service unavailable")}

    asyncio.run(extension.execute(data=data))
    asyncio.run(extension.execute(data=data))

    assert len(sends) == 1
    assert "could not complete the model request" in sends[0]["text"]
    assert sends[0]["reply_to"] == 456
    assert cleared == [True]
    assert typing_stopped == [True]
    assert agent.context.data[CTX_TG_ERROR_SENT] is True
    assert CTX_TG_REPLY_TO not in agent.context.data
