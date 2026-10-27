from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from helpers.modules import load_classes_from_file
from helpers.tool import Tool, coerce_bool
from plugins._a0_connector.helpers.event_bridge import log_entry_to_connector_event
from plugins._a0_connector.tools.computer_use_remote import ComputerUseRemote
from plugins._memory.tools.memory import MemoryTool


@pytest.mark.parametrize("value,expected", [(True, True), (False, False), (1, True), (0, False), (" YES ", True), ("false", False), ("null", False), ("maybe", False), ({"enabled": True}, False), ([1], False), (None, False)])
def test_bool_arguments_do_not_authorize_actions_through_truthiness(value, expected):
    assert coerce_bool(value, False) is expected


def test_bool_arguments_preserve_explicit_defaults():
    assert coerce_bool(None, True) is True
    assert coerce_bool("unknown", True) is True
    assert coerce_bool("false", True) is False


@pytest.mark.parametrize("value", ["null", "undefined", "maybe", [True], {"submit": True}])
def test_malformed_submit_does_not_submit_remote_input(value):
    tool = ComputerUseRemote(None, "computer_use_remote", None, {"text": "hello", "submit": value}, "", None)
    assert "submit" not in tool._build_payload(op_id="fixture", context_id="chat", action="type")


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["load", "save", "delete", "forget"])
async def test_legacy_memory_calls_use_new_implementation_and_fixed_action(monkeypatch, action):
    root = Path(__file__).resolve().parents[1]
    cls = load_classes_from_file(str(root / f"plugins/_memory/tools/memory_{action}.py"), Tool)[0]
    assert cls is MemoryTool
    tool = cls(None, f"memory_{action}", None, {}, "", None)
    handlers = {name: AsyncMock(return_value=name) for name in ("load", "save", "delete", "forget")}
    for name, handler in handlers.items():
        monkeypatch.setattr(tool, f"_{name}", handler)
    assert await tool.execute(action="delete", query="saved prompt") == action
    handlers[action].assert_awaited_once_with(query="saved prompt")
    for name, handler in handlers.items():
        if name != action:
            handler.assert_not_awaited()


@pytest.mark.parametrize("log_type", ["a2a_chat", "behavior_adjustment", "computer_use_remote", "document_query", "goal", "memory", "notify_user", "scheduler", "search_engine", "skills_tool", "vision_load", "tool"])
def test_tool_log_types_remain_connector_tool_events(log_type):
    event = log_entry_to_connector_event({"type": log_type, "no": 7, "heading": "Working", "content": "result", "kvps": {"query": "test"}}, "chat")
    assert event["event"] == "tool_start"
    assert event["sequence"] == 8
    assert event["data"] == {"heading": "Working", "text": "result", "meta": {"query": "test"}}


@pytest.mark.parametrize("log_type", ["wait", "progress"])
def test_wait_logs_remain_connector_status_events(log_type):
    assert log_entry_to_connector_event({"type": log_type}, "chat")["event"] == "status"


def test_legacy_behavior_spelling_uses_new_implementation():
    from plugins._behavior_adjustment.tools.behavior_adjustment import UpdateBehavior

    root = Path(__file__).resolve().parents[1]
    classes = load_classes_from_file(
        str(root / "plugins/_behavior_adjustment/tools/behaviour_adjustment.py"), Tool
    )
    assert classes == [UpdateBehavior]
