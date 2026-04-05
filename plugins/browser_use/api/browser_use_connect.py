"""Session lifecycle API: start, stop, status."""

from python.helpers.api import ApiHandler
from flask import Request
from agent import AgentContext


class BrowserUseConnect(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "status")
        context_id = input.get("context_id", "")

        context = self.use_context(context_id) if context_id else AgentContext.first()
        if not context:
            return {"error": "No agent context found", "status": "error"}

        agent = context.agent0

        from plugins.browser_use.helpers.session_manager import SessionManager

        if action == "start":
            manager = SessionManager.get_or_create(agent)
            await manager.ensure_started()
            return {
                "status": "connected",
                "cdp_ws_url": manager.cdp_ws_url,
                "context_id": context.id,
            }

        elif action == "stop":
            manager = SessionManager.get_existing(agent)
            if manager:
                await manager.close()
            return {"status": "closed"}

        elif action == "status":
            manager = SessionManager.get_existing(agent)
            if not manager:
                return {"alive": False, "url": "", "title": "", "busy": False}
            state = await manager.get_state()
            return state

        return {"error": f"Unknown action: {action}"}
