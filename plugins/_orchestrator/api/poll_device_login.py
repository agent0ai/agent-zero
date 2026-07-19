from __future__ import annotations

from helpers.api import ApiHandler, Request

from plugins._orchestrator.helpers.registry import get_adapter


class PollDeviceLogin(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        agent_id = str(input.get("agent_id") or "codex")
        try:
            adapter = get_adapter(agent_id)
            result = adapter.poll_device_login(input)
            return {"ok": True, "agent_id": adapter.id, **result}
        except Exception as exc:
            return {"ok": False, "agent_id": agent_id, "error": str(exc)}
