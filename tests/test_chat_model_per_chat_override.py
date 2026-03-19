from __future__ import annotations

import asyncio
import threading
from types import SimpleNamespace

from flask import Flask

from api.chat_model_set import ChatModelSet
from helpers.chat_model_override import get_override, set_override


def _fake_context():
    return SimpleNamespace(
        config=SimpleNamespace(
            chat_model=SimpleNamespace(
                provider="openrouter",
                name="openai/gpt-4o-mini",
                api_base="http://localhost:4000/v1",
                ctx_length=131072,
                vision=True,
                limit_requests=11,
                limit_input=22000,
                limit_output=44000,
                kwargs={"temperature": 0.25, "top_p": 0.9},
            )
        ),
        data={},
    )


def test_set_override_stores_and_removes_data():
    context = SimpleNamespace(data={})

    set_override(context, {"chat_model_name": "custom/model"})
    assert get_override(context) == {"chat_model_name": "custom/model"}

    set_override(context, None)
    assert get_override(context) is None


def test_chat_model_set_normalizes_and_applies_custom_settings(monkeypatch):
    app = Flask(__name__)
    handler = ChatModelSet(app, threading.RLock())
    context = _fake_context()

    monkeypatch.setattr(
        handler,
        "use_context",
        lambda ctxid, create_if_not_exists=False: context,
    )
    monkeypatch.setattr(
        "api.chat_model_set.persist_chat.save_tmp_chat",
        lambda _context: None,
    )
    monkeypatch.setattr(
        "api.chat_model_set.apply_override",
        lambda _context: None,
    )
    monkeypatch.setattr(
        "api.chat_model_set.settings.get_settings",
        lambda: {"chat_model_ctx_history": 0.42},
    )

    result = asyncio.run(
        handler.process(
            {
                "context": "ctx-1",
                "is_custom": True,
                "settings": {
                    "chat_model_provider": "",
                    "chat_model_name": "  custom/provider-model  ",
                    "chat_model_ctx_length": "invalid",
                    "chat_model_ctx_history": "bad",
                    "chat_model_vision": "false",
                    "chat_model_rl_requests": "25",
                    "chat_model_rl_input": None,
                    "chat_model_rl_output": "not-an-int",
                    "chat_model_kwargs": "temperature=0.15\nmax_tokens=2048\n",
                },
            },
            None,
        )
    )

    assert result["ok"] is True
    assert result["is_custom"] is True

    override = context.data["_chat_model_override"]
    assert override["chat_model_provider"] == "openrouter"
    assert override["chat_model_name"] == "custom/provider-model"
    assert override["chat_model_ctx_length"] == 131072
    assert override["chat_model_ctx_history"] == 0.42
    assert override["chat_model_vision"] is False
    assert override["chat_model_rl_requests"] == 25
    assert override["chat_model_rl_input"] == 22000
    assert override["chat_model_rl_output"] == 44000
    assert override["chat_model_kwargs"]["temperature"] == 0.15
    assert override["chat_model_kwargs"]["max_tokens"] == 2048
