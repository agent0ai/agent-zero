"""
Calendar OAuth Start API
Returns authorization URL for calendar providers.
"""

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response


class CalendarOauthStart(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response | dict:
        provider = input.get("provider", "google")
        from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager

        db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
        manager = CalendarHubManager(db_path)
        auth_url = manager.get_auth_url(provider)
        if not auth_url:
            return {"success": False, "error": "OAuth not configured for provider."}
        return {"success": True, "auth_url": auth_url}
