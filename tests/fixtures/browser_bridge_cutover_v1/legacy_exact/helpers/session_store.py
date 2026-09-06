from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import asdict, dataclass, field
from threading import RLock
from typing import Any

from agent import AgentContext

from usr.plugins.chrome_extension.helpers.constants import (
    CTX_BROWSER_SESSION_ID,
    CTX_CHROME_CAPABILITIES,
    CTX_SOURCE,
    SOURCE_NAME,
)


@dataclass
class BrowserTabSummary:
    tab_id: int
    window_id: int | None = None
    url: str = ""
    title: str = ""
    active: bool = False
    focused: bool = False


@dataclass
class BridgeCommand:
    command_id: str
    browser_session_id: str
    verb: str
    payload: dict[str, Any] = field(default_factory=dict)
    target_tab_id: int | None = None
    timeout_seconds: float = 30.0
    status: str = "queued"
    attempts: int = 0
    created_at: float = field(default_factory=time.time)
    dispatched_at: float | None = None
    completed_at: float | None = None
    result: dict[str, Any] | None = None
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


@dataclass
class BrowserSession:
    browser_session_id: str
    context_id: str = ""
    source: str = SOURCE_NAME
    active_tab_id: int | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)
    tabs: dict[int, BrowserTabSummary] = field(default_factory=dict)
    queue: list[str] = field(default_factory=list)
    commands: dict[str, BridgeCommand] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def snapshot(self, *, include_commands: bool = False) -> dict[str, Any]:
        tabs = [asdict(tab) for tab in self.tabs.values()]
        tabs.sort(key=lambda item: (not item.get("focused", False), not item.get("active", False), item.get("tab_id", 0)))
        data = {
            "browser_session_id": self.browser_session_id,
            "context_id": self.context_id,
            "source": self.source,
            "active_tab_id": self.active_tab_id,
            "capabilities": self.capabilities,
            "tabs": tabs,
            "last_seen": self.last_seen,
            "created_at": self.created_at,
            "pending_commands": sum(
                1 for command_id in self.queue if self.commands.get(command_id) and self.commands[command_id].status in {"queued", "dispatched"}
            ),
        }
        if include_commands:
            data["commands"] = [self.commands[command_id].to_dict() for command_id in self.queue if command_id in self.commands]
        return data


_lock = RLock()
_sessions: dict[str, BrowserSession] = {}


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_tab(raw: dict[str, Any]) -> BrowserTabSummary | None:
    if not isinstance(raw, dict):
        return None
    tab_id = _coerce_int(raw.get("tab_id", raw.get("id")))
    if tab_id is None:
        return None
    return BrowserTabSummary(
        tab_id=tab_id,
        window_id=_coerce_int(raw.get("window_id", raw.get("windowId"))),
        url=str(raw.get("url", "") or ""),
        title=str(raw.get("title", "") or ""),
        active=bool(raw.get("active", False)),
        focused=bool(raw.get("focused", False)),
    )


def _cleanup_locked(stale_after_seconds: float) -> None:
    now = time.time()
    stale_session_ids = [
        session_id
        for session_id, session in _sessions.items()
        if stale_after_seconds > 0 and (now - session.last_seen) > stale_after_seconds
    ]
    for session_id in stale_session_ids:
        del _sessions[session_id]


def _bind_context(context_id: str, browser_session_id: str, capabilities: dict[str, Any] | None = None) -> None:
    context = AgentContext.use(context_id) if context_id else None
    if not context:
        return
    context.data[CTX_SOURCE] = SOURCE_NAME
    context.data[CTX_BROWSER_SESSION_ID] = browser_session_id
    context.data[CTX_CHROME_CAPABILITIES] = capabilities or {}


def get_context_session_id(context_id: str) -> str:
    if not context_id:
        return ""
    context = AgentContext.use(context_id)
    if not context:
        return ""
    return str(context.data.get(CTX_BROWSER_SESSION_ID, "") or "")


def bind_context_to_session(context_id: str, browser_session_id: str, capabilities: dict[str, Any] | None = None) -> None:
    with _lock:
        session = _sessions.get(browser_session_id)
        if session:
            session.context_id = context_id
            if capabilities is not None:
                session.capabilities = dict(capabilities)
        _bind_context(context_id, browser_session_id, capabilities)


def upsert_session(
    browser_session_id: str,
    *,
    context_id: str = "",
    active_tab_id: int | None = None,
    tabs: list[dict[str, Any]] | None = None,
    capabilities: dict[str, Any] | None = None,
    stale_after_seconds: float = 600.0,
) -> dict[str, Any]:
    if not browser_session_id:
        raise ValueError("browser_session_id is required")

    with _lock:
        _cleanup_locked(stale_after_seconds)
        session = _sessions.get(browser_session_id)
        if not session:
            session = BrowserSession(browser_session_id=browser_session_id)
            _sessions[browser_session_id] = session

        session.last_seen = time.time()
        if context_id:
            session.context_id = context_id
        if capabilities is not None:
            session.capabilities = dict(capabilities)
        if active_tab_id is not None:
            session.active_tab_id = active_tab_id
        if tabs is not None:
            normalized_tabs = {}
            for raw_tab in tabs:
                tab = _normalize_tab(raw_tab)
                if tab:
                    normalized_tabs[tab.tab_id] = tab
            session.tabs = normalized_tabs
            if session.active_tab_id is None:
                active_tabs = [tab.tab_id for tab in normalized_tabs.values() if tab.active]
                if active_tabs:
                    session.active_tab_id = active_tabs[0]

        if session.context_id:
            _bind_context(session.context_id, session.browser_session_id, session.capabilities)

        return session.snapshot(include_commands=False)


def list_sessions(*, stale_after_seconds: float = 600.0, include_commands: bool = False) -> list[dict[str, Any]]:
    with _lock:
        _cleanup_locked(stale_after_seconds)
        sessions = [session.snapshot(include_commands=include_commands) for session in _sessions.values()]
    sessions.sort(key=lambda item: item.get("last_seen", 0), reverse=True)
    return sessions


def get_session(browser_session_id: str, *, stale_after_seconds: float = 600.0, include_commands: bool = False) -> dict[str, Any] | None:
    with _lock:
        _cleanup_locked(stale_after_seconds)
        session = _sessions.get(browser_session_id)
        return session.snapshot(include_commands=include_commands) if session else None


def get_session_or_context(browser_session_id: str = "", context_id: str = "", *, stale_after_seconds: float = 600.0) -> BrowserSession | None:
    with _lock:
        _cleanup_locked(stale_after_seconds)
        if browser_session_id:
            return _sessions.get(browser_session_id)
        if context_id:
            bound_session_id = get_context_session_id(context_id)
            if bound_session_id:
                return _sessions.get(bound_session_id)
        return None


def enqueue_command(
    browser_session_id: str,
    verb: str,
    *,
    payload: dict[str, Any] | None = None,
    target_tab_id: int | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    with _lock:
        session = _sessions.get(browser_session_id)
        if not session:
            raise KeyError(f"browser session '{browser_session_id}' is not connected")

        command = BridgeCommand(
            command_id=str(uuid.uuid4()),
            browser_session_id=browser_session_id,
            verb=verb,
            payload=dict(payload or {}),
            target_tab_id=target_tab_id,
            timeout_seconds=timeout_seconds,
        )
        session.commands[command.command_id] = command
        session.queue.append(command.command_id)
        session.last_seen = time.time()
        return command.to_dict()


def pull_next_command(
    browser_session_id: str,
    *,
    redelivery_seconds: float = 8.0,
    stale_after_seconds: float = 600.0,
) -> dict[str, Any] | None:
    with _lock:
        _cleanup_locked(stale_after_seconds)
        session = _sessions.get(browser_session_id)
        if not session:
            return None

        now = time.time()
        for command_id in list(session.queue):
            command = session.commands.get(command_id)
            if not command:
                continue

            expired = (now - command.created_at) > max(command.timeout_seconds, 1)
            if expired and command.status not in {"completed", "failed"}:
                command.status = "failed"
                command.completed_at = now
                command.error = "Command timed out before the extension returned a result."
                continue

            if command.status == "queued" or (
                command.status == "dispatched"
                and command.dispatched_at is not None
                and (now - command.dispatched_at) >= redelivery_seconds
            ):
                command.status = "dispatched"
                command.dispatched_at = now
                command.attempts += 1
                session.last_seen = now
                return command.to_dict()

        return None


def store_command_result(
    browser_session_id: str,
    command_id: str,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str = "",
    active_tab_id: int | None = None,
    tabs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    with _lock:
        session = _sessions.get(browser_session_id)
        if not session:
            raise KeyError(f"browser session '{browser_session_id}' is not connected")

        command = session.commands.get(command_id)
        if not command:
            raise KeyError(f"command '{command_id}' was not found")

        now = time.time()
        command.status = status
        command.completed_at = now
        command.result = dict(result or {})
        command.error = error
        session.last_seen = now

        if active_tab_id is not None:
            session.active_tab_id = active_tab_id
        if tabs is not None:
            normalized_tabs = {}
            for raw_tab in tabs:
                tab = _normalize_tab(raw_tab)
                if tab:
                    normalized_tabs[tab.tab_id] = tab
            if normalized_tabs:
                session.tabs = normalized_tabs
        if command_id in session.queue and command.status in {"completed", "failed"}:
            session.queue.remove(command_id)

        return command.to_dict()


async def wait_for_command_result(
    browser_session_id: str,
    command_id: str,
    *,
    timeout_seconds: float,
    poll_interval: float = 0.2,
) -> dict[str, Any]:
    started = time.time()
    while True:
        with _lock:
            session = _sessions.get(browser_session_id)
            command = session.commands.get(command_id) if session else None
            if not session or not command:
                raise RuntimeError("Chrome bridge command could not be found.")
            if command.status in {"completed", "failed"}:
                return command.to_dict()

        if (time.time() - started) >= timeout_seconds:
            with _lock:
                session = _sessions.get(browser_session_id)
                command = session.commands.get(command_id) if session else None
                if command and command.status not in {"completed", "failed"}:
                    command.status = "failed"
                    command.completed_at = time.time()
                    command.error = "Timed out while waiting for the Chrome extension to finish the command."
                    if command_id in session.queue:
                        session.queue.remove(command_id)
                    return command.to_dict()
            raise RuntimeError("Chrome bridge command timed out.")

        await asyncio.sleep(poll_interval)
