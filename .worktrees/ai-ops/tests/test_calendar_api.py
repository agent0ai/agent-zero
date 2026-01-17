import json
from types import SimpleNamespace

from python.api.calendar_dashboard import CalendarDashboard


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_calendar_dashboard_api(tmp_path, monkeypatch):
    from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager
    from python.helpers import files

    db_path = tmp_path / "calendar_hub.db"
    manager = CalendarHubManager(str(db_path))
    account = manager.connect_account(provider="google", mock=True)
    calendars = manager.list_calendars(account["id"])
    manager.create_event(
        calendar_id=calendars[0]["id"],
        title="Kickoff",
        start="2025-01-01T10:00:00Z",
        end="2025-01-01T10:30:00Z",
    )

    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    handler = CalendarDashboard(SimpleNamespace(), SimpleNamespace())
    result = await handler.process({"account_id": account["id"]}, DummyRequest({"account_id": account["id"]}))

    assert result["success"] is True
    assert len(result["events"]) >= 1
    assert "auth_url" in result
