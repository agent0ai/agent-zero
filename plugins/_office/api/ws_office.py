from __future__ import annotations

from typing import Any

from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from plugins._office.helpers import document_store, markdown_sessions


class WsOffice(WsHandler):
    async def on_disconnect(self, sid: str) -> None:
        markdown_sessions.get_manager().close_sid(sid)

    async def process(self, event: str, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult | None:
        if not event.startswith("office_"):
            return None
        try:
            if event == "office_open":
                return self._open(data, sid)
            if event == "office_input":
                return markdown_sessions.get_manager().input(
                    str(data.get("session_id") or ""),
                    text=data.get("text") if "text" in data else None,
                    patch=data.get("patch") if isinstance(data.get("patch"), dict) else None,
                )
            if event == "office_save":
                return markdown_sessions.get_manager().save(
                    str(data.get("session_id") or ""),
                    text=data.get("text") if "text" in data else None,
                )
            if event == "office_close":
                return markdown_sessions.get_manager().close(str(data.get("session_id") or ""))
        except FileNotFoundError as exc:
            return WsResult.error(code="OFFICE_SESSION_NOT_FOUND", message=str(exc), correlation_id=data.get("correlationId"))
        except Exception as exc:
            return WsResult.error(code="OFFICE_ERROR", message=str(exc), correlation_id=data.get("correlationId"))

        return WsResult.error(
            code="UNKNOWN_OFFICE_EVENT",
            message=f"Unknown office event: {event}",
            correlation_id=data.get("correlationId"),
        )

    def _open(self, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult:
        context_id = str(data.get("ctxid") or data.get("context_id") or "")
        file_id = str(data.get("file_id") or "").strip()
        path = str(data.get("path") or "").strip()
        if file_id:
            doc = document_store.get_document(file_id)
        elif path:
            doc = document_store.register_document(path, context_id=context_id)
        else:
            doc = document_store.create_document(
                kind=str(data.get("kind") or "document"),
                title=str(data.get("title") or "Untitled"),
                fmt=str(data.get("format") or "md"),
                content=str(data.get("content") or ""),
                context_id=context_id,
            )
        return markdown_sessions.get_manager().open(doc, sid=sid)
