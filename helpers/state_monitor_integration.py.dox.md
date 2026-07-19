# state_monitor_integration.py DOX

## Purpose

- Own the `state_monitor_integration.py` helper module.
- This module bridges dirty-state calls into the shared state monitor.
- Keep this file-level DOX profile synchronized with `state_monitor_integration.py` because this directory is intentionally flat.

## Ownership

- `state_monitor_integration.py` owns the runtime implementation.
- `state_monitor_integration.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `mark_dirty_all(reason: str | None=...) -> None`
- `mark_dirty_for_context(context_id: str, reason: str | None=...) -> None`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: settings/state persistence.
- Imported dependency areas include: `__future__`.

## Key Concepts

- Important called helpers/classes observed in the source: `get_state_monitor.mark_dirty_all`, `get_state_monitor.mark_dirty_for_context`, `get_state_monitor`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_model_config_api_keys.py`

## Child DOX Index

No child DOX files.
