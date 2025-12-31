from python.helpers.api import ApiHandler, Request, Response
from agent import AgentContext
from python.helpers.alert import emit_alert, AlertType
from typing import cast


class AlertTest(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        alert_type = input.get("alert_type", "")
        if alert_type not in ("task_complete", "input_needed", "subagent_complete"):
            return {"success": False, "error": "Invalid alert_type"}

        nm = AgentContext.get_notification_manager()
        start = len(nm.updates)

        # Emit as an alert.* notification, respecting current alert settings.
        emit_alert(cast(AlertType, alert_type))

        return {
            "success": True,
            "notifications": nm.output(start=start),
            "notifications_guid": nm.guid,
            "notifications_version": len(nm.updates),
        }


