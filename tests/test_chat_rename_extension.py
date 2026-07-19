from types import SimpleNamespace

import pytest

from extensions.python.monologue_start import _60_rename_chat as rename_chat
from plugins._model_config.helpers import model_config


pytestmark = pytest.mark.asyncio


class _History:
    def output_text(self) -> str:
        return "User: Please help me plan the launch."


class _Agent:
    def __init__(self, *, response: str | None = None, error: Exception | None = None):
        self.context = SimpleNamespace(id="ctx-rename", name="")
        self.history = _History()
        self._response = response
        self._error = error

    def read_prompt(self, name: str, **kwargs) -> str:
        return name

    async def call_utility_model(self, **kwargs) -> str:
        if self._error:
            raise self._error
        return self._response or ""


async def test_rename_failure_sends_utility_model_error_notification(monkeypatch):
    sent: list[dict] = []

    monkeypatch.setattr(model_config, "get_utility_model_config", lambda agent: {"ctx_length": 1000})
    monkeypatch.setattr(rename_chat.NotificationManager, "send_notification", lambda **kwargs: sent.append(kwargs))

    await rename_chat.RenameChat(agent=_Agent(error=RuntimeError("offline"))).change_name()

    assert len(sent) == 1
    assert sent[0]["type"] == rename_chat.NotificationType.ERROR
    assert sent[0]["title"] == "Chat Rename Failed"
    assert "Utility Model was not reachable" in sent[0]["message"]
    assert sent[0]["id"] == "chat_rename_failed_ctx-rename"


async def test_successful_rename_saves_clean_name_and_marks_state_dirty(monkeypatch):
    saved_names: list[str] = []
    dirty_reasons: list[str | None] = []

    monkeypatch.setattr(model_config, "get_utility_model_config", lambda agent: {"ctx_length": 1000})
    monkeypatch.setattr(rename_chat.persist_chat, "save_tmp_chat", lambda context: saved_names.append(context.name))
    monkeypatch.setattr(rename_chat, "mark_dirty_all", lambda *, reason=None: dirty_reasons.append(reason))

    agent = _Agent(response="\n\nLaunch Readiness Notes\n")
    await rename_chat.RenameChat(agent=agent).change_name()

    assert agent.context.name == "Launch Readiness Notes"
    assert saved_names == ["Launch Readiness Notes"]
    assert dirty_reasons == ["monologue_start.RenameChat.change_name"]
