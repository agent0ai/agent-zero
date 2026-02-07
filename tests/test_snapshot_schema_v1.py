import sys
import threading
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.poll import Poll


EXPECTED_SNAPSHOT_KEYS = {
    "deselect_chat",
    "context",
    "contexts",
    "tasks",
    "logs",
    "log_guid",
    "log_version",
    "log_progress",
    "log_progress_active",
    "paused",
    "notifications",
    "notifications_guid",
    "notifications_version",
}


@pytest.mark.asyncio
async def test_poll_snapshot_matches_contract_schema_key_set_null_context():
    app = Flask("poll-snapshot-schema-test")
    app.secret_key = "test-secret"
    lock = threading.RLock()

    poll = Poll(app, lock)
    payload = await poll.process(
        {
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        },
        None,  # Poll.process does not access the flask Request object.
    )

    assert set(payload.keys()) == EXPECTED_SNAPSHOT_KEYS
    assert payload["deselect_chat"] is False
    assert payload["context"] == ""
    assert payload["logs"] == []
    assert payload["log_guid"] == ""
    assert payload["log_version"] == 0
    assert payload["log_progress"] == 0
    assert payload["log_progress_active"] is False
    assert payload["paused"] is False


@pytest.mark.asyncio
async def test_snapshot_builder_produces_contract_schema_key_set_and_defaults():
    from python.helpers import state_snapshot as snapshot

    payload = await snapshot.build_snapshot(
        context=None,
        log_from=0,
        notifications_from=0,
        timezone="UTC",
    )

    snapshot.validate_snapshot_schema_v1(payload)
    assert set(payload.keys()) == EXPECTED_SNAPSHOT_KEYS
    assert payload["deselect_chat"] is False
    assert payload["context"] == ""
    assert payload["logs"] == []
    assert payload["log_guid"] == ""
    assert payload["log_version"] == 0
    assert payload["log_progress"] == 0
    assert payload["log_progress_active"] is False
    assert payload["paused"] is False
    assert isinstance(payload["contexts"], list)
    assert isinstance(payload["tasks"], list)
    assert isinstance(payload["notifications"], list)
    assert isinstance(payload["notifications_guid"], str)
    assert isinstance(payload["notifications_version"], int)
    assert payload["notifications_version"] >= 0


def test_snapshot_schema_rejects_unexpected_top_level_keys():
    from python.helpers import state_snapshot as snapshot

    payload = {
        "deselect_chat": False,
        "context": "",
        "contexts": [],
        "tasks": [],
        "logs": [],
        "log_guid": "",
        "log_version": 0,
        "log_progress": 0,
        "log_progress_active": False,
        "paused": False,
        "notifications": [],
        "notifications_guid": "guid",
        "notifications_version": 0,
        "api_key": "should-not-be-here",
    }

    with pytest.raises(ValueError):
        snapshot.validate_snapshot_schema_v1(payload)
