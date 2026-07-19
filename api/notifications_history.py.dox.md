# notifications_history.py DOX

## Purpose

- Own the `notifications_history.py` API endpoint.
- This module handles notification notifications history requests.
- Keep this file-level DOX profile synchronized with `notifications_history.py` because this directory is intentionally flat.

## Ownership

- `notifications_history.py` owns the runtime implementation.
- `notifications_history.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `NotificationsHistory` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `NotificationsHistory` is an `ApiHandler`.
- `NotificationsHistory` defines `process(...)`.
- `NotificationsHistory` defines `requires_auth(...)`.
- Imported dependency areas include: `agent`, `flask`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `AgentContext.get_notification_manager`, `notification_manager.output_all`.
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
