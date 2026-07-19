# functions.py DOX

## Purpose

- Own the `functions.py` helper module.
- This module provides safe generic callable execution helpers.
- Keep this file-level DOX profile synchronized with `functions.py` because this directory is intentionally flat.

## Ownership

- `functions.py` owns the runtime implementation.
- `functions.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `safe_call(func, *args, **kwargs)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `inspect`.

## Key Concepts

- Important called helpers/classes observed in the source: `inspect.signature`, `func`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_error_retry_plugin.py`
  - `tests/test_oauth_codex.py`
  - `tests/test_oauth_providers.py`

## Child DOX Index

No child DOX files.
