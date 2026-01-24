from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from python.helpers import runtime
from python.helpers.print_style import PrintStyle
from python.helpers.state_snapshot import (
    StateRequestV1,
    advance_state_request_after_snapshot,
    build_snapshot_from_request,
)
from python.helpers.websocket import ConnectionNotFoundError

if TYPE_CHECKING:  # pragma: no cover - hints only
    from python.helpers.websocket_manager import WebSocketManager


ConnectionIdentity = tuple[str, str]  # (namespace, sid)


@dataclass
class ConnectionProjection:
    namespace: str
    sid: str
    request: StateRequestV1 | None = None
    seq: int = 0
    seq_base: int = 0
    # Incremented on every dirty signal. Used to coalesce bursts without delaying
    # pushes indefinitely during continuous activity (throttled coalescing).
    dirty_version: int = 0
    pushed_version: int = 0
    # Development-only diagnostics - last known cause of the most recent dirty wave.
    dirty_reason: str | None = None
    dirty_wave_id: str | None = None
    created_at: float = field(default_factory=time.time)


class StateMonitor:
    """Per-sid dirty tracking with debounced snapshot push scheduling."""

    def __init__(self, debounce_seconds: float = 0.025) -> None:
        self.debounce_seconds = float(debounce_seconds)
        self._lock = threading.RLock()
        self._projections: dict[ConnectionIdentity, ConnectionProjection] = {}
        self._debounce_handles: dict[ConnectionIdentity, asyncio.TimerHandle] = {}
        self._push_tasks: dict[ConnectionIdentity, asyncio.Task[None]] = {}
        self._manager: WebSocketManager | None = None
        self._emit_handler_id: str | None = None
        self._dispatcher_loop: asyncio.AbstractEventLoop | None = None
        self._dirty_wave_seq: int = 0

    def bind_manager(self, manager: "WebSocketManager", *, handler_id: str | None = None) -> None:
        with self._lock:
            self._manager = manager
            if handler_id:
                self._emit_handler_id = handler_id
            # Use the manager's dispatcher loop for all scheduling so mark_dirty can be
            # invoked safely from non-async contexts and other threads.
            self._dispatcher_loop = getattr(manager, "_dispatcher_loop", None)
        if runtime.is_development():
            PrintStyle.debug(
                f"[StateMonitor] bind_manager handler_id={handler_id or self._emit_handler_id}"
            )

    def register_sid(self, namespace: str, sid: str) -> None:
        identity: ConnectionIdentity = (namespace, sid)
        with self._lock:
            self._projections.setdefault(
                identity, ConnectionProjection(namespace=namespace, sid=sid)
            )
        if runtime.is_development():
            PrintStyle.debug(f"[StateMonitor] register_sid namespace={namespace} sid={sid}")

    def unregister_sid(self, namespace: str, sid: str) -> None:
        identity: ConnectionIdentity = (namespace, sid)
        with self._lock:
            handle = self._debounce_handles.pop(identity, None)
            if handle is not None:
                handle.cancel()
            task = self._push_tasks.pop(identity, None)
            if task is not None:
                task.cancel()
            self._projections.pop(identity, None)
        if runtime.is_development():
            PrintStyle.debug(
                f"[StateMonitor] unregister_sid namespace={namespace} sid={sid}"
            )

    def mark_dirty_all(self, *, reason: str | None = None) -> None:
        wave_id = None
        if runtime.is_development():
            with self._lock:
                self._dirty_wave_seq += 1
                wave_id = f"all_{self._dirty_wave_seq}"
        with self._lock:
            identities = list(self._projections.keys())
        for namespace, sid in identities:
            self.mark_dirty(namespace, sid, reason=reason, wave_id=wave_id)

    def mark_dirty_for_context(self, context_id: str, *, reason: str | None = None) -> None:
        if not isinstance(context_id, str) or not context_id.strip():
            return
        target = context_id.strip()
        wave_id = None
        if runtime.is_development():
            with self._lock:
                self._dirty_wave_seq += 1
                wave_id = f"ctx_{self._dirty_wave_seq}"
        with self._lock:
            identities = [
                identity
                for identity, projection in self._projections.items()
                if projection.request is not None and projection.request.context == target
            ]
        for namespace, sid in identities:
            self.mark_dirty(namespace, sid, reason=reason, wave_id=wave_id)

    def update_projection(
        self,
        namespace: str,
        sid: str,
        *,
        request: StateRequestV1,
        seq_base: int,
    ) -> None:
        identity: ConnectionIdentity = (namespace, sid)
        with self._lock:
            projection = self._projections.setdefault(
                identity, ConnectionProjection(namespace=namespace, sid=sid)
            )
            projection.request = request
            projection.seq_base = seq_base
            projection.seq = seq_base
        if runtime.is_development():
            PrintStyle.debug(
                f"[StateMonitor] update_projection namespace={namespace} sid={sid} context={request.context!r} "
                f"log_from={request.log_from} notifications_from={request.notifications_from} "
                f"timezone={request.timezone!r} seq_base={seq_base}"
            )

    def mark_dirty(
        self,
        namespace: str,
        sid: str,
        *,
        reason: str | None = None,
        wave_id: str | None = None,
    ) -> None:
        identity: ConnectionIdentity = (namespace, sid)
        loop = self._dispatcher_loop
        if loop is None or loop.is_closed():
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is loop:
            self._mark_dirty_on_loop(identity, reason=reason, wave_id=wave_id)
            return

        loop.call_soon_threadsafe(self._mark_dirty_on_loop, identity, reason, wave_id)

    def _mark_dirty_on_loop(
        self,
        identity: ConnectionIdentity,
        reason: str | None = None,
        wave_id: str | None = None,
    ) -> None:
        with self._lock:
            projection = self._projections.get(identity)
            if projection is None:
                return
            projection.dirty_version += 1
            if runtime.is_development():
                projection.dirty_reason = (
                    reason.strip()
                    if isinstance(reason, str) and reason.strip()
                    else "unknown"
                )
                projection.dirty_wave_id = wave_id
        self._schedule_debounce_on_loop(identity)

    def _schedule_debounce_on_loop(self, identity: ConnectionIdentity) -> None:
        loop = asyncio.get_running_loop()
        with self._lock:
            projection = self._projections.get(identity)
            if projection is None:
                return
            # INVARIANT.STATE.GATING: do not schedule pushes until a successful state_request
            # established seq_base for this sid.
            if projection.seq_base <= 0:
                return

            # Throttled coalescing: schedule at most one push per debounce window.
            # Do not postpone the scheduled push on subsequent dirties; this keeps
            # streaming updates smooth while still capping to <= 1 push / 100ms / sid.
            existing = self._debounce_handles.get(identity)
            if existing is not None and not existing.cancelled():
                return

            running = self._push_tasks.get(identity)
            if running is not None and not running.done():
                return

            handle = loop.call_later(
                self.debounce_seconds, self._on_debounce_fire, identity
            )
            self._debounce_handles[identity] = handle
            if runtime.is_development():
                PrintStyle.debug(
                    f"[StateMonitor] schedule_push namespace={projection.namespace} sid={projection.sid} "
                    f"delay_s={self.debounce_seconds} "
                    f"dirty={projection.dirty_version} pushed={projection.pushed_version} "
                    f"reason={projection.dirty_reason!r} wave={projection.dirty_wave_id!r}"
                )

    def _on_debounce_fire(self, identity: ConnectionIdentity) -> None:
        with self._lock:
            self._debounce_handles.pop(identity, None)
            existing = self._push_tasks.get(identity)
            if existing is not None and not existing.done():
                return
            task = asyncio.create_task(self._flush_push(identity))
            self._push_tasks[identity] = task

    async def _flush_push(self, identity: ConnectionIdentity) -> None:
        namespace, sid = identity
        task = asyncio.current_task()
        base_version = 0
        dirty_reason: str | None = None
        dirty_wave_id: str | None = None
        try:
            with self._lock:
                projection = self._projections.get(identity)
                manager = self._manager
                handler_id = self._emit_handler_id

                if projection is None:
                    return
                if manager is None:
                    # The handler binds the manager on connect; if not bound yet,
                    # we cannot emit. Keep dirty cleared to avoid infinite retry loops.
                    return
                if projection.seq_base <= 0:
                    # INVARIANT.STATE.GATING: no push before a successful state_request.
                    return

                request = projection.request
                if request is None:
                    return
                base_version = projection.dirty_version
                dirty_reason = projection.dirty_reason
                dirty_wave_id = projection.dirty_wave_id

            snapshot = await build_snapshot_from_request(request=request)

            with self._lock:
                projection = self._projections.get(identity)
                if projection is None:
                    return
                if projection.request != request:
                    return

                # INVARIANT.STATE.SEQ_MONOTONIC + SEQ_RESET_ON_REQUEST
                projection.seq += 1
                seq = projection.seq

                # Advance cursors after successful snapshot emission (incremental mode).
                projection.request = advance_state_request_after_snapshot(request, snapshot)

                # Mark all dirties up to `base_version` as pushed. If new dirties
                # arrived while building/emitting, a follow-up push will be scheduled.
                projection.pushed_version = max(projection.pushed_version, base_version)

            payload = {
                "runtime_epoch": runtime.get_runtime_id(),
                "seq": seq,
                "snapshot": snapshot,
            }

            try:
                if runtime.is_development():
                    logs_len = (
                        len(snapshot.get("logs", []))
                        if isinstance(snapshot.get("logs"), list)
                        else None
                    )
                    PrintStyle.debug(
                        f"[StateMonitor] emit state_push namespace={namespace} sid={sid} seq={seq} "
                        f"context={request.context!r} logs_len={logs_len} "
                        f"reason={dirty_reason!r} wave={dirty_wave_id!r}"
                    )
                await manager.emit_to(
                    namespace,
                    sid,
                    "state_push",
                    payload,
                    handler_id=handler_id,
                )
            except ConnectionNotFoundError:
                # Sid was removed before the emit; treat as benign.
                if runtime.is_development():
                    PrintStyle.debug(
                        f"[StateMonitor] emit skipped: sid not found namespace={namespace} sid={sid}"
                    )
                return
            except RuntimeError:
                # Dispatcher loop may be closing (e.g., during shutdown or test teardown).
                if runtime.is_development():
                    PrintStyle.debug(
                        f"[StateMonitor] emit skipped: dispatcher closing namespace={namespace} sid={sid}"
                    )
                return
        finally:
            follow_up = False
            dirty_version = 0
            pushed_version = 0
            with self._lock:
                if task is not None and self._push_tasks.get(identity) is task:
                    self._push_tasks.pop(identity, None)
                projection = self._projections.get(identity)
                if projection is not None:
                    dirty_version = projection.dirty_version
                    pushed_version = projection.pushed_version
                    follow_up = dirty_version > pushed_version

        # More dirties accumulated during push; schedule another coalesced push.
        # IMPORTANT: this must not run from inside the `finally` block (a `return` in
        # `finally` can swallow exceptions from the push task).
        if not follow_up:
            return

        if runtime.is_development():
            PrintStyle.debug(
                f"[StateMonitor] follow_up_push namespace={namespace} sid={sid} dirty={dirty_version} pushed={pushed_version}"
            )
        try:
            loop = self._dispatcher_loop or asyncio.get_running_loop()
        except RuntimeError:
            return
        if loop.is_closed():
            return
        loop.call_soon_threadsafe(self._schedule_debounce_on_loop, identity)

    # Testing hook: keep argument surface stable for future extensions
    def _debug_state(self) -> dict[str, Any]:  # pragma: no cover - helper
        with self._lock:
            return {
                "identities": list(self._projections.keys()),
                "handles": list(self._debounce_handles.keys()),
            }


# Store singleton in a mutable container to avoid `global` assignment warnings while
# keeping a simple module-level accessor API.
_STATE_MONITOR_HOLDER: dict[str, StateMonitor | None] = {"monitor": None}
_STATE_MONITOR_LOCK = threading.RLock()


def get_state_monitor() -> StateMonitor:
    with _STATE_MONITOR_LOCK:
        monitor = _STATE_MONITOR_HOLDER.get("monitor")
        if monitor is None:
            monitor = StateMonitor()
            _STATE_MONITOR_HOLDER["monitor"] = monitor
        return monitor


def _reset_state_monitor_for_testing() -> None:  # pragma: no cover - helper
    with _STATE_MONITOR_LOCK:
        _STATE_MONITOR_HOLDER["monitor"] = None
