# nudge.py DOX

## Purpose

- Own the `nudge.py` API endpoint.
- This module handles nudge API requests.
- Keep this file-level DOX profile synchronized with `nudge.py` because this directory is intentionally flat.

## Ownership

- `nudge.py` owns the runtime implementation.
- `nudge.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Nudge` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Nudge` is an `ApiHandler`.
- `Nudge` defines `process(...)`.
- Imported dependency areas include: `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.use_context`, `context.nudge`, `context.log.log`, `Exception`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`

## Child DOX Index

No child DOX files.
