from __future__ import annotations

from helpers.api import ApiHandler, Request, Response
from plugins._time_travel.helpers.time_travel import (
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    resolve_workspace,
)


class HistoryRevert(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        context_id = str(input.get("context_id") or "").strip()
        try:
            workspace = resolve_workspace(context_id, context_loader=self.use_context)
            return TimeTravelService(workspace).revert(
                commit_hash=str(input.get("commit_hash") or ""),
                metadata=input.get("metadata") if isinstance(input.get("metadata"), dict) else {},
            )
        except WorkspaceRejectedError as exc:
            return {"ok": False, "locked": True, "error": str(exc)}
        except TimeTravelError as exc:
            details = getattr(exc, "stderr", "") or str(exc)
            return {"ok": False, "error": _human_conflict_summary(str(exc)), "technical_details": details}


def _human_conflict_summary(message: str) -> str:
    text = str(message or "").strip()
    if not text:
        return "Revert could not be applied cleanly."
    first = text.splitlines()[0]
    if "does not match index" in text or "patch failed" in text.lower() or "error:" in text.lower():
        return "Revert could not be applied cleanly because the current workspace has conflicting changes."
    return first
