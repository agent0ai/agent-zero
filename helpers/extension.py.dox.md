# extension.py DOX

## Purpose

- Own the `extension.py` helper module.
- This module discovers and dispatches Python and WebUI extension hooks.
- Keep this file-level DOX profile synchronized with `extension.py` because this directory is intentionally flat.

## Ownership

- `extension.py` owns the runtime implementation.
- `extension.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `_Unset` (no explicit base class)
- `Extension` (no explicit base class)
  - `execute(self, **kwargs) -> None | Awaitable[None]`
- Top-level functions:
- `_log_extension_call(name: str)`
- `extensible(func)`: Make a function emit two implicit extension points around its execution.
- `async call_extensions_async(extension_point: str, agent: 'Agent|None'=..., **kwargs)`
- `call_extensions_sync(extension_point: str, agent: 'Agent|None'=..., **kwargs)`
- `get_webui_extensions(agent: 'Agent | None', extension_point: str, filters: list[str] | None=...)`
- `_get_extension_classes(extension_point: str, agent: 'Agent|None'=..., **kwargs) -> list[Type[Extension]]`
- `_get_file_from_module(module_name: str) -> str`
- `_get_extensions(folder: str)`
- `register_extensions_watchdogs()`
- Notable constants/configuration names: `DEFAULT_EXTENSIONS_FOLDER`, `USER_EXTENSIONS_FOLDER`, `_EXTENSIONS_CACHE_AREA`, `_CLASSES_CACHE_AREA`, `_UNSET`, `_EXTENSIONS_LOG_COUNTS`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- `Extension` defines `execute(...)`.
- Observed side-effect areas: filesystem reads, WebSocket state, plugin state.
- Imported dependency areas include: `abc`, `functools`, `helpers`, `helpers.print_style`, `inspect`, `os`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `_Unset`, `inspect.iscoroutinefunction`, `wraps`, `_log_extension_call`, `_get_extension_classes`, `subagents.get_paths`, `cache.determine_cache_key`, `cache.add`, `files.get_abs_path`, `modules.load_classes_from_folder`, `watchdog.add_watchdog`, `os.path.join`, `_get_agent`, `_prepare_inputs`, `_process_result`, `call_extensions_sync`, `cls.execute`, `files.deabsolute_path`, `_get_file_from_module`, `module_name.split`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_api_chat_lifetime.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_extensions_stress.py`
  - `tests/test_history_compression_wait.py`
  - `tests/test_model_config_api_keys.py`
  - `tests/test_oauth_codex.py`

## Child DOX Index

No child DOX files.
