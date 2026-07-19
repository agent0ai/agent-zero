from dataclasses import dataclass, field
from datetime import timedelta
import asyncio
import logging
import os
import secrets
import threading
import time
from typing import Any

from flask import (
    Flask,
    Response,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)
from socketio import ASGIApp
from starlette.applications import Starlette
from starlette.routing import Mount
from uvicorn.middleware.wsgi import WSGIMiddleware
from werkzeug.wrappers.request import Request as WerkzeugRequest
import socketio  # type: ignore[import-untyped]

from helpers import dotenv, fasta2a_server, files, git, login, mcp_server, runtime
from helpers.api import register_api_route, requires_auth
from helpers.extension import extensible
from helpers.files import get_abs_path
from helpers.print_style import PrintStyle
from helpers.server_startup import StartupMonitor
from helpers import settings as settings_helper
from helpers.ws import register_ws_namespace, validate_ws_origin
from helpers.ws_manager import WsManager, set_shared_ws_manager


UPLOAD_LIMIT_BYTES = 5 * 1024 * 1024 * 1024


def configure_process_environment() -> None:
    logging.getLogger().setLevel(logging.WARNING)
    os.environ["TZ"] = "UTC"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    if hasattr(time, "tzset"):
        time.tzset()


@dataclass
class UiServerRuntime:
    webapp: Flask
    socketio_server: socketio.AsyncServer
    ws_manager: WsManager
    lock: threading.RLock
    settings_snapshot: dict[str, Any]
    _routes_registered: bool = False
    _transport_registered: bool = False
    _route_handlers: "UiRouteHandlers | None" = field(default=None, init=False)

    @classmethod
    def create(cls) -> "UiServerRuntime":
        webapp = Flask("app", static_folder=get_abs_path("./webui"), static_url_path="/")
        webapp.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)

        WerkzeugRequest.max_form_memory_size = UPLOAD_LIMIT_BYTES
        webapp.config.update(
            JSON_SORT_KEYS=False,
            SESSION_COOKIE_NAME="session_" + runtime.get_runtime_id(),
            SESSION_COOKIE_SAMESITE="Lax",
            SESSION_PERMANENT=True,
            PERMANENT_SESSION_LIFETIME=timedelta(days=1),
            MAX_CONTENT_LENGTH=int(
                os.getenv("FLASK_MAX_CONTENT_LENGTH", str(UPLOAD_LIMIT_BYTES))
            ),
            MAX_FORM_MEMORY_SIZE=int(
                os.getenv("FLASK_MAX_FORM_MEMORY_SIZE", str(UPLOAD_LIMIT_BYTES))
            ),
        )

        lock = threading.RLock()
        socketio_server = socketio.AsyncServer(
            async_mode="asgi",
            namespaces="*",
            cors_allowed_origins=lambda _origin, environ: validate_ws_origin(environ)[0],
            logger=False,
            engineio_logger=False,
            ping_interval=25,
            ping_timeout=20,
            max_http_buffer_size=50 * 1024 * 1024,
        )

        ws_manager = WsManager(socketio_server, lock)
        set_shared_ws_manager(ws_manager)

        server_runtime = cls(
            webapp=webapp,
            socketio_server=socketio_server,
            ws_manager=ws_manager,
            lock=lock,
            settings_snapshot={},
        )
        server_runtime.refresh_runtime_settings()
        return server_runtime

    def refresh_runtime_settings(self) -> None:
        self.settings_snapshot = settings_helper.get_settings()
        settings_helper.set_runtime_settings_snapshot(self.settings_snapshot)
        self.ws_manager.set_server_restart_broadcast(
            self.settings_snapshot.get("websocket_server_restart_enabled", True)
        )

    def register_http_routes(self) -> None:
        if self._routes_registered:
            return

        handlers = UiRouteHandlers(self)
        self._route_handlers = handlers
        self.webapp.add_url_rule(
            "/login",
            "login_handler",
            handlers.login_handler,
            methods=["GET", "POST"],
        )
        self.webapp.add_url_rule(
            "/logout",
            "logout_handler",
            handlers.logout_handler,
            methods=["GET"],
        )
        self.webapp.add_url_rule(
            "/",
            "serve_index",
            handlers.serve_index,
            methods=["GET"],
        )
        self.webapp.add_url_rule(
            "/plugins/<plugin_name>/<path:asset_path>",
            "serve_builtin_plugin_asset",
            handlers.serve_builtin_plugin_asset,
            methods=["GET"],
        )
        self.webapp.add_url_rule(
            "/usr/plugins/<plugin_name>/<path:asset_path>",
            "serve_plugin_asset",
            handlers.serve_plugin_asset,
            methods=["GET"],
        )
        self.webapp.add_url_rule(
            "/extensions/webui/<path:asset_path>",
            "serve_extension_asset",
            handlers.serve_extension_asset,
            methods=["GET"],
        )
        self._routes_registered = True

    def register_transport_handlers(self) -> None:
        if self._transport_registered:
            return
        register_api_route(self.webapp, self.lock)
        register_ws_namespace(
            self.socketio_server,
            self.webapp,
            self.lock,
            manager=self.ws_manager,
        )
        self._transport_registered = True

    def build_asgi_app(self, startup_monitor: StartupMonitor):
        with startup_monitor.stage("wsgi.middleware.create"):
            wsgi_app = WSGIMiddleware(self.webapp)

        with startup_monitor.stage("mcp.proxy.init"):
            mcp_app = mcp_server.DynamicMcpProxy.get_instance()

        with startup_monitor.stage("a2a.proxy.init"):
            a2a_app = fasta2a_server.DynamicA2AProxy.get_instance()

        with startup_monitor.stage("starlette.app.create"):
            starlette_app = Starlette(
                routes=[
                    Mount("/mcp", app=mcp_app),
                    Mount("/a2a", app=a2a_app),
                    Mount("/", app=wsgi_app),
                ],
                lifespan=startup_monitor.lifespan(),
            )

        with startup_monitor.stage("socketio.asgi.create"):
            return ASGIApp(self.socketio_server, other_asgi_app=starlette_app)

    def access_log_enabled(self) -> bool:
        return self.settings_snapshot.get("uvicorn_access_logs_enabled", False)


class UiRouteHandlers:
    def __init__(self, runtime_state: UiServerRuntime) -> None:
        self.runtime = runtime_state

    @extensible
    async def login_handler(self):
        error = None
        if request.method == "POST":
            user = dotenv.get_dotenv_value("AUTH_LOGIN")
            password = dotenv.get_dotenv_value("AUTH_PASSWORD")

            if request.form["username"] == user and request.form["password"] == password:
                session["authentication"] = login.get_credentials_hash()
                return redirect(url_for("serve_index"))
            else:
                await asyncio.sleep(1)
                error = "Invalid Credentials. Please try again."

        login_page_content = files.read_file("webui/login.html")
        return render_template_string(login_page_content, error=error)

    @extensible
    async def logout_handler(self):
        session.pop("authentication", None)
        return redirect(url_for("login_handler"))

    @requires_auth
    @extensible
    async def serve_index(self):
        try:
            gitinfo = git.get_git_info()
        except Exception:
            gitinfo = {
                "version": "unknown",
                "commit_time": "unknown",
            }

        index = files.read_file("webui/index.html")
        return files.replace_placeholders_text(
            _content=index,
            version_no=gitinfo["version"],
            version_time=gitinfo["commit_time"],
            runtime_id=runtime.get_runtime_id(),
            runtime_is_development=("true" if runtime.is_development() else "false"),
            logged_in=("true" if login.get_credentials_hash() else "false"),
        )

    @requires_auth
    async def serve_builtin_plugin_asset(self, plugin_name, asset_path):
        return await self._serve_plugin_asset(plugin_name, asset_path)

    @requires_auth
    async def serve_plugin_asset(self, plugin_name, asset_path):
        return await self._serve_plugin_asset(plugin_name, asset_path)

    @requires_auth
    async def serve_extension_asset(self, asset_path):
        exts = files.get_abs_path("extensions/webui")
        path = files.get_abs_path(exts, asset_path)
        if not files.is_in_dir(path, exts):
            return Response("Access denied", 403)
        return send_file(path)

    @extensible
    async def _serve_plugin_asset(self, plugin_name, asset_path):
        from helpers import plugins

        plugin_dir = plugins.find_plugin_dir(plugin_name)
        if not plugin_dir:
            return Response("Plugin not found", 404)

        try:
            asset_file = files.get_abs_path(plugin_dir, asset_path)
            webui_dir = files.get_abs_path(plugin_dir, "webui")
            webui_extensions_dir = files.get_abs_path(plugin_dir, "extensions/webui")

            if not files.is_in_dir(str(asset_file), str(webui_dir)) and not files.is_in_dir(
                str(asset_file), str(webui_extensions_dir)
            ):
                return Response("Access denied", 403)

            if not files.is_file(asset_file):
                return Response("Asset not found", 404)

            return send_file(str(asset_file))
        except Exception as e:
            PrintStyle.error(f"Error serving plugin asset: {e}")
            return Response("Error serving asset", 500)
