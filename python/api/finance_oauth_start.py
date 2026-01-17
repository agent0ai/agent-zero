"""
Finance OAuth Start API
Returns authorization URL for finance providers.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class FinanceOauthStart(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        provider = input.get("provider", "plaid")
        from instruments.custom.finance_manager.finance_manager import FinanceManager

        db_path = files.get_abs_path("./instruments/custom/finance_manager/data/finance_manager.db")
        manager = FinanceManager(db_path)
        auth_url = manager.get_auth_url(provider)
        if not auth_url:
            return {"success": False, "error": "OAuth not configured for provider."}
        return {"success": True, "auth_url": auth_url}
