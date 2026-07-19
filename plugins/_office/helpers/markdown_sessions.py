from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from plugins._office.helpers import document_store


@dataclass
class MarkdownSession:
    session_id: str
    file_id: str
    sid: str
    extension: str
    path: str
    title: str
    text: str = ""
    opened_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class MarkdownSessionManager:
    """Owns source-editor sessions for Markdown documents."""

    def __init__(self) -> None:
        self._sessions: dict[str, MarkdownSession] = {}

    def open(self, doc: dict[str, Any], sid: str = "") -> dict[str, Any]:
        ext = str(doc["extension"]).lower()
        if ext != "md":
            raise ValueError(f"Canvas editing is only available for Markdown. Open .{ext} files in the Desktop.")

        session = MarkdownSession(
            session_id=uuid.uuid4().hex,
            file_id=doc["file_id"],
            sid=sid,
            extension=ext,
            path=doc["path"],
            title=doc["basename"],
            text=document_store.read_text_for_editor(doc),
        )
        self._sessions[session.session_id] = session
        return self._payload(session, doc)

    def input(self, session_id: str, text: str | None = None, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        session = self._require(session_id)
        if text is not None:
            session.text = str(text)
        elif patch:
            session.text = _apply_text_patch(session.text, patch)
        session.updated_at = time.time()
        return {"ok": True, "session_id": session.session_id}

    def save(self, session_id: str, text: str | None = None) -> dict[str, Any]:
        session = self._require(session_id)
        if text is not None:
            session.text = str(text)

        updated = document_store.write_markdown(session.file_id, session.text)
        session.updated_at = time.time()
        session.path = updated["path"]
        session.title = updated["basename"]
        return {
            "ok": True,
            "document": _public_doc(updated),
            "version": document_store.item_version(updated),
        }

    def refresh_document(self, file_id: str) -> dict[str, Any]:
        normalized = str(file_id or "").strip()
        if not normalized:
            return {"ok": True, "refreshed": 0, "sessions": []}
        try:
            doc = document_store.get_document(normalized)
        except Exception:
            return {"ok": False, "refreshed": 0, "sessions": []}
        if str(doc.get("extension") or "").lower() != "md":
            return {"ok": True, "refreshed": 0, "sessions": []}

        refreshed: list[str] = []
        for session in self._sessions.values():
            if session.file_id != normalized:
                continue
            session.text = document_store.read_text_for_editor(doc)
            session.path = doc["path"]
            session.title = doc["basename"]
            session.updated_at = time.time()
            refreshed.append(session.session_id)
        return {"ok": True, "refreshed": len(refreshed), "sessions": refreshed}

    def close(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.pop(str(session_id or ""), None)
        if not session:
            return {"ok": True, "closed": 0}
        return {"ok": True, "closed": 1, "session_id": session_id}

    def close_sid(self, sid: str) -> int:
        doomed = [session_id for session_id, session in self._sessions.items() if session.sid == sid]
        for session_id in doomed:
            self._sessions.pop(session_id, None)
        return len(doomed)

    def _payload(self, session: MarkdownSession, doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "session_id": session.session_id,
            "file_id": session.file_id,
            "title": session.title,
            "extension": session.extension,
            "path": session.path,
            "text": session.text,
            "document": _public_doc(doc),
            "version": document_store.item_version(doc),
        }

    def _require(self, session_id: str) -> MarkdownSession:
        normalized = str(session_id or "").strip()
        session = self._sessions.get(normalized)
        if not session:
            raise FileNotFoundError(f"Editor session not found: {normalized}")
        return session


def get_manager() -> MarkdownSessionManager:
    global _manager
    try:
        return _manager
    except NameError:
        _manager = MarkdownSessionManager()
        return _manager


def _public_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_id": doc["file_id"],
        "path": document_store.display_path(doc["path"]),
        "basename": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
        "exists": Path(doc["path"]).exists(),
    }


def _apply_text_patch(text: str, patch: dict[str, Any]) -> str:
    if "content" in patch:
        return str(patch.get("content") or "")
    start = int(patch.get("start") or 0)
    end = int(patch.get("end") if patch.get("end") is not None else start)
    replacement = str(patch.get("text") or "")
    start = max(0, min(len(text), start))
    end = max(start, min(len(text), end))
    return text[:start] + replacement + text[end:]
