"""
Calendar Hub Tool for Agent Jumbo
Mock-friendly calendar integration with event CRUD and prep/follow-up hooks.
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class CalendarHub(Tool):
    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager

        db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
        self.manager = CalendarHubManager(db_path)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        if action == "connect_account":
            provider = self.args.get("provider", "google")
            mock = bool(self.args.get("mock", True))
            result = self.manager.connect_account(provider=provider, mock=mock)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "list_calendars":
            account_id = self.args.get("account_id")
            if account_id is None:
                return Response(message="account_id is required", break_loop=False)
            result = self.manager.list_calendars(int(account_id))
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "list_accounts":
            result = self.manager.list_accounts()
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "get_auth_url":
            provider = self.args.get("provider", "google")
            result = {"auth_url": self.manager.get_auth_url(provider)}
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "create_event":
            result = self.manager.create_event(
                calendar_id=int(self.args.get("calendar_id")),
                title=self.args.get("title"),
                start=self.args.get("start"),
                end=self.args.get("end"),
                attendees=self.args.get("attendees"),
                notes=self.args.get("notes"),
            )
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "list_events":
            calendar_id = self.args.get("calendar_id")
            limit = int(self.args.get("limit", 25))
            result = self.manager.list_events(int(calendar_id) if calendar_id is not None else None, limit=limit)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "set_rules":
            account_id = int(self.args.get("account_id"))
            rules = self.args.get("rules") or {}
            result = self.manager.set_rules(account_id, rules)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "get_rules":
            account_id = int(self.args.get("account_id"))
            result = self.manager.get_rules(account_id)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "generate_prep":
            event_id = int(self.args.get("event_id"))
            sources = self.args.get("sources") or []
            result = self.manager.generate_prep(event_id, sources)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "create_followup":
            event_id = int(self.args.get("event_id"))
            summary = self.args.get("summary")
            due_at = self.args.get("due_at")
            result = await self.manager.create_followup(event_id, summary, due_at)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "update_event":
            event_id = int(self.args.get("event_id"))
            updates = self.args.get("updates") or {}
            result = self.manager.update_event(event_id, updates)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "delete_event":
            event_id = int(self.args.get("event_id"))
            result = self.manager.delete_event(event_id)
            return Response(message=json.dumps({"deleted": result}, indent=4), break_loop=False)

        return Response(
            message="Unknown action. Use connect_account, list_accounts, get_auth_url, list_calendars, list_events, create_event, set_rules, get_rules, generate_prep, create_followup, update_event, delete_event.",
            break_loop=False,
        )
