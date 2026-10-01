import sys
import threading
from pathlib import Path

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.poll import Poll


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
    from helpers import state_snapshot as snapshot

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


@pytest.mark.asyncio
async def test_negotiated_incremental_snapshot_uses_null_collection_sentinel():
    from helpers import state_snapshot as snapshot

    request = snapshot.StateRequestV1(
        context=None,
        log_from=0,
        notifications_from=0,
        timezone="UTC",
        collections_delta=True,
    )
    payload = await snapshot.build_snapshot_from_request(
        request=request,
        include_collections=False,
    )

    snapshot.validate_snapshot_schema_v1(payload)
    assert set(payload) == EXPECTED_SNAPSHOT_KEYS
    assert payload["contexts"] is None
    assert payload["tasks"] is None


def test_state_request_collection_delta_is_optional_and_type_checked():
    from helpers import state_snapshot as snapshot

    base = {
        "context": None,
        "log_from": 0,
        "notifications_from": 0,
        "timezone": "UTC",
    }

    assert snapshot.parse_state_request_payload(base).collections_delta is False
    assert (
        snapshot.parse_state_request_payload(
            {**base, "collections_delta": True}
        ).collections_delta
        is True
    )
    with pytest.raises(snapshot.StateRequestValidationError) as error:
        snapshot.parse_state_request_payload(
            {**base, "collections_delta": "yes"}
        )
    assert error.value.reason == "collections_delta_type"


def test_snapshot_schema_rejects_unexpected_top_level_keys():
    from helpers import state_snapshot as snapshot

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


def test_notification_payload_and_cursor_are_captured_together():
    from helpers.notification import NotificationManager, NotificationPriority, NotificationType

    manager = NotificationManager()
    manager.add_notification(NotificationType.INFO, NotificationPriority.HIGH, "first")

    notifications, _, version = manager.output_with_state()
    manager.add_notification(NotificationType.INFO, NotificationPriority.HIGH, "second")

    assert [item["message"] for item in notifications] == ["first"]
    assert version == 1
    assert [item["message"] for item in manager.output(start=version)] == ["second"]
