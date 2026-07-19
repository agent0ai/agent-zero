# rfc.py DOX

## Purpose

- Own the `rfc.py` helper module.
- This module implements remote function call dispatch and serialization.
- Keep this file-level DOX profile synchronized with `rfc.py` because this directory is intentionally flat.

## Ownership

- `rfc.py` owns the runtime implementation.
- `rfc.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RFCInput` (`TypedDict`)
- `RFCCall` (`TypedDict`)
- Top-level functions:
- `async call_rfc(url: str, password: str, module: str, function_name: str, args: list, kwargs: dict)`
- `async handle_rfc(rfc_call: RFCCall, password: str)`
- `async _call_function(module: str, function_name: str, *args, **kwargs)`
- `_get_function(module: str, function_name: str)`
- `async _send_json_data(url: str, data)`

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem writes, network calls, settings/state persistence, secret handling.
- Imported dependency areas include: `aiohttp`, `helpers`, `importlib`, `inspect`, `json`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `RFCInput`, `RFCCall`, `json.loads`, `_get_function`, `inspect.iscoroutinefunction`, `importlib.import_module`, `_send_json_data`, `crypto.verify_data`, `Exception`, `_call_function`, `func`, `aiohttp.ClientSession`, `json.dumps`, `crypto.hash_data`, `session.post`, `response.json`, `response.text`.
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
