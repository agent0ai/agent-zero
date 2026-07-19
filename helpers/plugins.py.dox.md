# plugins.py DOX

## Purpose

- Own the `plugins.py` helper module.
- This module discovers plugins, resolves plugin config/toggles, runs hooks, and tracks plugin updates.
- Keep this file-level DOX profile synchronized with `plugins.py` because this directory is intentionally flat.

## Ownership

- `plugins.py` owns the runtime implementation.
- `plugins.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `PluginAssetFile` (`TypedDict`)
- `PluginMetadata` (`BaseModel`)
- `PluginListItem` (`BaseModel`)
- `PluginUpdateInfo` (`BaseModel`)
- Top-level functions:
- `register_watchdogs()`
- `after_plugin_change(plugin_names: list[str] | None=..., python_change: bool=...)`
- `refresh_plugin_modules(plugin_names: list[str] | None=...)`
- `clear_plugin_cache(plugin_names: list[str] | None=...)`
- `get_plugin_roots(plugin_name: str=...) -> List[str]`: Plugin root directories, ordered by priority (user first).
- `get_plugins_list()`
- `get_enhanced_plugins_list(custom: bool=..., builtin: bool=..., plugin_names: list[str] | None=...) -> List[PluginListItem]`: Discover plugins by directory convention. First root wins on ID conflict.
- `get_custom_plugins_updates(plugin_names: list[str] | None=...) -> List[PluginUpdateInfo]`
- `get_plugin_meta(plugin_name: str)`
- `find_plugin_dir(plugin_name: str)`
- `uninstall_plugin(plugin_name)`
- `delete_plugin(plugin_name: str)`
- `get_plugin_paths(*subpaths) -> List[str]`
- `get_enabled_plugin_paths(agent: Agent | None, *subpaths) -> List[str]`
- `get_enabled_plugins(agent: Agent | None)`
- `determined_toggle_from_paths(default: bool, paths: Iterator[str])`
- `get_toggle_state(plugin_name: str) -> ToggleState`
- `toggle_plugin(plugin_name: str, enabled: bool, project_name: str=..., agent_profile: str=..., clear_overrides: bool=...)`
- `get_plugin_config(plugin_name: str, agent: Agent | None=..., project_name: str | None=..., agent_profile: str | None=...)`
- `get_default_plugin_config(plugin_name: str)`
- `save_plugin_config(plugin_name: str, project_name: str, agent_profile: str, settings: dict)`
- `find_plugin_asset(plugin_name: str, *subpaths, project_name=..., agent_profile=...)`
- `find_plugin_assets(*subpaths, plugin_name: str=..., project_name: str=..., agent_profile: str=..., only_first: bool=...) -> list[PluginAssetFile]`
- `determine_plugin_asset_path(plugin_name: str, project_name: str, agent_profile: str, *subpaths)`
- `send_frontend_reload_notification(plugin_names: list[str] | None=...)`: If the plugin changed has webui extensions, show a persistent reload notification that marks itself read before refreshing
- `call_plugin_hook(plugin_name: str, hook_name: str, default: Any=..., *args, **kwargs)`
- `_apply_defaults_from_env(plugin_name: str, config: dict[str, Any])`
- Notable constants/configuration names: `_META_TARGET_RE`, `META_FILE_NAME`, `CONFIG_FILE_NAME`, `CONFIG_DEFAULT_FILE_NAME`, `DISABLED_FILE_NAME`, `ENABLED_FILE_NAME`, `TOGGLE_FILE_PATTERN`, `HOOKS_SCRIPT`, `HOOKS_CACHE_AREA`, `PLUGINS_LIST_CACHE_AREA`, `ENABLED_PLUGINS_LIST_CACHE_AREA`, `ENABLED_PLUGINS_PATHS_CACHE_AREA`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, WebSocket state, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `__future__`, `asyncio`, `glob`, `helpers`, `helpers.defer`, `helpers.watchdog`, `json`, `pathlib`, `pydantic`, `re`, `regex`, `time`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `re.compile`, `Field`, `watchdog.add_watchdog`, `clear_plugin_cache`, `send_frontend_reload_notification`, `DeferredTask.start_task`, `get_plugin_roots`, `result.sort`, `cache.add`, `get_enhanced_plugins_list`, `find_plugin_dir`, `files.get_abs_path`, `files.exists`, `call_plugin_hook`, `delete_plugin`, `files.delete_dir`, `after_plugin_change`, `get_enabled_plugins`, `get_plugins_list`, `get_plugin_meta`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_computer_use_metadata.py`
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_chat_compaction.py`
  - `tests/test_default_prompt_budget.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_host_browser_connector.py`

## Child DOX Index

No child DOX files.
