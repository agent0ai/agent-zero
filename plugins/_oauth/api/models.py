from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._oauth.helpers import codex


class Models(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        try:
            models = codex.fetch_models()
            return {"ok": True, "models": models}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "models": []}
