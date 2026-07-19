# restart.py DOX

## Purpose

- Own the `restart.py` API endpoint.
- This module requests server restart or reload behavior.
- Keep this file-level DOX profile synchronized with `restart.py` because this directory is intentionally flat.

## Ownership

- `restart.py` owns the runtime implementation.
- `restart.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Restart` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Restart` is an `ApiHandler`.
- `Restart` defines `process(...)`.
- Imported dependency areas include: `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `process.reload`, `Response`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_self_update_tag_filter.py`
  - `tests/test_timezone_regressions.py`
  - `tests/test_ws_manager.py`

## Child DOX Index

No child DOX files.
