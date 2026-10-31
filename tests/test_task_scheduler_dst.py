"""Next-run reporting must use the offset on the scheduled date."""

from datetime import datetime, timedelta

import pytest
import pytz
from crontab import CronTab

from helpers import task_scheduler as scheduler
from helpers.localization import Localization


@pytest.fixture
def make_task(monkeypatch):
    def create(zone, now, day, month, hour="17", minute="30"):
        instant = datetime.fromisoformat(now)

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return instant.replace(tzinfo=None)
                return instant.astimezone(tz)

        monkeypatch.setattr(scheduler, "datetime", Clock)
        monkeypatch.setattr(scheduler, "_now", lambda: instant)
        localization = object.__new__(Localization)
        localization.timezone = zone
        monkeypatch.setattr(Localization, "_instance", localization)
        task = scheduler.ScheduledTask.create(
            name="DST reporting",
            system_prompt="",
            prompt="test",
            schedule=scheduler.TaskSchedule(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                weekday="*",
                timezone=zone,
            ),
        )
        return task, instant

    return create


@pytest.mark.parametrize(
    "zone,now,day,month,expected",
    [
        (
            "America/Los_Angeles",
            "2026-10-29T10:00:00+00:00",
            "4",
            "11",
            "2026-11-05T01:30:00+00:00",
        ),
        (
            "America/Los_Angeles",
            "2026-03-06T10:00:00+00:00",
            "11",
            "3",
            "2026-03-12T00:30:00+00:00",
        ),
        (
            "Europe/Rome",
            "2026-10-23T10:00:00+00:00",
            "28",
            "10",
            "2026-10-28T16:30:00+00:00",
        ),
        (
            "Europe/Rome",
            "2026-03-27T10:00:00+00:00",
            "1",
            "4",
            "2026-04-01T15:30:00+00:00",
        ),
        (
            "Australia/Lord_Howe",
            "2026-04-03T00:00:00+00:00",
            "8",
            "4",
            "2026-04-08T07:00:00+00:00",
        ),
        (
            "Australia/Lord_Howe",
            "2026-10-02T00:00:00+00:00",
            "7",
            "10",
            "2026-10-07T06:30:00+00:00",
        ),
        (
            "America/Los_Angeles",
            "2026-10-28T10:00:00+00:00",
            "29",
            "10",
            "2026-10-30T00:30:00+00:00",
        ),
        ("UTC", "2026-10-29T10:00:00+00:00", "4", "11", "2026-11-04T17:30:00+00:00"),
        (
            "Asia/Kolkata",
            "2026-10-29T10:00:00+00:00",
            "4",
            "11",
            "2026-11-04T12:00:00+00:00",
        ),
    ],
)
def test_next_run_uses_scheduled_date_offset(
    make_task, zone, now, day, month, expected
):
    task, instant = make_task(zone, now, day, month)
    expected_utc = datetime.fromisoformat(expected)

    assert task.get_next_run() == expected_utc
    assert task.get_next_run_minutes() == int(
        (expected_utc - instant).total_seconds() / 60
    )
    assert (
        scheduler.serialize_task(task)["next_run"]
        == expected_utc.astimezone(pytz.timezone(zone)).isoformat()
    )


@pytest.mark.parametrize(
    "zone,now,day,month,hour,minute",
    [
        ("America/Los_Angeles", "2026-10-30T10:00:00+00:00", "1", "11", "1", "30"),
        ("America/Los_Angeles", "2026-03-06T10:00:00+00:00", "8", "3", "2", "30"),
        ("Australia/Lord_Howe", "2026-04-03T00:00:00+00:00", "5", "4", "1", "45"),
        ("Australia/Lord_Howe", "2026-10-02T00:00:00+00:00", "4", "10", "2", "15"),
    ],
)
def test_transition_hour_matches_existing_cron_delay_policy(
    make_task, zone, now, day, month, hour, minute
):
    task, instant = make_task(zone, now, day, month, hour, minute)
    # The firing path uses CronTab's delay calculation. Preserve its existing
    # ambiguous/nonexistent-wall-time policy rather than inventing a new one.
    delay = CronTab(task.schedule.to_crontab()).next(
        now=instant.astimezone(pytz.timezone(zone)), return_datetime=False
    )
    assert task.get_next_run() == instant + timedelta(seconds=delay)


def test_next_run_preserves_no_future_result(make_task, monkeypatch):
    task, _ = make_task("UTC", "2026-10-29T10:00:00+00:00", "4", "11")
    monkeypatch.setattr(CronTab, "next", lambda *args, **kwargs: None)
    assert task.get_next_run() is None
    assert task.get_next_run_minutes() is None
    assert scheduler.serialize_task(task)["next_run"] is None
