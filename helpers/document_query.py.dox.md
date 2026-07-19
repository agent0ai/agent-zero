# document_query.py DOX

## Purpose

- Own the `document_query.py` helper module.
- This module provides compatibility exports for document query behavior.
- Keep this file-level DOX profile synchronized with `document_query.py` because this directory is intentionally flat.

## Ownership

- `document_query.py` owns the runtime implementation.
- `document_query.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: plugin state.
- Imported dependency areas include: `plugins._document_query.helpers.document_query`.

## Key Concepts

- This module is primarily declarative or delegates behavior through classes/imported objects.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_document_query_fallback.py`
  - `tests/test_document_query_plugin.py`

## Child DOX Index

No child DOX files.
