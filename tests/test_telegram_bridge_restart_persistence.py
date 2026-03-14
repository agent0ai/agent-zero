"""Regression tests for Telegram chat context persistence across restart."""

from __future__ import annotations

import importlib
import json


def _load_bridge(monkeypatch, tmp_path):
    state_path = tmp_path / "telegram_state.json"
    monkeypatch.setenv("TELEGRAM_STATE_PATH", str(state_path))

    import python.helpers.telegram_bridge as telegram_bridge

    return importlib.reload(telegram_bridge), state_path


def test_chat_context_mapping_survives_module_reload(monkeypatch, tmp_path):
    bridge, _ = _load_bridge(monkeypatch, tmp_path)

    bridge.set_context_for_chat("chat-1", "ctx-abc")
    assert bridge.get_context_for_chat("chat-1") == "ctx-abc"

    # Simulate process restart by reloading the module.
    bridge = importlib.reload(bridge)
    assert bridge.get_context_for_chat("chat-1") == "ctx-abc"


def test_legacy_state_without_last_update_is_compatible(monkeypatch, tmp_path):
    bridge, state_path = _load_bridge(monkeypatch, tmp_path)

    legacy_state = {"chat_contexts": {"chat-legacy": "ctx-legacy"}}
    state_path.write_text(json.dumps(legacy_state), encoding="utf-8")

    bridge = importlib.reload(bridge)
    assert bridge.get_context_for_chat("chat-legacy") == "ctx-legacy"

    assert bridge.should_ignore_update("chat-legacy", 100) is False
    bridge = importlib.reload(bridge)
    assert bridge.should_ignore_update("chat-legacy", 100) is True
