import os

from instruments.custom.finance_manager.finance_manager import FinanceManager


def test_finance_ingest_and_reporting(tmp_path):
    db_path = os.path.join(tmp_path, "finance.db")
    manager = FinanceManager(db_path)

    account = manager.connect_account(provider="mock", mock=True)
    transactions = manager.sync_transactions(account["id"], start="2025-01-01", end="2025-01-31")
    assert len(transactions) == 2

    first_txn = transactions[0]
    manager.categorize(first_txn["id"], "software")

    receipt = manager.upload_receipt(first_txn["id"], "/tmp/receipt.png")
    assert receipt["txn_id"] == first_txn["id"]
    assert receipt["ocr_text"] == "mock-ocr-text"

    report = manager.generate_report("2025-01", account_id=account["id"])
    assert report["total_count"] == 2

    estimate = manager.estimate_tax("2025-01", account_id=account["id"])
    assert estimate["period"] == "2025-01"

    roi = manager.roi_snapshot("2025-01", account_id=account["id"])
    assert roi["period"] == "2025-01"

    export = manager.export_business_xray_data("2025-01", account_id=account["id"])
    assert "monthly_revenue" in export
