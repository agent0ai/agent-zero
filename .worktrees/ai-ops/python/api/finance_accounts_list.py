"""
Finance Accounts List API
Returns configured finance accounts.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class FinanceAccountsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        from instruments.custom.finance_manager.finance_manager import FinanceManager

        db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
        manager = FinanceManager(db_path)
        accounts = manager.list_accounts()
        return {"success": True, "accounts": accounts}
