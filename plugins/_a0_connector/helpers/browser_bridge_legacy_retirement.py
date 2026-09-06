"""Explicit prototype retirement. Never imports legacy authority into bridge v1."""
from __future__ import annotations

import asyncio
import hashlib
import math
import os
from pathlib import Path
import sys
import threading
import time
import types
import uuid

from plugins._a0_connector.helpers.browser_bridge_cutover import (
    CUTOVER_CONTRACT, LEGACY_PLUGIN_NAME,
    detect_legacy_browser_bridge, _read_bounded_file,
)

STORE_KEY = "a0_browser_bridge_legacy_retirement_v1"
STORE_DIGEST = "28cd59d3bf1e3c5237d9c62102336f5b6f5fc88d89ec16528b6b03079c44cc43"
MAX_COMMANDS = 512
MAX_SESSIONS = 64
STATES = {"draining_legacy", "legacy_disabled", "blocked"}
COUNTERS = {"completed", "canceled_not_applied", "outcome_unknown"}


class LegacyRetirementDenied(ValueError):
    def __init__(self, code="migration_incomplete"):
        self.code = code
        super().__init__(code)


def _deny(*args, **kwargs):
    raise LegacyRetirementDenied("legacy_bridge_retired")


class PrototypeRegistryAdapter:
    """Only the exact inspected prototype implementation can be drained."""
    def __init__(self, module: types.ModuleType, root: Path):
        if type(module) is not types.ModuleType or not detect_legacy_browser_bridge(root).confirmed:
            raise LegacyRetirementDenied()
        if not hasattr(os, "O_NOFOLLOW"):
            raise LegacyRetirementDenied()
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            source = _read_bounded_file(fd, "helpers/session_store.py")
        finally:
            os.close(fd)
        expected = str(root / "helpers/session_store.py")
        if (not source.exists or source.unavailable or hashlib.sha256(source.data).hexdigest() != STORE_DIGEST
            or getattr(module, "__file__", None) != expected
            or type(getattr(module, "_lock", None)) is not type(threading.RLock())
            or type(getattr(module, "_sessions", None)) is not dict):
            raise LegacyRetirementDenied()
        for name in ("enqueue_command", "pull_next_command", "upsert_session", "store_command_result"):
            fn = getattr(module, name, None)
            if not isinstance(fn, types.FunctionType) or fn.__globals__ is not vars(module) or fn.__code__.co_filename != expected:
                raise LegacyRetirementDenied()
        self.module = module
        self.pending = {}
        self.counts = dict.fromkeys(COUNTERS, 0)
        self.started = False

    def begin(self):
        with self.module._lock:
            sessions = self.module._sessions
            if len(sessions) > MAX_SESSIONS:
                raise LegacyRetirementDenied()
            commands = []
            for session_id, session in sessions.items():
                if (type(session) is not self.module.BrowserSession or session.browser_session_id != session_id
                    or type(session.commands) is not dict or type(session.queue) is not list):
                    raise LegacyRetirementDenied()
                for command_id, command in session.commands.items():
                    if (type(command) is not self.module.BridgeCommand or command.command_id != command_id
                        or command.browser_session_id != session_id or command.status not in {"queued", "dispatched", "completed", "failed"}
                        or type(command.created_at) not in {int, float} or type(command.timeout_seconds) not in {int, float}
                        or type(command.attempts) is not int or not 0 <= command.attempts <= 2147483647
                        or not math.isfinite(command.created_at) or not math.isfinite(command.timeout_seconds)
                        or command.timeout_seconds <= 0):
                        raise LegacyRetirementDenied()
                    commands.append((session_id, command_id, command))
            if len(commands) > MAX_COMMANDS:
                raise LegacyRetirementDenied()
            now = time.time()
            # Existing tools reference this module; stop all producers under its
            # original queue lock before retaining only exact dispatched receipts.
            for name in ("enqueue_command", "pull_next_command", "upsert_session", "bind_context_to_session", "get_session", "get_session_or_context", "list_sessions"):
                setattr(self.module, name, _deny)
            self.module.store_command_result = self.accept_result
            self.started = True
            for session_id, command_id, command in commands:
                if command.status == "queued" and command.attempts == 0:
                    self.counts["canceled_not_applied"] += 1
                    command.status, command.error = "failed", "CANCELED_NOT_APPLIED"
                    command.completed_at = now
                elif command.status == "dispatched":
                    self.pending[(session_id, command_id)] = (command, min(now + 30, command.created_at + command.timeout_seconds))
                elif command.status in {"completed", "failed"} and command.result is not None:
                    self.counts["completed"] += 1
                else:
                    category = "outcome_unknown" if command.attempts else "canceled_not_applied"
                    self.counts[category] += 1
                    command.status, command.error = "failed", category.upper()
                command.payload, command.result, command.target_tab_id = {}, {}, None
            for session in sessions.values():
                session.tabs, session.capabilities, session.active_tab_id = {}, {}, None
                session.queue.clear()  # No redelivery, even from old queued code.
            return len(self.pending)

    def accept_result(self, browser_session_id, command_id, *, status, **ignored):
        with self.module._lock:
            if status not in {"completed", "failed"}:
                raise LegacyRetirementDenied("legacy_outcome_unknown")
            item = self.pending.pop((browser_session_id, command_id), None)
            if item is None:
                raise LegacyRetirementDenied("legacy_outcome_unknown")
            command, deadline = item
            if time.time() >= deadline:
                command.status, command.error = "failed", "OUTCOME_UNKNOWN"
                self.counts["outcome_unknown"] += 1
                raise LegacyRetirementDenied("legacy_outcome_unknown")
            command.status, command.error, command.completed_at = status, "", time.time()
            command.result = {}  # Incoming screenshots, text and tab metadata are discarded.
            self.counts["completed"] += 1
            return {"status": status}

    def remaining(self):
        with self.module._lock:
            now = time.time()
            for key, (command, deadline) in tuple(self.pending.items()):
                if now >= deadline:
                    command.status, command.error, command.completed_at = "failed", "OUTCOME_UNKNOWN", now
                    self.counts["outcome_unknown"] += 1
                    self.pending.pop(key)
            return bool(self.pending)

    def finish(self):
        with self.module._lock:
            for command, _deadline in self.pending.values():
                command.status, command.error = "failed", "OUTCOME_UNKNOWN"
                self.counts["outcome_unknown"] += 1
            self.pending.clear()
            self.module._sessions.clear()
            self.module.store_command_result = _deny
            return dict(self.counts)


def _installed_adapter():
    from helpers import plugins
    roots = list(plugins.get_plugin_roots(LEGACY_PLUGIN_NAME))
    root = next((Path(path) for path in roots if os.path.lexists(path)), None)
    if root is None or not detect_legacy_browser_bridge(root).confirmed:
        raise LegacyRetirementDenied()
    modules = [module for name, module in tuple(sys.modules.items()) if name in {
        "usr.plugins.chrome_extension.helpers.session_store", "plugins.chrome_extension.helpers.session_store"}]
    if len(modules) > 1:
        raise LegacyRetirementDenied()
    # Do not execute an unimported third-party plugin to manufacture drain proof.
    if not modules:
        return None
    return PrototypeRegistryAdapter(modules[0], root)


class LegacyRetirement:
    def __init__(self, *, load=None, save=None, adapter=None, disable=None):
        self.load = load or _load
        self.save = save or _save
        self.adapter = adapter or _installed_adapter
        self.disable = disable or _disable
        self.lock = threading.RLock()
        self.task = None
        self.failed = False
        self.guard_installed = False
        self.active_requests = 0

    def _journal(self):
        value = self.load()
        if value is None:
            return None
        keys = {"schema_version", "migration_id", "state", "started_at_ms", "completed", "canceled_not_applied", "outcome_unknown"}
        if (type(value) is not dict or set(value) != keys or type(value["schema_version"]) is not int or value["schema_version"] != 1
            or value["state"] not in STATES or not isinstance(value["migration_id"], str)
            or len(value["migration_id"]) != 36 or str(uuid.UUID(value["migration_id"])) != value["migration_id"]
            or type(value["started_at_ms"]) is not int or value["started_at_ms"] < 0
            or any(type(value[key]) is not int or not 0 <= value[key] <= MAX_COMMANDS for key in COUNTERS)):
            raise LegacyRetirementDenied()
        return dict(value)

    def blocked(self):
        try:
            with self.lock:
                return self.failed or self._journal() is not None
        except Exception:
            return True

    def status(self):
        try:
            with self.lock:
                journal = self._journal()
            state = journal["state"] if journal else "not_started"
            if self.failed or (state == "draining_legacy" and self.task is None):
                state = "blocked"
            return {"contract": CUTOVER_CONTRACT, "schema_version": 1, "state": state,
                    "counts": {key: journal[key] if journal else 0 for key in sorted(COUNTERS)},
                    "local_browser_cleanup": "operator_required", "browser_tabs_changed": False,
                    "activation_ready": False}
        except Exception:
            return {"contract": CUTOVER_CONTRACT, "schema_version": 1, "state": "blocked",
                    "reason_code": "migration_incomplete", "activation_ready": False}

    def _write(self, value):
        self.save(value)
        if self._journal() != value:
            raise LegacyRetirementDenied("storage_write_failed")

    async def retire(self):
        with self.lock:
            if not self.guard_installed or self.active_requests:
                raise LegacyRetirementDenied()
            previous = self._journal()
            if previous is not None:
                return self.status()  # Never replay an interrupted drain.
            adapter = self.adapter()
            journal = {"schema_version": 1, "migration_id": str(uuid.uuid4()), "state": "draining_legacy",
                       "started_at_ms": time.time_ns() // 1_000_000, **dict.fromkeys(COUNTERS, 0)}
            try:
                self._write(journal)
                pending = adapter.begin() if adapter is not None else 0
                # Crash recovery conservatively retains all dispatched work as
                # unknown. No raw command/session identifier enters the journal.
                if adapter is not None:
                    journal.update(adapter.counts)
                    journal["outcome_unknown"] += pending
                    self._write(journal)
            except Exception:
                self.failed = True
                if adapter is not None and adapter.started:
                    adapter.finish()
                raise LegacyRetirementDenied() from None
            self.task = asyncio.create_task(self._finish(adapter, journal))
        await asyncio.shield(self.task)
        return self.status()

    async def _finish(self, adapter, journal):
        try:
            while adapter is not None and adapter.remaining():
                await asyncio.sleep(0.05)
            if adapter is not None:
                journal.update(adapter.finish())
            self.disable()  # Existing plugin toggle runs only after bounded drain.
            journal["state"] = "legacy_disabled"
            with self.lock:
                self._write(journal)
        except BaseException:
            if adapter is not None:
                journal.update(adapter.finish())
            journal["state"] = "blocked"
            self.failed = True
            try:
                with self.lock:
                    self._write(journal)
            except Exception:
                pass


def _load():
    from helpers import kvp
    return kvp.get_persistent(STORE_KEY, None)


def _save(value):
    from helpers import kvp
    kvp.set_persistent(STORE_KEY, value)


def _disable():
    from helpers import plugins
    plugins.toggle_plugin(LEGACY_PLUGIN_NAME, False, clear_overrides=True)
    if plugins.get_toggle_state(LEGACY_PLUGIN_NAME) != "disabled":
        raise LegacyRetirementDenied()


_owner = LegacyRetirement()


def get_legacy_retirement():
    return _owner


def install_legacy_retirement_guard(app):
    """Install once at normal Flask startup; unrelated APIs remain untouched."""
    if app.extensions.get("a0_legacy_retirement_guard"):
        return
    from flask import Response, request, g
    import json

    @app.before_request
    def legacy_guard():
        prefix = next((value for value in ("/api/plugins/chrome_extension/", "/plugins/chrome_extension/") if request.path.startswith(value)), None)
        if prefix is None:
            return None
        with _owner.lock:
            if not _owner.blocked() or (request.path == prefix + "command_result" and _owner.task is not None and not _owner.task.done() and not _owner.failed):
                _owner.active_requests += 1
                g.a0_legacy_retirement_active = True
                return None  # Existing route still verifies its API credential.
            state = _owner.status()["state"]
        code = "LEGACY_CUTOVER_IN_PROGRESS" if state == "draining_legacy" else "LEGACY_BRIDGE_RETIRED"
        return Response(json.dumps({"error": code}), status=409 if state == "draining_legacy" else 410, mimetype="application/json")

    @app.teardown_request
    def legacy_request_finished(_error):
        if getattr(g, "a0_legacy_retirement_active", False):
            with _owner.lock:
                _owner.active_requests -= 1
            g.a0_legacy_retirement_active = False

    app.extensions["a0_legacy_retirement_guard"] = True
    _owner.guard_installed = True
