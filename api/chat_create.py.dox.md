# chat_create.py DOX

## Purpose

- Own the `chat_create.py` API endpoint.
- This module handles chat create requests.
- Keep this file-level DOX profile synchronized with `chat_create.py` because this directory is intentionally flat.

## Ownership

- `chat_create.py` owns the runtime implementation.
- `chat_create.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `CreateChat` (`ApiHandler`)
  - `async process(self, input: Input, request: Request) -> Output`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `CreateChat` is an `ApiHandler`.
- `CreateChat` defines `process(...)`.
- Observed side-effect areas: filesystem writes, model calls, plugin state, settings/state persistence.
- Imported dependency areas include: `agent`, `helpers`, `helpers.api`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.use_context`, `mark_dirty_all`, `guids.generate_id`, `current_context.get_data`, `current_context.get_output_data`, `new_context.set_data`, `new_context.set_output_data`, `is_chat_override_allowed`, `settings.get_settings`.
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
