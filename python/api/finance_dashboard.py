"""
Finance Dashboard API
Provides aggregated finance data for the UI dashboard.
"""

from python.helpers import files
from python.helpers.api import ApiHandler


class FinanceDashboard(ApiHandler):
    async def process(self, input: dict, request) -> dict:
        try:
            from instruments.custom.finance_manager.finance_manager import FinanceManager

            db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
            manager = FinanceManager(db_path)

            period = input.get("period", "")
            account_id = input.get("account_id")
            account_id = int(account_id) if account_id else None

            report = manager.generate_report(period, account_id=account_id)
            roi = manager.roi_snapshot(period, account_id=account_id)
            auth_url = manager.get_auth_url("plaid")

            return {"success": True, "report": report, "roi": roi, "auth_url": auth_url}
        except Exception as e:
            return {"success": False, "error": str(e)}
