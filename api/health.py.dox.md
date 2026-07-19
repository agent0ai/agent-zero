# health.py DOX

## Purpose

- Own the `health.py` API endpoint.
- This module reports process health for probes and startup checks.
- Keep this file-level DOX profile synchronized with `health.py` because this directory is intentionally flat.

## Ownership

- `health.py` owns the runtime implementation.
- `health.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `HealthCheck` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `requires_csrf(cls) -> bool`
  - `get_methods(cls) -> list[str]`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `HealthCheck` is an `ApiHandler`.
- `HealthCheck` defines `process(...)`.
- `HealthCheck` defines `get_methods(...)`.
- `HealthCheck` defines `requires_auth(...)`.
- `HealthCheck` defines `requires_csrf(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `git.get_git_info`, `errors.error_text`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_oauth_providers.py`
  - `tests/test_office_document_store.py`
  - `tests/test_self_update_tag_filter.py`

## Child DOX Index

No child DOX files.
