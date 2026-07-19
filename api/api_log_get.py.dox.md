# api_log_get.py DOX

## Purpose

- Own the `api_log_get.py` API endpoint.
- This module returns API/chat log data for external API clients.
- Keep this file-level DOX profile synchronized with `api_log_get.py` because this directory is intentionally flat.

## Ownership

- `api_log_get.py` owns the runtime implementation.
- `api_log_get.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ApiLogGet` (`ApiHandler`)
  - `get_methods(cls) -> list[str]`
  - `requires_auth(cls) -> bool`
  - `requires_csrf(cls) -> bool`
  - `requires_api_key(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `ApiLogGet` is an `ApiHandler`.
- `ApiLogGet` defines `process(...)`.
- `ApiLogGet` defines `get_methods(...)`.
- `ApiLogGet` defines `requires_auth(...)`.
- `ApiLogGet` defines `requires_csrf(...)`.
- `ApiLogGet` defines `requires_api_key(...)`.
- Observed side-effect areas: settings/state persistence, secret handling.
- Imported dependency areas include: `agent`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `AgentContext.use`, `Response`, `context.log.output`.
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
