from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from agent import AgentContext
from helpers import persist_chat
from initialize import initialize_agent


def _make_context(ctxid: str) -> AgentContext:
    return AgentContext(config=initialize_agent(), id=ctxid, set_current=False)


def _add_log_items(ctx: AgentContext, count: int, start: int = 0) -> list[str]:
    ids = []
    for i in range(start, start + count):
        ctx.log.log(
            type="info",
            heading=f"item {i}",
            content=f"content {i}",
            kvps={"seq": i},
            id=f"msg-{i:05d}",
        )
        ids.append(f"msg-{i:05d}")
    return ids


def _baseline_item_count(ctx: AgentContext) -> int:
    """Context construction logs exactly one greeting item (agent_init hook);
    production restore skips it because the loaded log is non-empty."""
    baseline = len(ctx.log.logs)
    assert baseline == 1, f"expected exactly the greeting item, found {baseline}"
    return baseline


@pytest.fixture
def chats_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(persist_chat, "CHATS_FOLDER", str(tmp_path))
    return tmp_path


def test_save_writes_untrimmed_jsonl(chats_folder):
    """The measured loss: legacy chat.json kept only the last LOG_SIZE=1000 log
    items on disk. The JSONL format must persist every item."""
    ctx = _make_context("ctx-jsonl-untrimmed")
    baseline = _baseline_item_count(ctx)
    _add_log_items(ctx, 1500)
    try:
        persist_chat.save_tmp_chat(ctx)

        jsonl = chats_folder / "ctx-jsonl-untrimmed" / "chat.jsonl"
        assert jsonl.exists(), "chat.jsonl was not written"
        lines = [line for line in jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert lines, "chat.jsonl is empty"
        docs = [json.loads(line) for line in lines]
        assert docs[0]["t"] == "meta"
        log_docs = [d for d in docs if d.get("t") == "log"]
        expected = baseline + 1500
        assert len(log_docs) == expected, (
            f"expected all {expected} items (greeting + 1500), found {len(log_docs)}"
        )
        assert log_docs[-1500]["id"] == "msg-00000"
        assert log_docs[-1]["id"] == "msg-01499"
    finally:
        AgentContext.remove("ctx-jsonl-untrimmed")


def test_load_round_trips_every_item_and_id(chats_folder):
    ctxid = "ctx-jsonl-roundtrip"
    ctx = _make_context(ctxid)
    baseline = _baseline_item_count(ctx)
    _add_log_items(ctx, 1200)
    try:
        persist_chat.save_tmp_chat(ctx)
        AgentContext.remove(ctxid)
        assert AgentContext.get(ctxid) is None

        ctxids = persist_chat.load_tmp_chats()
        assert ctxid in ctxids
        restored = AgentContext.get(ctxid)
        assert restored is not None
        assert len(restored.log.logs) == baseline + 1200
        assert [item.id for item in restored.log.logs][-1200:] == [
            f"msg-{i:05d}" for i in range(1200)
        ]
        assert (restored.log.logs[-1200].kvps or {}).get("seq") == 0
        assert (restored.log.logs[-1].kvps or {}).get("seq") == 1199
    finally:
        AgentContext.remove(ctxid)


def test_legacy_chat_json_migrates_to_jsonl(chats_folder):
    ctxid = "ctx-legacy-migrate"
    ctx = _make_context(ctxid)
    baseline = _baseline_item_count(ctx)
    _add_log_items(ctx, 5)
    try:
        legacy_payload = json.loads(persist_chat.export_json_chat(ctx))
        legacy_path = chats_folder / ctxid / "chat.json"
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(json.dumps(legacy_payload, ensure_ascii=False), encoding="utf-8")
        AgentContext.remove(ctxid)

        ctxids = persist_chat.load_tmp_chats()
        assert ctxid in ctxids

        jsonl = chats_folder / ctxid / "chat.jsonl"
        assert jsonl.exists(), "migration did not write chat.jsonl"
        assert not legacy_path.exists(), "legacy chat.json was not renamed away"
        assert (chats_folder / ctxid / "chat.json.legacy").exists(), "legacy backup missing"

        restored = AgentContext.get(ctxid)
        assert restored is not None
        assert [item.id for item in restored.log.logs][-5:] == [f"msg-{i:05d}" for i in range(5)]
    finally:
        AgentContext.remove(ctxid)


def test_migrated_jsonl_wins_over_stale_legacy(chats_folder):
    """After migration both files exist; a reload must use chat.jsonl and must
    not re-migrate (which would resurrect stale legacy bytes)."""
    ctxid = "ctx-double-file"
    ctx = _make_context(ctxid)
    baseline = _baseline_item_count(ctx)
    _add_log_items(ctx, 3)
    try:
        persist_chat.save_tmp_chat(ctx)  # writes chat.jsonl
        legacy_path = chats_folder / ctxid / "chat.json"
        legacy_path.write_text(json.dumps({"id": ctxid, "bogus": True}), encoding="utf-8")
        AgentContext.remove(ctxid)

        persist_chat.load_tmp_chats()
        restored = AgentContext.get(ctxid)
        assert restored is not None
        assert len(restored.log.logs) == baseline + 3, "loader used the stale legacy file"
    finally:
        AgentContext.remove(ctxid)


def test_chat_file_exists_and_saved_ids_cover_both_formats(chats_folder):
    assert persist_chat.chat_file_exists("ctx-nothing") is False

    legacy_dir = chats_folder / "ctx-legacy-only"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "chat.json").write_text("{}", encoding="utf-8")

    jsonl_dir = chats_folder / "ctx-jsonl-only"
    jsonl_dir.mkdir(parents=True)
    (jsonl_dir / "chat.jsonl").write_text('{"t": "meta"}\n', encoding="utf-8")

    assert persist_chat.chat_file_exists("ctx-legacy-only") is True
    assert persist_chat.chat_file_exists("ctx-jsonl-only") is True
    assert {"ctx-legacy-only", "ctx-jsonl-only"} <= persist_chat.saved_chat_ids()


def test_malformed_lines_are_skipped_not_fatal(chats_folder):
    """Atomic writes prevent torn lines, but a corrupted line must cost its own
    item, never the whole chat."""
    ctxid = "ctx-corrupt-line"
    ctx = _make_context(ctxid)
    baseline = _baseline_item_count(ctx)
    _add_log_items(ctx, 4)
    try:
        persist_chat.save_tmp_chat(ctx)
        AgentContext.remove(ctxid)

        jsonl = chats_folder / ctxid / "chat.jsonl"
        lines = jsonl.read_text(encoding="utf-8").splitlines()
        lines.insert(2, "{not json")
        jsonl.write_text("\n".join(lines) + "\n", encoding="utf-8")

        ctxids = persist_chat.load_tmp_chats()
        assert ctxid in ctxids
        restored = AgentContext.get(ctxid)
        assert restored is not None
        assert len(restored.log.logs) == baseline + 4  # one invalid line costs only its own item
    finally:
        AgentContext.remove(ctxid)
