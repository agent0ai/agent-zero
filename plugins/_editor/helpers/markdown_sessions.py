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
    context_id: str
    extension: str
    path: str
    title: str
    text: str = ""
    dirty: bool = False
    active: bool = False
    base_sha256: str = ""
    base_version: str = ""
    external_modified: bool = False
    external_version: str = ""
    opened_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)


class MarkdownSessionManager:
    """Owns native Editor sessions for Markdown and plain text documents."""

    def __init__(self) -> None:
        self._sessions: dict[str, MarkdownSession] = {}
        self._active_by_context: dict[str, str] = {}

    def open(self, doc: dict[str, Any], sid: str = "", context_id: str = "", refresh: bool = False) -> dict[str, Any]:
        ext = str(doc["extension"]).lower()
        if ext not in document_store.EDITOR_TEXT_EXTENSIONS:
            raise ValueError(f"Editor is only available for Markdown and text files. Open .{ext} files in the Desktop.")

        normalized_context = str(context_id or "")
        if refresh:
            try:
                doc = document_store.register_document(doc["path"], context_id=normalized_context)
            except Exception:
                pass

        for session in self._sessions.values():
            if session.file_id != doc["file_id"] or session.context_id != normalized_context:
                continue
            if sid:
                session.sid = sid
            doc_sha = str(doc.get("sha256") or "")
            should_reload = not session.dirty and (refresh or (doc_sha and doc_sha != session.base_sha256))
            if should_reload:
                session.text = document_store.read_text_for_editor(doc)
                session.dirty = False
                _set_session_base(session, doc)
            elif session.dirty and doc_sha and doc_sha != session.base_sha256:
                _mark_session_external(session, doc)
            session.path = doc["path"]
            session.title = doc["basename"]
            session.extension = ext
            session.updated_at = time.time()
            self.activate(session.session_id)
            return self._payload(session, doc)

        session = MarkdownSession(
            session_id=uuid.uuid4().hex,
            file_id=doc["file_id"],
            sid=sid,
            context_id=normalized_context,
            extension=ext,
            path=doc["path"],
            title=doc["basename"],
            text=document_store.read_text_for_editor(doc),
        )
        _set_session_base(session, doc)
        self._sessions[session.session_id] = session
        self.activate(session.session_id)
        return self._payload(session, doc)

    def input(self, session_id: str, text: str | None = None, patch: dict[str, Any] | None = None) -> dict[str, Any]:
        session = self._require(session_id)
        if text is not None:
            session.text = str(text)
        elif patch:
            session.text = _apply_text_patch(session.text, patch)
        session.dirty = True
        session.updated_at = time.time()
        self.activate(session.session_id)
        return {"ok": True, "session_id": session.session_id}

    def save(self, session_id: str, text: str | None = None) -> dict[str, Any]:
        session = self._require(session_id)
        if text is not None:
            session.text = str(text)

        conflict = self._save_conflict(session)
        if conflict is not None:
            return conflict

        updated = document_store.write_text_document(session.file_id, session.text)
        session.updated_at = time.time()
        session.dirty = False
        session.path = updated["path"]
        session.title = updated["basename"]
        session.extension = str(updated.get("extension") or session.extension).lower()
        _set_session_base(session, updated)
        self._refresh_file_sessions(
            updated,
            text=session.text,
            dirty=False,
            source_session_id=session.session_id,
        )
        return {
            "ok": True,
            "document": _public_doc(updated),
            "version": document_store.item_version(updated),
        }

    def save_as(self, session_id: str, path: str, text: str | None = None) -> dict[str, Any]:
        session = self._require(session_id)
        if text is not None:
            session.text = str(text)

        updated = document_store.save_text_document_as(
            session.file_id,
            path,
            session.text,
            context_id=session.context_id,
        )
        old_file_id = session.file_id
        session.file_id = updated["file_id"]
        session.updated_at = time.time()
        session.dirty = False
        session.path = updated["path"]
        session.title = updated["basename"]
        session.extension = str(updated.get("extension") or session.extension).lower()
        _set_session_base(session, updated)
        return {
            "ok": True,
            "previous_file_id": old_file_id,
            "document": _public_doc(updated),
            "version": document_store.item_version(updated),
        }

    def activate(self, session_id: str) -> dict[str, Any]:
        session = self._require(session_id)
        now = time.time()
        previous_id = self._active_by_context.get(session.context_id)
        if previous_id and previous_id in self._sessions:
            self._sessions[previous_id].active = False
        session.active = True
        session.last_active_at = now
        session.updated_at = now
        self._active_by_context[session.context_id] = session.session_id
        return {"ok": True, "session_id": session.session_id}

    def renamed(self, file_id: str, doc: dict[str, Any], text: str | None = None) -> dict[str, Any]:
        updated = self._refresh_file_sessions(doc, text=text, dirty=False, refresh_dirty=True)
        return {"ok": True, "updated": updated, "file_id": file_id}

    def refresh_document(self, file_id: str) -> dict[str, Any]:
        normalized = str(file_id or "").strip()
        if not normalized:
            return {"ok": True, "refreshed": 0, "sessions": []}
        try:
            doc = document_store.get_document(normalized)
        except Exception:
            return {"ok": False, "refreshed": 0, "sessions": []}
        if str(doc.get("extension") or "").lower() not in document_store.EDITOR_TEXT_EXTENSIONS:
            return {"ok": True, "refreshed": 0, "sessions": []}

        refreshed = self._refresh_file_sessions(
            doc,
            text=document_store.read_text_for_editor(doc),
            dirty=False,
        )
        return {"ok": True, "refreshed": len(refreshed), "sessions": refreshed}

    def sync_external_file_mutations(self, paths: list[str] | tuple[str, ...] | str, context_id: str = "") -> dict[str, Any]:
        raw_paths = [paths] if isinstance(paths, str) else list(paths or [])
        normalized_paths = [str(path or "").strip() for path in raw_paths if str(path or "").strip()]
        if not normalized_paths:
            return {"ok": True, "matched": 0, "sessions": []}

        matched_file_ids: set[str] = set()
        matched_sessions: list[str] = []
        for session in list(self._sessions.values()):
            if not any(_paths_match(path, session.path, session.context_id) for path in normalized_paths):
                continue
            matched_file_ids.add(session.file_id)
            matched_sessions.append(session.session_id)

        for file_id in matched_file_ids:
            sessions = [session for session in self._sessions.values() if session.file_id == file_id]
            if not sessions:
                continue
            session = sessions[0]
            try:
                doc = document_store.register_document(session.path, context_id=session.context_id)
            except Exception:
                try:
                    doc = document_store.get_document(file_id)
                except Exception:
                    continue
                for target in sessions:
                    _mark_session_external(target, doc)
                continue
            self.refresh_document(file_id)

        return {
            "ok": True,
            "matched": len(matched_file_ids),
            "sessions": matched_sessions,
        }

    def list_open(self, context_id: str = "", limit: int = 20) -> list[dict[str, Any]]:
        context_id = str(context_id or "")
        sessions = [session for session in self._sessions.values() if session.context_id == context_id]
        sessions.sort(key=lambda item: (not item.active, -item.last_active_at, -item.updated_at))

        grouped: dict[str, MarkdownSession] = {}
        counts: dict[str, int] = {}
        for session in sessions:
            key = session.file_id or session.path
            counts[key] = counts.get(key, 0) + 1
            current = grouped.get(key)
            if current is None or session.active or session.last_active_at > current.last_active_at:
                grouped[key] = session

        result = []
        for session in grouped.values():
            try:
                doc = document_store.get_document(session.file_id)
                version = document_store.item_version(doc)
                size = doc.get("size", 0)
                last_modified = doc.get("last_modified", "")
                path = document_store.display_path(doc.get("path", session.path))
                title = doc.get("basename") or session.title
            except Exception:
                version = ""
                size = 0
                last_modified = ""
                path = document_store.display_path(session.path)
                title = session.title
            result.append({
                "session_id": session.session_id,
                "file_id": session.file_id,
                "title": title,
                "extension": session.extension,
                "path": path,
                "version": version,
                "size": size,
                "last_modified": last_modified,
                "dirty": session.dirty,
                "active": session.active,
                "external_modified": session.external_modified,
                "external_version": session.external_version,
                "open_sessions": counts.get(session.file_id or session.path, 1),
                "last_active_at": session.last_active_at,
            })

        result.sort(key=lambda item: (not item["active"], -float(item["last_active_at"] or 0)))
        safe_limit = max(1, int(limit or 20))
        return result[:safe_limit]

    def close(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.pop(str(session_id or ""), None)
        if not session:
            return {"ok": True, "closed": 0}
        if self._active_by_context.get(session.context_id) == session.session_id:
            replacement = sorted(
                [item for item in self._sessions.values() if item.context_id == session.context_id],
                key=lambda item: item.last_active_at,
                reverse=True,
            )
            if replacement:
                self.activate(replacement[0].session_id)
            else:
                self._active_by_context.pop(session.context_id, None)
        return {"ok": True, "closed": 1, "session_id": session_id}

    def close_sid(self, sid: str) -> int:
        doomed = [session_id for session_id, session in self._sessions.items() if session.sid == sid]
        for session_id in doomed:
            self.close(session_id)
        return len(doomed)

    def _save_conflict(self, session: MarkdownSession) -> dict[str, Any] | None:
        try:
            doc = document_store.get_document(session.file_id)
        except Exception as exc:
            return {
                "ok": False,
                "code": "editor_document_missing",
                "error": f"Editor save failed because the document metadata is missing: {exc}",
            }

        path = Path(doc["path"])
        desired = str(session.text or "").encode("utf-8")
        desired_sha = document_store.sha256_bytes(desired)
        current_exists = path.exists()
        current = path.read_bytes() if current_exists else b""
        current_sha = document_store.sha256_bytes(current) if current_exists else ""
        expected_sha = session.base_sha256 or str(doc.get("sha256") or "")

        if expected_sha and current_sha != expected_sha:
            if current_exists and desired_sha == current_sha:
                updated = document_store.register_document(path, context_id=session.context_id)
                session.dirty = False
                session.path = updated["path"]
                session.title = updated["basename"]
                _set_session_base(session, updated)
                self._refresh_file_sessions(
                    updated,
                    text=session.text,
                    dirty=False,
                    source_session_id=session.session_id,
                )
                return {
                    "ok": True,
                    "document": _public_doc(updated),
                    "version": document_store.item_version(updated),
                }

            latest_doc = _refresh_registered_doc(doc, context_id=session.context_id)
            _mark_session_external(session, latest_doc)
            return {
                "ok": False,
                "code": "external_change_conflict",
                "error": (
                    "This file changed on disk since the Editor loaded it. "
                    "Reload it before saving to avoid overwriting the newer file."
                ),
                "document": _public_doc(latest_doc),
                "version": document_store.item_version(latest_doc),
            }

        return None

    def _refresh_file_sessions(
        self,
        doc: dict[str, Any],
        text: str | None = None,
        dirty: bool | None = None,
        *,
        source_session_id: str = "",
        refresh_dirty: bool = False,
    ) -> list[str]:
        file_id = str(doc.get("file_id") or "").strip()
        refreshed: list[str] = []
        for session in self._sessions.values():
            if session.file_id != file_id:
                continue
            can_replace_text = (
                text is not None
                and (
                    refresh_dirty
                    or not session.dirty
                    or (source_session_id and session.session_id == source_session_id)
                )
            )
            if can_replace_text:
                session.text = str(text)
            session.path = doc["path"]
            session.title = doc["basename"]
            session.extension = str(doc.get("extension") or session.extension).lower()
            if dirty is not None and (can_replace_text or refresh_dirty or not session.dirty):
                session.dirty = dirty
            if can_replace_text or not session.dirty:
                _set_session_base(session, doc)
            elif text is not None:
                _mark_session_external(session, doc)
            session.updated_at = time.time()
            refreshed.append(session.session_id)
        return refreshed

    def _payload(self, session: MarkdownSession, doc: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "session_id": session.session_id,
            "file_id": session.file_id,
            "title": session.title,
            "extension": session.extension,
            "path": session.path,
            "text": session.text,
            "dirty": session.dirty,
            "active": session.active,
            "external_modified": session.external_modified,
            "external_version": session.external_version,
            "context_id": session.context_id,
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
        "title": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
        "exists": Path(doc["path"]).exists(),
    }


def _set_session_base(session: MarkdownSession, doc: dict[str, Any]) -> None:
    session.base_sha256 = str(doc.get("sha256") or "")
    session.base_version = document_store.item_version(doc)
    session.external_modified = False
    session.external_version = ""


def _mark_session_external(session: MarkdownSession, doc: dict[str, Any]) -> None:
    session.external_modified = True
    try:
        session.external_version = document_store.item_version(doc)
    except Exception:
        session.external_version = ""


def _refresh_registered_doc(doc: dict[str, Any], context_id: str = "") -> dict[str, Any]:
    try:
        path = Path(doc["path"])
        if path.exists():
            return document_store.register_document(path, context_id=context_id)
    except Exception:
        pass
    return doc


def _paths_match(left: str, right: str, context_id: str = "") -> bool:
    left_path = _normalize_path_for_compare(left, context_id=context_id)
    right_path = _normalize_path_for_compare(right, context_id=context_id)
    return bool(left_path and right_path and left_path == right_path)


def _normalize_path_for_compare(path: str, context_id: str = "") -> str:
    value = str(path or "").strip()
    if not value:
        return ""
    try:
        return str(document_store.normalize_path(value, context_id=context_id))
    except Exception:
        pass
    try:
        return str(document_store._path_from_a0(value).resolve(strict=False))
    except Exception:
        return str(Path(value).expanduser().resolve(strict=False))


def _apply_text_patch(text: str, patch: dict[str, Any]) -> str:
    if "content" in patch:
        return str(patch.get("content") or "")
    start = int(patch.get("start") or 0)
    end = int(patch.get("end") if patch.get("end") is not None else start)
    replacement = str(patch.get("text") or "")
    start = max(0, min(len(text), start))
    end = max(start, min(len(text), end))
    return text[:start] + replacement + text[end:]
