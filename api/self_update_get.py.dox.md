# self_update_get.py DOX

## Purpose

- Own the `self_update_get.py` API endpoint.
- This module handles self update get API requests.
- Keep this file-level DOX profile synchronized with `self_update_get.py` because this directory is intentionally flat.

## Ownership

- `self_update_get.py` owns the runtime implementation.
- `self_update_get.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `SelfUpdateGet` (`ApiHandler`)
  - `get_methods(cls) -> list[str]`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `SelfUpdateGet` is an `ApiHandler`.
- `SelfUpdateGet` defines `process(...)`.
- `SelfUpdateGet` defines `get_methods(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `self_update.get_update_info`, `runtime.is_dockerized`, `self_update.load_pending_update`, `self_update.load_last_status`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
