# login.py DOX

## Purpose

- Own the `login.py` helper module.
- This module checks login requirements and credential hashes.
- Keep this file-level DOX profile synchronized with `login.py` because this directory is intentionally flat.

## Ownership

- `login.py` owns the runtime implementation.
- `login.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `get_credentials_hash()`
- `is_login_required()`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: secret handling.
- Imported dependency areas include: `hashlib`, `helpers`.

## Key Concepts

- Important called helpers/classes observed in the source: `dotenv.get_dotenv_value`, `hashlib.sha256.hexdigest`, `hashlib.sha256`, `encode`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_http_auth_csrf.py`
  - `tests/test_oauth_gemini_api.py`
  - `tests/test_oauth_github_copilot.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_oauth_xai_grok.py`
  - `tests/test_tunnel_remote_link.py`
  - `tests/test_ws_security.py`

## Child DOX Index

No child DOX files.
