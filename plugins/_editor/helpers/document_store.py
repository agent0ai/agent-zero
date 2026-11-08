from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import threading
import sqlite3
import stat
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from helpers import files
from helpers.file_browser import FileBrowser
from helpers.localization import Localization


# Retain the existing database and backups so upgrades preserve document history.
PLUGIN_NAME = "_office"
OPEN_DOCUMENT_EXTENSIONS = {"odt", "ods", "odp"}
OOXML_EXTENSIONS = {"docx", "xlsx", "pptx"}
EDITOR_TEXT_EXTENSIONS = {"md", "txt"}
SUPPORTED_EXTENSIONS = EDITOR_TEXT_EXTENSIONS
DEFAULT_TTL_SECONDS = 8 * 60 * 60
MAX_SAVE_BYTES = 512 * 1024 * 1024
STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME, "documents"))
DB_PATH = STATE_DIR / "documents.sqlite3"
BACKUP_DIR = STATE_DIR / "backups"
LEGACY_STATE_DIRS = [Path(files.get_abs_path('usr', *parts, 'documents'))
                     for parts in [('_office',), ('state', '_office'), ('state', 'office')]]
_migration_lock = threading.Lock()
WORKDIR = Path(files.get_abs_path("usr", "workdir"))
DOCUMENTS_DIR = WORKDIR / "documents"


def now() -> float:
    return time.time()


def now_iso() -> str:
    return Localization.get().now_iso(timespec="seconds")


def ensure_dirs() -> None:
    with _migration_lock:
        if not STATE_DIR.exists():
            for source in LEGACY_STATE_DIRS:
                if not source.is_dir():
                    continue
                STATE_DIR.parent.mkdir(parents=True, exist_ok=True)
                # Publish only a complete copy; never remove the legacy source.
                with tempfile.TemporaryDirectory(dir=STATE_DIR.parent) as staging:
                    copied = Path(staging) / 'documents'
                    shutil.copytree(source, copied, symlinks=True)
                    copied.rename(STATE_DIR)
                break
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    if BACKUP_DIR.stat().st_uid != os.geteuid():
        os.chown(BACKUP_DIR, os.geteuid(), -1)
    BACKUP_DIR.chmod(0o700)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_title(title: str, fallback: str = "Document") -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in title).strip(" ._")
    return cleaned or fallback


def normalize_extension(value: str) -> str:
    ext = value.lower().strip().lstrip(".")
    if not ext:
        ext = "md"
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document format: {ext}")
    return ext


def document_home(context_id: str = "") -> Path:
    context_id = str(context_id or "").strip()
    if context_id:
        try:
            from agent import AgentContext

            context = AgentContext.get(context_id)
            project_helpers = _projects()
            project_name = project_helpers.get_context_project_name(context) if context else None
            if project_name:
                return Path(project_helpers.get_project_folder(project_name)).resolve(strict=False)
        except Exception:
            pass

    configured = str(_settings().get_settings().get("workdir_path") or "").strip()
    if configured:
        return _path_from_a0(configured).resolve(strict=False)
    return WORKDIR.resolve(strict=False)


def document_binary_home(context_id: str = "") -> Path:
    if str(context_id or "").strip():
        return document_home(context_id) / "documents"
    return DOCUMENTS_DIR.resolve(strict=False)


def default_open_path(context_id: str = "") -> str:
    return display_path(document_home(context_id))


def display_path(path: str | Path) -> str:
    resolved = Path(path).resolve(strict=False)
    base = Path(files.get_base_dir()).resolve(strict=False)
    if str(base).startswith("/a0"):
        return str(resolved)
    try:
        return "/a0/" + str(resolved.relative_to(base)).lstrip("/")
    except ValueError:
        return str(path)


def _path_from_a0(path: str | Path) -> Path:
    raw = str(path)
    if raw.startswith("/a0/") and not files.get_base_dir().startswith("/a0"):
        raw = files.get_abs_path(raw.removeprefix("/a0/"))
    return Path(raw if os.path.isabs(raw) else files.get_abs_path(raw)).expanduser()


def allowed_roots(context_id: str = "", allow_base_dir: bool = False) -> list[Path]:
    project_helpers = _projects()
    roots = {
        WORKDIR.resolve(strict=False),
        DOCUMENTS_DIR.resolve(strict=False),
        Path(project_helpers.get_projects_parent_folder()).resolve(strict=False),
        document_home(context_id).resolve(strict=False),
        document_binary_home(context_id).resolve(strict=False),
    }
    configured = str(_settings().get_settings().get("workdir_path") or "").strip()
    if configured:
        roots.add(_path_from_a0(configured).resolve(strict=False))
    if allow_base_dir:
        roots.add(Path(files.get_base_dir()).resolve(strict=False))
    return sorted(roots, key=lambda item: str(item))


def _projects() -> Any:
    from helpers import projects

    return projects


def _settings() -> Any:
    from helpers import settings

    return settings


def normalize_path(path: str | Path, context_id: str = "", allow_base_dir: bool = False, file_browser: bool = False) -> Path:
    candidate = _path_from_a0(path)
    resolved = candidate.resolve(strict=False)
    roots = [Path("/")] if file_browser else allowed_roots(context_id, allow_base_dir=allow_base_dir)
    if not any(_is_relative_to(resolved, root) for root in roots):
        raise PermissionError("Document artifacts must stay inside the active project or workdir.")
    if candidate.exists():
        real = candidate.resolve(strict=True)
        if not any(_is_relative_to(real, root) for root in roots):
            raise PermissionError("Document artifact symlink escapes the active project or workdir.")
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        os.path.commonpath([str(path), str(root)])
    except ValueError:
        return False
    return os.path.commonpath([str(path), str(root)]) == str(root)


@contextmanager
def connect() -> Any:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS documents (
            file_id TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            basename TEXT NOT NULL,
            extension TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            size INTEGER NOT NULL,
            version INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            permission TEXT NOT NULL,
            origin TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            version TEXT NOT NULL,
            path TEXT NOT NULL,
            size INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            event_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        """
    )


def register_document(
    path: str | Path,
    owner_id: str = "a0",
    context_id: str = "",
    allow_base_dir: bool = False,
    file_browser: bool = False,
) -> dict[str, Any]:
    resolved = normalize_path(path, context_id=context_id, allow_base_dir=allow_base_dir, file_browser=file_browser)
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))
    ext = resolved.suffix.lstrip(".").lower()
    if is_editor_document({"extension": ext}):
        read_text_for_editor({"path": str(resolved), "extension": ext})
    data = resolved.read_bytes()
    digest = sha256_bytes(data)
    stat = resolved.stat()
    current_time = now()
    with connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE path = ?", (str(resolved),)).fetchone()
        if row:
            conn.execute(
                """
                UPDATE documents
                SET basename=?, extension=?, size=?, sha256=?, last_modified=?, updated_at=?
                WHERE file_id=?
                """,
                (resolved.name, ext, stat.st_size, digest, now_iso(), current_time, row["file_id"]),
            )
            return get_document(row["file_id"], conn=conn)

        file_id = uuid.uuid4().hex
        conn.execute(
            """
            INSERT INTO documents
            (file_id, path, basename, extension, owner_id, size, version, sha256, last_modified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, str(resolved), resolved.name, ext, owner_id, stat.st_size, 1, digest, now_iso(), current_time, current_time),
        )
        _record_version(conn, file_id, resolved, "1", data)
        return get_document(file_id, conn=conn)


def get_document(file_id: str, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    def _fetch(active: sqlite3.Connection) -> dict[str, Any]:
        row = active.execute("SELECT * FROM documents WHERE file_id = ?", (file_id,)).fetchone()
        if not row:
            raise FileNotFoundError(file_id)
        return dict(row)

    if conn is not None:
        return _fetch(conn)
    with connect() as active:
        return _fetch(active)


def update_document_path(file_id: str, path: str | Path, context_id: str = "") -> dict[str, Any]:
    resolved = normalize_path(path, context_id=context_id)
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))
    ext = resolved.suffix.lstrip(".").lower()
    if is_editor_document({"extension": ext}):
        read_text_for_editor({"path": str(resolved), "extension": ext})
    data = resolved.read_bytes()
    digest = sha256_bytes(data)
    stat = resolved.stat()
    changed_at = now()

    with connect() as conn:
        doc = get_document(file_id, conn=conn)
        row = conn.execute("SELECT file_id FROM documents WHERE path = ?", (str(resolved),)).fetchone()
        if row and row["file_id"] != file_id:
            raise ValueError(f"Document path is already registered: {display_path(resolved)}")
        conn.execute(
            """
            UPDATE documents
            SET path=?, basename=?, extension=?, size=?, sha256=?, last_modified=?, updated_at=?
            WHERE file_id=?
            """,
            (str(resolved), resolved.name, ext, stat.st_size, digest, now_iso(), changed_at, file_id),
        )
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                file_id,
                "renamed",
                json.dumps({"from": display_path(doc["path"]), "to": display_path(resolved)}),
                changed_at,
            ),
        )
        return get_document(file_id, conn=conn)


def rename_document(
    file_id: str,
    path: str | Path,
    content: str | None = None,
    context_id: str = "",
    file_browser: bool = False,
) -> dict[str, Any]:
    resolved = normalize_path(path, context_id=context_id, file_browser=file_browser)
    ext = resolved.suffix.lstrip(".").lower()
    data = None
    if content is not None:
        if not is_editor_document({"extension": ext}):
            raise ValueError("Inline content can only be provided for Editor text documents.")
        data = editor_text_bytes(str(content or ""))

    changed_at = now()
    with connect() as conn:
        doc = get_document(file_id, conn=conn)
        source = Path(doc["path"])
        source_resolved = source.resolve(strict=False)
        changed_path = str(source_resolved) != str(resolved)
        source_exists = source.exists()

        if ext != str(doc["extension"]).lower():
            raise ValueError("Document extension cannot change during rename.")

        row = conn.execute("SELECT file_id FROM documents WHERE path = ?", (str(resolved),)).fetchone()
        if row and row["file_id"] != file_id:
            raise ValueError(f"Document path is already registered: {display_path(resolved)}")
        if changed_path and resolved.exists():
            raise FileExistsError(f"Target already exists: {display_path(resolved)}")
        if not source_exists and data is None:
            raise FileNotFoundError(str(source_resolved))

        previous = source.read_bytes() if source_exists else b""
        content_changed = data is not None and data != previous

        if changed_path and data is None:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            source.rename(resolved)
            final_data = resolved.read_bytes()
            content_changed = final_data != previous
            if content_changed:
                _record_version(conn, file_id, source_resolved, item_version(doc), previous)
        elif data is not None:
            if content_changed:
                _record_version(conn, file_id, source_resolved, item_version(doc), previous)
            _write_atomic(resolved, data, source=source)
            if changed_path and source_exists:
                source.unlink(missing_ok=True)
            final_data = data
        else:
            final_data = previous

        file_stat = resolved.stat()
        next_version = int(doc["version"]) + 1 if content_changed else int(doc["version"])
        conn.execute(
            """
            UPDATE documents
            SET path=?, basename=?, extension=?, size=?, version=?, sha256=?, last_modified=?, updated_at=?
            WHERE file_id=?
            """,
            (
                str(resolved),
                resolved.name,
                ext,
                file_stat.st_size,
                next_version,
                sha256_bytes(final_data),
                now_iso(),
                changed_at,
                file_id,
            ),
        )
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                file_id,
                "renamed",
                json.dumps(
                    {
                        "from": display_path(source_resolved),
                        "to": display_path(resolved),
                        "saved": content_changed,
                        "materialized": not source_exists,
                    }
                ),
                changed_at,
            ),
        )
        return get_document(file_id, conn=conn)


def get_open_documents(limit: int = 6) -> list[dict[str, Any]]:
    with connect() as conn:
        _clear_expired_sessions(conn)
        rows = conn.execute(
            """
            SELECT
                d.*,
                COUNT(s.session_id) AS open_sessions,
                MAX(s.created_at) AS last_opened_at,
                MAX(s.expires_at) AS session_expires_at
            FROM documents d
            JOIN sessions s ON s.file_id = d.file_id
            WHERE s.expires_at > ?
            GROUP BY d.file_id
            ORDER BY last_opened_at DESC
            LIMIT ?
            """,
            (now(), limit),
        ).fetchall()
        return [dict(row) for row in rows]


def create_session(
    file_id: str,
    user_id: str = "agent-zero-user",
    permission: str = "write",
    origin: str = "",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict[str, Any]:
    permission = "write" if permission == "write" else "read"
    created = now()
    expires = created + ttl_seconds
    session_id = uuid.uuid4().hex
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, file_id, user_id, permission, origin, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, file_id, user_id, permission, origin, created, expires),
        )
    return {
        "session_id": session_id,
        "file_id": file_id,
        "expires_at": expires,
        "permission": permission,
        "origin": origin,
    }


def close_session(session_id: str = "", file_id: str = "") -> int:
    session_id = str(session_id or "").strip()
    file_id = str(file_id or "").strip()
    if not session_id and not file_id:
        return 0

    with connect() as conn:
        _clear_expired_sessions(conn)
        if session_id:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not row:
                return 0
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.execute(
                "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
                (row["file_id"], "close_session", json.dumps({"session_id": session_id}), now()),
            )
            return 1

        rows = conn.execute("SELECT session_id FROM sessions WHERE file_id = ?", (file_id,)).fetchall()
        conn.execute("DELETE FROM sessions WHERE file_id = ?", (file_id,))
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (file_id, "close_document_sessions", json.dumps({"closed": len(rows)}), now()),
        )
        return len(rows)


def is_editor_document(doc: dict[str, Any]) -> bool:
    return str(doc.get("extension") or "").lower() not in OPEN_DOCUMENT_EXTENSIONS | OOXML_EXTENSIONS


def editor_text_bytes(content: str) -> bytes:
    return FileBrowser.text_bytes(content)


def read_text_for_editor(doc: dict[str, Any]) -> str:
    if not is_editor_document(doc):
        raise ValueError(f"Text editing is not available for .{doc['extension']}.")
    return FileBrowser.read_text(doc["path"])


def write_text_document(file_id: str, content: str) -> dict[str, Any]:
    doc = get_document(file_id)
    if not is_editor_document(doc):
        raise ValueError(f"Editor text saves are not available for .{doc['extension']}.")
    return replace_document_bytes(file_id, editor_text_bytes(str(content or "")), actor=f"editor:{doc['extension']}")


def write_markdown(file_id: str, content: str) -> dict[str, Any]:
    return write_text_document(file_id, content)


def save_text_document_as(
    file_id: str,
    path: str | Path,
    content: str,
    context_id: str = "",
    file_browser: bool = False,
) -> dict[str, Any]:
    target = normalize_path(path, context_id=context_id, file_browser=file_browser)
    ext = target.suffix.lstrip(".").lower()
    if not is_editor_document({"extension": ext}):
        raise ValueError("Editor Save As requires a text file, not an office document.")
    if target.exists():
        raise FileExistsError(f"Target already exists: {display_path(target)}")

    data = editor_text_bytes(str(content or ""))

    with connect() as conn:
        source = get_document(file_id, conn=conn)
        source_ext = str(source.get("extension") or "").lower()
        if not is_editor_document(source):
            raise ValueError(f"Editor Save As is not available for .{source_ext}.")
        changed_at = now()
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_atomic(target, data, source=Path(source["path"]))
        digest = sha256_bytes(data)
        stat = target.stat()
        new_file_id = uuid.uuid4().hex
        conn.execute(
            """
            INSERT INTO documents
            (file_id, path, basename, extension, owner_id, size, version, sha256, last_modified, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_file_id,
                str(target),
                target.name,
                ext,
                str(source.get("owner_id") or "a0"),
                stat.st_size,
                1,
                digest,
                now_iso(),
                changed_at,
                changed_at,
            ),
        )
        _record_version(conn, new_file_id, target, "1", data)
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                file_id,
                "saved_as",
                json.dumps({"from": display_path(source["path"]), "to": display_path(target)}),
                changed_at,
            ),
        )
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                new_file_id,
                "created_from_save_as",
                json.dumps({"from": display_path(source["path"])}),
                changed_at,
            ),
        )
        return get_document(new_file_id, conn=conn)


def replace_document_bytes(
    file_id: str,
    data: bytes,
    actor: str = "agent",
    invalidate_sessions: bool = False,
) -> dict[str, Any]:
    if len(data) > MAX_SAVE_BYTES:
        raise OverflowError("Document save exceeds maximum size")
    with connect() as conn:
        doc = get_document(file_id, conn=conn)
        path = Path(doc["path"])
        previous = path.read_bytes() if path.exists() else b""
        if previous == data:
            return doc

        _record_version(conn, file_id, path, item_version(doc), previous)
        _write_atomic(path, data)
        digest = sha256_bytes(data)
        next_version = int(doc["version"]) + 1
        changed_at = now()
        conn.execute(
            """
            UPDATE documents
            SET size=?, version=?, sha256=?, last_modified=?, updated_at=?
            WHERE file_id=?
            """,
            (len(data), next_version, digest, now_iso(), changed_at, file_id),
        )
        if invalidate_sessions:
            conn.execute("DELETE FROM sessions WHERE file_id = ?", (file_id,))
        conn.execute(
            "INSERT INTO events (file_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
            (file_id, "saved", json.dumps({"actor": actor, "version": f"{next_version}-{digest[:12]}"}), changed_at),
        )
        return get_document(file_id, conn=conn)


def item_version(doc: dict[str, Any]) -> str:
    return f"{int(doc['version'])}-{str(doc['sha256'])[:12]}"


def _write_atomic(path: Path, data: bytes, *, source: Path | None = None) -> None:
    source = source or path
    metadata = source.stat() if source.exists() else None
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with os.fdopen(os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
            handle.write(data)
            handle.flush()
            if metadata:
                current = os.fstat(handle.fileno())
                if (current.st_uid, current.st_gid) != (metadata.st_uid, metadata.st_gid):
                    os.fchown(handle.fileno(), metadata.st_uid, metadata.st_gid)
                os.fchmod(handle.fileno(), stat.S_IMODE(metadata.st_mode))
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _clear_expired_sessions(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now(),))


def _record_version(conn: sqlite3.Connection, file_id: str, path: Path, version: str, data: bytes) -> None:
    if not data:
        return
    backup_path = BACKUP_DIR / f"{file_id}-{uuid.uuid4().hex}-{version.replace('/', '_')}"
    with os.fdopen(os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
        handle.write(data)
    conn.execute(
        "INSERT INTO versions (file_id, version, path, size, sha256, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (file_id, version, str(backup_path), len(data), sha256_bytes(data), now()),
    )


def version_history(file_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, file_id, version, path, size, sha256, created_at FROM versions WHERE file_id = ? ORDER BY id DESC",
            (file_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def restore_version(file_id: str, version_id: int) -> dict[str, Any]:
    with connect() as conn:
        doc = get_document(file_id, conn=conn)
        row = conn.execute("SELECT * FROM versions WHERE id = ? AND file_id = ?", (version_id, file_id)).fetchone()
        if not row:
            raise FileNotFoundError(f"Version {version_id} not found")
        data = Path(row["path"]).read_bytes()
        path = Path(doc["path"])
        _record_version(conn, file_id, path, item_version(doc), path.read_bytes() if path.exists() else b"")
        _write_atomic(path, data)
        digest = sha256_bytes(data)
        next_version = int(doc["version"]) + 1
        conn.execute(
            "UPDATE documents SET size=?, version=?, sha256=?, last_modified=?, updated_at=? WHERE file_id=?",
            (len(data), next_version, digest, now_iso(), now(), file_id),
        )
        return get_document(file_id, conn=conn)


def create_document(
    kind: str,
    title: str,
    fmt: str = "md",
    content: str = "",
    path: str = "",
    context_id: str = "",
) -> dict[str, Any]:
    ext = normalize_extension(fmt or "md")
    target = normalize_path(path, context_id=context_id) if path else _unique_document_path(title, ext, context_id=context_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(str(target))
    data = template_bytes(kind, ext, title, content)
    _write_atomic(target, data)
    return register_document(target, context_id=context_id)


def _unique_document_path(title: str, ext: str, context_id: str = "") -> Path:
    base = safe_document_stem(title, ext, "Document")
    root = document_home(context_id) if ext in EDITOR_TEXT_EXTENSIONS else document_binary_home(context_id)
    candidate = root / f"{base}.{ext}"
    index = 2
    while candidate.exists():
        candidate = root / f"{base} {index}.{ext}"
        index += 1
    return candidate.resolve(strict=False)


def safe_document_stem(title: str, ext: str, fallback: str = "Document") -> str:
    base = safe_title(title, fallback)
    suffix = f".{normalize_extension(ext)}"
    if base.casefold().endswith(suffix.casefold()):
        base = base[: -len(suffix)].rstrip(" ._") or fallback
    return base


def template_bytes(kind: str, ext: str, title: str, content: str) -> bytes:
    ext = normalize_extension(ext or "md")
    if ext == "md":
        return _markdown(title, content).encode("utf-8")
    if ext == "txt":
        return (str(content or "") or str(title or "")).encode("utf-8")
    raise ValueError(ext)


def _markdown(title: str, content: str) -> str:
    text = str(content or "").strip()
    if text:
        return text if text.startswith("#") else f"# {title}\n\n{text}\n"
    return f"# {title}\n"

