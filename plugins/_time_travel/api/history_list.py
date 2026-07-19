from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import (
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    resolve_workspace,
    unavailable_payload,
)


class HistoryList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        try:
            workspace = resolve_workspace(context_id, context_loader=self.use_context)
            return TimeTravelService(workspace).history_list(
                limit=int(input.get("limit") or 100),
                offset=int(input.get("offset") or 0),
                file_filter=str(input.get("file_filter") or ""),
            )
        except WorkspaceRejectedError as exc:
            return unavailable_payload(context_id, str(exc))
        except TimeTravelError as exc:
            return {"ok": False, "error": str(exc)}
