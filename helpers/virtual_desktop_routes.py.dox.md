# virtual_desktop_routes.py DOX

## Purpose

- Own the `virtual_desktop_routes.py` helper module.
- This module installs virtual desktop gateway route hooks.
- Keep this file-level DOX profile synchronized with `virtual_desktop_routes.py` because this directory is intentionally flat.

## Ownership

- `virtual_desktop_routes.py` owns the runtime implementation.
- `virtual_desktop_routes.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `VirtualDesktopGateway` (no explicit base class)
  - `async http(self, scope: Scope, receive: Receive, send: Send) -> None`
  - `async resize(self, scope: Scope, receive: Receive, send: Send) -> None`
  - `async proxy_http(self, scope: Scope, receive: Receive, send: Send, token: str, upstream_path: str) -> None`
  - `async websocket(self, scope: Scope, receive: Receive, send: Send) -> None`
  - `async open_websocket(self, endpoint: virtual_desktop.VirtualDesktopEndpoint, target: str, subprotocols: tuple[str, ...]) -> tuple[asyncio.StreamReader, asyncio.StreamWriter, WSConnection, str | None]`
  - `async browser_to_xpra(self, websocket: WebSocket, upstream: WSConnection, writer: asyncio.StreamWriter) -> None`
  - `async xpra_to_browser(self, websocket: WebSocket, upstream: WSConnection, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None`
  - `session_request(self, path: str) -> tuple[str, str] | None`
- Top-level functions:
- `install_route_hooks() -> None`
- `is_installed() -> bool`
- Notable constants/configuration names: `HOP_BY_HOP_HEADERS`, `XPRA_MENU_CUSTOM_PATCH`, `XPRA_WINDOW_OFFSET_WARNING`, `XPRA_WINDOW_OFFSET_WARNING_PATCH`, `XPRA_WINDOW_SCRIPT`, `XPRA_WINDOW_SCRIPT_PATCH`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Observed side-effect areas: filesystem deletion, network calls, subprocess/runtime control, WebSocket state, settings/state persistence, secret handling.
- Imported dependency areas include: `__future__`, `asyncio`, `flask.sessions`, `helpers`, `http.client`, `http.cookies`, `starlette.requests`, `starlette.responses`, `starlette.types`, `starlette.websockets`, `urllib.parse`, `wsproto`, `wsproto.events`.

## Key Concepts

- Important called helpers/classes observed in the source: `self.relative_path`, `self.session_request`, `self.query`, `virtual_desktop.proxy_for_token`, `WebSocket`, `self.upstream_target`, `WSConnection`, `writer.write`, `rest.partition`, `unquote`, `quote`, `http.client.HTTPConnection`, `query_string.decode`, `urlsplit`, `location.startswith`, `path.startswith`, `parse_qs`, `login.get_credentials_hash`, `SecureCookieSessionInterface.get_signing_serializer`, `dict.get.decode`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_office_canvas_setup.py`
  - `tests/test_office_document_store.py`

## Child DOX Index

No child DOX files.
