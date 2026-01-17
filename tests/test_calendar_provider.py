import os

from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager


def test_calendar_connect_returns_auth_url_key(tmp_path, monkeypatch):
    db_path = os.path.join(tmp_path, "calendar_hub.db")
    manager = CalendarHubManager(db_path)

    monkeypatch.delenv("GOOGLE_CALENDAR_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CALENDAR_REDIRECT_URI", raising=False)

    account = manager.connect_account(provider="google", mock=False)
    assert account["auth_state"] == "pending"
    assert "auth_url" in account
