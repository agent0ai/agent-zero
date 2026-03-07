"""Proactive heartbeat daemon.

Reads a HEARTBEAT.md checklist at a configurable interval and executes
each item via an agent context. Inspired by OpenClaw's autonomous
30-min heartbeat pattern but with event-driven triggers and full logging.
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from python.helpers.files import get_abs_path
from python.helpers.print_style import PrintStyle

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_INTERVAL_SECONDS = 30 * 60  # 30 minutes
DEFAULT_HEARTBEAT_PATH = "HEARTBEAT.md"
HEARTBEAT_LOG_PATH = "data/heartbeat_log.json"
HEARTBEAT_CONFIG_PATH = "data/heartbeat_config.json"
MAX_LOG_ENTRIES = 200


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class HeartbeatItem:
    """A single checklist item parsed from HEARTBEAT.md."""

    text: str
    completed: bool = False
    result: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass
class HeartbeatRun:
    """Record of a single heartbeat execution."""

    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str = ""
    finished_at: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, error
    error: str = ""


@dataclass
class HeartbeatConfig:
    """Persisted heartbeat configuration."""

    enabled: bool = False
    interval_seconds: int = DEFAULT_INTERVAL_SECONDS
    heartbeat_path: str = DEFAULT_HEARTBEAT_PATH
    last_run: str = ""
    run_count: int = 0


# ---------------------------------------------------------------------------
# HEARTBEAT.md parser
# ---------------------------------------------------------------------------


def parse_heartbeat_md(path: str) -> list[HeartbeatItem]:
    """Parse a HEARTBEAT.md file for checklist items.

    Supports standard markdown checklists:
        - [ ] Check system health
        - [x] Already completed item
        - Regular list item (treated as unchecked)
    """
    abs_path = get_abs_path(path)
    if not os.path.exists(abs_path):
        return []

    items: list[HeartbeatItem] = []
    with open(abs_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Match markdown checklist: - [ ] or - [x] or * [ ] etc
            m = re.match(r"^[-*+]\s+\[([xX ])\]\s+(.+)$", line)
            if m:
                checked = m.group(1).lower() == "x"
                items.append(HeartbeatItem(text=m.group(2).strip(), completed=checked))
            elif re.match(r"^[-*+]\s+\S", line):
                # Plain list item without checkbox — treat as unchecked task
                text = re.sub(r"^[-*+]\s+", "", line).strip()
                if text:
                    items.append(HeartbeatItem(text=text))
    return items


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _load_config() -> HeartbeatConfig:
    path = get_abs_path(HEARTBEAT_CONFIG_PATH)
    if os.path.exists(path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            return HeartbeatConfig(**{k: v for k, v in data.items() if k in HeartbeatConfig.__dataclass_fields__})
        except Exception:
            pass
    return HeartbeatConfig()


def _save_config(config: HeartbeatConfig) -> None:
    path = get_abs_path(HEARTBEAT_CONFIG_PATH)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")


def _load_log() -> list[dict[str, Any]]:
    path = get_abs_path(HEARTBEAT_LOG_PATH)
    if os.path.exists(path):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_log(log: list[dict[str, Any]]) -> None:
    path = get_abs_path(HEARTBEAT_LOG_PATH)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # Keep only the most recent entries
    trimmed = log[-MAX_LOG_ENTRIES:]
    Path(path).write_text(json.dumps(trimmed, indent=2) + "\n", encoding="utf-8")


def _append_log(run: HeartbeatRun) -> None:
    log = _load_log()
    log.append(asdict(run))
    _save_log(log)


# ---------------------------------------------------------------------------
# Heartbeat daemon
# ---------------------------------------------------------------------------


class HeartbeatDaemon:
    """Background daemon that periodically executes HEARTBEAT.md items."""

    _instance: HeartbeatDaemon | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._config = _load_config()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._printer = PrintStyle(italic=True, font_color="magenta", padding=False)

    # -- Singleton -----------------------------------------------------------

    @classmethod
    def get(cls) -> HeartbeatDaemon:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = HeartbeatDaemon()
        return cls._instance

    # -- Configuration -------------------------------------------------------

    def get_config(self) -> dict[str, Any]:
        self._config = _load_config()
        return asdict(self._config)

    def update_config(self, **kwargs: Any) -> dict[str, Any]:
        self._config = _load_config()
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        _save_config(self._config)

        # If enabled state changed, start/stop the daemon
        if "enabled" in kwargs:
            if self._config.enabled:
                self.start()
            else:
                self.stop()

        return asdict(self._config)

    def get_log(self, limit: int = 50) -> list[dict[str, Any]]:
        log = _load_log()
        return log[-limit:]

    # -- Lifecycle -----------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            self._printer.print("[Heartbeat] Already running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="Heartbeat")
        self._thread.start()
        self._printer.print(
            f"[Heartbeat] Started — interval={self._config.interval_seconds}s, " f"path={self._config.heartbeat_path}"
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._printer.print("[Heartbeat] Stopped")

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def trigger_now(self) -> dict[str, Any]:
        """Manually trigger a heartbeat run immediately."""
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._execute_heartbeat())
            return asdict(result)
        finally:
            loop.close()

    # -- Main loop -----------------------------------------------------------

    def _run_loop(self) -> None:
        """Background loop that runs heartbeat at the configured interval."""
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            self._config = _load_config()
            if not self._config.enabled:
                self._stop_event.wait(10)
                continue

            try:
                run = loop.run_until_complete(self._execute_heartbeat())
                self._printer.print(f"[Heartbeat] Run {run.run_id} completed: {run.status}")
            except Exception as exc:
                self._printer.print(f"[Heartbeat] Error: {exc}")

            # Wait for the configured interval or until stopped
            self._stop_event.wait(self._config.interval_seconds)

        loop.close()

    # -- Execution -----------------------------------------------------------

    async def _execute_heartbeat(self) -> HeartbeatRun:
        """Execute all uncompleted items in HEARTBEAT.md."""
        run = HeartbeatRun(
            started_at=datetime.now(timezone.utc).isoformat(),
            status="running",
        )

        items = parse_heartbeat_md(self._config.heartbeat_path)
        pending = [item for item in items if not item.completed]

        if not pending:
            run.status = "completed"
            run.finished_at = datetime.now(timezone.utc).isoformat()
            run.items = [asdict(item) for item in items]
            _append_log(run)
            self._printer.print("[Heartbeat] No pending items")
            return run

        self._printer.print(f"[Heartbeat] Processing {len(pending)} items")

        try:
            from agent import AgentContext, UserMessage
            from initialize import initialize_agent

            # Use a dedicated heartbeat context
            ctxid = "heartbeat-daemon"
            context = AgentContext.get(ctxid)
            if context is None:
                config = initialize_agent()
                context = AgentContext(config, id=ctxid, name="Heartbeat")

            for item in pending:
                item.started_at = datetime.now(timezone.utc).isoformat()
                try:
                    prompt = (
                        f"[Heartbeat Task] Execute the following checklist item "
                        f"and report the result concisely:\n\n{item.text}"
                    )
                    task = context.communicate(UserMessage(prompt, []))
                    result = await task.result()  # type: ignore[union-attr]
                    item.result = str(result)[:500]  # cap result length
                    item.completed = True
                except Exception as exc:
                    item.result = f"Error: {exc}"
                item.finished_at = datetime.now(timezone.utc).isoformat()

            run.status = "completed"
        except Exception as exc:
            run.status = "error"
            run.error = str(exc)
            self._printer.print(f"[Heartbeat] Fatal error: {exc}")

        run.finished_at = datetime.now(timezone.utc).isoformat()
        run.items = [asdict(item) for item in items]

        # Update config
        self._config.last_run = run.finished_at
        self._config.run_count += 1
        _save_config(self._config)

        # Persist log
        _append_log(run)

        return run


# ---------------------------------------------------------------------------
# Module-level helpers for API use
# ---------------------------------------------------------------------------


def get_heartbeat_config() -> dict[str, Any]:
    return HeartbeatDaemon.get().get_config()


def update_heartbeat_config(**kwargs: Any) -> dict[str, Any]:
    return HeartbeatDaemon.get().update_config(**kwargs)


def get_heartbeat_log(limit: int = 50) -> list[dict[str, Any]]:
    return HeartbeatDaemon.get().get_log(limit)


def trigger_heartbeat() -> dict[str, Any]:
    return HeartbeatDaemon.get().trigger_now()
