import asyncio

from plugins._telegram_integration.helpers import draft_stream
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_PROGRESS_LINES,
    CTX_TG_PROGRESS_MESSAGE_ID,
    CTX_TG_REPLY_TO,
    CTX_TG_RESPONSE_MESSAGE_ID,
)


class FakeBot:
    class Bot:
        token = "token"

    bot = Bot()


class FakeContext:
    def __init__(self):
        self.data = {
            CTX_TG_BOT: "main",
            CTX_TG_CHAT_ID: 123,
            CTX_TG_REPLY_TO: 456,
        }

    def get_data(self, key):
        return self.data.get(key)


def test_intermediate_response_sends_separate_non_reply_message(monkeypatch):
    calls = []

    async def fake_send(token, chat_id, text, reply_to_message_id=None, parse_mode="HTML", reply_markup=None):
        calls.append(
            {
                "token": token,
                "chat_id": chat_id,
                "text": text,
                "reply_to_message_id": reply_to_message_id,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )
        return 789

    context = FakeContext()
    monkeypatch.setattr(draft_stream, "_bot_instance", lambda ctx: FakeBot())
    monkeypatch.setattr(draft_stream.tc, "raw_send_text", fake_send)

    sent = asyncio.run(
        draft_stream.send_intermediate_response(
            context,
            "**Working** on the brief.",
            keyboard=[[{"text": "Open", "callback_data": "open"}]],
        )
    )

    assert sent is True
    assert calls == [
        {
            "token": "token",
            "chat_id": 123,
            "text": "<b>Working</b> on the brief.",
            "reply_to_message_id": None,
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [[{"text": "Open", "callback_data": "open"}]]},
        }
    ]
    assert CTX_TG_RESPONSE_MESSAGE_ID not in context.data


def test_intermediate_response_finalizes_active_stream_and_starts_next_tool_group(monkeypatch):
    calls = []
    next_message_id = 100

    async def fake_send(token, chat_id, text, reply_to_message_id=None, parse_mode="HTML", reply_markup=None):
        nonlocal next_message_id
        calls.append(
            {
                "method": "send",
                "text": text,
                "reply_to_message_id": reply_to_message_id,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
                "message_id": next_message_id,
            }
        )
        next_message_id += 1
        return next_message_id - 1

    async def fake_edit(token, chat_id, message_id, text, parse_mode="HTML", reply_markup=None):
        calls.append(
            {
                "method": "edit",
                "message_id": message_id,
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )
        return True

    context = FakeContext()
    monkeypatch.setattr(draft_stream, "_bot_instance", lambda ctx: FakeBot())
    monkeypatch.setattr(draft_stream.tc, "raw_send_text", fake_send)
    monkeypatch.setattr(draft_stream.tc, "raw_edit_text", fake_edit)

    asyncio.run(draft_stream.add_tool_start(context, "search_engine", {"query": "telegram bot api"}))
    asyncio.run(draft_stream.update_response(context, "Found the docs."))
    sent = asyncio.run(draft_stream.send_intermediate_response(context, "Found the docs."))
    asyncio.run(draft_stream.add_tool_start(context, "read_file", {"path": "notes.md"}))

    assert sent is True
    assert calls == [
        {
            "method": "send",
            "text": "🔎 search engine: telegram bot api",
            "reply_to_message_id": None,
            "parse_mode": None,
            "reply_markup": None,
            "message_id": 100,
        },
        {
            "method": "send",
            "text": "Found the docs.",
            "reply_to_message_id": 456,
            "parse_mode": "HTML",
            "reply_markup": None,
            "message_id": 101,
        },
        {
            "method": "edit",
            "message_id": 101,
            "text": "Found the docs.",
            "parse_mode": "HTML",
            "reply_markup": None,
        },
        {
            "method": "send",
            "text": "📖 read file: notes.md",
            "reply_to_message_id": None,
            "parse_mode": None,
            "reply_markup": None,
            "message_id": 102,
        },
    ]
    assert context.data[CTX_TG_PROGRESS_MESSAGE_ID] == 102
    assert context.data[CTX_TG_PROGRESS_LINES] == ["📖 read file: notes.md"]
    assert CTX_TG_RESPONSE_MESSAGE_ID not in context.data
