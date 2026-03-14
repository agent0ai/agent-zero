"""
Life OS Tool for Agent Jumbo
Event-driven dashboard aggregation and daily planning.
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class LifeOS(Tool):
    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        from instruments.custom.life_os.life_manager import LifeOSManager

        db_path = files.get_abs_path("./instruments/custom/life_os/data/life_os.db")
        self.manager = LifeOSManager(db_path)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        if action == "emit_event":
            event_type = self.args.get("type")
            payload = self.args.get("payload") or {}
            result = self.manager.emit_event(event_type, payload)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "get_dashboard":
            result = self.manager.get_dashboard()
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "generate_daily_plan":
            plan_date = self.args.get("date")
            result = self.manager.generate_daily_plan(plan_date)

            # MOS hook: merge Linear current cycle items into daily plan
            try:
                from instruments.custom.linear_integration.linear_db import LinearDatabase

                linear_db_path = files.get_abs_path(
                    "./instruments/custom/linear_integration/data/linear_integration.db"
                )
                linear_db = LinearDatabase(linear_db_path)
                linear_items = linear_db.get_issues(state_name="In Progress", limit=10)
                if linear_items:
                    result["linear_cycle_items"] = [
                        {
                            "identifier": i.get("identifier", ""),
                            "title": i.get("title", ""),
                            "priority": i.get("priority", 0),
                        }
                        for i in linear_items
                    ]
            except Exception:
                pass

            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "configure_widgets":
            widgets = self.args.get("widgets") or []
            result = self.manager.configure_widgets(widgets)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        return Response(
            message="Unknown action. Use emit_event, get_dashboard, generate_daily_plan, configure_widgets.",
            break_loop=False,
        )
