import asyncio
from datetime import timedelta
import os
import secrets
import time
import socket
import struct
from functools import wraps
import threading

import uvicorn
from flask import Flask, request, Response, session, redirect, url_for, render_template_string
from werkzeug.wrappers.response import Response as BaseResponse

import initialize
from python.helpers import files, git, mcp_server, fasta2a_server, settings as settings_helper
from python.helpers.files import get_abs_path
from python.helpers import runtime, dotenv, process
from python.helpers.websocket import validate_ws_csrf_flag
from datetime import datetime, timezone
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers.api import ApiHandler
from python.helpers.print_style import PrintStyle
from python.helpers import login
import socketio
from socketio import ASGIApp
from starlette.applications import Starlette
from starlette.routing import Mount
from uvicorn.middleware.wsgi import WSGIMiddleware
from python.helpers.websocket import WebSocketHandler
from python.helpers.websocket_manager import WebSocketManager

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
webapp.config.update(
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_NAME="session_" + runtime.get_runtime_id(),  # bind the session cookie name to runtime id to prevent session collision on same host
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)
)

lock = threading.RLock()

socketio_server = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
    logger=False,
    engineio_logger=False,
    ping_interval=25,  # explicit default to avoid future lib changes
    ping_timeout=20,   # explicit default to avoid future lib changes
    max_http_buffer_size=50 * 1024 * 1024,
)

websocket_manager = WebSocketManager(socketio_server, lock)
_settings = settings_helper.get_settings()
websocket_manager.set_server_restart_broadcast(
    _settings.get("websocket_server_restart_enabled", True)
)

# Set up basic authentication for UI and API but not MCP
# basic_auth = BasicAuth(webapp)


def is_loopback_address(address):
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0]
        >> (32 - 8)
        == 127,
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
        version_time=gitinfo["commit_time"]
    )
    return index

def run():
    PrintStyle().print("Initializing framework...")

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

    websocket_handler_classes = load_classes_from_folder(
        "python/websocket_handlers", "*.py", WebSocketHandler
    )
    websocket_handlers = [
        handler_cls.get_instance(socketio_server, lock)
        for handler_cls in websocket_handler_classes
    ]
    websocket_manager.register_handlers(websocket_handlers)

    @socketio_server.event
    async def connect(sid, environ, _auth):  # type: ignore[override]
        with webapp.request_context(environ):
            auth_required = any(
                handler.requires_auth() for handler in websocket_handlers
            )
            if auth_required:
                credentials_hash = login.get_credentials_hash()
                if credentials_hash:
                    if session.get("authentication") != credentials_hash:
                        PrintStyle.warning(
                            f"WebSocket authentication failed for {sid}: session not valid"
                        )
                        return False
                else:
                    PrintStyle.debug(
                        "WebSocket authentication required but credentials not configured; proceeding"
                    )

            csrf_expiry: float | None = None
            requires_csrf = any(
                handler.requires_csrf() for handler in websocket_handlers
            )
            if requires_csrf:
                now_ts = datetime.now(timezone.utc).timestamp()
                ok, reason, expiry = validate_ws_csrf_flag(session, now_ts)
                if not ok:
                    PrintStyle.warning(
                        f"WebSocket CSRF validation failed for {sid}: {reason or 'invalid'}"
                    )
                    return False
                csrf_expiry = expiry
                PrintStyle.debug(
                    f"WebSocket CSRF validated for {sid}; expires at {expiry}"
                )

            user_id = session.get("user_id") or "single_user"
            await websocket_manager.handle_connect(sid, csrf_expiry, user_id=user_id)
            return True

    @socketio_server.event
    async def disconnect(sid):  # type: ignore[override]
        await websocket_manager.handle_disconnect(sid)

    for event_type in websocket_manager.iter_event_types():
        @socketio_server.on(event_type)
        async def _event_handler(sid, data, _event_type=event_type):
            payload = data or {}
            results = await websocket_manager.route_event(
                _event_type, payload, sid
            )
            return results

    async def validate_sessions_loop():
        while True:
            await asyncio.sleep(30)
            now_ts = datetime.now(timezone.utc).timestamp()
            for sid in list(websocket_manager.connections.keys()):
                await websocket_manager.validate_session(sid, now_ts)

    socketio_server.start_background_task(validate_sessions_loop)

    init_a0()

    wsgi_app = WSGIMiddleware(webapp)
    starlette_app = Starlette(
        routes=[
            Mount("/mcp", app=mcp_server.DynamicMcpProxy.get_instance()),
            Mount("/a2a", app=fasta2a_server.DynamicA2AProxy.get_instance()),
            Mount("/", app=wsgi_app),
        ]
    )

    asgi_app = ASGIApp(socketio_server, other_asgi_app=starlette_app)

    config = uvicorn.Config(
        asgi_app,
        host=host,
        port=port,
        log_level="error",
        access_log=_settings.get("uvicorn_access_logs_enabled", False),
        ws="wsproto",
    )
    server = uvicorn.Server(config)

    class _UvicornServerWrapper:
        def __init__(self, server: uvicorn.Server):
            self._server = server

        def shutdown(self) -> None:
            self._server.should_exit = True

    process.set_server(_UvicornServerWrapper(server))

    PrintStyle().debug(f"Starting server at http://{host}:{port} ...")
    server.run()


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
