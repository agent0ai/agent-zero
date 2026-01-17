"""
Life OS Tool for Agent Zero
Event-driven dashboard aggregation and daily planning.
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class LifeOS(Tool):
    def __init__(self, agent, name: str, args: dict, message: str, **kwargs):
        super().__init__(agent, name, args, message, **kwargs)
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
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        if action == "configure_widgets":
            widgets = self.args.get("widgets") or []
            result = self.manager.configure_widgets(widgets)
            return Response(message=json.dumps(result, indent=4), break_loop=False)

        return Response(
            message="Unknown action. Use emit_event, get_dashboard, generate_daily_plan, configure_widgets.",
            break_loop=False,
        )
