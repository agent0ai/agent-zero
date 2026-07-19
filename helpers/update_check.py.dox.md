# update_check.py DOX

## Purpose

- Own the `update_check.py` helper module.
- This module checks available Agent Zero updates.
- Keep this file-level DOX profile synchronized with `update_check.py` because this directory is intentionally flat.

## Ownership

- `update_check.py` owns the runtime implementation.
- `update_check.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `async check_version()`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: network calls, settings/state persistence.
- Imported dependency areas include: `hashlib`, `helpers`.

## Key Concepts

- Important called helpers/classes observed in the source: `git.get_version`, `git.is_official_agent_zero_repo`, `hashlib.sha256.hexdigest`, `httpx.AsyncClient`, `response.json`, `client.post`, `hashlib.sha256`, `runtime.get_persistent_id.encode`, `runtime.get_persistent_id`.
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
