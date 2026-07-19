from __future__ import annotations

from pathlib import Path
from typing import Any

from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from plugins._desktop.helpers import desktop_session
from plugins._office.helpers import document_store


class WsOffice(WsHandler):
    async def on_disconnect(self, sid: str) -> None:
        return None

    async def process(self, event: str, data: dict[str, Any], sid: str) -> dict[str, Any] | WsResult | None:
        if not event.startswith("office_"):
            return None
        try:
            if event == "office_open":
                return self._open(data, sid)
            if event in {"office_input", "office_save", "office_close"}:
                return {
                    "ok": False,
                    "error": "Office WebSocket editing is not available for text documents; use the Editor surface.",
                }
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
            fmt = str(data.get("format") or "odt").lower().strip().lstrip(".")
            if fmt not in desktop_session.OFFICIAL_EXTENSIONS:
                return WsResult.error(
                    code="UNSUPPORTED_OFFICE_DOCUMENT",
                    message=f"Office can only create LibreOffice formats, not .{fmt}.",
                    correlation_id=data.get("correlationId"),
                )
            doc = document_store.create_document(
                kind=str(data.get("kind") or "document"),
                title=str(data.get("title") or "Untitled"),
                fmt=fmt,
                content=str(data.get("content") or ""),
                context_id=context_id,
            )
        ext = str(doc.get("extension") or "").lower()
        if ext in document_store.EDITOR_TEXT_EXTENSIONS:
            return WsResult.error(
                code="UNSUPPORTED_OFFICE_DOCUMENT",
                message="Text documents use the Editor surface.",
                correlation_id=data.get("correlationId"),
            )
        if ext in desktop_session.OFFICIAL_EXTENSIONS:
            return {
                "ok": True,
                "requires_desktop": True,
                "file_id": doc["file_id"],
                "title": doc["basename"],
                "extension": doc["extension"],
                "path": doc["path"],
                "document": _public_doc(doc),
                "version": document_store.item_version(doc),
            }
        return WsResult.error(
            code="UNSUPPORTED_OFFICE_DOCUMENT",
            message=f".{ext} documents are not supported by LibreOffice.",
            correlation_id=data.get("correlationId"),
        )


def _public_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_id": doc["file_id"],
        "path": document_store.display_path(doc["path"]),
        "basename": doc["basename"],
        "title": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
        "exists": Path(doc["path"]).exists(),
    }
