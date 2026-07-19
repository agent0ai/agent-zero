# tunnel.py DOX

## Purpose

- Own the `tunnel.py` API endpoint.
- This module manages tunnel provider status, start, and stop actions.
- Keep this file-level DOX profile synchronized with `tunnel.py` because this directory is intentionally flat.

## Ownership

- `tunnel.py` owns the runtime implementation.
- `tunnel.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `Tunnel` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`
- Top-level functions:
- `async process(input: dict) -> dict | Response`
- `stop()`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `Tunnel` is an `ApiHandler`.
- `Tunnel` defines `process(...)`.
- Observed side-effect areas: tunnel state.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.tunnel_manager`.

## Key Concepts

- Important called helpers/classes observed in the source: `TunnelManager.get_instance`, `tunnel_manager.stop_tunnel`, `runtime.get_web_ui_port`, `tunnel_manager.start_tunnel`, `tunnel_manager.get_last_error`, `process`, `tunnel_manager.get_notifications`, `stop`, `tunnel_manager.get_tunnel_url`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve authentication, CSRF, loopback, and API-key checks unless the endpoint contract explicitly changes.
- Update frontend callers, plugin callers, and tests together when payload shape changes.
- Use `helpers.api.Response` for non-JSON responses, files, redirects, or status-specific replies.

## Verification

- Run endpoint-specific or API/WebSocket tests for changed behavior; smoke-test browser callers when no focused test exists.
- Related tests observed by source search:
  - `tests/test_tunnel_remote_link.py`

## Child DOX Index

No child DOX files.
