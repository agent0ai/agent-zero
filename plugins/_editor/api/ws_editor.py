from __future__ import annotations

from typing import Any

from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from plugins._editor.helpers import markdown_sessions
from plugins._office.helpers import document_store


class WsEditor(WsHandler):
    async def on_disconnect(self, sid: str) -> None:
        markdown_sessions.get_manager().close_sid(sid)

    async def process(self, event: str, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult | None:
        if not event.startswith("editor_"):
            return None
        try:
            if event == "editor_open":
                return self._open(data, sid)
            if event == "editor_input":
                return markdown_sessions.get_manager().input(
                    str(data.get("session_id") or ""),
                    text=data.get("text") if "text" in data else None,
                    patch=data.get("patch") if isinstance(data.get("patch"), dict) else None,
                )
            if event == "editor_save":
                return markdown_sessions.get_manager().save(
                    str(data.get("session_id") or ""),
                    text=data.get("text") if "text" in data else None,
                )
            if event == "editor_activate":
                return markdown_sessions.get_manager().activate(str(data.get("session_id") or ""))
            if event == "editor_close":
                return markdown_sessions.get_manager().close(str(data.get("session_id") or ""))
        except FileNotFoundError as exc:
            return WsResult.error(code="EDITOR_SESSION_NOT_FOUND", message=str(exc), correlation_id=data.get("correlationId"))
        except Exception as exc:
            return WsResult.error(code="EDITOR_ERROR", message=str(exc), correlation_id=data.get("correlationId"))

        return WsResult.error(
            code="UNKNOWN_EDITOR_EVENT",
            message=f"Unknown editor event: {event}",
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
            fmt = str(data.get("format") or "md").lower().strip().lstrip(".")
            if fmt not in document_store.EDITOR_TEXT_EXTENSIONS:
                return WsResult.error(
                    code="UNSUPPORTED_EDITOR_DOCUMENT",
                    message=f"Editor can only create Markdown (.md) and text (.txt) documents, not .{fmt}.",
                    correlation_id=data.get("correlationId"),
                )
            doc = document_store.create_document(
                kind="document",
                title=str(data.get("title") or "Untitled"),
                fmt=fmt,
                content=str(data.get("content") or ""),
                context_id=context_id,
            )
        return markdown_sessions.get_manager().open(
            doc,
            sid=sid,
            context_id=context_id,
            refresh=data.get("refresh") is True,
        )
