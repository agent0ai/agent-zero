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
from python.api.poll import Poll


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

    from python.helpers import snapshot

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

        from python.helpers import snapshot

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
