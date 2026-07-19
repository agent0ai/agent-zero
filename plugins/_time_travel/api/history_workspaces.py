from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import list_selectable_workspaces


class HistoryWorkspaces(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        data = list_selectable_workspaces(context_id, context_loader=self.use_context)
        return {"ok": True, **data}
