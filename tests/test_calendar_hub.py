import asyncio
import os

from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager
from python.helpers.task_scheduler import TaskScheduler


def test_calendar_account_and_event_flow(tmp_path):
    db_path = os.path.join(tmp_path, "calendar_hub.db")
    manager = CalendarHubManager(db_path)

    account = manager.connect_account(provider="google", mock=True)
    calendars = manager.list_calendars(account["id"])
    assert len(calendars) == 1

    rules = manager.set_rules(
        account_id=account["id"],
        rules={"buffer_minutes": 15, "no_meeting_days": ["Saturday", "Sunday"]},
    )
    assert rules["buffer_minutes"] == 15

    event = manager.create_event(
        calendar_id=calendars[0]["id"],
        title="Kickoff",
        start="2025-01-01T10:00:00Z",
        end="2025-01-01T10:30:00Z",
        attendees=["a@example.com"],
        notes="Discuss scope",
    )
    assert event["title"] == "Kickoff"

    prep = manager.generate_prep(event["id"], sources=["gmail"])
    assert "Kickoff" in prep["brief_text"]

    followup = asyncio.run(
        manager.create_followup(
            event_id=event["id"],
            summary="Send recap email",
            due_at="2025-01-01T11:00:00+00:00",
        )
    )
    task = TaskScheduler.get().get_task_by_uuid(followup["task_uuid"])
    assert task is not None

    updated = manager.update_event(event["id"], {"title": "Kickoff v2"})
    assert updated["title"] == "Kickoff v2"

    deleted = manager.delete_event(event["id"])
    assert deleted is True

    asyncio.run(TaskScheduler.get().remove_task_by_uuid(followup["task_uuid"]))
