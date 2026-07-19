# state_monitor.py DOX

## Purpose

- Own the `state_monitor.py` helper module.
- This module tracks dirty state and connection projections for WebUI sync.
- Keep this file-level DOX profile synchronized with `state_monitor.py` because this directory is intentionally flat.

## Ownership

- `state_monitor.py` owns the runtime implementation.
- `state_monitor.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ConnectionProjection` (no explicit base class)
- `StateMonitor` (no explicit base class)
  - `bind_manager(self, manager: 'WsManager', handler_id: str | None=...) -> None`
  - `register_sid(self, namespace: str, sid: str) -> None`
  - `unregister_sid(self, namespace: str, sid: str) -> None`
  - `mark_dirty_all(self, reason: str | None=...) -> None`
  - `mark_dirty_for_context(self, context_id: str, reason: str | None=...) -> None`
  - `update_projection(self, namespace: str, sid: str, request: StateRequestV1, seq_base: int) -> None`
  - `mark_dirty(self, namespace: str, sid: str, reason: str | None=..., wave_id: str | None=...) -> None`
- Top-level functions:
- `get_state_monitor() -> StateMonitor`
- `_reset_state_monitor_for_testing() -> None`
- Notable constants/configuration names: `_STATE_MONITOR_HOLDER`, `_STATE_MONITOR_LOCK`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion, WebSocket state, settings/state persistence, scheduler state.
- Imported dependency areas include: `__future__`, `asyncio`, `dataclasses`, `helpers`, `helpers.print_style`, `helpers.state_snapshot`, `helpers.ws`, `helpers.ws_manager`, `os`, `threading`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `threading.RLock`, `field`, `ws_debug`, `_ws_debug_enabled`, `context_id.strip`, `loop.call_soon_threadsafe`, `self._schedule_debounce_on_loop`, `asyncio.get_running_loop`, `asyncio.current_task`, `loop.is_closed`, `self._debounce_handles.pop`, `self._push_tasks.pop`, `self._projections.pop`, `self.mark_dirty`, `self._mark_dirty_on_loop`, `runtime.is_development`, `loop.call_later`, `StateMonitor`, `ConnectionProjection`, `handle.cancel`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_model_config_api_keys.py`
  - `tests/test_multi_tab_isolation.py`
  - `tests/test_state_monitor.py`
  - `tests/test_state_sync_handler.py`
  - `tests/test_state_sync_welcome_screen.py`
  - `tests/test_ws_handlers.py`

## Child DOX Index

No child DOX files.
