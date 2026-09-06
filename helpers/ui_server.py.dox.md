# ui_server.py DOX

## Purpose

- Own the `ui_server.py` helper module.
- This module configures and owns Flask/WebUI runtime route handlers.
- Keep this file-level DOX profile synchronized with `ui_server.py` because this directory is intentionally flat.

## Ownership

- `ui_server.py` owns the runtime implementation.
- `ui_server.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `UiServerRuntime` (no explicit base class)
  - `create(cls) -> 'UiServerRuntime'`
  - `refresh_runtime_settings(self) -> None`
  - `register_http_routes(self) -> None`
  - `register_transport_handlers(self) -> None`
  - `build_asgi_app(self, startup_monitor: StartupMonitor)`
  - `access_log_enabled(self) -> bool`
- `UiRouteHandlers` (no explicit base class)
  - `async login_handler(self)`
  - `async logout_handler(self)`
  - `async serve_splash(self)`
  - `async serve_safe(self)`
  - `async serve_index(self)`
  - `async serve_ui_asset_bundle(self)`
  - `async serve_builtin_plugin_asset(self, plugin_name, asset_path)`
  - `async serve_plugin_asset(self, plugin_name, asset_path)`
  - `async serve_extension_asset(self, asset_path)`
  - `async serve_user_extension_asset(self, asset_path)`
- Top-level functions:
- `_positive_int_env(name: str, default: int) -> int`
- `configure_process_environment() -> None`
- Notable constants/configuration names: `UPLOAD_LIMIT_BYTES`, `SOCKETIO_PING_INTERVAL_SECONDS`, `SOCKETIO_PING_TIMEOUT_SECONDS`, `GZIP_MINIMUM_RESPONSE_BYTES`, `GZIP_COMPRESSION_LEVEL`, `UI_INDEX_ASSET_URL`, `A0_SOCKETIO_PING_INTERVAL_SECONDS`, `A0_SOCKETIO_PING_TIMEOUT_SECONDS`.

## Runtime Contracts

- Helper modules own reusable framework APIs and must preserve public callers unless all callers, tests, and docs are updated together.
- Update this file whenever public functions, classes, persistence behavior, path/security assumptions, side effects, or cross-module contracts change.
- Socket.IO heartbeat defaults are intentionally longer than Engine.IO's short defaults so CLI sessions survive long prompt/context work; environment overrides must remain positive integers and fall back to source defaults when invalid.
- Observed side-effect areas: filesystem reads, network calls, subprocess/runtime control, WebSocket state, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `asyncio`, `dataclasses`, `datetime`, `flask`, `helpers`, `helpers.api`, `helpers.extension`, `helpers.files`, `helpers.print_style`, `helpers.server_startup`, `helpers.ws`, `helpers.ws_manager`, `logging`, `os`, `secrets`, `socketio`, `starlette.middleware.gzip`.

## Key Concepts

- Important called helpers/classes observed in the source: `logging.getLogger.setLevel`, `Localization.get.apply_process_timezone`, `_positive_int_env`, `field`, `Flask`, `threading.RLock`, `socketio.AsyncServer`, `WsManager`, `set_shared_ws_manager`, `cls`, `server_runtime.refresh_runtime_settings`, `settings_helper.get_settings`, `settings_helper.set_runtime_settings_snapshot`, `self.ws_manager.set_server_restart_broadcast`, `UiRouteHandlers`, `self.webapp.add_url_rule`, `register_api_route`, `register_ws_namespace`, `files.read_file`, `render_template_string`, `session.pop`.
- `serve_index()` bootstraps the normalized UI control visibility map, timezone and time-format preferences, and the complete enabled WebUI extension manifest so startup extension discovery requires no per-surface API requests.
- Authenticated extension asset routes serve root-contained files from both `extensions/webui/` and `usr/extensions/webui/`, matching the URLs emitted by the WebUI extension manifest.
- The authenticated `/` route uses `serve_splash()` to return the no-store, self-contained bootstrap document. The authenticated extensionless `/ui/index` route renders the existing index and runtime/user placeholders for the splash to install into the current document without navigation; `/index.html` remains a direct fallback for the same rendering path. The authenticated `/safe` route first returns a no-store, self-contained document that unregisters all origin service workers, then renders the existing index through `serve_index()` when its internal `__direct=1` marker is present; it never initializes the asset bundle or a worker. The authenticated `serve_ui_asset_bundle()` endpoint passes the application entry URL to the generic recursive bundler and supports gzip transfer and payload-specific ETag revalidation while component, extension, and Alpine lifecycles remain unchanged.
- The Starlette HTTP branch applies negotiated gzip to responses of at least 1 KiB at compression level 6 while preserving already encoded responses; Socket.IO remains outside that middleware branch.
- `create` end hooks receive the constructed runtime before route registration.
  Service installation belongs to `webui_server_start`, called inside each ASGI
  lifespan with `runtime` and a fresh `shutdown` AsyncExitStack. Hooks register
  cleanup on that stack; startup failure, serving failure and normal shutdown
  all await it, even if plugins are subsequently disabled. Uvicorn retries can
  reuse the server object without reusing retired services or a spent stack.
  The shared server imports no plugin services.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Preserve public helper APIs used by core code and plugins unless every caller is updated.
- Keep path, auth, secret, persistence, network, and subprocess behavior explicit and bounded.
- Prefer adding cohesive helper functions here only when behavior is reused across modules.

## Verification

- Run targeted tests for changed helper behavior; run security regressions for auth, filesystem, WebSocket, tunnel, upload, or secret-handling helpers.
- No direct test reference was found by name search; choose the nearest behavioral test or perform a focused smoke check.

## Child DOX Index

No child DOX files.
