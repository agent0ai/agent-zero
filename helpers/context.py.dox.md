# context.py DOX

## Purpose

- Own the `context.py` helper module.
- This module provides compatibility helpers for reading and writing `AgentContext` data.
- Keep this file-level DOX profile synchronized with `context.py` because this directory is intentionally flat.

## Ownership

- `context.py` owns the runtime implementation.
- `context.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `_ensure_context() -> Dict[str, Any]`: Make sure a context dict exists, and return it.
- `set_context_data(key: str, value: Any)`: Set context data for the current async/task context.
- `delete_context_data(key: str)`: Delete a key from the current async/task context.
- `get_context_data(key: Optional[str]=..., default: T=...) -> T`: Get a key from the current context, or the full dict if key is None.
- `clear_context_data()`: Completely clear the context dict.
- Notable constants/configuration names: `T`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion, scheduler state.
- Imported dependency areas include: `contextvars`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `TypeVar`, `ContextVar`, `_ensure_context`, `cast`.
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
  - `tests/test_document_query_plugin.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_extensions_stress.py`
  - `tests/test_file_tree_visualize.py`
  - `tests/test_history_compression_wait.py`

## Child DOX Index

No child DOX files.
