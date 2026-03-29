from datetime import timedelta
import os
import secrets
import time
import threading
import asyncio

import urllib.request
import uvicorn
from flask import Flask, request, Response, session, redirect, url_for, render_template_string
from werkzeug.wrappers.request import Request as WerkzeugRequest

import initialize
from helpers import files, git, mcp_server, fasta2a_server, settings as settings_helper, extension
from helpers.files import get_abs_path
from helpers import runtime, dotenv, process
from helpers.api import register_api_route, requires_auth, csrf_protect
from helpers.ws import register_ws_namespace, validate_ws_origin
from helpers.print_style import PrintStyle
from helpers import login
import socketio  # type: ignore[import-untyped]
from socketio import ASGIApp, packet
from starlette.applications import Starlette
from starlette.routing import Mount
from uvicorn.middleware.wsgi import WSGIMiddleware
from helpers.ws_manager import WsManager, set_shared_ws_manager
from flask import send_file

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
    SESSION_COOKIE_SAMESITE="Lax",
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

ws_manager = WsManager(socketio_server, lock)
set_shared_ws_manager(ws_manager)
_settings = settings_helper.get_settings()
settings_helper.set_runtime_settings_snapshot(_settings)
ws_manager.set_server_restart_broadcast(
    _settings.get("websocket_server_restart_enabled", True)
)

# Set up basic authentication for UI and API but not MCP
# basic_auth = BasicAuth(webapp)


@webapp.route("/login", methods=["GET", "POST"])
@extension.extensible
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
@extension.extensible
async def logout_handler():
    session.pop('authentication', None)
    return redirect(url_for('login_handler'))


# handle default address, load index
@webapp.route("/", methods=["GET"])
@requires_auth
@extension.extensible
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


# Serve plugin assets
@webapp.route("/plugins/<plugin_name>/<path:asset_path>", methods=["GET"])
@requires_auth
async def serve_builtin_plugin_asset(plugin_name, asset_path):
    return await _serve_plugin_asset(plugin_name, asset_path)

@webapp.route("/usr/plugins/<plugin_name>/<path:asset_path>", methods=["GET"])
@requires_auth
async def serve_plugin_asset(plugin_name, asset_path):
    return await _serve_plugin_asset(plugin_name, asset_path)

@webapp.route("/extensions/webui/<path:asset_path>", methods=["GET"])
@requires_auth
async def serve_extension_asset(asset_path):
    exts = files.get_abs_path("extensions/webui")
    path = files.get_abs_path(exts, asset_path)
    if not files.is_in_dir(path, exts):
        return Response(f"Access denied", 403)
    return send_file(path)


@extension.extensible
async def _serve_plugin_asset(plugin_name, asset_path):
    """
    Serve static assets from plugin directories.
    Resolves using the plugin system (with overrides).
    """
    from helpers import plugins
    
    
    # Use the new find_plugin helper
    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if not plugin_dir:
        return Response("Plugin not found", 404)
    
    # Resolve the plugin asset path with security checks
    try:
        # Construct path using plugin root
        asset_file = files.get_abs_path(plugin_dir, asset_path)
        webui_dir = files.get_abs_path(plugin_dir, "webui")
        webui_extensions_dir = files.get_abs_path(plugin_dir, "extensions/webui")
        
        # Security: ensure the resolved path is within the plugin webui directory
        if not files.is_in_dir(str(asset_file), str(webui_dir)) and not files.is_in_dir(str(asset_file), str(webui_extensions_dir)):
            return Response("Access denied", 403)
            
        if not files.is_file(asset_file):
            return Response("Asset not found", 404)
            
        return send_file(str(asset_file))
    except Exception as e:
        PrintStyle.error(f"Error serving plugin asset: {e}")
        return Response("Error serving asset", 500)




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

    register_api_route(webapp, lock)

    register_ws_namespace(socketio_server, webapp, lock, manager=ws_manager)

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
    url = f"http://{host}:{port}/api/health"
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    PrintStyle().print("Agent Zero is running.")
                    return
        except Exception:
            pass
        time.sleep(1)


@extension.extensible
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
