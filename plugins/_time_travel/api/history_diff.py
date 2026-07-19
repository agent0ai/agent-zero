from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import (
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    resolve_workspace,
)


class HistoryDiff(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        try:
            workspace = resolve_workspace(context_id, context_loader=self.use_context)
            return TimeTravelService(workspace).history_diff(
                commit_hash=str(input.get("commit_hash") or ""),
                path=str(input.get("path") or ""),
                mode=str(input.get("mode") or "commit"),
            )
        except WorkspaceRejectedError as exc:
            return {"ok": False, "locked": True, "error": str(exc)}
        except TimeTravelError as exc:
            return {"ok": False, "error": str(exc)}
