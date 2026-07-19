from __future__ import annotations

from helpers.api import ApiHandler, Request

from plugins._orchestrator.helpers.registry import get_adapter


class StartDeviceLogin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        agent_id = str(input.get("agent_id") or "codex")
        try:
            adapter = get_adapter(agent_id)
            if not adapter.supports_device_login():
                raise RuntimeError(f"{adapter.title} does not support device login.")
            result = adapter.start_device_login()
            return {"ok": True, "agent_id": adapter.id, **result}
        except Exception as exc:
            return {"ok": False, "agent_id": agent_id, "error": str(exc)}
