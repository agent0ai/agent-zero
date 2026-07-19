# runtime.py DOX

## Purpose

- Own the `runtime.py` helper module.
- This module owns runtime identity, environment flags, and startup arguments.
- Keep this file-level DOX profile synchronized with `runtime.py` because this directory is intentionally flat.

## Ownership

- `runtime.py` owns the runtime implementation.
- `runtime.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `initialize()`
- `get_arg(name: str)`
- `has_arg(name: str)`
- `is_dockerized() -> bool`
- `is_development() -> bool`
- `get_local_url()`
- `get_runtime_id() -> str`
- `get_persistent_id() -> str`
- `async call_development_function(func: Callable[..., Awaitable[T]], *args, **kwargs) -> T`
- `async call_development_function(func: Callable[..., T], *args, **kwargs) -> T`
- `async call_development_function(func: Union[Callable[..., T], Callable[..., Awaitable[T]]], *args, **kwargs) -> T`
- `async handle_rfc(rfc_call: rfc.RFCCall)`
- `_get_rfc_password() -> str`
- `_get_rfc_url() -> str`
- `call_development_function_sync(func: Union[Callable[..., T], Callable[..., Awaitable[T]]], *args, **kwargs) -> T`
- `get_web_ui_port()`
- `get_tunnel_api_port()`
- `get_platform()`
- `is_windows()`
- `get_terminal_executable()`
- Notable constants/configuration names: `T`, `R`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, subprocess/runtime control, settings/state persistence, secret handling, tunnel state.
- Imported dependency areas include: `argparse`, `asyncio`, `helpers`, `inspect`, `nest_asyncio`, `pathlib`, `queue`, `secrets`, `sys`, `threading`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `nest_asyncio.apply`, `TypeVar`, `argparse.ArgumentParser`, `parser.add_argument`, `parser.parse_known_args`, `vars`, `is_dockerized`, `dotenv.get_dotenv_value`, `is_development`, `settings.get_settings`, `url.endswith`, `queue.Queue`, `threading.Thread`, `thread.start`, `thread.join`, `thread.is_alive`, `result_queue.get_nowait`, `cast`, `is_windows`, `get_arg`.
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
  - `tests/test_default_prompt_budget.py`
  - `tests/test_document_query_plugin.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_http_auth_csrf.py`
  - `tests/test_image_get_security.py`

## Child DOX Index

No child DOX files.
