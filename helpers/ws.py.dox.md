# ws.py DOX

## Purpose

- Own the `ws.py` helper module.
- This module defines WebSocket handler registration, origin validation, and security checks.
- Keep this file-level DOX profile synchronized with `ws.py` because this directory is intentionally flat.

## Ownership

- `ws.py` owns the runtime implementation.
- `ws.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `ConnectionNotFoundError` (`RuntimeError`)
- `_SecurityContext` (no explicit base class)
- `WsHandler` (no explicit base class)
  - `namespace(self) -> str`
  - `manager(self) -> 'WsManager'`
  - `identifier(self) -> str`
  - `bind_manager(self, manager: 'WsManager', namespace: str | None=...) -> None`
  - `requires_loopback(cls) -> bool`
  - `requires_api_key(cls) -> bool`
  - `requires_auth(cls) -> bool`
  - `requires_csrf(cls) -> bool`
- Top-level functions:
- `_ws_debug_enabled() -> bool`: Check A0_WS_DEBUG env var - lightweight, no heavy imports.
- `ws_debug(message: str) -> None`: Log *message* via :class:`PrintStyle` when ``A0_WS_DEBUG`` is active.
- `_default_port_for_scheme(scheme: str) -> int | None`
- `normalize_origin(value: Any) -> str | None`: Normalize an Origin/Referer header value to scheme://host[:port].
- `_parse_host_header(value: Any) -> tuple[str | None, int | None]`
- `validate_ws_origin(environ: dict[str, Any]) -> tuple[bool, str | None]`: Validate the browser Origin during the Socket.IO handshake.
- `_check_security(handler_cls: type[WsHandler], ctx: _SecurityContext) -> dict[str, Any] | None`: Return an error payload dict if the check fails, or ``None`` on success.
- `register_ws_namespace(socketio_server: socketio.AsyncServer, webapp: Flask, lock: ThreadLockType, manager: 'WsManager | None'=...) -> None`
- `_error_response(code: str, message: str, correlation_id: str) -> dict[str, Any]`
- Notable constants/configuration names: `NAMESPACE`, `CACHE_AREA`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- `WsHandler` defines `process(...)`.
- `WsHandler` defines `requires_auth(...)`.
- `WsHandler` defines `requires_csrf(...)`.
- `WsHandler` defines `requires_api_key(...)`.
- `WsHandler` defines `requires_loopback(...)`.
- Observed side-effect areas: filesystem reads, filesystem deletion, network calls, WebSocket state, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `abc`, `dataclasses`, `flask`, `helpers`, `helpers.errors`, `helpers.network`, `helpers.print_style`, `os`, `pathlib`, `socketio`, `threading`, `typing`, `urllib.parse`, `uuid`.

## Key Concepts

- Important called helpers/classes observed in the source: `threading.Lock`, `os.getenv.strip.lower`, `_ws_debug_enabled`, `urlparse`, `normalize_origin`, `_parse_host_header`, `handler_cls.requires_loopback`, `handler_cls.requires_auth`, `handler_cls.requires_csrf`, `handler_cls.requires_api_key`, `socketio_server.on`, `PrintStyle.debug`, `value.strip`, `origin_parsed.hostname.lower`, `_default_port_for_scheme`, `req_host.lower`, `forwarded_host_raw.strip`, `forwarded_host_raw.split.strip`, `forwarded_proto_raw.strip`, `forwarded_proto_raw.split.strip.lower`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- Related tests observed by source search:
  - `tests/test_a0_connector_computer_use_metadata.py`
  - `tests/test_a0_connector_prompt_gating.py`
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_docker_release_plan.py`
  - `tests/test_download_toast_regressions.py`
  - `tests/test_git_version_label.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_multi_tab_isolation.py`

## Child DOX Index

No child DOX files.
