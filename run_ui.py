from datetime import timedelta
import os
import secrets
import time
import socket
import struct
from functools import wraps
import threading
import asyncio

import urllib.request
import urllib.error
import uvicorn
from flask import Flask, request, Response, session, redirect, url_for, render_template_string
from werkzeug.wrappers.response import Response as BaseResponse
from werkzeug.wrappers.request import Request as WerkzeugRequest

import initialize
from python.helpers import files, git, mcp_server, fasta2a_server, settings as settings_helper
from python.api.agui_endpoint import create_agui_app
from python.helpers.files import get_abs_path
from python.helpers import runtime, dotenv, process
from python.helpers.websocket import WebSocketHandler, validate_ws_origin
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle
from python.helpers import login
import socketio  # type: ignore[import-untyped]
from socketio import ASGIApp, packet
from starlette.applications import Starlette
from starlette.routing import Mount
from uvicorn.middleware.wsgi import WSGIMiddleware
from python.helpers.websocket_manager import WebSocketManager
from python.helpers.websocket_namespace_discovery import discover_websocket_namespaces

# disable logging
import logging
logging.getLogger().setLevel(logging.WARNING)


# Set the new timezone to 'UTC'
os.environ["TZ"] = "UTC"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Apply the timezone change
if hasattr(time, 'tzset'):
    time.tzset()

# initialize the internal Flask server
webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024 * 1024

# Werkzeug's default max_form_memory_size is 500_000 bytes which can trigger 413 for multipart requests
# with larger non-file fields. Raise it to match our intended upload limit.
WerkzeugRequest.max_form_memory_size = UPLOAD_LIMIT_BYTES

webapp.config.update(
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_NAME="session_" + runtime.get_runtime_id(),  # bind the session cookie name to runtime id to prevent session collision on same host
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    MAX_CONTENT_LENGTH=int(os.getenv("FLASK_MAX_CONTENT_LENGTH", str(UPLOAD_LIMIT_BYTES))),
    MAX_FORM_MEMORY_SIZE=int(os.getenv("FLASK_MAX_FORM_MEMORY_SIZE", str(UPLOAD_LIMIT_BYTES))),
)

lock = threading.RLock()

socketio_server = socketio.AsyncServer(
    async_mode="asgi",
    namespaces="*",
    cors_allowed_origins=lambda _origin, environ: validate_ws_origin(environ)[0],
    logger=False,
    engineio_logger=False,
    ping_interval=25,  # explicit default to avoid future lib changes
    ping_timeout=20,   # explicit default to avoid future lib changes
    max_http_buffer_size=50 * 1024 * 1024,
)

websocket_manager = WebSocketManager(socketio_server, lock)
_settings = settings_helper.get_settings()
settings_helper.set_runtime_settings_snapshot(_settings)
websocket_manager.set_server_restart_broadcast(
    _settings.get("websocket_server_restart_enabled", True)
)

# Set up basic authentication for UI and API but not MCP
# basic_auth = BasicAuth(webapp)


def is_loopback_address(address):
    loopback_checker = {
        socket.AF_INET: lambda x: (
            struct.unpack("!I", socket.inet_aton(x))[0] >> (32 - 8)
        ) == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    address_type = "hostname"
    try:
        socket.inet_pton(socket.AF_INET6, address)
        address_type = "ipv6"
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET, address)
            address_type = "ipv4"
        except socket.error:
            address_type = "hostname"

    if address_type == "ipv4":
        return loopback_checker[socket.AF_INET](address)
    elif address_type == "ipv6":
        return loopback_checker[socket.AF_INET6](address)
    else:
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
            except socket.gaierror:
                return False
            for family, _, _, _, sockaddr in r:
                if not loopback_checker[family](sockaddr[0]):
                    return False
        return True


def requires_api_key(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Use the auth token from settings (same as MCP server)
        from python.helpers.settings import get_settings
        valid_api_key = get_settings()["mcp_server_token"]

        if api_key := request.headers.get("X-API-KEY"):
            if api_key != valid_api_key:
                return Response("Invalid API key", 401)
        elif request.json and request.json.get("api_key"):
            api_key = request.json.get("api_key")
            if api_key != valid_api_key:
                return Response("Invalid API key", 401)
        else:
            return Response("API key required", 401)
        return await f(*args, **kwargs)

    return decorated


# allow only loopback addresses
def requires_loopback(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        if not is_loopback_address(request.remote_addr):
            return Response(
                "Access denied.",
                403,
                {},
            )
        return await f(*args, **kwargs)

    return decorated


# require authentication for handlers
def requires_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        user_pass_hash = login.get_credentials_hash()
        # If no auth is configured, just proceed
        if not user_pass_hash:
            return await f(*args, **kwargs)

        if session.get('authentication') != user_pass_hash:
            return redirect(url_for('login_handler'))

        return await f(*args, **kwargs)

    return decorated


def csrf_protect(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        token = session.get("csrf_token")
        header = request.headers.get("X-CSRF-Token")
        cookie = request.cookies.get("csrf_token_" + runtime.get_runtime_id())
        sent = header or cookie
        if not token or not sent or token != sent:
            return Response("CSRF token missing or invalid", 403)
        return await f(*args, **kwargs)

    return decorated


@webapp.route("/login", methods=["GET", "POST"])
async def login_handler():
    error = None
    if request.method == 'POST':
        user = dotenv.get_dotenv_value("AUTH_LOGIN")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")

        if request.form['username'] == user and request.form['password'] == password:
            session['authentication'] = login.get_credentials_hash()
            return redirect(url_for('serve_index'))
        else:
            await asyncio.sleep(1)
            error = 'Invalid Credentials. Please try again.'

    login_page_content = files.read_file("webui/login.html")
    return render_template_string(login_page_content, error=error)


@webapp.route("/logout")
async def logout_handler():
    session.pop('authentication', None)
    return redirect(url_for('login_handler'))


# handle default address, load index
@webapp.route("/", methods=["GET"])
@requires_auth
async def serve_index():
    gitinfo = None
    try:
        gitinfo = git.get_git_info()
    except Exception:
        gitinfo = {
            "version": "unknown",
            "commit_time": "unknown",
        }
    index = files.read_file("webui/index.html")
    index = files.replace_placeholders_text(
        _content=index,
        version_no=gitinfo["version"],
        version_time=gitinfo["commit_time"],
        runtime_id=runtime.get_runtime_id(),
        runtime_is_development=("true" if runtime.is_development() else "false"),
        logged_in=("true" if login.get_credentials_hash() else "false"),
    )
    return index


def _build_websocket_handlers_by_namespace(
    socketio_server: socketio.AsyncServer,
    lock: threading.RLock,
) -> dict[str, list[WebSocketHandler]]:
    discoveries = discover_websocket_namespaces(
        handlers_folder="python/websocket_handlers",
        include_root_default=True,
    )

    handlers_by_namespace: dict[str, list[WebSocketHandler]] = {}
    for discovery in discoveries:
        namespace = discovery.namespace
        for handler_cls in discovery.handler_classes:
            handler = handler_cls.get_instance(socketio_server, lock)
            handlers_by_namespace.setdefault(namespace, []).append(handler)

    return handlers_by_namespace


def configure_websocket_namespaces(
    *,
    webapp: Flask,
    socketio_server: socketio.AsyncServer,
    websocket_manager: WebSocketManager,
    handlers_by_namespace: dict[str, list[WebSocketHandler]],
) -> set[str]:
    namespace_map: dict[str, list[WebSocketHandler]] = {
        namespace: list(handlers) for namespace, handlers in handlers_by_namespace.items()
    }

    # Always include the reserved root namespace. It is unhandled for application events by
    # default, but request-style calls must resolve deterministically with NO_HANDLERS.
    namespace_map.setdefault("/", [])

    websocket_manager.register_handlers(namespace_map)

    allowed_namespaces = set(namespace_map.keys())
    original_handle_connect = socketio_server._handle_connect  # type: ignore[attr-defined]

    async def _handle_connect_with_namespace_gatekeeper(eio_sid, namespace, data):
        requested = namespace or "/"
        if requested not in allowed_namespaces:
            await socketio_server._send_packet(
                eio_sid,
                socketio_server.packet_class(
                    packet.CONNECT_ERROR,
                    data={
                        "message": "UNKNOWN_NAMESPACE",
                        "data": {"code": "UNKNOWN_NAMESPACE", "namespace": requested},
                    },
                    namespace=requested,
                ),
            )
            return
        await original_handle_connect(eio_sid, namespace, data)

    socketio_server._handle_connect = _handle_connect_with_namespace_gatekeeper  # type: ignore[assignment]

    def _register_namespace_handlers(
        namespace: str, namespace_handlers: list[WebSocketHandler]
    ) -> None:
        # A namespace is the WebSocket equivalent of an API endpoint.
        # Security requirements must be consistent within the namespace (no any()-based union).
        auth_required = False
        csrf_required = False
        if namespace_handlers:
            auth_required = bool(namespace_handlers[0].requires_auth())
            csrf_required = bool(namespace_handlers[0].requires_csrf())
            for handler in namespace_handlers[1:]:
                if (
                    bool(handler.requires_auth()) != auth_required
                    or bool(handler.requires_csrf()) != csrf_required
                ):
                    raise ValueError(
                        f"WebSocket namespace {namespace!r} has mixed auth/csrf requirements across handlers"
                    )

        @socketio_server.on("connect", namespace=namespace)
        async def _connect(  # type: ignore[override]
            sid,
            environ,
            _auth,
            _namespace: str = namespace,
            _auth_required: bool = auth_required,
            _csrf_required: bool = csrf_required,
        ):
            with webapp.request_context(environ):
                origin_ok, origin_reason = validate_ws_origin(environ)
                if not origin_ok:
                    PrintStyle.warning(
                        f"WebSocket origin validation failed for {_namespace} {sid}: {origin_reason or 'invalid'}"
                    )
                    return False

                if _auth_required:
                    credentials_hash = login.get_credentials_hash()
                    if credentials_hash:
                        if session.get("authentication") != credentials_hash:
                            PrintStyle.warning(
                                f"WebSocket authentication failed for {_namespace} {sid}: session not valid"
                            )
                            return False
                    else:
                        PrintStyle.debug(
                            "WebSocket authentication required but credentials not configured; proceeding"
                        )

                if _csrf_required:
                    expected_token = session.get("csrf_token")
                    if not isinstance(expected_token, str) or not expected_token:
                        PrintStyle.warning(
                            f"WebSocket CSRF validation failed for {_namespace} {sid}: csrf_token not initialized"
                        )
                        return False

                    auth_token = None
                    if isinstance(_auth, dict):
                        auth_token = _auth.get("csrf_token") or _auth.get("csrfToken")
                    if not isinstance(auth_token, str) or not auth_token:
                        PrintStyle.warning(
                            f"WebSocket CSRF validation failed for {_namespace} {sid}: missing csrf_token in auth"
                        )
                        return False
                    if auth_token != expected_token:
                        PrintStyle.warning(
                            f"WebSocket CSRF validation failed for {_namespace} {sid}: csrf_token mismatch"
                        )
                        return False

                    cookie_name = f"csrf_token_{runtime.get_runtime_id()}"
                    cookie_token = request.cookies.get(cookie_name)
                    if cookie_token != expected_token:
                        PrintStyle.warning(
                            f"WebSocket CSRF validation failed for {_namespace} {sid}: csrf cookie mismatch"
                        )
                        return False

                user_id = session.get("user_id") or "single_user"
                await websocket_manager.handle_connect(_namespace, sid, user_id=user_id)
                return True

        @socketio_server.on("disconnect", namespace=namespace)
        async def _disconnect(sid, _namespace: str = namespace):  # type: ignore[override]
            await websocket_manager.handle_disconnect(_namespace, sid)

        def _register_socketio_event(event_type: str) -> None:
            @socketio_server.on(event_type, namespace=namespace)
            async def _event_handler(
                sid,
                data,
                _event_type: str = event_type,
                _namespace: str = namespace,
            ):
                payload = data or {}
                return await websocket_manager.route_event(
                    _namespace, _event_type, payload, sid
                )

        for _event_type in websocket_manager.iter_event_types(namespace):
            _register_socketio_event(_event_type)

        @socketio_server.on("*", namespace=namespace)
        async def _catch_all(event, sid, data, _namespace: str = namespace):
            payload = data or {}
            return await websocket_manager.route_event(_namespace, event, payload, sid)

    for namespace, namespace_handlers in namespace_map.items():
        _register_namespace_handlers(namespace, namespace_handlers)

    return allowed_namespaces


def run():
    PrintStyle().print("Initializing framework...")

    # migrate data before anything else
    initialize.initialize_migration()

    # # Suppress only request logs but keep the startup messages
    # from werkzeug.serving import WSGIRequestHandler
    # from werkzeug.serving import make_server
    # from werkzeug.middleware.dispatcher import DispatcherMiddleware
    # from a2wsgi import ASGIMiddleware

    PrintStyle().print("Starting server...")

    # class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
    #     def log_request(self, code="-", size="-"):
    #         pass  # Override to suppress request logging

    # Get configuration from environment
    port = runtime.get_web_ui_port()
    host = (
        runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "localhost"
    )

    def register_api_handler(app, handler: type[ApiHandler]):
        name = handler.__module__.split(".")[-1]
        instance = handler(app, lock)

        async def handler_wrap() -> BaseResponse:
            return await instance.handle_request(request=request)

        if handler.requires_loopback():
            handler_wrap = requires_loopback(handler_wrap)
        if handler.requires_auth():
            handler_wrap = requires_auth(handler_wrap)
        if handler.requires_api_key():
            handler_wrap = requires_api_key(handler_wrap)
        if handler.requires_csrf():
            handler_wrap = csrf_protect(handler_wrap)

        app.add_url_rule(
            f"/{name}",
            f"/{name}",
            handler_wrap,
            methods=handler.get_methods(),
        )

    handlers = load_classes_from_folder("python/api", "*.py", ApiHandler)
    for handler in handlers:
        register_api_handler(webapp, handler)

    handlers_by_namespace = _build_websocket_handlers_by_namespace(socketio_server, lock)
    configure_websocket_namespaces(
        webapp=webapp,
        socketio_server=socketio_server,
        websocket_manager=websocket_manager,
        handlers_by_namespace=handlers_by_namespace,
    )

    init_a0()

    wsgi_app = WSGIMiddleware(webapp)
    starlette_app = Starlette(
        routes=[
            Mount("/mcp", app=mcp_server.DynamicMcpProxy.get_instance()),
            Mount("/a2a", app=fasta2a_server.DynamicA2AProxy.get_instance()),
            Mount("/agui", app=create_agui_app(lock)),
            Mount("/", app=wsgi_app),
        ]
    )

    asgi_app = ASGIApp(socketio_server, other_asgi_app=starlette_app)

    def flush_and_shutdown_callback() -> None:
        """
        TODO(dev): add cleanup + flush-to-disk logic here.
        """
        return
    flush_ran = False

    def _run_flush(reason: str) -> None:
        nonlocal flush_ran
        if flush_ran:
            return
        flush_ran = True
        try:
            flush_and_shutdown_callback()
        except Exception as e:
            PrintStyle.warning(f"Shutdown flush failed ({reason}): {e}")

    config = uvicorn.Config(
        asgi_app,
        host=host,
        port=port,
        log_level="info",
        access_log=_settings.get("uvicorn_access_logs_enabled", False),
        ws="wsproto",
    )
    server = uvicorn.Server(config)

    class _UvicornServerWrapper:
        def __init__(self, server: uvicorn.Server):
            self._server = server

        def shutdown(self) -> None:
            _run_flush("shutdown")
            self._server.should_exit = True

    process.set_server(_UvicornServerWrapper(server))

    PrintStyle().debug(f"Starting server at http://{host}:{port} ...")
    threading.Thread(target=wait_for_health, args=(host, port), daemon=True).start()
    try:
        server.run()
    finally:
        _run_flush("server_exit")


def wait_for_health(host: str, port: int):
    url = f"http://{host}:{port}/health"
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    PrintStyle().print("Agent Zero is running.")
                    return
        except Exception:
            pass
        time.sleep(1)


def init_a0():
    # initialize contexts and MCP
    init_chats = initialize.initialize_chats()
    # only wait for init chats, otherwise they would seem to disappear for a while on restart
    init_chats.result_sync()

    initialize.initialize_mcp()
    # start job loop
    initialize.initialize_job_loop()
    # preload
    initialize.initialize_preload()


# run the internal server
if __name__ == "__main__":
    runtime.initialize()
    dotenv.load_dotenv()
    run()
