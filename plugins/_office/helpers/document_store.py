from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import time
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from helpers import files
from plugins._office.helpers import pptx_writer


PLUGIN_NAME = "_office"
OPEN_DOCUMENT_EXTENSIONS = {"odt", "ods", "odp"}
OOXML_EXTENSIONS = {"docx", "xlsx", "pptx"}
SUPPORTED_EXTENSIONS = {"md", *OPEN_DOCUMENT_EXTENSIONS, *OOXML_EXTENSIONS}
DEFAULT_TTL_SECONDS = 8 * 60 * 60
MAX_SAVE_BYTES = 512 * 1024 * 1024
ODF_OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
ODF_TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
ODF_TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"
ODF_DRAW_NS = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
ODF_PRESENTATION_NS = "urn:oasis:names:tc:opendocument:xmlns:presentation:1.0"
ODF_STYLE_NS = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
ODF_FO_NS = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
ODF_MANIFEST_NS = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
ODF_VERSION = "1.2"
ODF_MIMETYPES = {
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
}

STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME, "documents"))
DB_PATH = STATE_DIR / "documents.sqlite3"
BACKUP_DIR = STATE_DIR / "backups"
WORKDIR = Path(files.get_abs_path("usr", "workdir"))
DOCUMENTS_DIR = WORKDIR / "documents"


def now() -> float:
    return time.time()


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


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


def allowed_roots(context_id: str = "") -> list[Path]:
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
    return sorted(roots, key=lambda item: str(item))


def _projects() -> Any:
    from helpers import projects

    return projects


def _settings() -> Any:
    from helpers import settings

    return settings


def normalize_path(path: str | Path, context_id: str = "") -> Path:
    candidate = _path_from_a0(path)
    resolved = candidate.resolve(strict=False)
    roots = allowed_roots(context_id)
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


def register_document(path: str | Path, owner_id: str = "a0", context_id: str = "") -> dict[str, Any]:
    resolved = normalize_path(path, context_id=context_id)
    if not resolved.exists():
        raise FileNotFoundError(str(resolved))
    ext = normalize_extension(resolved.suffix.lstrip("."))
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
    ext = normalize_extension(resolved.suffix.lstrip("."))
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
) -> dict[str, Any]:
    resolved = normalize_path(path, context_id=context_id)
    ext = normalize_extension(resolved.suffix.lstrip("."))
    data = None
    if content is not None:
        if ext != "md":
            raise ValueError("Inline content can only be provided for Markdown documents.")
        data = str(content or "").encode("utf-8")
        if len(data) > MAX_SAVE_BYTES:
            raise OverflowError("Document save exceeds maximum size")

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
        elif data is not None:
            if content_changed:
                _record_version(conn, file_id, source_resolved, item_version(doc), previous)
            _write_atomic(resolved, data)
            if changed_path and source_exists:
                source.unlink(missing_ok=True)
            final_data = data
        else:
            final_data = previous

        stat = resolved.stat()
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
                stat.st_size,
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


def read_text_for_editor(doc: dict[str, Any]) -> str:
    path = Path(doc["path"])
    ext = str(doc["extension"]).lower()
    if ext == "md":
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"Text editing is not available for .{ext}.")


def write_markdown(file_id: str, content: str) -> dict[str, Any]:
    return replace_document_bytes(file_id, str(content or "").encode("utf-8"), actor="office:markdown")


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


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp_path.open("wb") as handle:
            handle.write(data)
            handle.flush()
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
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{file_id}-{int(time.time() * 1000)}-{version.replace('/', '_')}"
    backup_path.write_bytes(data)
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
    root = document_home(context_id) if ext == "md" else document_binary_home(context_id)
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
    if ext == "odt":
        return odt_bytes(title, content)
    if ext == "ods":
        return ods_bytes(title, content)
    if ext == "odp":
        return odp_bytes(title, content)
    if ext == "docx":
        return _docx(title, content)
    if ext == "xlsx":
        return _xlsx(title, content)
    if ext == "pptx":
        return _pptx(title, content)
    raise ValueError(ext)


def _markdown(title: str, content: str) -> str:
    text = str(content or "").strip()
    if text:
        return text if text.startswith("#") else f"# {title}\n\n{text}\n"
    return f"# {title}\n"


def _zip_bytes(files_map: dict[str, str | bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in files_map.items():
            data = value.encode("utf-8") if isinstance(value, str) else value
            archive.writestr(name, data)
    return buffer.getvalue()


def odf_zip_bytes(ext: str, files_map: dict[str, str | bytes]) -> bytes:
    ext = normalize_extension(ext)
    if ext not in ODF_MIMETYPES:
        raise ValueError(f"Unsupported ODF format: {ext}")
    media_type = ODF_MIMETYPES[ext]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", media_type, compress_type=zipfile.ZIP_STORED)
        for name, value in files_map.items():
            if name == "mimetype":
                continue
            data = value.encode("utf-8") if isinstance(value, str) else value
            archive.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def odt_bytes(title: str, content: str) -> bytes:
    return odt_bytes_from_paragraphs(_document_lines(title, content))


def odt_bytes_from_paragraphs(paragraphs: list[str]) -> bytes:
    lines = [str(line) for line in paragraphs] or [""]
    body = "\n".join(_odt_paragraph(line, index == 0) for index, line in enumerate(lines))
    return _odf_package(
        "odt",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {_odf_content_namespaces()} office:version="{ODF_VERSION}">
  <office:body>
    <office:text>
      {body}
    </office:text>
  </office:body>
</office:document-content>
""",
    )


def ods_bytes(title: str, content: str) -> bytes:
    return ods_bytes_from_sheets([{"name": "Sheet1", "rows": _xlsx_rows(title, content)}])


def ods_bytes_from_sheets(sheets: list[dict[str, Any]]) -> bytes:
    normalized = []
    for index, sheet in enumerate(sheets or []):
        name = safe_title(str(sheet.get("name") or f"Sheet{index + 1}"), f"Sheet{index + 1}")[:31] or f"Sheet{index + 1}"
        rows = sheet.get("rows") or []
        normalized.append({"name": name, "rows": rows})
    if not normalized:
        normalized = [{"name": "Sheet1", "rows": [["Spreadsheet"]]}]

    tables = "\n".join(
        f"""<table:table table:name="{escape(sheet['name'])}">
          {''.join(_ods_row(row) for row in sheet['rows'])}
        </table:table>"""
        for sheet in normalized
    )
    return _odf_package(
        "ods",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {_odf_content_namespaces()} office:version="{ODF_VERSION}">
  <office:body>
    <office:spreadsheet>
      {tables}
    </office:spreadsheet>
  </office:body>
</office:document-content>
""",
    )


def odp_bytes(title: str, content: str) -> bytes:
    return odp_bytes_from_slides(pptx_writer.slides_from_text(title, content))


def odp_bytes_from_slides(slides: list[dict[str, Any]]) -> bytes:
    normalized = pptx_writer.normalize_slides(slides)
    if not normalized:
        normalized = [{"title": "Presentation", "bullets": []}]
    pages = "\n".join(_odp_page(slide, index) for index, slide in enumerate(normalized, start=1))
    return _odf_package(
        "odp",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content {_odf_content_namespaces()} office:version="{ODF_VERSION}">
  <office:body>
    <office:presentation>
      {pages}
    </office:presentation>
  </office:body>
</office:document-content>
""",
    )


def _document_lines(title: str, content: str) -> list[str]:
    lines = [str(title or "Document").strip() or "Document"]
    lines.extend(line.rstrip() for line in str(content or "").splitlines() if line.strip())
    if len(lines) == 1:
        lines.append("")
    return lines


def _odf_package(ext: str, content_xml: str) -> bytes:
    return odf_zip_bytes(
        ext,
        {
            "content.xml": content_xml,
            "styles.xml": _odf_styles_xml(),
            "meta.xml": _odf_meta_xml(),
            "settings.xml": _odf_settings_xml(),
            "META-INF/manifest.xml": _odf_manifest_xml(ODF_MIMETYPES[ext]),
        },
    )


def _odf_content_namespaces() -> str:
    return (
        f'xmlns:office="{ODF_OFFICE_NS}" '
        f'xmlns:text="{ODF_TEXT_NS}" '
        f'xmlns:table="{ODF_TABLE_NS}" '
        f'xmlns:draw="{ODF_DRAW_NS}" '
        f'xmlns:presentation="{ODF_PRESENTATION_NS}" '
        f'xmlns:style="{ODF_STYLE_NS}" '
        f'xmlns:fo="{ODF_FO_NS}"'
    )


def _odf_styles_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles {_odf_content_namespaces()} office:version="{ODF_VERSION}">
  <office:styles>
    <style:style style:name="Standard" style:family="paragraph"/>
    <style:style style:name="Heading_20_1" style:display-name="Heading 1" style:family="paragraph">
      <style:text-properties fo:font-weight="bold" fo:font-size="18pt"/>
    </style:style>
  </office:styles>
</office:document-styles>
"""


def _odf_meta_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="{ODF_OFFICE_NS}" office:version="{ODF_VERSION}">
  <office:meta/>
</office:document-meta>
"""


def _odf_settings_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-settings xmlns:office="{ODF_OFFICE_NS}" office:version="{ODF_VERSION}">
  <office:settings/>
</office:document-settings>
"""


def _odf_manifest_xml(media_type: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="{ODF_MANIFEST_NS}" manifest:version="{ODF_VERSION}">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="{media_type}"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""


def _odt_paragraph(line: str, heading: bool = False) -> str:
    text = escape(str(line))
    if heading:
        return f'<text:h text:outline-level="1">{text}</text:h>'
    return f"<text:p>{text}</text:p>"


def _ods_row(row: list[Any]) -> str:
    cells = "".join(_ods_cell(value) for value in row)
    return f"<table:table-row>{cells}</table:table-row>"


def _ods_cell(value: Any) -> str:
    value = _xlsx_value(value)
    if value in (None, ""):
        return "<table:table-cell/>"
    if isinstance(value, bool):
        text = "TRUE" if value else "FALSE"
        return (
            f'<table:table-cell office:value-type="boolean" office:boolean-value="{str(value).lower()}">'
            f"<text:p>{text}</text:p></table:table-cell>"
        )
    if isinstance(value, (int, float)):
        return (
            f'<table:table-cell office:value-type="float" office:value="{value}">'
            f"<text:p>{value}</text:p></table:table-cell>"
        )
    text = escape(str(value))
    return f'<table:table-cell office:value-type="string"><text:p>{text}</text:p></table:table-cell>'


def _odp_page(slide: dict[str, Any], index: int) -> str:
    title = escape(str(slide.get("title") or f"Slide {index}"))
    bullets = [escape(str(item)) for item in slide.get("bullets") or []]
    bullet_items = "".join(f"<text:list-item><text:p>{bullet}</text:p></text:list-item>" for bullet in bullets)
    body = f"<text:list>{bullet_items}</text:list>" if bullet_items else "<text:p/>"
    return f"""<draw:page draw:name="Slide {index}" draw:master-page-name="Default">
  <draw:frame presentation:class="title" draw:name="Title {index}" svg:width="24cm" svg:height="2cm" svg:x="1.5cm" svg:y="1cm" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0">
    <draw:text-box><text:p>{title}</text:p></draw:text-box>
  </draw:frame>
  <draw:frame presentation:class="outline" draw:name="Content {index}" svg:width="24cm" svg:height="12cm" svg:x="1.5cm" svg:y="3.5cm" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0">
    <draw:text-box>{body}</draw:text-box>
  </draw:frame>
</draw:page>"""


def _docx(title: str, content: str) -> bytes:
    lines = [title] + [line for line in content.splitlines() if line.strip()]
    if len(lines) == 1:
        lines.append("")
    body = "".join(_docx_paragraph(line) for line in lines)
    return _zip_bytes({
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>""",
        "word/document.xml": f"""<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}<w:sectPr/></w:body></w:document>""",
    })


def _docx_paragraph(line: str) -> str:
    if not str(line).strip():
        return '<w:p><w:r><w:t xml:space="preserve">&#160;</w:t></w:r></w:p>'
    return f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>"


def _xlsx(title: str, content: str) -> bytes:
    rows = _xlsx_rows(title, content)
    sheet_rows = "".join(
        f'<row r="{row_idx}">{"".join(_xlsx_cell(row_idx, col_idx, value) for col_idx, value in enumerate(row, start=1))}</row>'
        for row_idx, row in enumerate(rows, start=1)
    )
    return _zip_bytes({
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>""",
        "xl/worksheets/sheet1.xml": f"""<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{sheet_rows}</sheetData></worksheet>""",
    })


def _xlsx_rows(title: str, content: str) -> list[list[Any]]:
    parsed = _tabular_rows(content)
    if parsed:
        return parsed
    lines = [line for line in str(content or "").splitlines() if line.strip()]
    if lines:
        return [[title], *[[line] for line in lines]]
    return [[title]]


def _tabular_rows(content: str) -> list[list[Any]]:
    text = str(content or "").strip("\n")
    if not text.strip():
        return []
    lines = [line for line in text.splitlines() if line.strip()]
    markdown_rows = _markdown_table_rows(lines)
    if markdown_rows:
        return markdown_rows

    delimiter = "\t" if any("\t" in line for line in lines) else ("," if any("," in line for line in lines) else None)
    if not delimiter:
        return []
    return [[_xlsx_value(cell) for cell in row] for row in csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)]


def _markdown_table_rows(lines: list[str]) -> list[list[Any]]:
    table_lines = [line.strip() for line in lines if line.strip().startswith("|") and line.strip().endswith("|")]
    if len(table_lines) < 2:
        return []
    rows = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append([_xlsx_value(cell) for cell in cells])
    return rows


def _xlsx_cell(row_idx: int, col_idx: int, value: Any) -> str:
    ref = f"{_column_name(col_idx)}{row_idx}"
    value = _xlsx_value(value)
    if value in (None, ""):
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def _xlsx_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped.lower() in {"true", "false"}:
        return stripped.lower() == "true"
    if re.fullmatch(r"[+-]?\d+", stripped) and not (len(stripped.lstrip("+-")) > 1 and stripped.lstrip("+-").startswith("0")):
        try:
            return int(stripped)
        except ValueError:
            return stripped
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?", stripped) or re.fullmatch(r"[+-]?\d+[eE][+-]?\d+", stripped):
        try:
            return float(stripped)
        except ValueError:
            return stripped
    return stripped


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _pptx(title: str, content: str) -> bytes:
    return pptx_writer.pptx_from_text(title, content)
