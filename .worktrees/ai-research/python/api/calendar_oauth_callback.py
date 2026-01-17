"""
Calendar OAuth Callback API
Mock handler to store OAuth tokens.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class CalendarOauthCallback(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        account_id = input.get("account_id")
        token_ref = input.get("token_ref", "mock-token")
        scopes = input.get("scopes", [])

        if not account_id:
            return {"success": False, "error": "account_id is required"}

        from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager

        db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
        manager = CalendarHubManager(db_path)
        result = manager.complete_oauth(int(account_id), token_ref, scopes)
        return {"success": True, "account": result}
