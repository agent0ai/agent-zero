import json
from types import SimpleNamespace

from python.api.calendar_connect import CalendarConnect
from python.api.finance_accounts_list import FinanceAccountsList
from python.api.finance_connect import FinanceConnect


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_calendar_connect_api(tmp_path, monkeypatch):
    from python.helpers import files

    db_path = tmp_path / "calendar_hub.db"
    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    handler = CalendarConnect(SimpleNamespace(), SimpleNamespace())
    result = await handler.process({"provider": "google", "mock": True}, DummyRequest({"provider": "google"}))

    assert result["success"] is True
    assert result["auth_state"] == "connected"
    assert "id" in result


async def test_finance_connect_and_list_api(tmp_path, monkeypatch):
    from python.helpers import files

    db_path = tmp_path / "finance_manager.db"
    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    connect_handler = FinanceConnect(SimpleNamespace(), SimpleNamespace())
    connect_result = await connect_handler.process({"provider": "plaid", "mock": True}, DummyRequest({"provider": "plaid"}))

    assert connect_result["success"] is True
    assert connect_result["status"] == "connected"

    list_handler = FinanceAccountsList(SimpleNamespace(), SimpleNamespace())
    list_result = await list_handler.process({}, DummyRequest({}))

    assert list_result["success"] is True
    assert len(list_result["accounts"]) == 1
