"""
Calendar Dashboard API
Provides aggregated calendar data for the UI dashboard.
"""

from python.helpers import files
from python.helpers.api import ApiHandler


class CalendarDashboard(ApiHandler):
    async def process(self, input: dict, request) -> dict:
        try:
            from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager

            db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
            manager = CalendarHubManager(db_path)

            accounts = manager.list_accounts()
            account_id = input.get("account_id")
            if account_id is None and accounts:
                account_id = accounts[0]["id"]

            calendars = manager.list_calendars(int(account_id)) if account_id else []
            calendar_id = input.get("calendar_id")
            if calendar_id is None and calendars:
                calendar_id = calendars[0]["id"]

            events = manager.list_events(int(calendar_id) if calendar_id else None, limit=25)
            rules = manager.get_rules(int(account_id)) if account_id else {}

            try:
                auth_url = manager.get_auth_url("google")
            except Exception:
                auth_url = None

            return {
                "success": True,
                "accounts": accounts,
                "calendars": calendars,
                "events": events,
                "rules": rules,
                "auth_url": auth_url,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
