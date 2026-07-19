# message_queue_remove.py DOX

## Purpose

- Own the `message_queue_remove.py` API endpoint.
- This module handles message queue remove API requests.
- Keep this file-level DOX profile synchronized with `message_queue_remove.py` because this directory is intentionally flat.

## Ownership

- `message_queue_remove.py` owns the runtime implementation.
- `message_queue_remove.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `MessageQueueRemove` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `MessageQueueRemove` is an `ApiHandler`.
- `MessageQueueRemove` defines `process(...)`.
- Observed side-effect areas: filesystem deletion, settings/state persistence.
- Imported dependency areas include: `agent`, `helpers`, `helpers.api`, `helpers.state_monitor_integration`.

## Key Concepts

- Important called helpers/classes observed in the source: `mq.remove`, `mark_dirty_for_context`, `Response`.
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
