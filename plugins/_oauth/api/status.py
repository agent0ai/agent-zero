from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers import codex
from plugins._oauth.helpers.config import codex_config
from plugins._oauth.helpers.route_bootstrap import is_installed


class Status(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        cfg = codex_config()
        return {
            "ok": True,
            "routes_installed": is_installed(),
            "codex": {
                **codex.status(),
                "enabled": cfg["enabled"],
                "proxy_base_path": cfg["proxy_base_path"],
                "callback_path": cfg["callback_path"],
                "v1_base_path": f'{cfg["proxy_base_path"]}/v1',
            },
        }
