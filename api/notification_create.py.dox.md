# notification_create.py DOX

## Purpose

- Own the `notification_create.py` API endpoint.
- This module handles notification notification create requests.
- Keep this file-level DOX profile synchronized with `notification_create.py` because this directory is intentionally flat.

## Ownership

- `notification_create.py` owns the runtime implementation.
- `notification_create.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `NotificationCreate` (`ApiHandler`)
  - `requires_auth(cls) -> bool`
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `NotificationCreate` is an `ApiHandler`.
- `NotificationCreate` defines `process(...)`.
- `NotificationCreate` defines `requires_auth(...)`.
- Imported dependency areas include: `flask`, `helpers.api`, `helpers.notification`.

## Key Concepts

- Important called helpers/classes observed in the source: `NotificationManager.send_notification`, `NotificationType`, `notification.output`, `notification_type.lower`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_download_toast_regressions.py`

## Child DOX Index

No child DOX files.
