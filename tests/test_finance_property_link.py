import os

from instruments.custom.finance_manager.finance_manager import FinanceManager


def test_finance_property_link(tmp_path):
    db_path = os.path.join(tmp_path, "finance.db")
    manager = FinanceManager(db_path)

    account = manager.connect_account(provider="mock", mock=True)
    transactions = manager.sync_transactions(account["id"], start="2025-01-01", end="2025-01-31")
    txn_id = transactions[0]["id"]

    link = manager.link_property_expense(txn_id, property_id=101)
    assert link["transaction_id"] == txn_id
