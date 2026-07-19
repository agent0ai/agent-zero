from __future__ import annotations

from helpers.api import ApiHandler, Request
from helpers.plugins import get_plugin_config

from plugins._orchestrator.helpers.registry import adapter_config, get_adapter

PLUGIN_NAME = "_orchestrator"


class Disconnect(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        agent_id = str(input.get("agent_id") or "codex")
        try:
            adapter = get_adapter(agent_id)
            plugin_config = get_plugin_config(PLUGIN_NAME) or {}
            cfg = adapter_config(adapter.id, plugin_config)
            result = adapter.disconnect(cfg)
            return {"ok": True, "agent_id": adapter.id, **result}
        except Exception as exc:
            return {"ok": False, "agent_id": agent_id, "error": str(exc)}
