"""Tests for python/helpers/persist_chat.py — serialize/deserialize, get_chat_folder_path, etc."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_deserialize_log_preserves_item_id() -> None:
    from python.helpers.log import Log
    from python.helpers.persist_chat import _deserialize_log, _serialize_log

    log = Log()
    log.log(type="user", heading="User message", content="hello", id="msg-123")
    log.log(type="assistant", heading="Assistant", content="hi")

    serialized = _serialize_log(log)
    restored = _deserialize_log(serialized)

    assert restored.logs[0].type == "user"
    assert restored.logs[0].id == "msg-123"
    assert restored.logs[1].type == "assistant"
    assert restored.logs[1].id is None


def test_get_chat_folder_path() -> None:
    from python.helpers.persist_chat import get_chat_folder_path

    with patch("python.helpers.persist_chat.files") as mf:
        mf.get_abs_path.return_value = "/a0/usr/chats/ctx-1"
        path = get_chat_folder_path("ctx-1")
    mf.get_abs_path.assert_called_once_with("usr/chats", "ctx-1")
    assert path == "/a0/usr/chats/ctx-1"


def test_get_chat_msg_files_folder() -> None:
    from python.helpers.persist_chat import get_chat_msg_files_folder

    with patch("python.helpers.persist_chat.files") as mf:
        mf.get_abs_path.side_effect = lambda *a: "/a0/usr/chats/ctx/messages"
        path = get_chat_msg_files_folder("ctx")
    assert "messages" in str(mf.get_abs_path.call_args)


def test_get_chat_file_path() -> None:
    from python.helpers.persist_chat import _get_chat_file_path

    with patch("python.helpers.persist_chat.files") as mf:
        mf.get_abs_path.return_value = "/a0/usr/chats/ctx/chat.json"
        path = _get_chat_file_path("ctx")
    assert path == "/a0/usr/chats/ctx/chat.json"
    mf.get_abs_path.assert_called_with("usr/chats", "ctx", "chat.json")


def test_load_json_chats() -> None:
    from python.helpers.persist_chat import load_json_chats

    with patch("python.helpers.persist_chat._deserialize_context") as md:
        mock_ctx = MagicMock()
        mock_ctx.id = "new-ctx-1"
        md.return_value = mock_ctx
        jsons = ['{"name": "Chat 1", "type": "user", "id": "old-id"}']
        ctxids = load_json_chats(jsons)
    assert ctxids == ["new-ctx-1"]
    md.assert_called_once()
    call_data = md.call_args[0][0]
    assert "id" not in call_data


def test_remove_chat() -> None:
    from python.helpers.persist_chat import remove_chat

    with patch("python.helpers.persist_chat.files") as mf:
        with patch("python.helpers.persist_chat.get_chat_folder_path", return_value="/chats/ctx"):
            remove_chat("ctx")
    mf.delete_dir.assert_called_once_with("/chats/ctx")


def test_remove_msg_files() -> None:
    from python.helpers.persist_chat import remove_msg_files

    with patch("python.helpers.persist_chat.files") as mf:
        with patch("python.helpers.persist_chat.get_chat_msg_files_folder", return_value="/chats/ctx/messages"):
            remove_msg_files("ctx")
    mf.delete_dir.assert_called_once_with("/chats/ctx/messages")


def test_safe_json_serialize_skips_non_serializable() -> None:
    from python.helpers.persist_chat import _safe_json_serialize

    obj = {"a": 1, "b": object()}
    result = _safe_json_serialize(obj)
    parsed = __import__("json").loads(result)
    assert "a" in parsed
    assert parsed["a"] == 1
