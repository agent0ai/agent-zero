"""
Calendar Connect API
Creates a calendar account and returns OAuth URL if available.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class CalendarConnect(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        provider = input.get("provider", "google")
        mock = input.get("mock", False)
        if isinstance(mock, str):
            mock = mock.lower() in ("1", "true", "yes", "y")

        from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager

        db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
        manager = CalendarHubManager(db_path)
        account = manager.connect_account(provider=provider, mock=bool(mock))
        return {"success": True, **account}
