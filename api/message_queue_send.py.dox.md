# message_queue_send.py DOX

## Purpose

- Own the `message_queue_send.py` API endpoint.
- This module handles message queue send API requests.
- Keep this file-level DOX profile synchronized with `message_queue_send.py` because this directory is intentionally flat.

## Ownership

- `message_queue_send.py` owns the runtime implementation.
- `message_queue_send.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `MessageQueueSend` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `MessageQueueSend` is an `ApiHandler`.
- `MessageQueueSend` defines `process(...)`.
- Observed side-effect areas: settings/state persistence.
- Imported dependency areas include: `agent`, `helpers`, `helpers.api`, `helpers.state_monitor_integration`.

## Key Concepts

- Important called helpers/classes observed in the source: `mq.send_message`, `mark_dirty_for_context`, `Response`, `mq.has_queue`, `mq.send_all_aggregated`, `mq.pop_item`, `mq.pop_first`.
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
