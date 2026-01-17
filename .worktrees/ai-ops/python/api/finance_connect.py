"""
Finance Connect API
Creates a finance account and returns OAuth URL if available.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class FinanceConnect(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        provider = input.get("provider", "plaid")
        mock = input.get("mock", False)
        if isinstance(mock, str):
            mock = mock.lower() in ("1", "true", "yes", "y")

        from instruments.custom.finance_manager.finance_manager import FinanceManager

        db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
        manager = FinanceManager(db_path)
        account = manager.connect_account(provider=provider, mock=bool(mock))
        return {"success": True, **account}
