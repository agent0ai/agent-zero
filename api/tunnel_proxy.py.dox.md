# tunnel_proxy.py DOX

## Purpose

- Own the `tunnel_proxy.py` API endpoint.
- This module proxies tunnel-related HTTP traffic through the configured tunnel provider.
- Keep this file-level DOX profile synchronized with `tunnel_proxy.py` because this directory is intentionally flat.

## Ownership

- `tunnel_proxy.py` owns the runtime implementation.
- `tunnel_proxy.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `TunnelProxy` (`ApiHandler`)
  - `async process(self, input: dict, request: Request) -> dict | Response`
- Top-level functions:
- `async process(input: dict) -> dict | Response`

## Runtime Contracts

- HTTP handlers must derive from `helpers.api.ApiHandler`; WebSocket handlers must derive from `helpers.ws.WsHandler`.
- Update this file whenever request payloads, authentication or CSRF requirements, response shapes, route side effects, or WebSocket event contracts change.
- `TunnelProxy` is an `ApiHandler`.
- `TunnelProxy` defines `process(...)`.
- Observed side-effect areas: network calls, settings/state persistence, tunnel state.
- Imported dependency areas include: `helpers`, `helpers.api`, `helpers.tunnel_manager`, `requests`.

## Key Concepts

- Important called helpers/classes observed in the source: `runtime.get_arg`, `requests.post`, `process`, `dotenv.get_dotenv_value`, `response.json`, `local_process`.
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
