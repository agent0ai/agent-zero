# rfc.py DOX

## Purpose

- Own the `rfc.py` API endpoint.
- This module dispatches remote function calls through the RFC helper layer.
- Keep this file-level DOX profile synchronized with `rfc.py` because this directory is intentionally flat.

## Ownership

- `rfc.py` owns the runtime implementation.
- `rfc.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `RFC` (`ApiHandler`)
  - `requires_csrf(cls) -> bool`
  - `requires_auth(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `RFC` is an `ApiHandler`.
- `RFC` defines `process(...)`.
- `RFC` defines `requires_auth(...)`.
- `RFC` defines `requires_csrf(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `runtime.handle_rfc`.
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
