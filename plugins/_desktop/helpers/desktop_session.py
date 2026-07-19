from __future__ import annotations

import atexit
import fcntl
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from helpers import files, virtual_desktop
from plugins._desktop.helpers import desktop_state
from plugins._office.helpers import document_store, libreoffice


OFFICIAL_EXTENSIONS = {"odt", "ods", "odp", "docx", "xlsx", "pptx"}
PLUGIN_NAME = "_desktop"
SYSTEM_SESSION_ID = "agent-zero-desktop"
SYSTEM_FILE_ID = "system-desktop"
SYSTEM_TITLE = "Desktop"
STATE_DIR = Path(files.get_abs_path("usr", "plugins", PLUGIN_NAME))
RETIRED_STATE_DIR = Path(files.get_abs_path("usr", PLUGIN_NAME))
SESSION_DIR = STATE_DIR / "sessions"
PROFILE_DIR = STATE_DIR / "profiles"
LEGACY_SESSION_DIRS = (
    RETIRED_STATE_DIR / "sessions",
    Path(files.get_abs_path("tmp", "_office", "desktop", "sessions")),
)
DISPLAY_BASE = 120
XPRA_PORT_BASE = 14500
MAX_SESSIONS = 12
DEFAULT_SCREEN_WIDTH = virtual_desktop.DEFAULT_WIDTH
DEFAULT_SCREEN_HEIGHT = virtual_desktop.DEFAULT_HEIGHT
MAX_SCREEN_WIDTH = virtual_desktop.MAX_WIDTH
MAX_SCREEN_HEIGHT = virtual_desktop.MAX_HEIGHT
BLOCKING_DIALOG_TITLES = ("Remote Files", "File Services")
DISPLAY_START_TIMEOUT_SECONDS = 30.0
PORT_START_TIMEOUT_SECONDS = 30.0
STARTUP_GRACE_SECONDS = 45
RUNTIME_INSTALL_MESSAGE = (
    "Installing Agent Zero Desktop runtime dependencies. "
    "This can take a few minutes after an update."
)
HIDDEN_XPRA_DESKTOP_ENTRIES = (
    "xpra.desktop",
    "xpra-gui.desktop",
    "xpra-launcher.desktop",
    "xpra-shadow.desktop",
    "xpra-start.desktop",
)
HIDDEN_XFCE_MENU_ENTRIES = (
    ("exo-mail-reader.desktop", "Mail Reader"),
    ("exo-web-browser.desktop", "Web Browser"),
    ("xfce4-mail-reader.desktop", "Mail Reader"),
    ("xfce4-web-browser.desktop", "Web Browser"),
    ("xfce4-session-logout.desktop", "Log Out"),
    ("xfce4-lock-screen.desktop", "Lock Screen"),
    ("xflock4.desktop", "Lock Screen"),
    ("xfce4-switch-user.desktop", "Switch User"),
)
DESKTOP_README_SOURCE = Path(__file__).resolve().parents[1] / "assets" / "desktop" / "README.md"
DESKTOP_FOLDER_LINKS = (
    ("Projects", ("usr", "projects")),
    ("Skills", ("usr", "skills")),
    ("Agents", ("usr", "agents")),
    ("Downloads", ("usr", "downloads")),
)
URL_INTENT_MAX_ITEMS = 50
URL_INTENT_MAX_LENGTH = 8192
URL_HANDLER_DESKTOP_ID = "agent-zero-browser.desktop"
SHUTDOWN_HANDLER_DESKTOP_ID = "agent-zero-shutdown.desktop"
SHUTDOWN_PANEL_LAUNCHER_ID = SHUTDOWN_HANDLER_DESKTOP_ID
SHUTDOWN_CONFIRM_SECONDS = 8
OOR_NS = "http://openoffice.org/2001/registry"
XS_NS = "http://www.w3.org/2001/XMLSchema"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


@dataclass
class DesktopSession:
    session_id: str
    file_id: str
    extension: str
    path: str
    title: str
    display: int
    xpra_port: int
    token: str
    url: str
    profile_dir: Path
    width: int = DEFAULT_SCREEN_WIDTH
    height: int = DEFAULT_SCREEN_HEIGHT
    processes: dict[str, subprocess.Popen[Any]] = field(default_factory=dict)
    process_ids: dict[str, int] = field(default_factory=dict)
    owns_processes: bool = True
    started_at: float = field(default_factory=time.time)

    def alive(self) -> bool:
        return _running(self.processes.get("xpra")) or _pid_is_running(self.process_ids.get("xpra", 0))

    def public(self, doc: dict[str, Any] | None = None) -> dict[str, Any]:
        title = str(doc.get("basename") or "") if doc else self.title
        path = str(doc.get("path") or "") if doc else self.path
        extension = str(doc.get("extension") or "") if doc else self.extension
        file_id = str(doc.get("file_id") or "") if doc else self.file_id
        return {
            "available": True,
            "session_id": self.session_id,
            "file_id": file_id,
            "extension": extension,
            "title": title,
            "path": document_store.display_path(path),
            "url": self.url,
            "token": self.token,
            "display": f":{self.display}",
            "desktop_path": virtual_desktop.SESSION_PATH,
            "width": self.width,
            "height": self.height,
            "started_at": self.started_at,
        }


class DesktopSessionManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, DesktopSession] = {}

    def ensure_system_desktop(self) -> dict[str, Any]:
        try:
            with self._lock:
                self._reap_dead_locked()
                session = self._ensure_system_desktop_locked()
                return session.public()
        except Exception as exc:
            status = collect_desktop_status()
            return {
                "available": False,
                "error": str(exc),
                "status": status,
            }

    def open(self, doc: dict[str, Any], *, refresh: bool = False) -> dict[str, Any]:
        ext = str(doc.get("extension") or "").lower()
        if ext not in OFFICIAL_EXTENSIONS:
            return {"available": False, "reason": f".{ext} does not use the LibreOffice desktop surface."}

        with self._lock:
            self._reap_dead_locked()
            try:
                session = self._ensure_system_desktop_locked()
            except Exception as exc:
                status = collect_desktop_status()
                return {
                    "available": False,
                    "error": str(exc),
                    "status": status,
                }
            refreshed = False
            try:
                if refresh and session.file_id == str(doc.get("file_id") or ""):
                    refreshed = self._reload_document_locked(session, doc)
                else:
                    self._open_document_locked(session, doc)
            except Exception as exc:
                return {
                    "available": False,
                    "error": str(exc),
                    "status": collect_desktop_status(),
                }
            session.file_id = str(doc["file_id"])
            session.extension = ext
            session.path = str(doc["path"])
            session.title = str(doc["basename"])
            self._write_manifest(session)
            public = session.public(doc)
            public["refreshed"] = refreshed
            return public

    def refresh_document(self, file_id: str) -> dict[str, Any]:
        normalized = str(file_id or "").strip()
        if not normalized:
            return {"ok": True, "refreshed": False}
        try:
            doc = document_store.get_document(normalized)
        except Exception:
            return {"ok": False, "refreshed": False, "error": "Document not found."}

        ext = str(doc.get("extension") or "").lower()
        if ext not in OFFICIAL_EXTENSIONS:
            return {"ok": True, "refreshed": False}

        with self._lock:
            self._reap_dead_locked()
            session = self._find_by_file_id_locked(normalized)
            if not session:
                existing = self._load_system_desktop_from_manifest_locked()
                if existing:
                    self._sessions[existing.session_id] = existing
                    self._register_virtual_desktop(existing)
                    if existing.file_id == normalized:
                        session = existing
            if not session:
                return {"ok": True, "refreshed": False}
            refreshed = self._reload_document_locked(session, doc)
            session.file_id = str(doc["file_id"])
            session.extension = ext
            session.path = str(doc["path"])
            session.title = str(doc["basename"])
            self._write_manifest(session)
            return {"ok": True, "refreshed": refreshed, "desktop": session.public(doc)}

    def save(self, session_id: str, file_id: str = "") -> dict[str, Any]:
        session = self.require(session_id)
        doc = self._document_for_save(session, file_id)
        xdotool = shutil.which("xdotool")
        if not xdotool:
            updated = document_store.register_document(doc["path"]) if doc else None
            return {
                "ok": False,
                "error": "xdotool is not installed; use LibreOffice's Save control inside the canvas.",
                "document": _public_doc(updated) if updated else None,
            }

        result = subprocess.run(
            [xdotool, "key", "--clearmodifiers", "ctrl+s"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
            env=self._display_env(session),
        )
        time.sleep(0.8)
        updated = document_store.register_document(doc["path"]) if doc else None
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            return {
                "ok": False,
                "error": detail or "LibreOffice desktop save shortcut failed.",
                "document": _public_doc(updated) if updated else None,
            }
        return {
            "ok": True,
            "session_id": session.session_id,
            "document": _public_doc(updated) if updated else None,
        }

    def sync(self, session_id: str = "", file_id: str = "") -> dict[str, Any]:
        session = self.get(session_id) if session_id else self._find_by_file_id(file_id)
        if not session:
            return {"ok": False, "error": "LibreOffice desktop session not found."}
        if not _url_bridge_script_path(session).exists():
            try:
                self._prepare_desktop_url_bridge(session)
                self._refresh_xfce_desktop(session)
            except Exception:
                pass
        url_intents = self.claim_url_intents(session.session_id)
        shutdown_request = self.claim_shutdown_request(session.session_id)
        if shutdown_request:
            return self.shutdown_system_desktop(
                save_first=True,
                source=str(shutdown_request.get("source") or "tray"),
            )
        doc = self._document_for_save(session, file_id)
        if not doc:
            return {
                "ok": True,
                "session_id": session.session_id,
                "desktop": session.public(),
                "url_intents": url_intents,
            }
        updated = document_store.register_document(doc["path"])
        return {
            "ok": True,
            "session_id": session.session_id,
            "document": _public_doc(updated),
            "url_intents": url_intents,
        }

    def state(self, *, include_screenshot: bool = False, context_id: str = "") -> dict[str, Any]:
        with self._lock:
            self._reap_dead_locked()
        return desktop_state.collect_state(
            include_screenshot=include_screenshot,
            context_id=context_id,
        )

    def claim_url_intents(self, session_id: str = SYSTEM_SESSION_ID) -> list[dict[str, Any]]:
        session = self.get(session_id) or self.get(SYSTEM_SESSION_ID)
        if not session:
            return []
        return _claim_url_intents(session)

    def claim_shutdown_request(self, session_id: str = SYSTEM_SESSION_ID) -> dict[str, Any] | None:
        session = self.get(session_id) or self.get(SYSTEM_SESSION_ID)
        if not session:
            return None
        return _claim_shutdown_request(session)

    def shutdown_system_desktop(self, *, save_first: bool = True, source: str = "api") -> dict[str, Any]:
        with self._lock:
            session = self._sessions.get(SYSTEM_SESSION_ID)
        if not session:
            _remove_system_manifest()
            return {
                "ok": True,
                "closed": 0,
                "session_id": SYSTEM_SESSION_ID,
                "shutdown": True,
                "intentional_shutdown": True,
                "source": source,
            }

        save_result = None
        if save_first:
            try:
                save_result = self.save(session.session_id)
            except Exception as exc:
                save_result = {"ok": False, "error": str(exc)}

        with self._lock:
            if self._sessions.get(SYSTEM_SESSION_ID) is session:
                self._sessions.pop(SYSTEM_SESSION_ID, None)
        virtual_desktop.unregister_session(session.token)
        self._terminate_session(session, include_rehydrated=True)
        self._remove_manifest(session.session_id)
        _clear_shutdown_request(session)
        return {
            "ok": True,
            "closed": 1,
            "session_id": session.session_id,
            "shutdown": True,
            "intentional_shutdown": True,
            "source": source,
            "save": save_result,
        }

    def retarget_document(self, file_id: str, doc: dict[str, Any]) -> dict[str, Any]:
        session = self._find_by_file_id(file_id)
        if not session:
            return {"ok": True, "updated": False}
        with self._lock:
            session.path = str(doc["path"])
            session.title = str(doc["basename"])
            session.extension = str(doc["extension"])
            self._write_manifest(session)
            return {"ok": True, "updated": True, "desktop": session.public(doc)}

    def close(self, session_id: str, save_first: bool = True) -> dict[str, Any]:
        with self._lock:
            normalized = str(session_id or "").strip()
            session = self._sessions.get(normalized)
        if not session:
            return {"ok": True, "closed": 0}
        if session.session_id == SYSTEM_SESSION_ID:
            save_result = None
            if save_first:
                try:
                    save_result = self.save(session.session_id)
                except Exception as exc:
                    save_result = {"ok": False, "error": str(exc)}
            return {
                "ok": True,
                "closed": 0,
                "session_id": session.session_id,
                "persistent": True,
                "save": save_result,
            }

        save_result = None
        if save_first:
            try:
                save_result = self.save(session.session_id)
            except Exception as exc:
                save_result = {"ok": False, "error": str(exc)}
        with self._lock:
            self._sessions.pop(session.session_id, None)
        virtual_desktop.unregister_session(session.token)
        self._terminate_session(session, include_rehydrated=True)
        self._remove_manifest(session.session_id)
        return {"ok": True, "closed": 1, "session_id": session.session_id, "save": save_result}

    def close_file(self, file_id: str) -> int:
        return 0

    def resize(self, session_id: str, width: int, height: int) -> dict[str, Any]:
        session = self.get(session_id)
        if not session:
            return {"ok": False, "error": "LibreOffice desktop session not found."}
        is_system_desktop = session.session_id == SYSTEM_SESSION_ID and session.extension == "desktop"
        result = virtual_desktop.resize_display(
            display=session.display,
            width=width,
            height=height,
            max_width=MAX_SCREEN_WIDTH,
            max_height=MAX_SCREEN_HEIGHT,
            window_class="" if is_system_desktop else "libreoffice",
            keys=() if is_system_desktop else ("Escape",),
            xauthority=self._xauthority(session),
            home=str(session.profile_dir),
        )
        if result.get("ok"):
            session.width = int(result["width"])
            session.height = int(result["height"])
            if not is_system_desktop:
                self._dismiss_blocking_dialogs(session)
        return result

    def proxy_for_token(self, token: str) -> tuple[str, int] | None:
        normalized = str(token or "").strip()
        with self._lock:
            session = self._sessions.get(normalized)
            if not session:
                session = next((item for item in self._sessions.values() if item.token == normalized), None)
            if not session or not session.alive():
                return None
            return ("127.0.0.1", session.xpra_port)

    def resize_for_token(self, token: str, width: int, height: int) -> dict[str, Any]:
        normalized = str(token or "").strip()
        with self._lock:
            session = self._sessions.get(normalized)
            if not session:
                session = next((item for item in self._sessions.values() if item.token == normalized), None)
        if not session:
            return {"ok": False, "error": "LibreOffice desktop session not found."}
        return self.resize(session.session_id, width, height)

    def get(self, session_id: str) -> DesktopSession | None:
        with self._lock:
            session = self._sessions.get(str(session_id or "").strip())
            return session if session and session.alive() else None

    def require(self, session_id: str) -> DesktopSession:
        session = self.get(session_id)
        if not session:
            raise FileNotFoundError(f"LibreOffice desktop session not found: {session_id}")
        return session

    def shutdown(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            virtual_desktop.unregister_session(session.token)
            if session.owns_processes:
                self._terminate_session(session)
                self._remove_manifest(session.session_id)

    def _document_for_save(self, session: DesktopSession, file_id: str = "") -> dict[str, Any] | None:
        normalized = str(file_id or "").strip()
        if normalized == SYSTEM_FILE_ID:
            return None
        if normalized and normalized != SYSTEM_FILE_ID:
            return document_store.get_document(normalized)
        if session.file_id and session.file_id != SYSTEM_FILE_ID:
            try:
                return document_store.get_document(session.file_id)
            except Exception:
                path = Path(session.path)
                if path.is_file():
                    return document_store.register_document(path)
        return None

    def _register_virtual_desktop(self, session: DesktopSession) -> None:
        virtual_desktop.register_session(
            token=session.token,
            host="127.0.0.1",
            port=session.xpra_port,
            owner="desktop",
            title=session.title,
            resize=lambda width, height, session_id=session.session_id: self.resize(session_id, width, height),
        )

    def _ensure_system_desktop_locked(self) -> DesktopSession:
        existing = self._sessions.get(SYSTEM_SESSION_ID)
        if existing and existing.alive():
            self._prepare_desktop_url_bridge(existing)
            self._refresh_xfce_desktop(existing)
            return existing

        existing = self._load_system_desktop_from_manifest_locked()
        if existing:
            self._sessions[existing.session_id] = existing
            self._register_virtual_desktop(existing)
            self._prepare_desktop_url_bridge(existing)
            self._refresh_xfce_desktop(existing)
            return existing

        status = collect_desktop_status()
        if not status["healthy"]:
            raise RuntimeError(status["message"])

        display, xpra_port = self._allocate_endpoint_locked()
        profile_dir = PROFILE_DIR / SYSTEM_SESSION_ID
        session = DesktopSession(
            session_id=SYSTEM_SESSION_ID,
            file_id=SYSTEM_FILE_ID,
            extension="desktop",
            path=str(document_store.document_binary_home()),
            title=SYSTEM_TITLE,
            display=display,
            xpra_port=xpra_port,
            token=SYSTEM_SESSION_ID,
            url=_xpra_url(SYSTEM_SESSION_ID),
            profile_dir=profile_dir,
        )
        try:
            self._prepare_profile(session)
            self._prepare_desktop_launchers(session)
            self._spawn_desktop_locked(session)
        except Exception:
            self._terminate_session(session)
            raise
        self._sessions[session.session_id] = session
        self._register_virtual_desktop(session)
        self._write_manifest(session)
        return session

    def _load_system_desktop_from_manifest_locked(self) -> DesktopSession | None:
        manifest = SESSION_DIR / f"{SYSTEM_SESSION_ID}.json"
        if not manifest.exists():
            return None
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            display = int(payload.get("display") or 0)
            xpra_port = int(payload.get("xpra_port") or 0)
            process_ids = {
                str(name): pid
                for name, value in dict(payload.get("pids") or {}).items()
                if (pid := _coerce_pid(value))
            }
            if not display or not xpra_port:
                return None
            if not _pid_is_running(process_ids.get("xpra", 0)):
                return None
            if not _port_is_accepting("127.0.0.1", xpra_port):
                return None

            path = str(payload.get("path") or document_store.document_binary_home())
            file_id = str(payload.get("file_id") or SYSTEM_FILE_ID)
            extension = str(payload.get("extension") or "").lower()
            if not extension:
                extension = "desktop" if file_id == SYSTEM_FILE_ID else Path(path).suffix.lower().lstrip(".")
            title = str(payload.get("title") or "")
            if not title:
                title = SYSTEM_TITLE if file_id == SYSTEM_FILE_ID else Path(path).name or SYSTEM_TITLE
            return DesktopSession(
                session_id=SYSTEM_SESSION_ID,
                file_id=file_id,
                extension=extension,
                path=path,
                title=title,
                display=display,
                xpra_port=xpra_port,
                token=SYSTEM_SESSION_ID,
                url=_xpra_url(SYSTEM_SESSION_ID),
                profile_dir=_state_path_from_retired_root(
                    Path(payload.get("profile_dir") or PROFILE_DIR / SYSTEM_SESSION_ID)
                ),
                width=int(payload.get("width") or DEFAULT_SCREEN_WIDTH),
                height=int(payload.get("height") or DEFAULT_SCREEN_HEIGHT),
                process_ids=process_ids,
                owns_processes=False,
                started_at=float(payload.get("started_at") or time.time()),
            )
        except Exception:
            return None

    def _spawn_desktop_locked(self, session: DesktopSession) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        session.profile_dir.mkdir(parents=True, exist_ok=True)

        xpra = _require_binary("xpra")
        xvfb = _require_binary("Xvfb")
        _require_binary("xfce4-session")
        _require_binary("dbus-launch")
        xfce_launcher = self._prepare_xfce_launcher(session)

        session.processes["xvfb"] = subprocess.Popen(
            _xvfb_command(xvfb, session),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._session_env(session),
        )
        self._wait_for_display(session)
        self._set_display_size(session, session.width, session.height)
        self._prepare_root_window(session)
        session.processes["xfce"] = subprocess.Popen(
            [str(xfce_launcher)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._display_env(session),
        )
        self._wait_for_xfce(session)
        session.processes["xpra"] = subprocess.Popen(
            _xpra_shadow_command(xpra, session),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._display_env(session),
        )
        _wait_for_port(
            "127.0.0.1",
            session.xpra_port,
            timeout=PORT_START_TIMEOUT_SECONDS,
            process=session.processes.get("xpra"),
        )
        self._refresh_xfce_desktop(session)

    def _restart_xpra_shadow(self, session: DesktopSession) -> None:
        xpra = _require_binary("xpra")
        process = session.processes.get("xpra")
        if process:
            _terminate_process(process)
        session.processes["xpra"] = subprocess.Popen(
            _xpra_shadow_command(xpra, session),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._display_env(session),
        )
        _wait_for_port(
            "127.0.0.1",
            session.xpra_port,
            timeout=PORT_START_TIMEOUT_SECONDS,
            process=session.processes.get("xpra"),
        )

    def _open_document_locked(self, session: DesktopSession, doc: dict[str, Any]) -> None:
        soffice = libreoffice.find_soffice()
        if not soffice:
            raise RuntimeError("LibreOffice is not installed in this runtime.")
        path = str(doc["path"])
        self._remove_stale_lock_file(session, path=path)
        process_key = f"soffice-{doc['file_id']}"
        session.processes[process_key] = subprocess.Popen(
            [
                soffice,
                "--norestore",
                "--nofirststartwizard",
                "--nolockcheck",
                f"-env:UserInstallation=file://{session.profile_dir}",
                path,
            ],
            cwd=str(Path(path).parent),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self._display_env(session),
        )
        self._fit_office_window(session, process=session.processes[process_key])
        window_id = self._wait_for_office_window_locked(
            session,
            title=str(doc.get("basename") or ""),
            process=session.processes[process_key],
        )
        if not window_id:
            raise RuntimeError(
                f"LibreOffice did not show {doc.get('basename') or 'the document'} "
                f"on desktop :{session.display}.",
            )
        self._fit_office_window_id_locked(
            session,
            window_id,
            env=self._display_env(session),
            keys=("Escape",),
        )

    def _reload_document_locked(self, session: DesktopSession, doc: dict[str, Any]) -> bool:
        if self._close_document_window_locked(session, doc):
            self._open_document_locked(session, doc)
            return True
        if self._send_reload_shortcut_locked(session, doc):
            return True
        self._open_document_locked(session, doc)
        return False

    def _close_document_window_locked(self, session: DesktopSession, doc: dict[str, Any]) -> bool:
        xdotool = shutil.which("xdotool")
        if not xdotool:
            return False
        title = str(doc.get("basename") or Path(str(doc.get("path") or "")).name or "").strip()
        if not title:
            return False
        window_id = self._office_window_id_locked(session, title=title, fallback=False)
        if not window_id:
            return False
        env = self._display_env(session)
        self._fit_office_window_id_locked(session, window_id, env=env, keys=("Escape",))
        for command in (
            [xdotool, "key", "--clearmodifiers", "alt+F4"],
            [xdotool, "windowclose", window_id],
        ):
            try:
                subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if self._wait_for_window_closed_locked(session, window_id):
                return True
        self._dismiss_blocking_dialogs(session)
        return self._wait_for_window_closed_locked(session, window_id, timeout_seconds=1.5)

    def _send_reload_shortcut_locked(self, session: DesktopSession, doc: dict[str, Any]) -> bool:
        xdotool = shutil.which("xdotool")
        if not xdotool:
            return False
        window_id = self._office_window_id_locked(
            session,
            title=str(doc.get("basename") or ""),
        )
        if not window_id:
            return False
        env = self._display_env(session)
        self._fit_office_window_id_locked(session, window_id, env=env, keys=("Escape",))
        try:
            result = subprocess.run(
                [xdotool, "key", "--clearmodifiers", "ctrl+shift+r"],
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        time.sleep(0.8)
        self._dismiss_blocking_dialogs(session)
        self._fit_office_window_id_locked(session, window_id, env=env, keys=("Escape",))
        return result.returncode == 0

    def _office_window_id_locked(
        self,
        session: DesktopSession,
        *,
        title: str = "",
        fallback: bool = True,
    ) -> str:
        xdotool = shutil.which("xdotool")
        if not xdotool:
            return ""
        env = self._display_env(session)
        title = str(title or "").strip()
        searches: list[list[str]] = []
        if title:
            escaped_title = re.escape(title)
            searches.append([
                xdotool,
                "search",
                "--onlyvisible",
                "--name",
                escaped_title,
            ])
            for window_class in (
                "libreoffice",
                "libreoffice-writer",
                "libreoffice-calc",
                "libreoffice-impress",
            ):
                searches.append([
                    xdotool,
                    "search",
                    "--onlyvisible",
                    "--class",
                    window_class,
                    "--name",
                    escaped_title,
                ])
        if fallback:
            for window_class in (
                "libreoffice",
                "libreoffice-writer",
                "libreoffice-calc",
                "libreoffice-impress",
            ):
                searches.append([xdotool, "search", "--onlyvisible", "--class", window_class])
            searches.append([xdotool, "search", "--onlyvisible", "--name", "LibreOffice"])
        for command in searches:
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=2,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            window_ids = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ]
            if window_ids:
                return window_ids[-1]
        return ""

    def _wait_for_office_window_locked(
        self,
        session: DesktopSession,
        *,
        title: str = "",
        process: subprocess.Popen[Any] | None = None,
        timeout_seconds: float = 20.0,
    ) -> str:
        deadline = time.time() + timeout_seconds
        last_fallback = ""
        title = str(title or "").strip()
        while time.time() < deadline:
            window_id = self._office_window_id_locked(session, title=title, fallback=False)
            if window_id:
                return window_id
            last_fallback = self._office_window_id_locked(session, fallback=True) or last_fallback
            if last_fallback and not title:
                return last_fallback
            if process and process.poll() is not None and last_fallback:
                return last_fallback
            time.sleep(0.25)
        return self._office_window_id_locked(session, title=title, fallback=True) or last_fallback

    def _wait_for_window_closed_locked(
        self,
        session: DesktopSession,
        window_id: str,
        *,
        timeout_seconds: float = 6.0,
    ) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            if not self._window_exists_locked(session, window_id):
                return True
            time.sleep(0.2)
        return not self._window_exists_locked(session, window_id)

    def _window_exists_locked(self, session: DesktopSession, window_id: str) -> bool:
        xdotool = shutil.which("xdotool")
        if not xdotool or not window_id:
            return False
        try:
            result = subprocess.run(
                [xdotool, "getwindowname", str(window_id)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                env=self._display_env(session),
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _fit_office_window_id_locked(
        self,
        session: DesktopSession,
        window_id: str,
        *,
        env: dict[str, str],
        keys: tuple[str, ...] = (),
    ) -> None:
        xdotool = shutil.which("xdotool")
        if not xdotool or not window_id:
            return
        for command in (
            [xdotool, "windowactivate", window_id],
            [
                xdotool,
                "windowmove",
                window_id,
                "0",
                "0",
                "windowsize",
                window_id,
                str(session.width),
                str(session.height),
            ],
        ):
            try:
                subprocess.run(
                    command,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
        for key in keys:
            try:
                subprocess.run(
                    [xdotool, "key", "--clearmodifiers", key],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2,
                    env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue

    def _prepare_profile(self, session: DesktopSession) -> None:
        user_dir = session.profile_dir / "user"
        user_dir.mkdir(parents=True, exist_ok=True)
        registry = user_dir / "registrymodifications.xcu"
        _write_libreoffice_registry_defaults(registry, document_store.document_home())

    def _prepare_desktop_launchers(self, session: DesktopSession) -> None:
        soffice = libreoffice.find_soffice()
        if not soffice:
            raise RuntimeError("LibreOffice is not installed in this runtime.")
        workdir_home = document_store.document_home()
        workdir_home.mkdir(parents=True, exist_ok=True)
        documents_home = document_store.document_binary_home()
        documents_home.mkdir(parents=True, exist_ok=True)
        downloads_home = Path(files.get_abs_path("usr", "downloads"))
        downloads_home.mkdir(parents=True, exist_ok=True)

        desktop_dir = session.profile_dir / "Desktop"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        _install_desktop_readme(desktop_dir)
        _remove_path_if_owned(desktop_dir / "Browser.desktop")
        _remove_path_if_owned(desktop_dir / "Files.desktop")
        config_dir = session.profile_dir / ".config"
        config_dir.mkdir(parents=True, exist_ok=True)
        _remove_path_if_owned(config_dir / "xfce4" / "panel")
        data_dir = session.profile_dir / ".local" / "share"
        data_dir.mkdir(parents=True, exist_ok=True)
        applications_dir = data_dir / "applications"
        applications_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = session.profile_dir / ".cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "user-dirs.dirs").write_text(
            "\n".join(
                [
                    'XDG_DESKTOP_DIR="$HOME/Desktop"',
                    f'XDG_DOCUMENTS_DIR="{workdir_home}"',
                    f'XDG_DOWNLOAD_DIR="{downloads_home}"',
                    f'XDG_TEMPLATES_DIR="{workdir_home}"',
                    f'XDG_PUBLICSHARE_DIR="{workdir_home}"',
                    f'XDG_MUSIC_DIR="{workdir_home}"',
                    f'XDG_PICTURES_DIR="{downloads_home}"',
                    f'XDG_VIDEOS_DIR="{workdir_home}"',
                    "",
                ],
            ),
            encoding="utf-8",
        )
        xfce_conf_dir = config_dir / "xfce4" / "xfconf" / "xfce-perchannel-xml"
        xfce_conf_dir.mkdir(parents=True, exist_ok=True)
        (xfce_conf_dir / "xfce4-desktop.xml").write_text(
            f"""<?xml version="1.1" encoding="UTF-8"?>

<channel name="xfce4-desktop" version="1.0">
  <property name="last-settings-migration-version" type="uint" value="1"/>
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="image-path" type="string" value="{_xml_attr(str(downloads_home))}"/>
      </property>
    </property>
  </property>
  <property name="desktop-icons" type="empty">
    <property name="style" type="int" value="2"/>
    <property name="file-icons" type="empty">
      <property name="show-home" type="bool" value="false"/>
      <property name="show-filesystem" type="bool" value="false"/>
      <property name="show-removable" type="bool" value="false"/>
      <property name="show-trash" type="bool" value="false"/>
    </property>
  </property>
</channel>
""",
            encoding="utf-8",
        )
        _write_thunar_defaults(xfce_conf_dir / "thunar.xml")
        self._hide_xpra_desktop_entries(applications_dir)
        self._hide_xfce_menu_entries(applications_dir)
        self._prepare_desktop_url_bridge(session)

        base_args = (
            soffice,
            "--norestore",
            "--nofirststartwizard",
            "--nolockcheck",
            f"-env:UserInstallation=file://{session.profile_dir}",
        )
        office_launchers = (
            ("LibreOffice Writer", "libreoffice-writer", "--writer", "Office;WordProcessor;"),
            ("LibreOffice Calc", "libreoffice-calc", "--calc", "Office;Spreadsheet;"),
            ("LibreOffice Impress", "libreoffice-impress", "--impress", "Office;Presentation;"),
        )
        for name, icon, mode, categories in office_launchers:
            _write_desktop_launcher(
                desktop_dir / f"{name}.desktop",
                name=name,
                exec_line=_desktop_exec(*base_args, mode),
                icon=icon,
                categories=categories,
                try_exec=soffice,
                working_dir=workdir_home,
            )

        terminal = shutil.which("xfce4-terminal") or "xfce4-terminal"
        settings = shutil.which("xfce4-settings-manager") or "xfce4-settings-manager"
        desktop_apps = (
            {
                "filename": "Terminal.desktop",
                "name": "Terminal",
                "exec": _desktop_exec(terminal, f"--working-directory={workdir_home}"),
                "try_exec": terminal,
                "icon": _desktop_icon(
                    "/usr/share/icons/hicolor/128x128/apps/org.xfce.terminal.png",
                    "/usr/share/icons/hicolor/scalable/apps/org.xfce.terminal.svg",
                    "org.xfce.terminal",
                    "utilities-terminal",
                ),
                "categories": "System;TerminalEmulator;",
            },
            {
                "filename": "Settings.desktop",
                "name": "Settings",
                "exec": _desktop_exec(settings),
                "try_exec": settings,
                "icon": _desktop_icon(
                    "/usr/share/icons/hicolor/128x128/apps/org.xfce.settings.manager.png",
                    "/usr/share/icons/hicolor/scalable/apps/org.xfce.settings.manager.svg",
                    "org.xfce.settings.manager",
                    "preferences-system",
                ),
                "categories": "Settings;DesktopSettings;",
            },
        )
        for app in desktop_apps:
            _write_desktop_launcher(
                desktop_dir / str(app["filename"]),
                name=str(app["name"]),
                exec_line=str(app["exec"]),
                icon=str(app["icon"]),
                categories=str(app["categories"]),
                try_exec=str(app["try_exec"]),
            )
        _ensure_desktop_folder_link(desktop_dir, "Workdir", workdir_home)
        for label, target_parts in DESKTOP_FOLDER_LINKS:
            _ensure_desktop_folder_link(desktop_dir, label, Path(files.get_abs_path(*target_parts)))

        self._trust_desktop_launchers(session, desktop_dir)
        self._prepare_xfce_panel_config(session)
        self._prepare_xfce_profile_autostart(session)

    def _prepare_desktop_url_bridge(self, session: DesktopSession) -> None:
        desktop_dir = session.profile_dir / "Desktop"
        config_dir = session.profile_dir / ".config"
        data_dir = session.profile_dir / ".local" / "share"
        applications_dir = data_dir / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        config_dir.mkdir(parents=True, exist_ok=True)
        applications_dir.mkdir(parents=True, exist_ok=True)

        browser_bridge = _write_url_bridge_script(session)
        shutdown_bridge = _write_shutdown_bridge_script(session)
        helpers_rc = config_dir / "xfce4" / "helpers.rc"
        helpers_rc.parent.mkdir(parents=True, exist_ok=True)
        helpers_rc.write_text(
            "\n".join(
                [
                    "TerminalEmulator=xfce4-terminal",
                    "FileManager=thunar",
                    "WebBrowser=agent-zero-browser",
                    "",
                ],
            ),
            encoding="utf-8",
        )
        _write_xfce_browser_helper(
            config_dir / "xfce4" / "helpers" / "agent-zero-browser.desktop",
            browser_bridge,
        )
        _write_mimeapps_defaults(config_dir / "mimeapps.list", URL_HANDLER_DESKTOP_ID)
        _write_mimeapps_defaults(data_dir / "applications" / "mimeapps.list", URL_HANDLER_DESKTOP_ID)
        _write_desktop_launcher(
            applications_dir / URL_HANDLER_DESKTOP_ID,
            name="Agent Zero Browser",
            exec_line=_desktop_exec(browser_bridge, "%U"),
            icon="web-browser",
            categories="Network;WebBrowser;",
            try_exec=str(browser_bridge),
            mime_types=_url_handler_mime_types(),
            no_display=True,
        )
        _write_desktop_launcher(
            applications_dir / SHUTDOWN_HANDLER_DESKTOP_ID,
            name="Shutdown Desktop",
            exec_line=_desktop_exec(shutdown_bridge),
            icon="system-shutdown",
            categories="System;",
            try_exec=str(shutdown_bridge),
            no_display=True,
        )
        _write_desktop_launcher(
            config_dir / "xfce4" / "panel" / "launcher-9" / SHUTDOWN_HANDLER_DESKTOP_ID,
            name="Shutdown Desktop",
            exec_line=_desktop_exec(shutdown_bridge),
            icon="system-shutdown",
            categories="System;",
            try_exec=str(shutdown_bridge),
        )
        _write_desktop_launcher(
            desktop_dir / "Browser.desktop",
            name="Browser",
            exec_line=_desktop_exec(browser_bridge),
            icon="web-browser",
            categories="Network;WebBrowser;",
            try_exec=str(browser_bridge),
        )
        self._trust_desktop_launchers(session, desktop_dir)

    def _hide_xpra_desktop_entries(self, applications_dir: Path) -> None:
        for filename in HIDDEN_XPRA_DESKTOP_ENTRIES:
            _write_hidden_application_entry(applications_dir / filename, "Xpra")

    def _hide_xfce_menu_entries(self, applications_dir: Path) -> None:
        for filename, name in HIDDEN_XFCE_MENU_ENTRIES:
            _write_hidden_application_entry(applications_dir / filename, name)

    def _prepare_xfce_panel_config(self, session: DesktopSession) -> None:
        panel_xml = (
            session.profile_dir
            / ".config"
            / "xfce4"
            / "xfconf"
            / "xfce-perchannel-xml"
            / "xfce4-panel.xml"
        )
        panel_xml.parent.mkdir(parents=True, exist_ok=True)

        root = ET.Element("channel", {"name": "xfce4-panel", "version": "1.0"})
        ET.SubElement(root, "property", {"name": "configver", "type": "int", "value": "2"})

        panels = ET.SubElement(root, "property", {"name": "panels", "type": "array"})
        ET.SubElement(panels, "value", {"type": "int", "value": "1"})
        panel = ET.SubElement(panels, "property", {"name": "panel-1", "type": "empty"})
        for name, prop_type, value in (
            ("position", "string", "p=6;x=0;y=0"),
            ("length", "uint", "100"),
            ("position-locked", "bool", "true"),
            ("size", "uint", "24"),
            ("mode", "uint", "0"),
            ("autohide-behavior", "uint", "0"),
            ("disable-struts", "bool", "false"),
            ("nrows", "uint", "1"),
        ):
            ET.SubElement(panel, "property", {"name": name, "type": prop_type, "value": value})
        plugin_ids = ET.SubElement(panel, "property", {"name": "plugin-ids", "type": "array"})
        for plugin_id in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            ET.SubElement(plugin_ids, "value", {"type": "int", "value": plugin_id})

        plugins = ET.SubElement(root, "property", {"name": "plugins", "type": "empty"})
        ET.SubElement(plugins, "property", {"name": "plugin-1", "type": "string", "value": "applicationsmenu"})
        ET.SubElement(plugins, "property", {"name": "plugin-2", "type": "string", "value": "tasklist"})
        tasklist = _xfce_property(plugins, "plugin-2", "string", "tasklist")
        ET.SubElement(tasklist, "property", {"name": "flat-buttons", "type": "bool", "value": "true"})
        ET.SubElement(tasklist, "property", {"name": "show-handle", "type": "bool", "value": "false"})
        ET.SubElement(tasklist, "property", {"name": "show-labels", "type": "bool", "value": "true"})
        separator = ET.SubElement(plugins, "property", {"name": "plugin-3", "type": "string", "value": "separator"})
        ET.SubElement(separator, "property", {"name": "expand", "type": "bool", "value": "true"})
        ET.SubElement(separator, "property", {"name": "style", "type": "uint", "value": "0"})
        ET.SubElement(plugins, "property", {"name": "plugin-4", "type": "string", "value": "pager"})
        ET.SubElement(plugins, "property", {"name": "plugin-5", "type": "string", "value": "systray"})
        ET.SubElement(plugins, "property", {"name": "plugin-6", "type": "string", "value": "separator"})
        ET.SubElement(plugins, "property", {"name": "plugin-7", "type": "string", "value": "clock"})
        ET.SubElement(plugins, "property", {"name": "plugin-8", "type": "string", "value": "separator"})
        shutdown = ET.SubElement(plugins, "property", {"name": "plugin-9", "type": "string", "value": "launcher"})
        shutdown_items = ET.SubElement(shutdown, "property", {"name": "items", "type": "array"})
        ET.SubElement(shutdown_items, "value", {"type": "string", "value": SHUTDOWN_PANEL_LAUNCHER_ID})

        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ")
        except AttributeError:
            pass
        tree.write(panel_xml, encoding="utf-8", xml_declaration=True)

    def _prepare_xfce_profile_autostart(self, session: DesktopSession) -> None:
        script = session.profile_dir / "prepare-xfce-profile.sh"
        script.write_text(
            """#!/bin/sh
set -eu
export HOME="${HOME:-%s}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_CONFIG_DIRS="/etc/xdg${XDG_CONFIG_DIRS:+:$XDG_CONFIG_DIRS}"
export XDG_DATA_DIRS="/usr/local/share:/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"
export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-XFCE}"
mkdir -p "$HOME/Desktop" "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$XDG_CACHE_HOME"
if command -v xfconf-query >/dev/null 2>&1; then
  xfconf-query -c thunar -p /last-show-hidden -n -t bool -s true >/dev/null 2>&1 || true
  xfconf-query -c xfce4-desktop -p /desktop-icons/style -n -t int -s 2 >/dev/null 2>&1 || true
  xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-home -n -t bool -s false >/dev/null 2>&1 || true
  xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-filesystem -n -t bool -s false >/dev/null 2>&1 || true
  xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-removable -n -t bool -s false >/dev/null 2>&1 || true
  xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-trash -n -t bool -s false >/dev/null 2>&1 || true
fi
for launcher in "$HOME"/Desktop/*.desktop; do
  [ -f "$launcher" ] || continue
  chmod +x "$launcher" 2>/dev/null || true
  if command -v gio >/dev/null 2>&1; then
    checksum="$(sha256sum "$launcher" 2>/dev/null | cut -d " " -f 1)"
    gio set "$launcher" metadata::trusted true >/dev/null 2>&1 || true
    if [ -n "$checksum" ]; then
      gio set -t string "$launcher" metadata::xfce-exe-checksum "$checksum" >/dev/null 2>&1 || true
    fi
  fi
done
if command -v xfdesktop >/dev/null 2>&1; then
  timeout 4 xfdesktop --reload >/dev/null 2>&1 || true
fi
""" % str(session.profile_dir),
            encoding="utf-8",
        )
        try:
            script.chmod(0o700)
        except OSError:
            pass

        autostart_dir = session.profile_dir / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        autostart = autostart_dir / "agent-zero-desktop.desktop"
        autostart.write_text(
            "\n".join(
                [
                    "[Desktop Entry]",
                    "Type=Application",
                    "Name=Agent Zero desktop profile",
                    f"Exec={script}",
                    "Terminal=false",
                    "OnlyShowIn=XFCE;",
                    "X-GNOME-Autostart-enabled=true",
                    "",
                ],
            ),
            encoding="utf-8",
        )

    def _prepare_xfce_launcher(self, session: DesktopSession) -> Path:
        launcher = session.profile_dir / "start-xfce.sh"
        launcher.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"',
                    'export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"',
                    'export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"',
                    'export XDG_CONFIG_DIRS="/etc/xdg${XDG_CONFIG_DIRS:+:$XDG_CONFIG_DIRS}"',
                    'export XDG_DATA_DIRS="/usr/local/share:/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"',
                    'export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-XFCE}"',
                    (
                        "exec dbus-launch --exit-with-session sh -c "
                        f"'\"{session.profile_dir / 'prepare-xfce-profile.sh'}\" >/dev/null 2>&1 || true; exec xfce4-session'"
                    ),
                    "",
                ],
            ),
            encoding="utf-8",
        )
        try:
            launcher.chmod(0o700)
        except OSError:
            pass
        return launcher

    def _prepare_root_window(self, session: DesktopSession) -> None:
        xsetroot = shutil.which("xsetroot")
        if not xsetroot:
            return
        subprocess.run(
            [xsetroot, "-solid", "#20242a"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            env=self._display_env(session),
        )

    def _fit_office_window(
        self,
        session: DesktopSession,
        *,
        process: subprocess.Popen[Any] | None = None,
    ) -> None:
        virtual_desktop.fit_window_until(
            display=session.display,
            width=session.width,
            height=session.height,
            window_class="libreoffice",
            keys=("Escape",),
            settle_seconds=4,
            timeout_seconds=10,
            process=process,
            xauthority=self._xauthority(session),
            home=str(session.profile_dir),
        )
        self._dismiss_blocking_dialogs(session)

    def _set_display_size(self, session: DesktopSession, width: int, height: int) -> dict[str, Any]:
        result = virtual_desktop.resize_display(
            display=session.display,
            width=width,
            height=height,
            max_width=MAX_SCREEN_WIDTH,
            max_height=MAX_SCREEN_HEIGHT,
            window_class="",
            keys=(),
            xauthority=self._xauthority(session),
            home=str(session.profile_dir),
        )
        if result.get("ok"):
            session.width = int(result["width"])
            session.height = int(result["height"])
        return result

    def _dismiss_blocking_dialogs(self, session: DesktopSession) -> None:
        virtual_desktop.close_windows(
            display=session.display,
            names=BLOCKING_DIALOG_TITLES,
            xauthority=self._xauthority(session),
            home=str(session.profile_dir),
        )

    def _refresh_xfce_desktop(self, session: DesktopSession) -> None:
        xfdesktop = shutil.which("xfdesktop")
        if not xfdesktop:
            return
        env = self._xfce_process_env(session, "xfdesktop")
        try:
            subprocess.run(
                [xfdesktop, "--reload"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=4,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired):
            return

    def _trust_desktop_launchers(self, session: DesktopSession, desktop_dir: Path) -> None:
        gio = shutil.which("gio")
        if not gio:
            return
        env = self._xfce_process_env(session, "xfdesktop")
        for launcher in desktop_dir.glob("*.desktop"):
            try:
                launcher.chmod(0o755)
                checksum = hashlib.sha256(launcher.read_bytes()).hexdigest()
            except OSError:
                continue
            for command in (
                [gio, "set", str(launcher), "metadata::trusted", "true"],
                [gio, "set", "-t", "string", str(launcher), "metadata::xfce-exe-checksum", checksum],
            ):
                try:
                    subprocess.run(
                        command,
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=4,
                        env=env,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    continue

    def _xfce_process_env(self, session: DesktopSession, command_name: str) -> dict[str, str]:
        env = self._display_env(session)
        proc = Path("/proc")
        for candidate in proc.iterdir():
            if not candidate.name.isdigit():
                continue
            try:
                if (candidate / "comm").read_text(encoding="utf-8").strip() != command_name:
                    continue
                process_env = self._read_process_env(candidate)
            except OSError:
                continue
            if process_env.get("HOME") != str(session.profile_dir):
                continue
            if process_env.get("DISPLAY") != f":{session.display}":
                continue
            for key, value in process_env.items():
                if (
                    key in {"DBUS_SESSION_BUS_ADDRESS", "DISPLAY", "HOME", "XAUTHORITY"}
                    or key.startswith("XDG_")
                ):
                    env[key] = value
            break
        return env

    def _read_process_env(self, proc_dir: Path) -> dict[str, str]:
        raw = (proc_dir / "environ").read_bytes()
        env: dict[str, str] = {}
        for item in raw.split(b"\0"):
            if not item or b"=" not in item:
                continue
            key, value = item.split(b"=", 1)
            env[key.decode("utf-8", errors="ignore")] = value.decode("utf-8", errors="ignore")
        return env

    def _session_env(self, session: DesktopSession) -> dict[str, str]:
        env = {
            **os.environ,
            "HOME": str(session.profile_dir),
            "LANG": os.environ.get("LANG") or "C.UTF-8",
        }
        browser_bridge = _url_bridge_script_path(session)
        if browser_bridge.exists():
            env["BROWSER"] = str(browser_bridge)
        env.setdefault("XDG_RUNTIME_DIR", str(STATE_DIR / "xdg-runtime"))
        runtime_dir = Path(env["XDG_RUNTIME_DIR"])
        runtime_dir.mkdir(parents=True, exist_ok=True)
        try:
            runtime_dir.chmod(0o700)
        except OSError:
            pass
        return env

    def _display_env(self, session: DesktopSession) -> dict[str, str]:
        env = {
            **self._session_env(session),
            "DISPLAY": f":{session.display}",
            "SAL_USE_VCLPLUGIN": os.environ.get("SAL_USE_VCLPLUGIN") or "gtk3",
        }
        xauthority = self._xauthority(session)
        if xauthority:
            env["XAUTHORITY"] = xauthority
        return env

    def _xauthority(self, session: DesktopSession) -> str:
        path = session.profile_dir / ".Xauthority"
        return str(path) if path.exists() else ""

    def _allocate_endpoint_locked(self) -> tuple[int, int]:
        used_displays = {session.display for session in self._sessions.values()}
        used_ports = {session.xpra_port for session in self._sessions.values()}
        for offset in range(MAX_SESSIONS):
            display = DISPLAY_BASE + offset
            port = XPRA_PORT_BASE + offset
            if display in used_displays or port in used_ports:
                continue
            if _port_is_free(port):
                return display, port
        raise RuntimeError("No LibreOffice desktop slots are available.")

    def _find_by_file_id_locked(self, file_id: str) -> DesktopSession | None:
        for session in self._sessions.values():
            if session.file_id == file_id and session.alive():
                return session
        return None

    def _find_by_file_id(self, file_id: str) -> DesktopSession | None:
        with self._lock:
            return self._find_by_file_id_locked(str(file_id or "").strip())

    def _reap_dead_locked(self) -> None:
        for session_id, session in list(self._sessions.items()):
            if not session.alive():
                self._terminate_session(session)
                virtual_desktop.unregister_session(session.token)
                self._sessions.pop(session_id, None)
                self._remove_manifest(session_id)

    def _wait_for_display(self, session: DesktopSession) -> None:
        marker = Path(f"/tmp/.X11-unix/X{session.display}")
        deadline = time.time() + DISPLAY_START_TIMEOUT_SECONDS
        while time.time() < deadline:
            process = session.processes.get("xvfb") or session.processes.get("xpra")
            if process and process.poll() is not None:
                raise RuntimeError("The LibreOffice X display exited before it was ready.")
            if marker.exists():
                return
            time.sleep(0.1)
        raise TimeoutError("Timed out waiting for the LibreOffice X display.")

    def _wait_for_xfce(self, session: DesktopSession) -> None:
        deadline = time.time() + STARTUP_GRACE_SECONDS
        while time.time() < deadline:
            process = session.processes.get("xfce")
            if process and process.poll() is not None:
                return
            if virtual_desktop.has_window(
                display=session.display,
                name="xfce4-panel",
                xauthority=self._xauthority(session),
                home=str(session.profile_dir),
            ):
                return
            time.sleep(0.25)

    def _write_manifest(self, session: DesktopSession) -> None:
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        pids = dict(session.process_ids)
        pids.update({name: process.pid for name, process in session.processes.items()})
        payload = {
            "session_id": session.session_id,
            "file_id": session.file_id,
            "extension": session.extension,
            "path": session.path,
            "title": session.title,
            "display": session.display,
            "xpra_port": session.xpra_port,
            "profile_dir": str(session.profile_dir),
            "width": session.width,
            "height": session.height,
            "started_at": session.started_at,
            "owner_pid": os.getpid(),
            "pids": pids,
        }
        (SESSION_DIR / f"{session.session_id}.json").write_text(json.dumps(payload), encoding="utf-8")

    def _remove_manifest(self, session_id: str) -> None:
        (SESSION_DIR / f"{session_id}.json").unlink(missing_ok=True)

    def _terminate_session(self, session: DesktopSession, *, include_rehydrated: bool = False) -> None:
        process_names = [name for name in session.processes if name.startswith("soffice")]
        process_names.extend(["xfce", "xpra", "xvfb"])
        terminated_pids: set[int] = set()
        for name in process_names:
            process = session.processes.get(name)
            if not process:
                continue
            if process.pid:
                terminated_pids.add(process.pid)
            _terminate_process(process)
        if session.owns_processes or include_rehydrated:
            for name, pid in session.process_ids.items():
                if pid in terminated_pids:
                    continue
                if name.startswith("soffice") or name in {"xfce", "xpra", "xvfb"}:
                    _kill_pid(pid)
        self._remove_stale_lock_file(session)

    def _remove_stale_lock_file(self, session: DesktopSession, *, path: str | Path | None = None) -> None:
        path = Path(path or session.path)
        if not path.name:
            return
        lock_file = path.with_name(f".~lock.{path.name}#")
        try:
            lock_file.unlink(missing_ok=True)
        except OSError:
            pass


def collect_desktop_status() -> dict[str, Any]:
    desktop = virtual_desktop.collect_status()
    binaries = {
        **desktop["binaries"],
        "soffice": libreoffice.find_soffice(),
        "thunar": shutil.which("thunar") or "",
        "xfce4-terminal": shutil.which("xfce4-terminal") or "",
        "xfce4-settings-manager": shutil.which("xfce4-settings-manager") or "",
        "gio": shutil.which("gio") or "",
    }
    missing = [
        name
        for name in (
            "soffice",
            "thunar",
            "xfce4-terminal",
            "xfce4-settings-manager",
            "gio",
        )
        if not binaries[name]
    ]
    missing.extend(
        name
        for name in ("xpra", "Xvfb", "xfce4-session", "dbus-launch", "xrandr", "xdotool")
        if not binaries.get(name)
    )
    if not desktop.get("xpra_html_root"):
        missing.append("xpra-html5")
    if desktop.get("binaries", {}).get("xpra") and desktop.get("packages", {}).get("xpra-x11") is False:
        missing.append("xpra-x11")
    healthy = not missing
    preparation = _runtime_preparation_status()
    installing = bool(preparation.get("preparing")) and not healthy
    return {
        "ok": True,
        "healthy": healthy,
        "state": "healthy" if healthy else "installing" if installing else "missing",
        "installing": installing,
        "missing": missing,
        "preparation": preparation,
        "binaries": binaries,
        "xpra_html_root": str(desktop.get("xpra_html_root") or ""),
        "message": (
            "Agent Zero Desktop sessions are available."
            if healthy
            else RUNTIME_INSTALL_MESSAGE
            if installing
            else f"Agent Zero Desktop sessions need: {', '.join(missing)}."
        ),
    }


def _state_path_from_retired_root(path: Path) -> Path:
    try:
        relative = path.resolve(strict=False).relative_to(
            RETIRED_STATE_DIR.resolve(strict=False)
        )
    except ValueError:
        return path
    return STATE_DIR / relative


def _runtime_preparation_status() -> dict[str, Any]:
    try:
        from plugins._desktop import hooks

        return hooks.runtime_preparation_status()
    except Exception:
        return {"preparing": False, "active_count": 0, "started_at": 0.0, "completed_at": 0.0}


def cleanup_stale_runtime_state() -> dict[str, Any]:
    killed: list[int] = []
    errors: list[str] = []
    seen_dirs: set[Path] = set()
    for session_dir in (SESSION_DIR, *LEGACY_SESSION_DIRS):
        if session_dir in seen_dirs:
            continue
        seen_dirs.add(session_dir)
        if session_dir.exists():
            for manifest in session_dir.glob("*.json"):
                try:
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    owner_pid = _coerce_pid(payload.get("owner_pid"))
                    if owner_pid and _pid_is_running(owner_pid):
                        continue
                    for pid in dict(payload.get("pids") or {}).values():
                        pid_int = _coerce_pid(pid)
                        if not pid_int:
                            continue
                        if _kill_pid(pid_int):
                            killed.append(pid_int)
                    manifest.unlink(missing_ok=True)
                except Exception as exc:
                    errors.append(str(exc))
    return {"ok": not errors, "killed": killed, "errors": errors}


def get_manager() -> DesktopSessionManager:
    global _manager
    try:
        return _manager
    except NameError:
        _manager = DesktopSessionManager()
        atexit.register(_manager.shutdown)
        return _manager


def _xpra_url(token: str) -> str:
    return virtual_desktop.session_url(token, title="Desktop")


def _xvfb_command(xvfb: str, session: DesktopSession) -> list[str]:
    return [
        xvfb,
        f":{session.display}",
        "-screen",
        "0",
        f"{MAX_SCREEN_WIDTH}x{MAX_SCREEN_HEIGHT}x24",
        "+extension",
        "GLX",
        "+extension",
        "RANDR",
        "+extension",
        "RENDER",
        "+extension",
        "Composite",
        "-extension",
        "DOUBLE-BUFFER",
        "-nolisten",
        "tcp",
        "-noreset",
        "-ac",
    ]


def _xpra_shadow_command(xpra: str, session: DesktopSession) -> list[str]:
    return [
        xpra,
        "shadow",
        f":{session.display}",
        "--daemon=no",
        "--mdns=no",
        "--html=on",
        "--tray=no",
        "--system-tray=no",
        "--notifications=no",
        "--clipboard=yes",
        "--clipboard-direction=both",
        "--file-transfer=yes",
        "--open-files=no",
        "--open-url=no",
        "--printing=yes",
        "--audio=no",
        "--speaker=off",
        "--microphone=off",
        "--encoding=jpeg",
        "--quality=85",
        "--speed=80",
        f"--bind-tcp=127.0.0.1:{session.xpra_port}",
        "--resize-display=yes",
        f"--log-dir={session.profile_dir}",
        "--log-file=xpra.log",
    ]


def _desktop_exec(*args: str | Path) -> str:
    return " ".join(_desktop_exec_arg(str(arg)) for arg in args if str(arg))


def _desktop_icon(*candidates: str) -> str:
    for candidate in candidates:
        if candidate.startswith("/") and Path(candidate).exists():
            return candidate
    return next(
        (candidate for candidate in candidates if not candidate.startswith("/")),
        candidates[-1],
    )


def _ensure_desktop_folder_link(desktop_dir: Path, label: str, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    link = desktop_dir / label
    try:
        if link.is_symlink() or link.is_file():
            link.unlink()
        if not link.exists():
            link.symlink_to(target, target_is_directory=True)
    except OSError:
        return


def _url_bridge_dir(session: DesktopSession) -> Path:
    return session.profile_dir / ".agent-zero"


def _url_bridge_script_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "open-url"


def _url_bridge_queue_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "browser-url-intents.jsonl"


def _url_bridge_lock_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "browser-url-intents.lock"


def _shutdown_request_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "shutdown-request.json"


def _shutdown_arm_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "shutdown-request.arm.json"


def _shutdown_lock_path(session: DesktopSession) -> Path:
    return _url_bridge_dir(session) / "shutdown-request.lock"


def _write_url_bridge_script(session: DesktopSession) -> Path:
    bridge_dir = _url_bridge_dir(session)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    script = _url_bridge_script_path(session)
    queue = _url_bridge_queue_path(session)
    lock = _url_bridge_lock_path(session)
    script.write_text(
        f"""#!/usr/bin/env python3
import fcntl
import json
import os
import sys
import time

QUEUE_PATH = {str(queue)!r}
LOCK_PATH = {str(lock)!r}
MAX_URL_LENGTH = {URL_INTENT_MAX_LENGTH}


def main():
    urls = [str(arg or "").strip()[:MAX_URL_LENGTH] for arg in sys.argv[1:] if str(arg or "").strip()]
    if not urls:
        urls = [""]
    os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
    with open(LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        with open(QUEUE_PATH, "a", encoding="utf-8") as queue_file:
            for url in urls:
                queue_file.write(json.dumps({{
                    "url": url,
                    "created_at": time.time(),
                    "source": "desktop",
                }}, ensure_ascii=True) + "\\n")
            queue_file.flush()
            os.fsync(queue_file.fileno())
        fcntl.flock(lock_file, fcntl.LOCK_UN)


if __name__ == "__main__":
    main()
""",
        encoding="utf-8",
    )
    try:
        script.chmod(0o755)
    except OSError:
        pass
    return script


def _write_shutdown_bridge_script(session: DesktopSession) -> Path:
    bridge_dir = _url_bridge_dir(session)
    bridge_dir.mkdir(parents=True, exist_ok=True)
    script = bridge_dir / "shutdown-desktop"
    request = _shutdown_request_path(session)
    arm = _shutdown_arm_path(session)
    lock = _shutdown_lock_path(session)
    script.write_text(
        f"""#!/usr/bin/env python3
import fcntl
import json
import os
import shutil
import subprocess
import time

REQUEST_PATH = {str(request)!r}
ARM_PATH = {str(arm)!r}
LOCK_PATH = {str(lock)!r}
CONFIRM_SECONDS = {SHUTDOWN_CONFIRM_SECONDS}


def notify(message, timeout=None):
    if not os.environ.get("DISPLAY"):
        return
    xmessage = shutil.which("xmessage")
    if not xmessage:
        return
    try:
        subprocess.Popen(
            [
                xmessage,
                "-buttons",
                "",
                "-timeout",
                str(timeout or CONFIRM_SECONDS),
                "-center",
                message,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def read_arm(now):
    try:
        with open(ARM_PATH, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    try:
        created_at = float(payload.get("created_at"))
    except (TypeError, ValueError):
        return None
    if now - created_at > CONFIRM_SECONDS:
        return None
    return created_at


def write_json_atomic(path, payload):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True)
        handle.write("\\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, path)


def main():
    os.makedirs(os.path.dirname(REQUEST_PATH), exist_ok=True)
    now = time.time()
    with open(LOCK_PATH, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        armed_at = read_arm(now)
        if armed_at is None:
            write_json_atomic(ARM_PATH, {{"created_at": now, "source": "tray"}})
            notify(
                f"Shutdown Desktop armed. Click Shutdown Desktop again within {{CONFIRM_SECONDS}} seconds to close it.",
                CONFIRM_SECONDS,
            )
            return
        try:
            os.unlink(ARM_PATH)
        except OSError:
            pass
        payload = {{
            "created_at": now,
            "armed_at": armed_at,
            "source": "tray",
        }}
        write_json_atomic(REQUEST_PATH, payload)
        notify("Shutting down Agent Zero Desktop.", 2)


if __name__ == "__main__":
    main()
""",
        encoding="utf-8",
    )
    try:
        script.chmod(0o755)
    except OSError:
        pass
    return script


def _claim_url_intents(session: DesktopSession) -> list[dict[str, Any]]:
    queue = _url_bridge_queue_path(session)
    lock = _url_bridge_lock_path(session)
    if not queue.exists():
        return []
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(lock, "a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                raw = queue.read_text(encoding="utf-8")
                queue.write_text("", encoding="utf-8")
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
    except OSError:
        return []

    intents: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        url = str(payload.get("url") or "").strip()
        if len(url) > URL_INTENT_MAX_LENGTH:
            url = url[:URL_INTENT_MAX_LENGTH]
        created_at = payload.get("created_at")
        try:
            created_at = float(created_at)
        except (TypeError, ValueError):
            created_at = time.time()
        intents.append(
            {
                "url": url,
                "created_at": created_at,
                "source": str(payload.get("source") or "desktop"),
            },
        )
        if len(intents) >= URL_INTENT_MAX_ITEMS:
            break
    return intents


def _claim_shutdown_request(session: DesktopSession) -> dict[str, Any] | None:
    request = _shutdown_request_path(session)
    if not request.exists():
        return None
    try:
        raw = request.read_text(encoding="utf-8")
        request.unlink(missing_ok=True)
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {}
    created_at = payload.get("created_at")
    try:
        created_at = float(created_at)
    except (TypeError, ValueError):
        created_at = time.time()
    return {
        "created_at": created_at,
        "source": str(payload.get("source") or "tray"),
    }


def _clear_shutdown_request(session: DesktopSession) -> None:
    request = _shutdown_request_path(session)
    arm = _shutdown_arm_path(session)
    lock = _shutdown_lock_path(session)
    request.unlink(missing_ok=True)
    request.with_suffix(request.suffix + ".tmp").unlink(missing_ok=True)
    arm.unlink(missing_ok=True)
    arm.with_suffix(arm.suffix + ".tmp").unlink(missing_ok=True)
    lock.unlink(missing_ok=True)


def _remove_system_manifest() -> None:
    (SESSION_DIR / f"{SYSTEM_SESSION_ID}.json").unlink(missing_ok=True)


def _url_handler_mime_types() -> tuple[str, ...]:
    return (
        "x-scheme-handler/http",
        "x-scheme-handler/https",
        "text/html",
        "application/xhtml+xml",
    )


def _write_mimeapps_defaults(path: Path, desktop_id: str) -> None:
    associations = ";".join([desktop_id, ""])
    lines = [
        "[Default Applications]",
        *(f"{mime_type}={desktop_id}" for mime_type in _url_handler_mime_types()),
        "",
        "[Added Associations]",
        *(f"{mime_type}={associations}" for mime_type in _url_handler_mime_types()),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_xfce_browser_helper(path: Path, bridge_script: Path) -> None:
    command = _desktop_exec(bridge_script)
    command_with_parameter = _desktop_exec(bridge_script, "%s")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "NoDisplay=true",
                "Version=1.0",
                "Type=X-XFCE-Helper",
                "X-XFCE-Category=WebBrowser",
                f"X-XFCE-Commands={command}",
                f"X-XFCE-CommandsWithParameter={command_with_parameter}",
                "Icon=web-browser",
                "Name=Agent Zero Browser",
                "",
            ],
        ),
        encoding="utf-8",
    )


def _remove_path_if_owned(path: Path) -> None:
    try:
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except OSError:
        return


def _desktop_exec_arg(value: str) -> str:
    if not any(char.isspace() or char in '"\\' for char in value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _xml_attr(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _oor(name: str) -> str:
    return f"{{{OOR_NS}}}{name}"


def _file_uri(path: str | Path) -> str:
    return Path(path).resolve(strict=False).as_uri()


def _write_libreoffice_registry_defaults(registry: Path, workdir: str | Path) -> None:
    Path(workdir).mkdir(parents=True, exist_ok=True)
    ET.register_namespace("oor", OOR_NS)
    ET.register_namespace("xs", XS_NS)
    ET.register_namespace("xsi", XSI_NS)
    root = _read_libreoffice_registry(registry)
    workdir_uri = _file_uri(workdir)
    for path, prop, value in (
        ("/org.openoffice.Office.Common/Misc", "FirstRun", "false"),
        ("/org.openoffice.Setup/Office", "ooSetupInstCompleted", "true"),
        ("/org.openoffice.Setup/Office", "MigrationCompleted", "true"),
        ("/org.openoffice.Setup/Office", "OfficeRestartInProgress", "false"),
        ("/org.openoffice.Setup/L10N", "ooLocale", "en-US"),
        ("/org.openoffice.Office.Paths/Variables", "Work", workdir_uri),
        (
            "/org.openoffice.Office.Paths/Paths/org.openoffice.Office.Paths:NamedPath['Work']",
            "WritePath",
            workdir_uri,
        ),
    ):
        _set_registry_prop(root, path, prop, value)
    registry.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(registry, encoding="utf-8", xml_declaration=True)


def _read_libreoffice_registry(registry: Path) -> ET.Element:
    if registry.exists():
        try:
            return ET.parse(registry).getroot()
        except ET.ParseError:
            pass
    return ET.Element(
        _oor("items"),
        {
            "xmlns:xs": XS_NS,
            "xmlns:xsi": XSI_NS,
        },
    )


def _set_registry_prop(root: ET.Element, item_path: str, prop_name: str, value: str) -> None:
    item = _find_registry_item(root, item_path)
    if item is None:
        item = ET.SubElement(root, "item", {_oor("path"): item_path})
    prop = next((child for child in item.findall("prop") if child.get(_oor("name")) == prop_name), None)
    if prop is None:
        prop = ET.SubElement(item, "prop", {_oor("name"): prop_name, _oor("op"): "fuse"})
    else:
        prop.set(_oor("op"), "fuse")
    value_node = prop.find("value")
    if value_node is None:
        value_node = ET.SubElement(prop, "value")
    value_node.text = str(value)


def _find_registry_item(root: ET.Element, item_path: str) -> ET.Element | None:
    for item in root.findall("item"):
        if item.get(_oor("path")) == item_path:
            return item
    return None


def _write_desktop_launcher(
    path: Path,
    *,
    name: str,
    exec_line: str,
    icon: str,
    categories: str,
    try_exec: str = "",
    working_dir: str | Path | None = None,
    mime_types: tuple[str, ...] = (),
    no_display: bool = False,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "[Desktop Entry]",
        "Version=1.0",
        "Type=Application",
        f"Name={name}",
        f"Exec={exec_line}",
    ]
    if try_exec:
        lines.append(f"TryExec={try_exec}")
    if working_dir:
        lines.append(f"Path={working_dir}")
    if mime_types:
        lines.append(f"MimeType={';'.join(mime_types)};")
    if no_display:
        lines.append("NoDisplay=true")
    lines.extend(
        [
            f"Icon={icon}",
            "Terminal=false",
            f"Categories={categories}",
            "StartupNotify=true",
            "X-XFCE-Trusted=true",
            "",
        ],
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    try:
        path.chmod(0o755)
    except OSError:
        pass


def _write_hidden_application_entry(path: Path, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={name}",
                "NoDisplay=true",
                "Hidden=true",
                "",
            ],
        ),
        encoding="utf-8",
    )


def _write_thunar_defaults(path: Path) -> None:
    root = _read_xfce_channel(path, "thunar")
    if _find_xfce_property(root, "last-view") is None:
        _xfce_property(root, "last-view", "string", "ThunarIconView")
    _xfce_property(root, "last-show-hidden", "bool", "true")
    _write_xfce_channel(path, root)


def _read_xfce_channel(path: Path, channel_name: str) -> ET.Element:
    if path.exists():
        try:
            root = ET.parse(path).getroot()
            if root.tag == "channel" and root.get("name") == channel_name:
                root.set("version", root.get("version") or "1.0")
                return root
        except (ET.ParseError, OSError):
            pass
    return ET.Element("channel", {"name": channel_name, "version": "1.0"})


def _write_xfce_channel(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        pass
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _find_xfce_property(parent: ET.Element, name: str) -> ET.Element | None:
    return next((child for child in parent.findall("property") if child.get("name") == name), None)


def _install_desktop_readme(desktop_dir: Path) -> None:
    if not DESKTOP_README_SOURCE.exists():
        return
    target = desktop_dir / "README.md"
    try:
        content = DESKTOP_README_SOURCE.read_text(encoding="utf-8")
        if target.exists() and target.read_text(encoding="utf-8") == content:
            return
        target.write_text(content, encoding="utf-8")
        target.chmod(0o644)
    except OSError:
        return


def _xfce_property(parent: ET.Element, name: str, property_type: str, value: str | None = None) -> ET.Element:
    for child in parent.findall("property"):
        if child.get("name") == name:
            child.set("type", property_type)
            if value is None:
                child.attrib.pop("value", None)
            else:
                child.set("value", value)
            return child
    attributes = {"name": name, "type": property_type}
    if value is not None:
        attributes["value"] = value
    return ET.SubElement(parent, "property", attributes)


def _public_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_id": doc["file_id"],
        "path": document_store.display_path(doc["path"]),
        "basename": doc["basename"],
        "extension": doc["extension"],
        "size": doc["size"],
        "version": document_store.item_version(doc),
        "last_modified": doc["last_modified"],
    }


def _require_binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} is required for official LibreOffice desktop sessions.")
    return found


def _running(process: subprocess.Popen[Any] | None) -> bool:
    return bool(process and process.poll() is None)


def _wait_for_port(
    host: str,
    port: int,
    timeout: float = 15.0,
    process: subprocess.Popen[Any] | None = None,
) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process and process.poll() is not None:
            raise RuntimeError(f"Xpra exited before port {port} was ready.")
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for Xpra port {port}.")


def _port_is_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False


def _port_is_accepting(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def _terminate_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=2)
        return
    except Exception:
        pass
    try:
        process.kill()
        process.wait(timeout=2)
    except Exception:
        pass


def _kill_pid(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 15)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False


def _coerce_pid(value: Any) -> int:
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return 0
    return pid if pid > 0 else 0


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
