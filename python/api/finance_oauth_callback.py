"""
Finance OAuth Callback API
Mock handler to store OAuth tokens.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class FinanceOauthCallback(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        account_id = input.get("account_id")

        if not account_id:
            return {"success": False, "error": "account_id is required"}

        from instruments.custom.finance_manager.finance_manager import FinanceManager

        db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
        manager = FinanceManager(db_path)
        result = manager.complete_oauth(int(account_id))
        return {"success": True, "account": result}
