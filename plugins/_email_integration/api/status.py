"""Return secret-free status for configured email inboxes."""

import sys

from helpers import plugins
from helpers.api import ApiHandler, Request


PLUGIN_NAME = "_email_integration"
HANDLER_MODULE = "plugins._email_integration.helpers.handler"


class Status(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        handlers = config.get("handlers", [])
        module = sys.modules.get(HANDLER_MODULE)
        tasks = getattr(module, "_poll_tasks", {}) if module else {}

        inboxes = []
        for index, handler in enumerate(handlers):
            if not isinstance(handler, dict):
                continue
            name = str(handler.get("name") or f"Inbox {index + 1}")
            task = tasks.get(name)
            inboxes.append({
                "name": name,
                "address": str(handler.get("username") or ""),
                "enabled": bool(handler.get("enabled")),
                "configured": bool(
                    handler.get("username")
                    and handler.get("password")
                    and handler.get("imap_server")
                    and (handler.get("smtp_server") or handler.get("imap_server"))
                ),
                "running": bool(task and not task.done()),
                "protocol": "Exchange" if handler.get("account_type") == "exchange" else "IMAP",
                "project": str(handler.get("project") or "Default project"),
            })

        return {
            "inboxes": inboxes,
            "total": len(inboxes),
            "enabled": sum(inbox["enabled"] for inbox in inboxes),
            "running": sum(inbox["running"] for inbox in inboxes),
        }
