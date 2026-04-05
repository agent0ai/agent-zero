"""HTTP interaction fallback for browser control."""

import time
from python.helpers.api import ApiHandler
from python.helpers import files, persist_chat
from flask import Request
from agent import AgentContext


class BrowserUseInteract(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict:
        action = input.get("action", "")
        context_id = input.get("context_id", "")

        context = self.use_context(context_id) if context_id else AgentContext.first()
        if not context:
            return {"error": "No agent context found"}

        agent = context.agent0

        from plugins.browser_use.helpers.session_manager import SessionManager

        manager = SessionManager.get_existing(agent)
        if not manager or not manager.is_alive:
            return {"error": "No active browser session. Start one first."}

        if action == "navigate":
            url = input.get("url", "")
            if not url:
                return {"error": "'url' is required"}
            async with manager.lock:
                page = await manager.get_page()
                if page:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    return {"url": page.url, "title": await page.title()}
            return {"error": "No page available"}

        elif action == "screenshot":
            page = await manager.get_page()
            if not page:
                return {"error": "No page available"}
            path = files.get_abs_path(
                persist_chat.get_chat_folder_path(context.id),
                "browser", "screenshots", f"interact_{int(time.time())}.png",
            )
            files.make_dirs(path)
            await page.screenshot(path=path, full_page=False)
            return {"path": f"img://{path}&t={time.time()}"}

        elif action == "state":
            state = await manager.get_state()
            return state

        return {"error": f"Unknown action: {action}"}
