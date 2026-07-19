# ws_manager.py DOX

## Purpose

- Own the `ws_manager.py` helper module.
- This module manages WebSocket connections, event validation, buffering, and dispatch.
- Keep this file-level DOX profile synchronized with `ws_manager.py` because this directory is intentionally flat.

## Ownership

- `ws_manager.py` owns the runtime implementation.
- `ws_manager.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `WsResult` (no explicit base class)
  - `ok(cls, data: dict[str, Any] | None=..., correlation_id: str | None=..., duration_ms: float | None=...) -> 'WsResult'`
  - `error(cls, code: str, message: str, details: Any | None=..., correlation_id: str | None=..., duration_ms: float | None=...) -> 'WsResult'`
  - `as_result(self, handler_id: str, fallback_correlation_id: str | None, duration_ms: float | None=...) -> dict[str, Any]`
- `BufferedEvent` (no explicit base class)
- `ConnectionInfo` (no explicit base class)
- `_HandlerExecution` (no explicit base class)
- `WsManager` (no explicit base class)
  - `register_diagnostic_watcher(self, namespace: str, sid: str) -> bool`
  - `unregister_diagnostic_watcher(self, namespace: str, sid: str) -> None`
  - `register_handlers(self, handlers_by_namespace: dict[str, Iterable[WsHandler]]) -> None`
  - `iter_namespaces(self) -> list[str]`
  - `async process_client_event(self, namespace: str, event_type: str, data: dict[str, Any], sid: str, handlers: list[WsHandler]) -> dict[str, Any]`
  - `async handle_connect(self, namespace: str, sid: str, user_id: str | None=...) -> None`
  - `async handle_disconnect(self, namespace: str, sid: str) -> None`
  - `async route_event(self, namespace: str, event_type: str, data: dict[str, Any], sid: str, ack: Optional[Callable[[Any], None]]=..., include_handlers: Set[str] | None=..., exclude_handlers: Set[str] | None=..., allow_exclude: bool=..., handler_id: str | None=...) -> dict[str, Any]`
- Top-level functions:
- `validate_event_type(event_type: str) -> str`: Validate an event name: must be lowercase_snake_case and not reserved.
- `async send_data(event_type: str, data: dict[str, Any], endpoint_name: str=..., connection_id: str | None=...) -> None`: Convenience wrapper around :pymeth:`WsManager.send_data`.
- `_utcnow() -> datetime`
- `set_shared_ws_manager(manager: 'WsManager') -> None`
- `get_shared_ws_manager() -> 'WsManager'`
- Notable constants/configuration names: `_EVENT_NAME_PATTERN`, `_RESERVED_EVENT_NAMES`, `BUFFER_MAX_SIZE`, `BUFFER_TTL`, `DIAGNOSTIC_EVENT`, `LIFECYCLE_CONNECT_EVENT`, `LIFECYCLE_DISCONNECT_EVENT`, `STATE_PUSH_EVENT`, `SERVER_RESTART_EVENT`, `ERR_NO_HANDLERS`, `ERR_HANDLER_ERROR`, `ERR_INVALID_FILTER`, `ERR_INVALID_EVENT`, `ERR_CONNECTION_NOT_FOUND`, `ERR_TIMEOUT`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion, network calls, WebSocket state, settings/state persistence, scheduler state.
- Imported dependency areas include: `__future__`, `asyncio`, `collections`, `dataclasses`, `datetime`, `helpers`, `helpers.defer`, `helpers.print_style`, `helpers.ws`, `os`, `re`, `socketio`, `threading`, `time`, `typing`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `re.compile`, `timedelta`, `get_shared_ws_manager`, `datetime.now`, `field`, `cls`, `TypeError`, `_EVENT_NAME_PATTERN.fullmatch`, `ValueError`, `manager.send_data`, `RuntimeError`, `defaultdict`, `runtime.is_development`, `ws_debug`, `self._ensure_dispatcher_loop`, `dispatcher_loop.is_closed`, `asyncio.run_coroutine_threadsafe`, `_utcnow.isoformat.replace`, `self._copy_diagnostic_watchers`, `self._lifecycle_tasks.add`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_state_sync_handler.py`
  - `tests/test_state_sync_welcome_screen.py`
  - `tests/test_tool_action_contracts.py`
  - `tests/test_ws_handlers.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
