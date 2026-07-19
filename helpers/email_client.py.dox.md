# email_client.py DOX

## Purpose

- Own the `email_client.py` helper module.
- This module provides shared email client plumbing for mail integrations.
- Keep this file-level DOX profile synchronized with `email_client.py` because this directory is intentionally flat.

## Ownership

- `email_client.py` owns the runtime implementation.
- `email_client.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem reads, filesystem writes, filesystem deletion, WebSocket state, settings/state persistence, secret handling.

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
  - `tests/email_parser_test.py`

## Child DOX Index

No child DOX files.
