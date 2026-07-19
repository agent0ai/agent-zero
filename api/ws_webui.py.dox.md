# ws_webui.py DOX

## Purpose

- Own the `ws_webui.py` API endpoint.
- This module owns the primary WebUI WebSocket namespace and event bridge.
- Keep this file-level DOX profile synchronized with `ws_webui.py` because this directory is intentionally flat.

## Ownership

- `ws_webui.py` owns the runtime implementation.
- `ws_webui.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `WsWebui` (`WsHandler`)
  - `async on_connect(self, sid: str) -> None`
  - `async on_disconnect(self, sid: str) -> None`
  - `async process(self, event: str, data: dict, sid: str) -> dict | None`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `WsWebui` is a `WsHandler`.
- `WsWebui` defines `process(...)`.
- Observed side-effect areas: network calls, WebSocket state, settings/state persistence.
- Imported dependency areas include: `helpers`, `helpers.ws`.

## Key Concepts

- Important called helpers/classes observed in the source: `extension.call_extensions_async`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_state_sync_handler.py`
  - `tests/test_state_sync_welcome_screen.py`
  - `tests/test_ws_handlers.py`

## Child DOX Index

No child DOX files.
