from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from flask import Flask, request


REQUIRED_FIELDS = {
    "timestamp",
    "agent_role",
    "user_action",
    "sources",
    "output_hash",
    "file_paths_touched",
}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _assert_required_fields(entry: dict) -> None:
    missing = REQUIRED_FIELDS - set(entry.keys())
    assert not missing, f"missing required fields: {sorted(missing)}"
    assert isinstance(entry["sources"], list)
    assert isinstance(entry["file_paths_touched"], list)
    assert isinstance(entry["timestamp"], str) and entry["timestamp"]
    assert isinstance(entry["agent_role"], str) and entry["agent_role"]
    assert isinstance(entry["user_action"], str) and entry["user_action"]
    assert isinstance(entry["output_hash"], str) and entry["output_hash"].startswith("sha256:")


def test_message_async_intake_writes_audit_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("A0_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    from python.api.message import Message
    from python.api.message_async import MessageAsync

    async def _fake_process(self, input: dict, request):  # noqa: ANN001
        return {"ok": True}

    monkeypatch.setattr(Message, "process", _fake_process)

    app = Flask("test_message_async_audit")
    handler = MessageAsync(app, threading.RLock())

    with app.test_request_context(
        "/message_async",
        method="POST",
        json={"text": "hello", "context": "ctx-1", "message_id": "m-1"},
    ):
        result = asyncio.run(handler.process({}, request))
        assert result == {"ok": True}

    entries = _read_jsonl(tmp_path / "audit.jsonl")
    assert len(entries) == 1
    _assert_required_fields(entries[0])
    assert entries[0]["user_action"] == "api:/message_async:intake"


def test_search_tool_after_execution_writes_audit_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("A0_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    from python.helpers.tool import Response, Tool

    class _DummyLog:
        def update(self, **kwargs):  # noqa: ANN003
            return None

    class _DummyAgent:
        agent_name = "Agent 0"

        def hist_add_tool_result(self, *args, **kwargs):  # noqa: ANN002,ANN003
            return None

    class _DummyTool(Tool):
        async def execute(self, **kwargs):  # noqa: ANN003
            raise AssertionError("not used in this test")

    tool = _DummyTool(
        agent=_DummyAgent(),
        name="search_engine",
        method=None,
        args={"query": "test"},
        message="",
        loop_data=None,
    )
    tool.log = _DummyLog()

    asyncio.run(tool.after_execution(Response(message="Sources: https://example.com", break_loop=False)))

    entries = _read_jsonl(tmp_path / "audit.jsonl")
    assert len(entries) == 1
    _assert_required_fields(entries[0])
    assert entries[0]["user_action"] == "tool:search_engine"
    assert "https://example.com" in entries[0]["sources"]


def test_ingest_cli_writes_audit_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("A0_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    from legalflow.ingest_public_corpus import main

    fixtures_dir = Path("tests/fixtures/legalflow_public_corpus").resolve()
    out_dir = tmp_path / "public_corpus_out"

    rc = main(
        [
            "--dry-run",
            "--limit",
            "1",
            "--fixtures-dir",
            str(fixtures_dir),
            "--output-dir",
            str(out_dir),
            "--json",
        ]
    )
    assert rc in (0, 2)

    entries = _read_jsonl(tmp_path / "audit.jsonl")
    assert len(entries) == 1
    _assert_required_fields(entries[0])
    assert entries[0]["user_action"] == "cli:legalflow.ingest_public_corpus"


def test_chat_export_writes_audit_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("A0_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    from python.api.chat_export import ExportChat
    from python.helpers import persist_chat

    monkeypatch.setattr(persist_chat, "export_json_chat", lambda context: '{"url":"https://example.com"}')
    monkeypatch.setattr(ExportChat, "use_context", lambda self, ctxid, create_if_not_exists=True: type("Ctx", (), {"id": ctxid})())

    app = Flask("test_chat_export_audit")
    handler = ExportChat(app, threading.RLock())

    with app.test_request_context("/chat_export", method="POST", json={"ctxid": "ctx-99"}):
        result = asyncio.run(handler.process({"ctxid": "ctx-99"}, request))
        assert result["ctxid"] == "ctx-99"

    entries = _read_jsonl(tmp_path / "audit.jsonl")
    assert len(entries) == 1
    _assert_required_fields(entries[0])
    assert entries[0]["user_action"] == "api:/chat_export"
    assert "https://example.com" in entries[0]["sources"]
    assert "usr/chats/ctx-99/chat.json" in entries[0]["file_paths_touched"]


def test_gatekeeper_draft_and_review_write_audit_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("A0_AUDIT_LOG_PATH", str(tmp_path / "audit.jsonl"))

    from agent import LoopData
    from python.helpers.tool import Response
    from python.tools.call_subordinate import Delegation
    from agents.gatekeeper.extensions.message_loop_start._10_legalflow_gatekeeper_router import (
        LegalFlowGatekeeperRouter,
    )

    async def _fake_execute(self, **kwargs):  # noqa: ANN001,ANN003
        return Response(message="ok", break_loop=False)

    monkeypatch.setattr(Delegation, "execute", _fake_execute)

    class _DummyAgent:
        agent_name = "gatekeeper"

        def __init__(self) -> None:
            self._data: dict = {}

        def get_data(self, key: str):  # noqa: ANN001
            return self._data.get(key)

        def set_data(self, key: str, value):  # noqa: ANN001,ANN002
            self._data[key] = value

    class _Msg:
        ai = False
        content = {"user_message": ""}

    router = LegalFlowGatekeeperRouter(agent=_DummyAgent())

    msg = _Msg()
    msg.content = {
        "user_message": "intent: draft\njurisdiction: CA, USA\ndocument_type: demand letter\nfacts: test\n"
    }
    asyncio.run(router.execute(loop_data=LoopData(user_message=msg)))

    msg2 = _Msg()
    msg2.content = {
        "user_message": "intent: review\njurisdiction: CA, USA\nreview_focus: risks\ndocument_text: ```\nThis is a contract.\n```\n"
    }
    asyncio.run(router.execute(loop_data=LoopData(user_message=msg2)))

    entries = _read_jsonl(tmp_path / "audit.jsonl")
    assert len(entries) == 2
    for entry in entries:
        _assert_required_fields(entry)
    assert entries[0]["user_action"] == "intent:draft"
    assert entries[1]["user_action"] == "intent:review"
