# ws_dev_test.py DOX

## Purpose

- Own the `ws_dev_test.py` API endpoint.
- This module provides a development WebSocket test namespace.
- Keep this file-level DOX profile synchronized with `ws_dev_test.py` because this directory is intentionally flat.

## Ownership

- `ws_dev_test.py` owns the runtime implementation.
- `ws_dev_test.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `WsDevTest` (`WsHandler`)
  - `async process(self, event: str, data: dict, sid: str) -> dict[str, Any] | WsResult | None`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `WsDevTest` is a `WsHandler`.
- `WsDevTest` defines `process(...)`.
- Observed side-effect areas: filesystem writes, network calls, WebSocket state.
- Imported dependency areas include: `asyncio`, `helpers`, `helpers.print_style`, `helpers.ws`, `helpers.ws_manager`, `typing`.

## Key Concepts

- Important called helpers/classes observed in the source: `event.startswith`, `self.manager.register_diagnostic_watcher`, `self.manager.unregister_diagnostic_watcher`, `PrintStyle.info`, `PrintStyle.debug`, `PrintStyle.warning`, `runtime.is_development`, `WsResult.error`, `self.broadcast`, `asyncio.sleep`, `self.emit_to`, `self.dispatch_to_all_sids`.
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
