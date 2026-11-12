from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from plugins._a0_connector.helpers import browser_bridge_legacy_quarantine as quarantine
from plugins._a0_connector.helpers.browser_bridge_legacy_retirement import LegacyRetirementDenied


def result():
    return {"tool_name": "chrome_bridge", "tool_result": "Captured", "browser_session_id": "old-session", "command_id": "old-command", "command_status": "completed", "image_data_url": "data:image/png;base64,private", "image_width": 800}


def document():
    message = {"_cls": "Message", "ai": False, "content": result(), "metadata": {"user_attachment": "keep"}}
    user = {"_cls": "Message", "ai": False, "content": {"image_data_url": "user-owned-image", "text": "chrome_bridge"}}
    tree = {"_cls": "History", "bulks": [{"_cls": "Bulk", "records": [{"_cls": "Topic", "messages": [message]}]}], "topics": [], "current": {"_cls": "Topic", "messages": [user]}}
    return {"id": "chat-owned", "data": {"source": "chrome_extension", "chrome_browser_session_id": "old-session", "chrome_extension_capabilities": {"read": True}, "user_data": "keep"}, "agents": [{"history": json.dumps(tree)}], "attachments": ["user-owned-image"]}


def test_exact_serialized_slots_are_recoverable_and_idempotent():
    doc, retained = document(), []
    assert quarantine.quarantine_document(doc, store=retained.append) == {"context_keys": 3, "screenshots": 1}
    assert doc["data"] == {"user_data": "keep"}
    tree = json.loads(doc["agents"][0]["history"])
    message = tree["bulks"][0]["records"][0]["messages"][0]
    assert "image_data_url" not in message["content"]
    assert message["content"]["image_width"] == 800
    assert message["metadata"] == {"user_attachment": "keep"}
    assert tree["current"]["messages"][0]["content"]["image_data_url"] == "user-owned-image"
    assert doc["attachments"] == ["user-owned-image"]
    recovery = json.loads(retained[0])
    assert len(recovery["entries"]) == 4
    assert "data:image/png;base64,private" in retained[0].decode()
    assert "user-owned-image" not in retained[0].decode()
    unchanged = copy.deepcopy(doc)
    assert quarantine.quarantine_document(doc, store=retained.append) == {"context_keys": 0, "screenshots": 0}
    assert doc == unchanged and len(retained) == 1


def test_foreign_context_keys_and_non_tool_images_are_preserved():
    doc = document()
    doc["data"]["source"] = "other-client"
    tree = json.loads(doc["agents"][0]["history"])
    tree["bulks"][0]["records"][0]["messages"][0]["ai"] = True
    doc["agents"][0]["history"] = json.dumps(tree)
    original = copy.deepcopy(doc)
    assert quarantine.quarantine_document(doc, store=lambda raw: pytest.fail("no owned data")) == {"context_keys": 0, "screenshots": 0}
    assert doc == original


def test_backup_failure_never_removes_original_data():
    doc = document()
    original = copy.deepcopy(doc)
    def fail(_raw):
        raise LegacyRetirementDenied("storage_write_failed")
    with pytest.raises(LegacyRetirementDenied):
        quarantine.quarantine_document(doc, store=fail)
    assert doc == original


def test_private_backup_is_exact_private_and_refuses_symlinks(tmp_path):
    (tmp_path / "usr").mkdir()
    raw = b'{"synthetic":"recover-me"}'
    quarantine.retain_private(raw, root=tmp_path)
    folder = tmp_path / "usr/browser_bridge_legacy_quarantine"
    blob = folder / (hashlib.sha256(raw).hexdigest() + ".json")
    assert blob.read_bytes() == raw
    assert blob.stat().st_mode & 0o777 == 0o600
    assert folder.stat().st_mode & 0o777 == 0o700
    quarantine.retain_private(raw, root=tmp_path)
    assert len(list(folder.iterdir())) == 1
    other = tmp_path / "other"
    other.mkdir()
    (other / "usr").symlink_to(tmp_path / "usr", target_is_directory=True)
    with pytest.raises(LegacyRetirementDenied):
        quarantine.retain_private(raw, root=other)
    assert blob.read_bytes() == raw


def live_context():
    from helpers.history import History, Message
    from helpers.log import Log
    agent = SimpleNamespace(data={}, config=SimpleNamespace(profile=""), number=0)
    agent.history = History(agent)
    agent.history.current.messages = [Message(False, result(), tokens=10), Message(False, {"image_data_url": "user-owned-image"}, tokens=10)]
    return SimpleNamespace(id="synthetic", data={"source": "chrome_extension", "chrome_browser_session_id": "old"}, agent0=agent, config=agent.config,
        output_data={}, name="Synthetic", created_at=None, last_message=None, type=SimpleNamespace(value="user"), streaming_agent=None, log=Log())


def test_real_persistence_save_hook_quarantines_live_history(monkeypatch):
    from helpers import persist_chat, extension
    path = Path(__file__).parents[1] / "plugins/_a0_connector/extensions/python/_functions/helpers/persist_chat/_serialize_context/start/_05_legacy_quarantine.py"
    spec = importlib.util.spec_from_file_location("quarantine_fixture_hook", path)
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    retained = []
    monkeypatch.setattr(hook, "enabled", lambda: True)
    monkeypatch.setattr(quarantine, "retain_private", retained.append)
    monkeypatch.setattr(extension, "_get_extension_classes", lambda point, **kwargs: [hook.QuarantineLegacyContext] if point == "_functions/helpers/persist_chat/_serialize_context/start" else [])
    context = live_context()
    serialized = persist_chat._serialize_context(context)
    assert context.data == {} and serialized["data"] == {}
    assert "image_data_url" not in context.agent0.history.current.messages[0].content
    assert context.agent0.history.current.messages[0].tokens == 0
    assert "private" not in serialized["agents"][0]["history"]
    assert "user-owned-image" in serialized["agents"][0]["history"]
    assert len(retained) == 1


def test_sweep_is_bounded_and_has_no_dormant_file_authority(monkeypatch):
    from agent import AgentContext
    from helpers import persist_chat
    contexts = [SimpleNamespace(id=f"context-{i:02}") for i in range(25)]
    saved = []
    monkeypatch.setattr(quarantine, "enabled", lambda: True)
    monkeypatch.setattr(AgentContext, "all", lambda: contexts)
    monkeypatch.setattr(quarantine, "quarantine_context", lambda context: {"context_keys": 1, "screenshots": 0})
    monkeypatch.setattr(persist_chat, "save_tmp_chat", lambda context: saved.append(context.id))
    first = quarantine.sweep_loaded()
    assert first["processed"] == 20 and first["next_offset"] == 20
    second = quarantine.sweep_loaded(first["next_offset"])
    assert second["processed"] == 5 and second["next_offset"] is None
    assert len(saved) == len(set(saved)) == 25
    assert first["activation_ready"] is False
    assert first["dormant_chats"] == "quarantined_on_next_load"


def test_exact_compressed_result_summary_is_quarantined_without_prose_rewriting():
    doc = document()
    tree = json.loads(doc["agents"][0]["history"])
    message = tree["bulks"][0]["records"][0]["messages"][0]
    message["summary"] = json.dumps(result())
    doc["agents"][0]["history"] = json.dumps(tree)
    assert quarantine.quarantine_document(doc, store=lambda raw: None)["screenshots"] == 2
    tree = json.loads(doc["agents"][0]["history"])
    message = tree["bulks"][0]["records"][0]["messages"][0]
    assert "image_data_url" not in json.loads(message["summary"])
    assert message["content"]["tool_result"] == "Captured"


def test_duplicate_live_slot_is_rejected_before_backup_or_partial_removal():
    context = live_context()
    message = context.agent0.history.current.messages[0]
    context.agent0.history.current.messages.append(message)
    original = copy.deepcopy(context.data)
    retained = []
    with pytest.raises(LegacyRetirementDenied, match="legacy_quarantine_ambiguous"):
        quarantine.quarantine_context(context, store=retained.append)
    assert retained == [] and context.data == original
    assert message.content["image_data_url"] == "data:image/png;base64,private"
