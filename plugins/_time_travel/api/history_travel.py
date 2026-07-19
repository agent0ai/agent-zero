from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import (
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    resolve_workspace,
)


class HistoryTravel(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        try:
            workspace = resolve_workspace(context_id, context_loader=self.use_context)
            return TimeTravelService(workspace).travel(
                commit_hash=str(input.get("commit_hash") or ""),
                metadata=input.get("metadata") if isinstance(input.get("metadata"), dict) else {},
            )
        except WorkspaceRejectedError as exc:
            return {"ok": False, "locked": True, "error": str(exc)}
        except TimeTravelError as exc:
            return {
                "ok": False,
                "error": str(exc),
                "technical_details": getattr(exc, "stderr", "") or str(exc),
            }
