import sys
import threading
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentContext
from initialize import initialize_agent
from api.poll import Poll


@pytest.mark.asyncio
async def test_snapshot_builder_matches_poll_output_for_null_context():
    app = Flask("snapshot-parity-test")
    app.secret_key = "test-secret"
    lock = threading.RLock()

    poll = Poll(app, lock)
    poll_payload = await poll.process(
        {
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        },
        None,  # Poll.process does not access the flask Request object.
    )

    from helpers import state_snapshot as snapshot

    builder_payload = await snapshot.build_snapshot(
        context=None,
        log_from=0,
        notifications_from=0,
        timezone="UTC",
    )

    assert builder_payload == poll_payload


@pytest.mark.asyncio
async def test_snapshot_builder_active_context_includes_incremental_logs():
    ctxid = "ctx-snapshot-parity"
    ctx = AgentContext(config=initialize_agent(), id=ctxid, set_current=False)
    try:
        ctx.log.log(type="user", heading="hi", content="hello")
        first = await Poll(Flask("parity-active"), threading.RLock()).process(
            {
                "context": ctxid,
                "log_from": 0,
                "notifications_from": 0,
                "timezone": "UTC",
            },
            None,
        )
        assert first["context"] == ctxid
        assert first["logs"]
        assert first["log_version"] == len(ctx.log.updates)

        from helpers import state_snapshot as snapshot

        second = await snapshot.build_snapshot(
            context=ctxid,
            log_from=first["log_version"],
            notifications_from=0,
            timezone="UTC",
        )
        assert second["context"] == ctxid
        assert second["logs"] == []
        assert second["log_version"] == first["log_version"]
    finally:
        AgentContext.remove(ctxid)


@pytest.mark.asyncio
async def test_snapshot_prunes_saved_context_missing_from_chat_files(monkeypatch):
    from helpers import persist_chat
    from helpers import state_snapshot as snapshot

    missing_id = "ctx-saved-missing-chat-file"
    unsaved_id = "ctx-unsaved-chat-file"
    missing = AgentContext(config=initialize_agent(), id=missing_id, set_current=False)
    unsaved = AgentContext(config=initialize_agent(), id=unsaved_id, set_current=False)
    persist_chat.mark_chat_saved(missing)
    monkeypatch.setattr(persist_chat, "saved_chat_ids", lambda: set())

    try:
        payload = await snapshot.build_snapshot(
            context=missing_id,
            log_from=0,
            notifications_from=0,
            timezone="UTC",
        )

        context_ids = {ctx["id"] for ctx in payload["contexts"]}
        assert payload["deselect_chat"] is True
        assert payload["context"] == ""
        assert missing_id not in context_ids
        assert unsaved_id in context_ids
        assert AgentContext.get(missing_id) is None
    finally:
        AgentContext.remove(missing_id)
        AgentContext.remove(unsaved_id)
