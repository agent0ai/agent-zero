import asyncio

from plugins._telegram_integration.helpers import heartbeat
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_HEARTBEAT_STOP,
    CTX_TG_HEARTBEAT_TASK,
)


class FakeBot:
    class Bot:
        token = "token"

    bot = Bot()


class FakeLog:
    progress = "icon://search[Search] A0: Searching official docs"


class FakeContext:
    def __init__(self):
        self.data = {
            CTX_TG_BOT: "main",
            CTX_TG_CHAT_ID: 123,
        }
        self.log = FakeLog()


def test_heartbeat_text_omits_iteration_count():
    text = heartbeat.heartbeat_text(180, "waiting for provider response")

    assert text == "Still working... (3 min elapsed - waiting for provider response)"
    assert "iteration" not in text


def test_heartbeat_sends_periodic_status_and_stops(monkeypatch):
    calls = []

    async def fake_send(token, chat_id, text, parse_mode=None, **kwargs):
        calls.append(
            {
                "token": token,
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
        )
        return len(calls)

    context = FakeContext()
    monkeypatch.setattr(heartbeat, "HEARTBEAT_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(heartbeat, "get_bot", lambda name: FakeBot())
    monkeypatch.setattr(heartbeat.tc, "raw_send_text", fake_send)

    async def run():
        await heartbeat.start(context)
        await asyncio.sleep(0.025)
        await heartbeat.stop(context)

    asyncio.run(run())

    assert calls
    assert calls[0]["chat_id"] == 123
    assert calls[0]["parse_mode"] is None
    assert "Still working..." in calls[0]["text"]
    assert "A0: Searching official docs" in calls[0]["text"]
    assert CTX_TG_HEARTBEAT_TASK not in context.data
    assert CTX_TG_HEARTBEAT_STOP not in context.data
