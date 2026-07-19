# ws_hello.py DOX

## Purpose

- Own the `ws_hello.py` API endpoint.
- This module provides a small WebSocket hello/test namespace.
- Keep this file-level DOX profile synchronized with `ws_hello.py` because this directory is intentionally flat.

## Ownership

- `ws_hello.py` owns the runtime implementation.
- `ws_hello.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `WsHello` (`WsHandler`)
  - `async process(self, event: str, data: dict, sid: str) -> dict | None`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `WsHello` is a `WsHandler`.
- `WsHello` defines `process(...)`.
- Observed side-effect areas: WebSocket state.
- Imported dependency areas include: `helpers.print_style`, `helpers.ws`.

## Key Concepts

- Important called helpers/classes observed in the source: `PrintStyle.info`.
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
