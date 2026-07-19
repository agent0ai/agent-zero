from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import (
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    _snapshot_public,
    resolve_workspace,
)


class HistorySnapshot(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        try:
            workspace = resolve_workspace(context_id, context_loader=self.use_context)
            snapshot = TimeTravelService(workspace).snapshot(
                trigger=str(input.get("trigger") or "manual"),
                message=str(input.get("message") or ""),
                metadata=input.get("metadata") if isinstance(input.get("metadata"), dict) else {},
                changed_path_hints=input.get("changed_path_hints") if isinstance(input.get("changed_path_hints"), list) else None,
            )
            return {"ok": True, "snapshot": _snapshot_public(snapshot)}
        except WorkspaceRejectedError as exc:
            return {"ok": False, "locked": True, "error": str(exc)}
        except TimeTravelError as exc:
            return {"ok": False, "error": str(exc), "technical_details": getattr(exc, "stderr", "")}
