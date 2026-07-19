from __future__ import annotations

from helpers.api import ApiHandler, Request
from plugins._desktop.helpers import desktop_session
from plugins._office.helpers import document_store, libreoffice


class OfficeSession(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict:
        action = str(input.get("action") or "open").lower().strip()
        context_id = str(input.get("ctxid") or input.get("context_id") or "").strip()

        if action == "status":
            return libreoffice.collect_status()
        if action == "home":
            return {"ok": True, "path": document_store.default_open_path(context_id)}
        if action == "close":
            closed = document_store.close_session(
                session_id=str(input.get("session_id") or ""),
                file_id=str(input.get("file_id") or ""),
            )
            return {"ok": True, "closed": closed}
        if action == "create":
            fmt = str(input.get("format") or "odt").lower().strip().lstrip(".")
            if fmt not in desktop_session.OFFICIAL_EXTENSIONS:
                return {"ok": False, "error": f"Office can only create LibreOffice formats, not .{fmt}."}
            try:
                doc = document_store.create_document(
                    kind=str(input.get("kind") or "document"),
                    title=str(input.get("title") or "Untitled"),
                    fmt=fmt,
                    content=str(input.get("content") or ""),
                    path=str(input.get("path") or ""),
                    context_id=context_id,
                )
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            if doc["extension"] in {"odt", "ods", "odp"}:
                validation = libreoffice.validate_odf(doc["path"])
                if not validation.get("ok"):
                    return {"ok": False, "error": validation.get("error") or "ODF validation failed."}
            if doc["extension"] == "docx":
                validation = libreoffice.validate_docx(doc["path"])
                if not validation.get("ok"):
                    return {"ok": False, "error": validation.get("error") or "DOCX validation failed."}
            return await self._open_document(doc, input, request)
        if action == "open":
            file_id = str(input.get("file_id") or "").strip()
            try:
                doc = (
                    document_store.get_document(file_id)
                    if file_id
                    else document_store.register_document(str(input.get("path") or ""), context_id=context_id)
                )
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}
            return await self._open_document(doc, input, request)
        if action == "save":
            return self._save(input)
        if action == "renamed":
            return self._renamed(input, context_id)
        return {"ok": False, "error": f"Unsupported office session action: {action}"}

    async def _open_document(self, doc: dict, input: dict, request: Request) -> dict:
        mode = "edit" if str(input.get("mode") or "edit").lower() == "edit" else "view"
        if str(doc.get("extension") or "").lower() in document_store.EDITOR_TEXT_EXTENSIONS:
            return {
                "ok": False,
                "error": "Text documents use the Editor surface.",
                "document": _public_doc(doc),
            }
        if str(doc.get("extension") or "").lower() in desktop_session.OFFICIAL_EXTENSIONS:
            if input.get("open_in_desktop") is not True:
                return {
                    "ok": True,
                    "requires_desktop": True,
                    "file_id": doc["file_id"],
                    "title": doc["basename"],
                    "extension": doc["extension"],
                    "path": doc["path"],
                    "text": "",
                    "document": _public_doc(doc),
                    "version": document_store.item_version(doc),
                    "mode": mode,
                }
            store_session = document_store.create_session(
                doc["file_id"],
                user_id=str(input.get("user_id") or "agent-zero-user"),
                permission="write" if mode == "edit" else "read",
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
                "mode": mode,
            }
        return {"ok": False, "error": f".{doc.get('extension', '')} documents are not supported by LibreOffice."}

    def _save(self, input: dict) -> dict:
        return {"ok": False, "error": "Text document saves use /plugins/_editor/editor_session."}

    def _renamed(self, input: dict, context_id: str = "") -> dict:
        file_id = str(input.get("file_id") or "").strip()
        path = str(input.get("path") or "").strip()
        if not file_id:
            return {"ok": False, "error": "file_id is required."}
        if not path:
            return {"ok": False, "error": "path is required."}
        try:
            updated = document_store.rename_document(
                file_id,
                path,
                content=input.get("text") if "text" in input else None,
                context_id=context_id,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        desktop = None
        if str(updated.get("extension") or "").lower() in desktop_session.OFFICIAL_EXTENSIONS:
            desktop = desktop_session.get_manager().retarget_document(file_id, updated)
        return {
            "ok": True,
            "document": _public_doc(updated),
            "version": document_store.item_version(updated),
            "desktop": desktop,
            "refreshFiles": False,
        }

    def _origin(self, request: Request) -> str:
        origin = request.headers.get("Origin") or request.host_url.rstrip("/")
        return origin.rstrip("/")


def _public_doc(doc: dict) -> dict:
    result = {
        "file_id": doc["file_id"],
        "path": document_store.display_path(doc["path"]),
        "basename": doc["basename"],
        "title": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
    }
    for key in ("open_sessions", "last_opened_at", "session_expires_at"):
        if key in doc:
            result[key] = doc[key]
    return result
