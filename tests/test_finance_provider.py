import os

from instruments.custom.finance_manager.finance_manager import FinanceManager


def test_finance_connect_returns_auth_url_key(tmp_path, monkeypatch):
    db_path = os.path.join(tmp_path, "finance.db")
    manager = FinanceManager(db_path)

    monkeypatch.delenv("PLAID_CLIENT_ID", raising=False)
    monkeypatch.delenv("PLAID_REDIRECT_URI", raising=False)

    account = manager.connect_account(provider="plaid", mock=False)
    assert account["status"] == "pending"
    assert "auth_url" in account
