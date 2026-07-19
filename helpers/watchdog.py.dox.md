# watchdog.py DOX

## Purpose

- Own the `watchdog.py` helper module.
- This module registers filesystem watchdogs with debouncing and path filtering.
- Keep this file-level DOX profile synchronized with `watchdog.py` because this directory is intentionally flat.

## Ownership

- `watchdog.py` owns the runtime implementation.
- `watchdog.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `_DispatchHandler` (no explicit base class)
  - `dispatch(self, event: Any)`
- `_Watch` (no explicit base class)
- `_PendingBatch` (no explicit base class)
- `_WatchRegistry` (no explicit base class)
  - `add(self, id: str, roots: list[str], patterns: list[str] | None, ignore_patterns: list[str] | None, events: WatchEvents, debounce: float, handler: WatchHandler) -> None`
  - `remove(self, id: str) -> bool`
  - `clear(self) -> None`
  - `start(self) -> None`
  - `stop(self) -> None`
  - `dispatch(self, scheduled_root: str, event: Any) -> None`
- Top-level functions:
- `_normalize_root(root: str) -> str`
- `_normalize_roots(roots: list[str]) -> list[str]`
- `_normalize_patterns(patterns: list[str] | None, default: list[str] | None=...) -> list[str]`
- `_normalize_events(events: WatchEvents) -> frozenset[WatchEvent]`
- `_map_event_type(event_type: str) -> WatchEvent | None`
- `_normalize_debounce(debounce: float) -> float`
- `_covering_roots(roots: Iterable[str]) -> set[str]`
- `_is_same_or_nested(path: str, root: str) -> bool`
- `_is_under_watch(path: str, watch: _Watch) -> bool`
- `_compile_matcher(root: str, patterns: list[str], ignore_patterns: list[str]) -> PatternMatcher`
- `_compile_single_matcher(root: str, patterns: list[str]) -> PatternMatcher`
- `add_watchdog(id: str, roots: list[str], patterns: list[str] | None=..., ignore_patterns: list[str] | None=..., events: WatchEvents=..., debounce: float=..., handler: WatchHandler | None=...) -> None`
- `remove_watchdog(id: str) -> bool`
- `clear_watchdogs() -> None`
- `start_watchdog_daemon() -> None`
- `stop_watchdog_daemon() -> None`
- Notable constants/configuration names: `_DEFAULT_PATTERNS`, `_DEFAULT_IGNORE_PATTERNS`, `_VALID_EVENTS`, `_EVENT_ALIASES`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion.
- Imported dependency areas include: `__future__`, `dataclasses`, `os`, `pathlib`, `threading`, `typing`, `watchdog.observers`.

## Key Concepts

- Important called helpers/classes observed in the source: `frozenset`, `dataclass`, `_WatchRegistry`, `_registry.start`, `os.path.abspath`, `_compile_single_matcher`, `_registry.add`, `_registry.remove`, `_registry.clear`, `_registry.stop`, `self.registry.dispatch`, `threading.RLock`, `self._ensure_watchdog_available`, `_normalize_roots`, `_normalize_patterns`, `_normalize_events`, `_normalize_debounce`, `self._stop_observer`, `_map_event_type`, `_covering_roots`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_model_config_api_keys.py`
  - `tests/test_model_config_project_presets.py`
  - `tests/test_time_travel.py`

## Child DOX Index

No child DOX files.
