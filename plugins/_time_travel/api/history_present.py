from __future__ import annotations

import asyncio

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import TimeTravelError, TimeTravelService, resolve_workspace


class HistoryPresent(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            workspace = resolve_workspace(
                str(input.get("context_id") or ""),
                workspace_id=str(input.get("workspace_id") or ""),
                context_loader=self.use_context,
            )
            present = await asyncio.to_thread(TimeTravelService(workspace).present_summary)
            return {"ok": True, "present": present}
        except TimeTravelError as exc:
            return {"ok": False, "error": str(exc)}
