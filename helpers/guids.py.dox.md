# guids.py DOX

## Purpose

- Own the `guids.py` helper module.
- This module generates framework IDs.
- Keep this file-level DOX profile synchronized with `guids.py` because this directory is intentionally flat.

## Ownership

- `guids.py` owns the runtime implementation.
- `guids.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `generate_id(length: int=...) -> str`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `random`, `string`.

## Key Concepts

- Important called helpers/classes observed in the source: `join`, `random.choices`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
