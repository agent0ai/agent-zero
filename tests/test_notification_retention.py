"""Notification delta cursors must survive bounded-history eviction."""

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)


@pytest.fixture(autouse=True)
def isolated_notifications(monkeypatch):
    clock = SimpleNamespace(
        now=lambda: datetime(2026, 10, 31, 9, tzinfo=UTC),
        serialize_datetime=lambda value: value.isoformat(),
    )
    monkeypatch.setattr("helpers.notification.Localization.get", lambda: clock)
    monkeypatch.setattr(
        "helpers.state_monitor_integration.mark_dirty_all", lambda **kwargs: None
    )


def add(manager, message, **kwargs):
    return manager.add_notification(
        NotificationType.INFO, NotificationPriority.HIGH, message, **kwargs
    )


@pytest.mark.parametrize("limit", [1, 3, 100])
def test_each_new_notification_is_delivered_after_retention_limit(limit):
    manager = NotificationManager(max_notifications=limit)
    cursor = 0
    guid = manager.guid
    for number in range(limit + 5):
        item = add(manager, str(number))
        payload, current_guid, version = manager.output_with_state(start=cursor)
        assert [value["id"] for value in payload] == [item.id]
        assert version == cursor + 1
        assert current_guid == guid
        cursor = version
        assert manager.output(start=cursor) == []
        assert len(manager.notifications) <= limit
        assert len(manager.updates) <= limit


def test_updates_and_read_changes_keep_their_cursors_after_eviction():
    manager = NotificationManager(max_notifications=2)
    old = add(manager, "Old")
    retained = add(manager, "Retained", id="retained")
    add(manager, "Old changed", id=old.id)
    _, guid, cursor = manager.output_with_state()
    newest = add(manager, "Newest")
    payload, current_guid, version = manager.output_with_state(start=cursor)
    assert [value["id"] for value in payload] == [newest.id]
    assert current_guid == guid
    assert version == cursor + 1

    for change in (
        lambda: add(manager, "Retained changed", id=retained.id),
        lambda: manager.mark_read_by_ids([retained.id]),
        lambda: manager.update_item(newest.no, title="Updated title"),
        manager.mark_all_read,
    ):
        cursor = version
        change()
        payload, _, version = manager.output_with_state(start=cursor)
        assert payload
        assert version > cursor
        assert all(value["id"] != old.id for value in payload)
    assert all(item.read for item in manager.notifications)


def test_lagging_cursor_and_end_select_original_update_positions():
    manager = NotificationManager(max_notifications=2)
    old = add(manager, "Old")
    retained = add(manager, "Retained")
    add(manager, "Old changed", id=old.id)
    newest = add(manager, "Newest")
    # Version 2 belonged to the now-evicted item; compacting must not move
    # version 3 into its position or shift the retained item's version 1.
    assert [item["id"] for item in manager.output(start=1, end=2)] == [retained.id]
    assert manager.output(start=2, end=3) == []
    assert [item["id"] for item in manager.output(start=3, end=4)] == [newest.id]
    assert [item["id"] for item in manager.output()] == [retained.id, newest.id]


def test_clear_starts_a_new_cursor_generation():
    manager = NotificationManager(max_notifications=1)
    for number in range(4):
        add(manager, str(number))
    _, old_guid, _ = manager.output_with_state()
    manager.clear_all()
    payload, guid, version = manager.output_with_state()
    assert payload == []
    assert guid != old_guid
    assert version == 0
    item = add(manager, "After clear")
    payload, same_guid, version = manager.output_with_state()
    assert [value["id"] for value in payload] == [item.id]
    assert same_guid == guid
    assert version == 1


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_webui_store_receives_new_toasts_beyond_default_retention():
    manager = NotificationManager()
    snapshots = []
    cursor = 0
    for number in range(105):
        add(manager, str(number), id=f"notification-{number}")
        payload, guid, cursor = manager.output_with_state(start=cursor)
        snapshots.append(
            {
                "notifications": payload,
                "notifications_guid": guid,
                "notifications_version": cursor,
            }
        )

    root = Path(__file__).resolve().parents[1]
    source = (root / "webui/components/notifications/notification-store.js").read_text()
    source = source.split("// Create and export the store")[0]
    source = re.sub(r"^import .*?;\n", "", source, flags=re.MULTILINE)
    source = source.replace("export const ", "const ")
    script = (
        "import assert from 'node:assert/strict';\nconst callJsExtensions = () => {};\n"
    )
    script += source
    script += "\nconst received = []; model.addToToastStack = item => received.push(item.id);\n"
    script += f"const snapshots = {json.dumps(snapshots)};\n"
    script += """
for (let i = 0; i < snapshots.length; i++) {
  model.updateFromPoll(snapshots[i]);
  assert.equal(received.at(-1), `notification-${i}`);
  assert.equal(received.length, i + 1);
  assert.equal(model.lastNotificationVersion, i + 1);
}
assert.equal(model.notifications.length, 100);
assert.equal(model.notifications[0].id, 'notification-104');
assert.equal(new Set(received).size, 105);
"""
    subprocess.run(["node", "--input-type=module"], input=script, text=True, check=True)
