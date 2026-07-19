import os
import sys
import threading
from datetime import datetime
from pathlib import Path

import pytest
import pytz
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import helpers.localization as localization_module
import helpers.plugins as plugins_module
import helpers.settings as settings_module
from helpers.localization import Localization
from helpers.task_scheduler import (
    TaskPlan,
    parse_task_plan,
    serialize_task_plan,
)
from plugins._memory.api.memory_dashboard import MemoryDashboard
from plugins._desktop.helpers import desktop_session


@pytest.fixture
def isolated_localization(monkeypatch):
    saved: list[tuple[str, str]] = []

    def fake_get_dotenv_value(key, default=None):
        if key == "DEFAULT_USER_TIMEZONE":
            return default or "UTC"
        if key == "DEFAULT_USER_UTC_OFFSET_MINUTES":
            return None
        return default

    monkeypatch.setattr(localization_module, "get_dotenv_value", fake_get_dotenv_value)
    monkeypatch.setattr(
        localization_module,
        "save_dotenv_value",
        lambda key, value: saved.append((key, str(value))),
    )
    monkeypatch.setattr(
        localization_module.PrintStyle,
        "error",
        staticmethod(lambda *args, **kwargs: None),
    )
    Localization._instance = None
    original_tz = os.environ.get("TZ")

    yield saved

    Localization._instance = None
    if original_tz is None:
        monkeypatch.delenv("TZ", raising=False)
    else:
        monkeypatch.setenv("TZ", original_tz)


def set_test_timezone(timezone: str) -> Localization:
    Localization._instance = Localization(timezone)
    return Localization.get()


def test_invalid_timezone_preserves_current_user_timezone(isolated_localization):
    saved = isolated_localization
    localization = set_test_timezone("Europe/Rome")
    saved.clear()

    localization.set_timezone("Mars/Olympus")

    assert localization.get_timezone() == "Europe/Rome"
    assert os.environ["TZ"] == "Europe/Rome"
    assert not any(item == ("DEFAULT_USER_TIMEZONE", "UTC") for item in saved)
    assert not any(item == ("DEFAULT_USER_TIMEZONE", "Mars/Olympus") for item in saved)


def test_startup_refreshes_stale_persisted_offset(monkeypatch):
    saved: list[tuple[str, str]] = []

    def fake_get_dotenv_value(key, default=None):
        if key == "DEFAULT_USER_TIMEZONE":
            return "Europe/Rome"
        if key == "DEFAULT_USER_UTC_OFFSET_MINUTES":
            return "0"
        return default

    monkeypatch.setattr(localization_module, "get_dotenv_value", fake_get_dotenv_value)
    monkeypatch.setattr(
        localization_module,
        "save_dotenv_value",
        lambda key, value: saved.append((key, str(value))),
    )
    Localization._instance = None

    localization = Localization.get()
    expected_offset = int(
        datetime.now(pytz.timezone("Europe/Rome")).utcoffset().total_seconds() // 60
    )

    assert localization.get_timezone() == "Europe/Rome"
    assert localization.get_offset_minutes() == expected_offset
    assert ("DEFAULT_USER_UTC_OFFSET_MINUTES", str(expected_offset)) in saved


def test_scheduler_naive_plan_times_round_trip_as_user_local(isolated_localization):
    set_test_timezone("Europe/Rome")

    plan = parse_task_plan({"todo": ["2026-05-03T09:30:00"], "in_progress": None, "done": []})
    serialized = serialize_task_plan(plan)

    assert serialized["todo"] == ["2026-05-03T09:30:00+02:00"]


def test_settings_auto_timezone_resolves_to_browser_timezone(isolated_localization, monkeypatch):
    set_test_timezone("UTC")
    hooks: list[dict] = []
    base_settings = settings_module.get_default_settings()
    monkeypatch.setattr(
        settings_module,
        "_settings",
        {**base_settings, "timezone": settings_module.TIMEZONE_AUTO},
    )
    monkeypatch.setattr(
        plugins_module,
        "call_plugin_hook",
        lambda plugin_name, hook_name, *args, **kwargs: hooks.append(
            {
                "plugin_name": plugin_name,
                "hook_name": hook_name,
                "kwargs": kwargs,
            }
        ),
    )

    settings_module._apply_timezone_setting(
        {**base_settings, "timezone": settings_module.TIMEZONE_AUTO},
        browser_timezone="Europe/Rome",
    )

    assert Localization.get().get_timezone() == "Europe/Rome"
    assert hooks[0]["plugin_name"] == "_office"
    assert hooks[0]["hook_name"] == "timezone_changed"
    assert hooks[0]["kwargs"]["previous_timezone"] == "UTC"
    assert hooks[0]["kwargs"]["timezone"] == "Europe/Rome"


def test_settings_fixed_timezone_ignores_browser_timezone(isolated_localization, monkeypatch):
    set_test_timezone("Europe/Rome")
    base_settings = settings_module.get_default_settings()
    monkeypatch.setattr(
        settings_module,
        "_settings",
        {**base_settings, "timezone": "America/New_York"},
    )
    monkeypatch.setattr(plugins_module, "call_plugin_hook", lambda *args, **kwargs: None)

    settings_module._apply_timezone_setting(
        {**base_settings, "timezone": settings_module.TIMEZONE_AUTO},
        browser_timezone="Europe/Rome",
    )

    assert Localization.get().get_timezone() == "America/New_York"


def test_settings_fixed_timezone_reapplies_when_runtime_drifted(isolated_localization, monkeypatch):
    set_test_timezone("Europe/Rome")
    base_settings = settings_module.get_default_settings()
    fixed_settings = {**base_settings, "timezone": "America/New_York"}
    hooks: list[dict] = []
    monkeypatch.setattr(settings_module, "_settings", fixed_settings)
    monkeypatch.setattr(
        plugins_module,
        "call_plugin_hook",
        lambda plugin_name, hook_name, *args, **kwargs: hooks.append(
            {
                "plugin_name": plugin_name,
                "hook_name": hook_name,
                "kwargs": kwargs,
            }
        ),
    )

    settings_module._apply_timezone_setting(
        {**base_settings, "timezone": "America/New_York"},
        browser_timezone="Europe/Rome",
    )

    assert Localization.get().get_timezone() == "America/New_York"
    assert hooks[0]["plugin_name"] == "_office"
    assert hooks[0]["hook_name"] == "timezone_changed"
    assert hooks[0]["kwargs"]["previous_timezone"] == "Europe/Rome"
    assert hooks[0]["kwargs"]["timezone"] == "America/New_York"


def test_settings_rejects_invalid_timezone_value():
    settings_data = settings_module.get_default_settings()
    normalized = settings_module.normalize_settings(
        {**settings_data, "timezone": "Mars/Olympus"}
    )

    assert normalized["timezone"] == settings_module.TIMEZONE_AUTO


def test_settings_rejects_invalid_time_format_value():
    settings_data = settings_module.get_default_settings()

    invalid = settings_module.normalize_settings(
        {**settings_data, "time_format": "bananas"}
    )
    twenty_four = settings_module.normalize_settings(
        {**settings_data, "time_format": settings_module.TIME_FORMAT_24H}
    )

    assert invalid["time_format"] == settings_module.TIME_FORMAT_12H
    assert twenty_four["time_format"] == settings_module.TIME_FORMAT_24H


def test_scheduler_naive_plan_times_follow_changed_user_timezone(isolated_localization):
    set_test_timezone("America/New_York")

    plan = parse_task_plan({"todo": ["2026-05-03T09:30:00"], "in_progress": None, "done": []})
    serialized = serialize_task_plan(plan)

    assert serialized["todo"] == ["2026-05-03T09:30:00-04:00"]


def test_task_plan_create_localizes_naive_datetimes(isolated_localization):
    set_test_timezone("Europe/Rome")

    plan = TaskPlan.create(todo=[datetime(2026, 5, 3, 9, 30)])

    assert plan.todo[0].isoformat() == "2026-05-03T09:30:00+02:00"


def test_memory_dashboard_normalizes_legacy_naive_timestamps(isolated_localization):
    set_test_timezone("Europe/Rome")
    dashboard = MemoryDashboard(app=None, thread_lock=threading.RLock())

    formatted = dashboard._format_memory_for_dashboard(
        Document(
            page_content="legacy memory",
            metadata={
                "id": "memory-1",
                "area": "main",
                "timestamp": "2026-05-02 18:27:51",
            },
        )
    )

    assert formatted["timestamp"] == "2026-05-02T18:27:51+02:00"
    assert formatted["metadata"]["timestamp"] == "2026-05-02 18:27:51"


def test_memory_dashboard_converts_aware_timestamps_to_user_timezone(isolated_localization):
    set_test_timezone("Europe/Rome")
    dashboard = MemoryDashboard(app=None, thread_lock=threading.RLock())

    assert (
        dashboard._serialize_memory_timestamp("2026-05-02T16:27:51+00:00")
        == "2026-05-02T18:27:51+02:00"
    )


class FakeProcess:
    pid = 4242

    def poll(self):
        return None


def test_desktop_session_env_uses_session_timezone(isolated_localization, tmp_path):
    set_test_timezone("Europe/Rome")
    session = desktop_session.DesktopSession(
        session_id=desktop_session.SYSTEM_SESSION_ID,
        file_id=desktop_session.SYSTEM_FILE_ID,
        extension="desktop",
        path=str(tmp_path),
        title="Desktop",
        display=120,
        xpra_port=14500,
        token=desktop_session.SYSTEM_SESSION_ID,
        url="/desktop/session/agent-zero-desktop/index.html",
        profile_dir=tmp_path / "profile",
        timezone="America/New_York",
    )

    env = desktop_session.DesktopSessionManager()._session_env(session)

    assert env["TZ"] == "America/New_York"


def test_desktop_timezone_sync_restarts_active_system_desktop(
    isolated_localization,
    monkeypatch,
    tmp_path,
):
    set_test_timezone("America/New_York")
    manager = desktop_session.DesktopSessionManager()
    old_session = desktop_session.DesktopSession(
        session_id=desktop_session.SYSTEM_SESSION_ID,
        file_id=desktop_session.SYSTEM_FILE_ID,
        extension="desktop",
        path=str(tmp_path),
        title="Desktop",
        display=120,
        xpra_port=14500,
        token=desktop_session.SYSTEM_SESSION_ID,
        url="/desktop/session/agent-zero-desktop/index.html",
        profile_dir=tmp_path / "profile-old",
        timezone="Europe/Rome",
        processes={"xpra": FakeProcess()},
    )
    replacement = desktop_session.DesktopSession(
        session_id=desktop_session.SYSTEM_SESSION_ID,
        file_id=desktop_session.SYSTEM_FILE_ID,
        extension="desktop",
        path=str(tmp_path),
        title="Desktop",
        display=120,
        xpra_port=14500,
        token=desktop_session.SYSTEM_SESSION_ID,
        url="/desktop/session/agent-zero-desktop/index.html",
        profile_dir=tmp_path / "profile-new",
        timezone="America/New_York",
        processes={"xpra": FakeProcess()},
    )
    manager._sessions[desktop_session.SYSTEM_SESSION_ID] = old_session
    restarted: list[desktop_session.DesktopSession] = []

    def fake_restart(session):
        restarted.append(session)
        manager._sessions[desktop_session.SYSTEM_SESSION_ID] = replacement
        return replacement

    monkeypatch.setattr(manager, "_restart_system_desktop_for_timezone_locked", fake_restart)

    result = manager.sync_timezone("America/New_York")

    assert result == {
        "ok": True,
        "restarted": True,
        "session_id": desktop_session.SYSTEM_SESSION_ID,
        "timezone": "America/New_York",
    }
    assert restarted == [old_session]
