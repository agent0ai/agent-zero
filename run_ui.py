# disable logging
import contextlib
import logging
import os
import secrets
import socket
import struct
import threading
import time
import warnings
from datetime import timedelta
from functools import wraps

from flask import Flask, Response, redirect, render_template_string, request, session, url_for
from werkzeug.wrappers.response import Response as BaseResponse

logging.getLogger().setLevel(logging.WARNING)
with contextlib.suppress(Exception):
    from requests import RequestsDependencyWarning

    warnings.filterwarnings("ignore", category=RequestsDependencyWarning)

import initialize
from python.helpers import dotenv, fasta2a_server, files, git, login, mcp_server, perf_metrics, process, runtime
from python.helpers.api import ApiHandler
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers.files import get_abs_path
from python.helpers.print_style import PrintStyle

# Set the new timezone to 'UTC'
os.environ["TZ"] = "UTC"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Apply the timezone change
if hasattr(time, "tzset"):
    time.tzset()

# initialize the internal Flask server
webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
webapp.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
webapp.config.update(
    JSON_SORT_KEYS=False,
    SESSION_COOKIE_NAME="session_"
    + runtime.get_runtime_id(),  # bind the session cookie name to runtime id to prevent session collision on same host
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
)

lock = threading.Lock()
_mcp_token_lock = threading.Lock()
_active_mcp_token: str | None = None
_startup_tasks: list[object] = []


def _is_laptop_mode() -> bool:
    return os.getenv("AGENT_ZERO_LAPTOP_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


# Set up basic authentication for UI and API but not MCP
# basic_auth = BasicAuth(webapp)


def is_loopback_address(address):
    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0] >> (32 - 8) == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    address_type = "hostname"
    try:
        socket.inet_pton(socket.AF_INET6, address)
        address_type = "ipv6"
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET, address)
            address_type = "ipv4"
        except OSError:
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

        if session.get("authentication") != user_pass_hash:
            return redirect(url_for("login_handler"))

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
    if request.method == "POST":
        user = dotenv.get_dotenv_value("AUTH_LOGIN")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")

        if request.form["username"] == user and request.form["password"] == password:
            session["authentication"] = login.get_credentials_hash()
            return redirect(url_for("serve_index"))
        else:
            error = "Invalid Credentials. Please try again."

    login_page_content = files.read_file("webui/login.html")
    return render_template_string(login_page_content, error=error)


@webapp.route("/logout")
async def logout_handler():
    session.pop("authentication", None)
    return redirect(url_for("login_handler"))


@webapp.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://* blob:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://* blob:; "
        "script-src-elem 'self' 'unsafe-inline' 'unsafe-eval' https://* blob:; "
        "img-src 'self' data: https://* blob:; "
        "font-src 'self' data: https://fonts.gstatic.com;"
    )
    return response


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
        _content=index, version_no=gitinfo["version"], version_time=gitinfo["commit_time"]
    )
    response = Response(response=index, status=200, mimetype="text/html")
    if _is_laptop_mode():
        return response

    # Auto-provision MCP token details on main page load.
    # Use explicit refresh to rotate safely without invalidating active sessions unexpectedly.
    refresh_requested = request.args.get("refresh_mcp_token", "").lower() in {"1", "true", "yes"}
    token = _ensure_active_mcp_token(force_rotate=refresh_requested)
    sse_url = f"/mcp/t-{token}/sse"
    streamable_http_url = f"/mcp/t-{token}/http/"
    base_url = request.host_url.rstrip("/")

    response.headers["X-Agent-Zero-MCP-Token"] = token
    response.headers["X-Agent-Zero-MCP-SSE"] = sse_url
    response.headers["X-Agent-Zero-MCP-HTTP"] = streamable_http_url
    response.headers["X-Agent-Zero-MCP-SSE-URL"] = f"{base_url}{sse_url}"
    response.headers["X-Agent-Zero-MCP-HTTP-URL"] = f"{base_url}{streamable_http_url}"
    response.set_cookie(
        f"mcp_token_{runtime.get_runtime_id()}",
        token,
        httponly=False,
        samesite="Strict",
    )
    return response


def _ensure_active_mcp_token(force_rotate: bool = False) -> str:
    global _active_mcp_token
    with _mcp_token_lock:
        if _active_mcp_token and not force_rotate:
            return _active_mcp_token

        # Generate an ephemeral token for MCP clients.
        token = secrets.token_urlsafe(18)
        _active_mcp_token = token

        try:
            mcp_server.DynamicMcpProxy.get_instance().reconfigure(token=token)
        except Exception as e:
            PrintStyle(font_color="yellow").print(f"[!] MCP token reconfigure failed: {e}")
        try:
            fasta2a_server.DynamicA2AProxy.get_instance().reconfigure(token=token)
        except Exception as e:
            PrintStyle(font_color="yellow").print(f"[!] A2A token reconfigure failed: {e}")

        return token


def run():
    PrintStyle().print("Initializing framework...")

    # Suppress only request logs but keep the startup messages
    from a2wsgi import ASGIMiddleware
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.serving import WSGIRequestHandler, make_server

    PrintStyle().print("Starting server...")

    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):
        def log_request(self, code="-", size="-"):
            pass  # Override to suppress request logging

    # Get configuration from environment
    port = runtime.get_web_ui_port()
    host = runtime.get_arg("host") or dotenv.get_dotenv_value("WEB_UI_HOST") or "localhost"
    server = None

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

    # Load ALL API handlers at startup (Flask 3.x requires all routes registered before first request)
    # Note: Expensive imports should be made lazy INSIDE handlers via try/except ImportError
    PrintStyle(font_color="yellow").print("[boot] Loading API handlers...")
    all_handlers = load_classes_from_folder("python/api", "*.py", ApiHandler)
    PrintStyle(font_color="yellow").print("[boot] Registering API handlers...")
    for handler in all_handlers:
        register_api_handler(webapp, handler)
    PrintStyle(font_color="green").print(f"[✓] API handlers loaded ({len(all_handlers)} handlers)")

    # Initialize messaging gateway with channel adapters.
    # Keep UI boot resilient if gateway dependencies are mid-refactor.
    if _is_laptop_mode():
        PrintStyle(font_color="yellow").print("[!] Gateway init skipped (laptop mode)")
    else:
        try:
            from python.helpers.gateway_init import initialize_gateway

            initialize_gateway()
        except Exception as e:
            PrintStyle(font_color="yellow").print(f"[!] Gateway init skipped: {e}")

    # Add the webapp, mcp, and a2a to the app.
    # Protect startup from blocking proxy initialization.
    middleware_routes = {}

    def _init_route(path: str, factory):
        try:
            app_obj = factory()
            middleware_routes[path] = ASGIMiddleware(app=app_obj)  # type: ignore
            PrintStyle(font_color="green").print(f"[✓] Mounted {path} route")
        except Exception as e:
            PrintStyle(font_color="yellow").print(f"[!] Skipping {path} route: {e}")

    if _is_laptop_mode():
        PrintStyle(font_color="yellow").print("[!] MCP/A2A routes skipped (laptop mode)")
    else:
        _init_route("/mcp", mcp_server.DynamicMcpProxy.get_instance)
        _init_route("/a2a", fasta2a_server.DynamicA2AProxy.get_instance)

    PrintStyle(font_color="yellow").print("[boot] Building WSGI dispatcher...")
    app = DispatcherMiddleware(webapp, middleware_routes)  # type: ignore

    PrintStyle(font_color="yellow").print(f"[boot] Binding HTTP server on {host}:{port}...")
    PrintStyle().debug(f"Starting server at http://{host}:{port} ...")

    server = make_server(
        host=host,
        port=port,
        app=app,
        request_handler=NoRequestLoggingWSGIRequestHandler,
        threaded=True,
    )
    process.set_server(server)
    server.log_startup()

    # Start init_a0 in a background thread when server starts
    threading.Thread(target=init_a0, daemon=True).start()

    # run the server
    server.serve_forever()


def init_a0():
    def _record_startup_phase_result(phase: str, started_at: float, status: str = "success", error: str = ""):
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        perf_metrics.record_startup_phase(phase, duration_ms, status=status, error=error or None)
        if status == "success":
            PrintStyle(font_color="green").print(f"[boot] {phase} completed in {duration_ms:.1f}ms")
        else:
            PrintStyle(font_color="yellow").print(f"[boot] {phase} failed in {duration_ms:.1f}ms: {error}")

    def _watch_background_startup_task(phase: str, task, started_at: float):
        def _watch():
            try:
                task.result_sync()
                _record_startup_phase_result(phase, started_at, "success")
            except Exception as e:
                _record_startup_phase_result(phase, started_at, "error", str(e))

        thread = threading.Thread(target=_watch, daemon=True, name=f"startup-metric-{phase}")
        thread.start()

    # Load chats deterministically first so users retain context after restart.
    # This is lightweight and avoids races with background task GC/cancellation.
    chats_started = time.perf_counter()
    chats_task = initialize.initialize_chats()
    if chats_task is not None:
        try:
            chats_task.result_sync(timeout=10)
        except Exception as e:
            _record_startup_phase_result("initialize_chats", chats_started, "error", str(e))
            PrintStyle(font_color="yellow").print(f"[!] Chat restore incomplete: {e}")
        else:
            _record_startup_phase_result("initialize_chats", chats_started, "success")
            _startup_tasks.append(chats_task)
    else:
        _record_startup_phase_result("initialize_chats", chats_started, "success")

    # Initialize heavier subsystems in background.
    for phase, initializer in (
        ("initialize_mcp", initialize.initialize_mcp),  # Background - connects on first tool call
        ("initialize_job_loop", initialize.initialize_job_loop),
        ("initialize_preload", initialize.initialize_preload),
    ):
        phase_started = time.perf_counter()
        task = initializer()
        if task is not None:
            _startup_tasks.append(task)
            _watch_background_startup_task(phase, task, phase_started)
        else:
            _record_startup_phase_result(phase, phase_started, "success")
    PrintStyle(font_color="green").print("[✓] Background initialization started")


# run the internal server
if __name__ == "__main__":
    runtime.initialize()
    dotenv.load_dotenv()
    run()
