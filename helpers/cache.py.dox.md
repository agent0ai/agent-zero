# cache.py DOX

## Purpose

- Own the `cache.py` helper module.
- This module provides in-process cache areas with optional global and area toggles.
- Keep this file-level DOX profile synchronized with `cache.py` because this directory is intentionally flat.

## Ownership

- `cache.py` owns the runtime implementation.
- `cache.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `CacheEntry` (no explicit base class)
- Top-level functions:
- `toggle_global(enabled: bool) -> None`
- `toggle_area(area: str, enabled: bool) -> None`
- `has(area: str, key: Any) -> bool`
- `add(area: str, key: Any, data: Any) -> None`
- `get(area: str, key: Any, default: Any=...) -> Any`
- `remove(area: str, key: Any) -> None`
- `clear(area: str) -> None`
- `trim_cache(area: str, seconds: float=...) -> None`
- `clear_all() -> None`
- `_is_enabled(area: str) -> bool`
- `_create_entry(value: Any) -> CacheEntry`
- `_touch_entry(entry: CacheEntry) -> None`
- `_get_matching_areas(area: str) -> list[str]`
- `determine_cache_key(agent, *additional)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion, plugin state, settings/state persistence.
- Imported dependency areas include: `dataclasses`, `fnmatch`, `threading`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `threading.RLock`, `dataclass`, `CacheEntry`, `time.time`, `_is_enabled`, `_touch_entry`, `_create_entry`, `_cache.pop`, `_get_matching_areas`, `_cache.clear`, `agent.context.get_data`, `area_cache.pop`, `fnmatch.fnmatch`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_file_tree_visualize.py`
  - `tests/test_office_canvas_setup.py`
  - `tests/test_office_document_store.py`
  - `tests/test_self_update_tag_filter.py`
  - `tests/test_time_travel.py`
  - `tests/test_webui_extension_surfaces.py`
  - `tests/test_whatsapp_bridge_manager.py`

## Child DOX Index

No child DOX files.
