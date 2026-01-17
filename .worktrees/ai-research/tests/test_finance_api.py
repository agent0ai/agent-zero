import json
from types import SimpleNamespace

from python.api.finance_dashboard import FinanceDashboard


class DummyRequest:
    def __init__(self, payload):
        self._payload = payload
        self.is_json = True
        self.data = json.dumps(payload).encode("utf-8")

    def get_json(self):
        return self._payload


async def test_finance_dashboard_api(tmp_path, monkeypatch):
    from instruments.custom.finance_manager.finance_manager import FinanceManager
    from python.helpers import files

    db_path = tmp_path / "finance.db"
    manager = FinanceManager(str(db_path))
    account = manager.connect_account(provider="mock", mock=True)
    manager.sync_transactions(account["id"], start="2025-01-01", end="2025-01-31")

    monkeypatch.setattr(files, "get_abs_path", lambda path: str(db_path))

    handler = FinanceDashboard(SimpleNamespace(), SimpleNamespace())
    result = await handler.process({"period": "2025-01", "account_id": account["id"]}, DummyRequest({"period": "2025-01", "account_id": account["id"]}))

    assert result["success"] is True
    assert result["report"]["total_count"] >= 1
    assert "auth_url" in result
