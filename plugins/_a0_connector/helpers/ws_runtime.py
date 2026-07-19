from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class PendingFileOperation:
    sid: str
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future[dict[str, Any]]
    context_id: str | None = None


@dataclass
class PendingExecOperation:
    sid: str
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future[dict[str, Any]]
    context_id: str | None = None


@dataclass
class PendingComputerUseOperation:
    sid: str
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future[dict[str, Any]]
    context_id: str | None = None


@dataclass
class PendingBrowserOperation:
    sid: str
    loop: asyncio.AbstractEventLoop
    future: asyncio.Future[dict[str, Any]]
    context_id: str | None = None


@dataclass(frozen=True)
class RemoteTreeSnapshot:
    sid: str
    payload: dict[str, Any]
    updated_at: float


@dataclass(frozen=True)
class ComputerUseMetadata:
    supported: bool
    enabled: bool
    trust_mode: str
    status: str
    last_error: str
    restore_token_present: bool
    artifact_root: str
    backend_id: str
    backend_family: str
    features: tuple[str, ...]
    support_reason: str
    updated_at: float


@dataclass(frozen=True)
class HostBrowserMetadata:
    supported: bool
    can_prepare: bool
    enabled: bool
    status: str
    browser_family: str
    profile_label: str
    profile_path: str
    cdp_endpoint: str
    content_helper_sha256: str
    features: tuple[str, ...]
    support_reason: str
    updated_at: float


@dataclass(frozen=True)
class RemoteFileMetadata:
    enabled: bool
    write_enabled: bool
    mode: str
    updated_at: float


@dataclass(frozen=True)
class RemoteExecMetadata:
    enabled: bool
    updated_at: float


_context_subscriptions: dict[str, set[str]] = {}
_sid_contexts: dict[str, set[str]] = {}
_pending_file_ops: dict[str, PendingFileOperation] = {}
_pending_exec_ops: dict[str, PendingExecOperation] = {}
_pending_computer_use_ops: dict[str, PendingComputerUseOperation] = {}
_pending_browser_ops: dict[str, PendingBrowserOperation] = {}
_remote_tree_snapshots: dict[str, RemoteTreeSnapshot] = {}
_sid_computer_use_metadata: dict[str, ComputerUseMetadata] = {}
_sid_host_browser_metadata: dict[str, HostBrowserMetadata] = {}
_sid_remote_file_metadata: dict[str, RemoteFileMetadata] = {}
_sid_remote_exec_metadata: dict[str, RemoteExecMetadata] = {}
_state_lock = threading.RLock()


def register_sid(sid: str) -> None:
    with _state_lock:
        _sid_contexts.setdefault(sid, set())


def unregister_sid(sid: str) -> set[str]:
    with _state_lock:
        contexts = _sid_contexts.pop(sid, set())
        _remote_tree_snapshots.pop(sid, None)
        _sid_computer_use_metadata.pop(sid, None)
        _sid_host_browser_metadata.pop(sid, None)
        _sid_remote_file_metadata.pop(sid, None)
        _sid_remote_exec_metadata.pop(sid, None)
        for context_id in contexts:
            subscribers = _context_subscriptions.get(context_id)
            if not subscribers:
                continue
            subscribers.discard(sid)
            if not subscribers:
                _context_subscriptions.pop(context_id, None)
    return contexts


def subscribe_sid_to_context(sid: str, context_id: str) -> None:
    with _state_lock:
        _sid_contexts.setdefault(sid, set()).add(context_id)
        _context_subscriptions.setdefault(context_id, set()).add(sid)


def unsubscribe_sid_from_context(sid: str, context_id: str) -> None:
    with _state_lock:
        contexts = _sid_contexts.get(sid)
        if contexts is not None:
            contexts.discard(context_id)
            if not contexts:
                _sid_contexts.pop(sid, None)

        subscribers = _context_subscriptions.get(context_id)
        if subscribers is not None:
            subscribers.discard(sid)
            if not subscribers:
                _context_subscriptions.pop(context_id, None)


def subscribed_contexts_for_sid(sid: str) -> set[str]:
    with _state_lock:
        return set(_sid_contexts.get(sid, set()))


def subscribed_sids_for_context(context_id: str) -> set[str]:
    with _state_lock:
        return set(_context_subscriptions.get(context_id, set()))


def connected_sids() -> set[str]:
    with _state_lock:
        return set(_sid_contexts.keys())


def _candidate_sids_for_context_locked(context_id: str) -> list[str]:
    context_sids = sorted(_context_subscriptions.get(context_id, set()))
    context_set = set(context_sids)
    global_sids = sorted(sid for sid in _sid_contexts if sid not in context_set)
    return context_sids + global_sids


def remote_tool_sids_for_context(context_id: str) -> list[str]:
    """Return connected CLI candidates, preferring clients subscribed to context_id."""
    with _state_lock:
        return _candidate_sids_for_context_locked(context_id)


def store_remote_tree_snapshot(
    sid: str,
    payload: dict[str, Any],
) -> RemoteTreeSnapshot:
    snapshot = RemoteTreeSnapshot(
        sid=sid,
        payload=dict(payload),
        updated_at=time.time(),
    )
    with _state_lock:
        _remote_tree_snapshots[sid] = snapshot
    return snapshot


def clear_remote_tree_snapshot(sid: str) -> None:
    with _state_lock:
        _remote_tree_snapshots.pop(sid, None)


def latest_remote_tree_for_context(
    context_id: str,
    *,
    max_age_seconds: float = 90.0,
) -> dict[str, Any] | None:
    now = time.time()
    with _state_lock:
        context_sids = sorted(_context_subscriptions.get(context_id, set()))
        context_set = set(context_sids)
        global_sids = sorted(sid for sid in _sid_contexts if sid not in context_set)
        snapshot_groups = [
            [
                _remote_tree_snapshots[sid]
                for sid in context_sids
                if sid in _remote_tree_snapshots
            ],
            [
                _remote_tree_snapshots[sid]
                for sid in global_sids
                if sid in _remote_tree_snapshots
            ],
        ]

    for snapshots in snapshot_groups:
        snapshots.sort(key=lambda item: item.updated_at, reverse=True)
        for snapshot in snapshots:
            if max_age_seconds > 0 and now - snapshot.updated_at > max_age_seconds:
                continue
            payload = dict(snapshot.payload)
            payload["sid"] = snapshot.sid
            payload["updated_at"] = snapshot.updated_at
            return payload
    return None


def select_target_sid(context_id: str) -> str | None:
    with _state_lock:
        subscribers = _context_subscriptions.get(context_id, set())
        if not subscribers:
            return None
        return sorted(subscribers)[0]


def store_sid_remote_file_metadata(sid: str, payload: dict[str, Any]) -> RemoteFileMetadata:
    write_enabled = bool(payload.get("write_enabled"))
    mode = str(payload.get("mode", "") or "").strip().lower()
    if mode not in {"read_only", "read_write"}:
        mode = "read_write" if write_enabled else "read_only"
    metadata = RemoteFileMetadata(
        enabled=bool(payload.get("enabled", True)),
        write_enabled=write_enabled,
        mode=mode,
        updated_at=time.time(),
    )
    with _state_lock:
        _sid_remote_file_metadata[sid] = metadata
    return metadata


def clear_sid_remote_file_metadata(sid: str) -> None:
    with _state_lock:
        _sid_remote_file_metadata.pop(sid, None)


def remote_file_metadata_for_sid(sid: str) -> dict[str, Any] | None:
    with _state_lock:
        metadata = _sid_remote_file_metadata.get(sid)
    if metadata is None:
        return None
    return {
        "enabled": metadata.enabled,
        "write_enabled": metadata.write_enabled,
        "mode": metadata.mode,
        "updated_at": metadata.updated_at,
    }


def select_remote_file_target_sid(context_id: str, *, require_writes: bool = False) -> str | None:
    with _state_lock:
        for sid in _candidate_sids_for_context_locked(context_id):
            metadata = _sid_remote_file_metadata.get(sid)
            if metadata is None:
                continue
            if not metadata.enabled:
                continue
            if require_writes and not metadata.write_enabled:
                continue
            return sid
    return None


def store_sid_remote_exec_metadata(sid: str, payload: dict[str, Any]) -> RemoteExecMetadata:
    metadata = RemoteExecMetadata(
        enabled=bool(payload.get("enabled")),
        updated_at=time.time(),
    )
    with _state_lock:
        _sid_remote_exec_metadata[sid] = metadata
    return metadata


def clear_sid_remote_exec_metadata(sid: str) -> None:
    with _state_lock:
        _sid_remote_exec_metadata.pop(sid, None)


def remote_exec_metadata_for_sid(sid: str) -> dict[str, Any] | None:
    with _state_lock:
        metadata = _sid_remote_exec_metadata.get(sid)
    if metadata is None:
        return None
    return {
        "enabled": metadata.enabled,
        "updated_at": metadata.updated_at,
    }


def select_remote_exec_target_sid(context_id: str, *, require_writes: bool = False) -> str | None:
    with _state_lock:
        for sid in _candidate_sids_for_context_locked(context_id):
            metadata = _sid_remote_exec_metadata.get(sid)
            if metadata is None:
                continue
            if metadata.enabled:
                if require_writes:
                    file_metadata = _sid_remote_file_metadata.get(sid)
                    if file_metadata is None or (
                        not file_metadata.enabled or not file_metadata.write_enabled
                    ):
                        continue
                return sid
    return None


def store_sid_computer_use_metadata(sid: str, payload: dict[str, Any]) -> ComputerUseMetadata:
    features_value = payload.get("features")
    if isinstance(features_value, (list, tuple)):
        features = tuple(str(item).strip() for item in features_value if str(item).strip())
    else:
        features = ()
    metadata = ComputerUseMetadata(
        supported=bool(payload.get("supported")),
        enabled=bool(payload.get("supported")) and bool(payload.get("enabled")),
        trust_mode=str(payload.get("trust_mode", "") or "").strip(),
        status=str(payload.get("status", "") or "").strip(),
        last_error=str(payload.get("last_error", "") or "").strip(),
        restore_token_present=bool(payload.get("restore_token_present")),
        artifact_root=str(payload.get("artifact_root", "") or "").strip(),
        backend_id=str(payload.get("backend_id", "") or "").strip(),
        backend_family=str(payload.get("backend_family", "") or "").strip(),
        features=features,
        support_reason=str(payload.get("support_reason", "") or "").strip(),
        updated_at=time.time(),
    )
    with _state_lock:
        _sid_computer_use_metadata[sid] = metadata
    return metadata


def clear_sid_computer_use_metadata(sid: str) -> None:
    with _state_lock:
        _sid_computer_use_metadata.pop(sid, None)


def computer_use_metadata_for_sid(sid: str) -> dict[str, Any] | None:
    with _state_lock:
        metadata = _sid_computer_use_metadata.get(sid)
    if metadata is None:
        return None
    return {
        "supported": metadata.supported,
        "enabled": metadata.enabled,
        "trust_mode": metadata.trust_mode,
        "status": metadata.status,
        "last_error": metadata.last_error,
        "restore_token_present": metadata.restore_token_present,
        "artifact_root": metadata.artifact_root,
        "backend_id": metadata.backend_id,
        "backend_family": metadata.backend_family,
        "features": list(metadata.features),
        "support_reason": metadata.support_reason,
        "updated_at": metadata.updated_at,
    }


def store_sid_host_browser_metadata(sid: str, payload: dict[str, Any]) -> HostBrowserMetadata:
    features_value = payload.get("features")
    if isinstance(features_value, (list, tuple)):
        features = tuple(str(item).strip() for item in features_value if str(item).strip())
    else:
        features = ()
    support_reason = str(payload.get("support_reason", "") or "").strip()
    metadata = HostBrowserMetadata(
        supported=bool(payload.get("supported")),
        can_prepare=_host_browser_can_prepare(payload, features=features, support_reason=support_reason),
        enabled=bool(payload.get("supported")) and bool(payload.get("enabled")),
        status=str(payload.get("status", "") or "").strip(),
        browser_family=str(payload.get("browser_family", "") or "").strip(),
        profile_label=str(payload.get("profile_label", "") or "").strip(),
        profile_path=str(payload.get("profile_path", "") or "").strip(),
        cdp_endpoint=str(payload.get("cdp_endpoint", "") or "").strip(),
        content_helper_sha256=str(payload.get("content_helper_sha256", "") or "").strip().lower(),
        features=features,
        support_reason=support_reason,
        updated_at=time.time(),
    )
    with _state_lock:
        _sid_host_browser_metadata[sid] = metadata
    return metadata


def _host_browser_can_prepare(
    payload: dict[str, Any],
    *,
    features: tuple[str, ...],
    support_reason: str,
) -> bool:
    if "can_prepare" in payload:
        return bool(payload.get("can_prepare"))
    if "ensure" not in features:
        return False
    reason = support_reason.lower()
    return (
        "python playwright" in reason
        or "a0-controlled local profile" in reason
        or "chrome-a0" in reason
        or "remote debugging" in reason
    )


def clear_sid_host_browser_metadata(sid: str) -> None:
    with _state_lock:
        _sid_host_browser_metadata.pop(sid, None)


def host_browser_metadata_for_sid(sid: str) -> dict[str, Any] | None:
    with _state_lock:
        metadata = _sid_host_browser_metadata.get(sid)
    if metadata is None:
        return None
    return {
        "supported": metadata.supported,
        "can_prepare": metadata.can_prepare,
        "enabled": metadata.enabled,
        "status": metadata.status,
        "browser_family": metadata.browser_family,
        "profile_label": metadata.profile_label,
        "profile_path": metadata.profile_path,
        "cdp_endpoint": metadata.cdp_endpoint,
        "content_helper_sha256": metadata.content_helper_sha256,
        "features": list(metadata.features),
        "support_reason": metadata.support_reason,
        "updated_at": metadata.updated_at,
    }


def select_host_browser_target_sid(context_id: str) -> str | None:
    with _state_lock:
        fallback: str | None = None
        for sid in _candidate_sids_for_context_locked(context_id):
            metadata = _sid_host_browser_metadata.get(sid)
            if not metadata:
                continue
            if not metadata.supported:
                continue
            if metadata.enabled and metadata.status in {"ready", "active"}:
                return sid
            if metadata.enabled and fallback is None:
                fallback = sid
    return fallback


def select_host_browser_candidate_sid(context_id: str) -> str | None:
    with _state_lock:
        fallback: str | None = None
        for sid in _candidate_sids_for_context_locked(context_id):
            metadata = _sid_host_browser_metadata.get(sid)
            if not metadata or not (metadata.supported or metadata.can_prepare):
                continue
            if metadata.enabled and metadata.status in {"ready", "active"}:
                return sid
            if metadata.enabled and fallback is None:
                fallback = sid
            elif fallback is None:
                fallback = sid
    return fallback


def host_browser_metadata_for_context(context_id: str) -> list[dict[str, Any]]:
    with _state_lock:
        candidates = _candidate_sids_for_context_locked(context_id)
    rows: list[dict[str, Any]] = []
    for sid in candidates:
        metadata = host_browser_metadata_for_sid(sid)
        if metadata is not None:
            metadata["sid"] = sid
            rows.append(metadata)
    return rows


def all_host_browser_metadata() -> list[dict[str, Any]]:
    with _state_lock:
        items = sorted(_sid_host_browser_metadata.items())
    rows: list[dict[str, Any]] = []
    for sid, metadata in items:
        rows.append(
            {
                "sid": sid,
                "supported": metadata.supported,
                "enabled": metadata.enabled,
                "status": metadata.status,
                "browser_family": metadata.browser_family,
                "profile_label": metadata.profile_label,
                "profile_path": metadata.profile_path,
                "content_helper_sha256": metadata.content_helper_sha256,
                "features": list(metadata.features),
                "support_reason": metadata.support_reason,
                "updated_at": metadata.updated_at,
            }
        )
    return rows


def select_computer_use_target_sid(context_id: str) -> str | None:
    with _state_lock:
        for sid in _candidate_sids_for_context_locked(context_id):
            metadata = _sid_computer_use_metadata.get(sid)
            if metadata and metadata.supported and metadata.enabled:
                return sid
    return None


def store_pending_file_op(
    op_id: str,
    *,
    sid: str,
    future: asyncio.Future[dict[str, Any]],
    loop: asyncio.AbstractEventLoop,
    context_id: str | None = None,
) -> None:
    with _state_lock:
        _pending_file_ops[op_id] = PendingFileOperation(
            sid=sid,
            loop=loop,
            future=future,
            context_id=context_id,
        )


def clear_pending_file_op(op_id: str) -> None:
    with _state_lock:
        _pending_file_ops.pop(op_id, None)


def resolve_pending_file_op(
    op_id: str,
    *,
    sid: str,
    payload: dict[str, Any],
) -> bool:
    return _resolve_pending(_pending_file_ops, op_id, sid=sid, payload=payload)


def fail_pending_file_op(
    op_id: str,
    *,
    sid: str | None = None,
    error: str,
) -> bool:
    return _fail_pending(_pending_file_ops, op_id, sid=sid, error=error)


def fail_pending_file_ops_for_sid(sid: str, *, error: str) -> None:
    _fail_pending_for_sid(_pending_file_ops, sid=sid, error=error)


def store_pending_exec_op(
    op_id: str,
    *,
    sid: str,
    future: asyncio.Future[dict[str, Any]],
    loop: asyncio.AbstractEventLoop,
    context_id: str | None = None,
) -> None:
    with _state_lock:
        _pending_exec_ops[op_id] = PendingExecOperation(
            sid=sid,
            loop=loop,
            future=future,
            context_id=context_id,
        )


def clear_pending_exec_op(op_id: str) -> None:
    with _state_lock:
        _pending_exec_ops.pop(op_id, None)


def resolve_pending_exec_op(
    op_id: str,
    *,
    sid: str,
    payload: dict[str, Any],
) -> bool:
    return _resolve_pending(_pending_exec_ops, op_id, sid=sid, payload=payload)


def fail_pending_exec_op(
    op_id: str,
    *,
    sid: str | None = None,
    error: str,
) -> bool:
    return _fail_pending(_pending_exec_ops, op_id, sid=sid, error=error)


def fail_pending_exec_ops_for_sid(sid: str, *, error: str) -> None:
    _fail_pending_for_sid(_pending_exec_ops, sid=sid, error=error)


def store_pending_computer_use_op(
    op_id: str,
    *,
    sid: str,
    future: asyncio.Future[dict[str, Any]],
    loop: asyncio.AbstractEventLoop,
    context_id: str | None = None,
) -> None:
    with _state_lock:
        _pending_computer_use_ops[op_id] = PendingComputerUseOperation(
            sid=sid,
            loop=loop,
            future=future,
            context_id=context_id,
        )


def clear_pending_computer_use_op(op_id: str) -> None:
    with _state_lock:
        _pending_computer_use_ops.pop(op_id, None)


def resolve_pending_computer_use_op(
    op_id: str,
    *,
    sid: str,
    payload: dict[str, Any],
) -> bool:
    return _resolve_pending(_pending_computer_use_ops, op_id, sid=sid, payload=payload)


def fail_pending_computer_use_op(
    op_id: str,
    *,
    sid: str | None = None,
    error: str,
) -> bool:
    return _fail_pending(_pending_computer_use_ops, op_id, sid=sid, error=error)


def fail_pending_computer_use_ops_for_sid(sid: str, *, error: str) -> None:
    _fail_pending_for_sid(_pending_computer_use_ops, sid=sid, error=error)


def store_pending_browser_op(
    op_id: str,
    *,
    sid: str,
    future: asyncio.Future[dict[str, Any]],
    loop: asyncio.AbstractEventLoop,
    context_id: str | None = None,
) -> None:
    with _state_lock:
        _pending_browser_ops[op_id] = PendingBrowserOperation(
            sid=sid,
            loop=loop,
            future=future,
            context_id=context_id,
        )


def clear_pending_browser_op(op_id: str) -> None:
    with _state_lock:
        _pending_browser_ops.pop(op_id, None)


def resolve_pending_browser_op(
    op_id: str,
    *,
    sid: str,
    payload: dict[str, Any],
) -> bool:
    return _resolve_pending(_pending_browser_ops, op_id, sid=sid, payload=payload)


def fail_pending_browser_op(
    op_id: str,
    *,
    sid: str | None = None,
    error: str,
) -> bool:
    return _fail_pending(_pending_browser_ops, op_id, sid=sid, error=error)


def fail_pending_browser_ops_for_sid(sid: str, *, error: str) -> None:
    _fail_pending_for_sid(_pending_browser_ops, sid=sid, error=error)


def _resolve_pending(
    registry: dict[str, PendingFileOperation | PendingExecOperation | PendingComputerUseOperation | PendingBrowserOperation],
    op_id: str,
    *,
    sid: str,
    payload: dict[str, Any],
) -> bool:
    with _state_lock:
        pending = registry.get(op_id)
        if pending is None or pending.sid != sid:
            return False
        registry.pop(op_id, None)

    pending.loop.call_soon_threadsafe(_set_future_result, pending.future, dict(payload))
    return True


def _fail_pending(
    registry: dict[str, PendingFileOperation | PendingExecOperation | PendingComputerUseOperation | PendingBrowserOperation],
    op_id: str,
    *,
    sid: str | None,
    error: str,
) -> bool:
    with _state_lock:
        pending = registry.get(op_id)
        if pending is None:
            return False
        if sid is not None and pending.sid != sid:
            return False
        registry.pop(op_id, None)

    pending.loop.call_soon_threadsafe(
        _set_future_result,
        pending.future,
        {"op_id": op_id, "ok": False, "error": error},
    )
    return True


def _fail_pending_for_sid(
    registry: dict[str, PendingFileOperation | PendingExecOperation | PendingComputerUseOperation | PendingBrowserOperation],
    *,
    sid: str,
    error: str,
) -> None:
    with _state_lock:
        matches = [
            (op_id, pending)
            for op_id, pending in registry.items()
            if pending.sid == sid
        ]
        for op_id, _pending in matches:
            registry.pop(op_id, None)

    for op_id, pending in matches:
        pending.loop.call_soon_threadsafe(
            _set_future_result,
            pending.future,
            {"op_id": op_id, "ok": False, "error": error},
        )


def _set_future_result(
    future: asyncio.Future[dict[str, Any]],
    payload: dict[str, Any],
) -> None:
    if not future.done():
        future.set_result(payload)
