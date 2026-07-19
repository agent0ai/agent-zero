# poll.py DOX

## Purpose

- Own the `poll.py` API endpoint.
- This module returns chat/log/status changes for polling clients.
- Keep this file-level DOX profile synchronized with `poll.py` because this directory is intentionally flat.

## Ownership

- `poll.py` owns the runtime implementation.
- `poll.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Poll` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Poll` is an `ApiHandler`.
- `Poll` defines `process(...)`.
- Observed side-effect areas: settings/state persistence.
- Imported dependency areas include: `helpers.api`, `helpers.state_snapshot`.

## Key Concepts

- Important called helpers/classes observed in the source: `build_snapshot`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_multi_tab_isolation.py`
  - `tests/test_oauth_github_copilot.py`
  - `tests/test_oauth_providers.py`
  - `tests/test_office_document_store.py`
  - `tests/test_snapshot_parity.py`
  - `tests/test_snapshot_schema_v1.py`
  - `tests/test_timezone_regressions.py`
  - `tests/test_tunnel_remote_link.py`

## Child DOX Index

No child DOX files.
