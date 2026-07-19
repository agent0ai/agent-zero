from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._desktop.helpers import desktop_session
from plugins._office.helpers import document_store, markdown_sessions
from plugins._office.helpers import libreoffice


class DesktopSession(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        action = str(input.get("action") or "desktop").lower().strip()

        if action == "status":
            return desktop_session.collect_desktop_status()
        if action in {"desktop", "open", "session"}:
            return self._desktop()
        if action in {"open_document", "document"}:
            return self._open_document(input, request)
        if action in {"save", "desktop_save"}:
            return self._save(input)
        if action in {"sync", "desktop_sync", "heartbeat"}:
            return self._sync(input)
        if action in {"state", "desktop_state"}:
            return self._state(input)
        if action in {"shutdown", "desktop_shutdown"}:
            return self._shutdown(input)
        return {"ok": False, "error": f"Unsupported desktop session action: {action}"}

    def _desktop(self) -> dict:
        desktop = desktop_session.get_manager().ensure_system_desktop()
        if not desktop.get("available"):
            return {
                "ok": False,
                "error": desktop.get("error") or "Desktop session is unavailable.",
                "status": desktop.get("status") or {},
                "desktop": desktop,
                "libreoffice": libreoffice.collect_status(),
            }
        document = {
            "file_id": desktop_session.SYSTEM_FILE_ID,
            "path": desktop["path"],
            "basename": desktop["title"],
            "title": desktop["title"],
            "extension": "desktop",
            "size": 0,
            "version": 0,
        }
        return {
            "ok": True,
            "session_id": desktop["session_id"],
            "desktop_session_id": desktop["session_id"],
            "file_id": desktop_session.SYSTEM_FILE_ID,
            "title": desktop["title"],
            "extension": "desktop",
            "path": desktop["path"],
            "text": "",
            "document": document,
            "version": 0,
            "desktop": desktop,
            "store_session_id": "",
            "mode": "desktop",
        }

    def _open_document(self, input: dict, request: Request) -> dict:
        context_id = str(input.get("ctxid") or input.get("context_id") or "").strip()
        file_id = str(input.get("file_id") or "").strip()
        try:
            doc = (
                document_store.get_document(file_id)
                if file_id
                else document_store.register_document(str(input.get("path") or ""), context_id=context_id)
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        ext = str(doc.get("extension") or "").lower()
        if ext == "md":
            return self._open_markdown(doc, input, request)
        if ext not in desktop_session.OFFICIAL_EXTENSIONS:
            return {"ok": False, "error": f".{ext} documents do not use the Desktop surface."}

        store_session = document_store.create_session(
            doc["file_id"],
            user_id=str(input.get("user_id") or "agent-zero-user"),
            permission="write",
            origin=self._origin(request),
        )
        desktop = desktop_session.get_manager().open(doc, refresh=input.get("refresh") is True)
        if not desktop.get("available"):
            document_store.close_session(session_id=store_session["session_id"])
            return {
                "ok": False,
                "error": desktop.get("error") or desktop.get("reason") or "Desktop session is unavailable.",
                "desktop": desktop,
                "libreoffice": libreoffice.collect_status(),
            }
        return {
            "ok": True,
            "session_id": desktop["session_id"],
            "desktop_session_id": desktop["session_id"],
            "file_id": doc["file_id"],
            "title": doc["basename"],
            "extension": doc["extension"],
            "path": doc["path"],
            "text": "",
            "document": _public_doc(doc),
            "version": document_store.item_version(doc),
            "desktop": desktop,
            "store_session_id": store_session["session_id"],
            "mode": "edit",
        }

    def _open_markdown(self, doc: dict, input: dict, request: Request) -> dict:
        mode = "edit" if str(input.get("mode") or "edit").lower() == "edit" else "view"
        store_session = document_store.create_session(
            doc["file_id"],
            user_id=str(input.get("user_id") or "agent-zero-user"),
            permission="write" if mode == "edit" else "read",
            origin=self._origin(request),
        )
        try:
            editor = markdown_sessions.get_manager().open(doc, sid="")
        except ValueError as exc:
            document_store.close_session(session_id=store_session["session_id"])
            return {"ok": False, "error": str(exc)}
        return {
            **editor,
            "store_session_id": store_session["session_id"],
            "session_id": editor["session_id"],
            "mode": mode,
        }

    def _save(self, input: dict) -> dict:
        session_id = str(input.get("desktop_session_id") or input.get("session_id") or "").strip()
        if not session_id:
            return {"ok": False, "error": "desktop_session_id is required."}
        return desktop_session.get_manager().save(
            session_id,
            file_id=str(input.get("file_id") or ""),
        )

    def _sync(self, input: dict) -> dict:
        return desktop_session.get_manager().sync(
            session_id=str(input.get("desktop_session_id") or input.get("session_id") or ""),
            file_id=str(input.get("file_id") or ""),
        )

    def _state(self, input: dict) -> dict:
        return desktop_session.get_manager().state(
            include_screenshot=bool(input.get("include_screenshot") is True),
            context_id=str(input.get("ctxid") or input.get("context_id") or ""),
        )

    def _shutdown(self, input: dict) -> dict:
        return desktop_session.get_manager().shutdown_system_desktop(
            save_first=input.get("save_first") is not False,
            source=str(input.get("source") or "api"),
        )

    def _origin(self, request: Request) -> str:
        origin = request.headers.get("Origin") or request.host_url.rstrip("/")
        return origin.rstrip("/")


def _public_doc(doc: dict) -> dict:
    return {
        "file_id": doc["file_id"],
        "path": document_store.display_path(doc["path"]),
        "basename": doc["basename"],
        "title": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
    }
