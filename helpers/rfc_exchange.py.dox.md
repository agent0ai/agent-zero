# rfc_exchange.py DOX

## Purpose

- Own the `rfc_exchange.py` helper module.
- This module handles privileged RFC exchange data such as root password provisioning.
- Keep this file-level DOX profile synchronized with `rfc_exchange.py` because this directory is intentionally flat.

## Ownership

- `rfc_exchange.py` owns the runtime implementation.
- `rfc_exchange.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Top-level functions:
- `async get_root_password()`
- `_provide_root_password(public_key_pem: str)`
- `_get_root_password()`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Imported dependency areas include: `helpers`.

## Key Concepts

- Important called helpers/classes observed in the source: `runtime.is_dockerized`, `_get_root_password`, `crypto.encrypt_data`, `crypto._generate_private_key`, `crypto._generate_public_key`, `crypto.decrypt_data`, `dotenv.get_dotenv_value`, `runtime.call_development_function`.
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
