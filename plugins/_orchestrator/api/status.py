from __future__ import annotations

from helpers.api import ApiHandler, Request
from helpers.plugins import get_plugin_config

from plugins._orchestrator.helpers.registry import adapter_config, list_adapters

PLUGIN_NAME = "_orchestrator"


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        plugin_config = get_plugin_config(PLUGIN_NAME) or {}
        agents = []
        for adapter in list_adapters():
            cfg = adapter_config(adapter.id, plugin_config)
            try:
                auth = adapter.auth_status(cfg)
            except Exception as exc:
                auth = {
                    "connected": False,
                    "mode": "",
                    "auth_path": "",
                    "error": str(exc),
                }
            agents.append(
                {
                    "id": adapter.id,
                    "title": adapter.title,
                    "description": adapter.description,
                    "binary": adapter.resolve_binary(cfg),
                    "installed": adapter.is_installed(cfg),
                    "install_hint": adapter.install_hint,
                    "supports_device_login": adapter.supports_device_login(),
                    "can_disconnect": adapter.can_disconnect(cfg),
                    "auth": auth,
                }
            )
        return {"ok": True, "agents": agents}
