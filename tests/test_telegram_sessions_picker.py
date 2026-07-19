import asyncio
from types import SimpleNamespace

from plugins._telegram_integration.helpers import command_ui
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_CHAT_ID,
    CTX_TG_USER_ID,
    CTX_TG_USERNAME,
)


class FakeContext:
    def __init__(self, id, name, last_message, *, running=False):
        self.id = id
        self.name = name
        self.data = {}
        self._last_message = last_message
        self._running = running

    def output(self):
        return {"last_message": self._last_message}

    def is_running(self):
        return self._running


def test_session_picker_shows_four_recent_sessions(monkeypatch):
    contexts = [
        FakeContext("ctx-1", "One", "2026-05-01T10:00:00"),
        FakeContext("ctx-2", "Two", "2026-05-02T10:00:00"),
        FakeContext("ctx-3", "Three", "2026-05-03T10:00:00"),
        FakeContext("ctx-4", "Four", "2026-05-04T10:00:00"),
        FakeContext("ctx-5", "Five", "2026-05-05T10:00:00"),
    ]
    current = contexts[4]
    monkeypatch.setattr(command_ui, "AgentContext", SimpleNamespace(all=lambda: contexts))

    text, markup = command_ui._session_view(current, 0)

    assert "Current session: <b>Five</b>" in text
    assert "Showing 1-4 of 5." in text
    rows = markup["inline_keyboard"]
    assert [row[0]["text"] for row in rows[:4]] == ["• Five", "Four", "Three", "Two"]
    assert rows[-1] == [{"text": "Next", "callback_data": "tg:session:page:1"}]


def test_select_session_remaps_telegram_chat(monkeypatch):
    current = FakeContext("ctx-current", "Current", "2026-05-03T10:00:00")
    target = FakeContext("ctx-target", "Target", "2026-05-04T10:00:00")
    current.data.update(
        {
            CTX_TG_BOT: "main",
            CTX_TG_CHAT_ID: 123,
            CTX_TG_USER_ID: 456,
            CTX_TG_USERNAME: "anmol",
        }
    )
    saved = []
    dirty = []
    state_out = {}

    monkeypatch.setattr(command_ui, "AgentContext", SimpleNamespace(all=lambda: [current, target]))
    monkeypatch.setattr(command_ui, "save_tmp_chat", lambda context: saved.append(context.id))
    monkeypatch.setattr(command_ui, "mark_dirty_for_context", lambda context_id, *, reason=None: dirty.append((context_id, reason)))
    monkeypatch.setattr(command_ui, "_load_telegram_state", lambda: {"chats": {}})
    monkeypatch.setattr(command_ui, "_save_telegram_state", lambda state: state_out.update(state))

    selected = asyncio.run(command_ui._select_session(current, 0))

    assert selected is target
    assert target.data[CTX_TG_BOT] == "main"
    assert target.data[CTX_TG_CHAT_ID] == 123
    assert target.data[CTX_TG_USER_ID] == 456
    assert target.data[CTX_TG_USERNAME] == "anmol"
    assert state_out["chats"]["main:456:123"] == "ctx-target"
    assert saved == ["ctx-target"]
    assert ("ctx-target", "telegram.session_select") in dirty
