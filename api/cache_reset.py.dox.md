# cache_reset.py DOX

## Purpose

- Own the `cache_reset.py` API endpoint.
- This module handles cache reset API requests.
- Keep this file-level DOX profile synchronized with `cache_reset.py` because this directory is intentionally flat.

## Ownership

- `cache_reset.py` owns the runtime implementation.
- `cache_reset.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `CacheReset` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_csrf(cls) -> bool`
  - `requires_api_key(cls) -> bool`
  - `requires_loopback(cls) -> bool`
  - `get_methods(cls) -> list[str]`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `CacheReset` is an `ApiHandler`.
- `CacheReset` defines `process(...)`.
- `CacheReset` defines `get_methods(...)`.
- `CacheReset` defines `requires_auth(...)`.
- `CacheReset` defines `requires_csrf(...)`.
- `CacheReset` defines `requires_api_key(...)`.
- `CacheReset` defines `requires_loopback(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `cache.clear_all`, `cache.clear`.
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
