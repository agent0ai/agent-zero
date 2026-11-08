from __future__ import annotations

import asyncio
import http.client
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, quote, unquote, urlsplit

from flask.sessions import SecureCookieSessionInterface
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.types import Receive, Scope, Send
from starlette.websockets import WebSocket
from wsproto import ConnectionType, WSConnection
from wsproto.events import (
    AcceptConnection,
    BytesMessage,
    CloseConnection,
    Ping,
    RejectConnection,
    Request as WebSocketRequest,
    TextMessage,
)

from helpers import login, virtual_desktop


HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "cookie",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


XPRA_MENU_CUSTOM_PATCH = b"""
;(function () {
  function a0DesktopElement(selector) {
    return document.querySelector(selector);
  }

  window.noWindowList = function noWindowList() {
    const openWindows = a0DesktopElement("#open_windows");
    if (openWindows) openWindows.remove();
  };

  const originalAddWindowListItem = window.addWindowListItem;
  if (typeof originalAddWindowListItem === "function" && !originalAddWindowListItem.__a0SafeWindowList) {
    const safeAddWindowListItem = function addWindowListItem(...args) {
      if (!a0DesktopElement("#open_windows_list")) return undefined;
      return originalAddWindowListItem.apply(this, args);
    };
    safeAddWindowListItem.__a0SafeWindowList = true;
    window.addWindowListItem = safeAddWindowListItem;
  }
}());
"""

XPRA_WINDOW_OFFSET_WARNING = b'&&this.warn("window does not fit in canvas, offsets: ",x,y)'
XPRA_WINDOW_OFFSET_WARNING_PATCH = b'&&false&&this.warn("window does not fit in canvas, offsets: ",x,y)'
XPRA_WINDOW_SCRIPT = b'src="js/Window.js"'
XPRA_WINDOW_SCRIPT_PATCH = b'src="js/Window.js?a0_desktop_patch=20260506"'


class VirtualDesktopGateway:
    def __init__(self, flask_app=None, mount_path: str = "/desktop") -> None:
        self.flask_app = flask_app
        self.mount_path = "/" + mount_path.strip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            await self.websocket(scope, receive, send)
            return
        if scope["type"] == "http":
            await self.http(scope, receive, send)
            return
        await PlainTextResponse("Unsupported scope", status_code=500)(scope, receive, send)

    async def http(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.is_authorized(scope):
            await PlainTextResponse("Authentication required", status_code=401)(scope, receive, send)
            return

        path = self.relative_path(scope)
        if path in {"", "/"}:
            await RedirectResponse(f"{self.mount_path}/health")(scope, receive, send)
            return
        if path == "/health":
            await JSONResponse(virtual_desktop.collect_status())(scope, receive, send)
            return
        if path == "/resize":
            await self.resize(scope, receive, send)
            return

        session_request = self.session_request(path)
        if not session_request:
            await PlainTextResponse("Desktop session not found.", status_code=404)(scope, receive, send)
            return
        token, upstream_path = session_request
        if upstream_path in {"", "/"}:
            await RedirectResponse(self.session_index_url(token))(scope, receive, send)
            return
        await self.proxy_http(scope, receive, send, token, upstream_path)

    async def resize(self, scope: Scope, receive: Receive, send: Send) -> None:
        query = self.query(scope)
        payload: dict[str, object] = {}
        if scope.get("method") == "POST":
            try:
                payload = await Request(scope, receive).json()
            except Exception:
                payload = {}
        token = str(payload.get("token") or query.get("token", [""])[0])
        width = payload.get("width") or query.get("width", [0])[0]
        height = payload.get("height") or query.get("height", [0])[0]
        try:
            result = virtual_desktop.resize_session(token, int(float(width)), int(float(height)))
        except (TypeError, ValueError):
            result = {"ok": False, "error": "Invalid virtual desktop size."}
        await JSONResponse(result, status_code=200 if result.get("ok") else 400)(scope, receive, send)

    async def proxy_http(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        token: str,
        upstream_path: str,
    ) -> None:
        endpoint = virtual_desktop.proxy_for_token(token)
        if not endpoint:
            await PlainTextResponse("Desktop session not found.", status_code=404)(scope, receive, send)
            return

        body = await Request(scope, receive).body()
        try:
            status, headers, content = await asyncio.to_thread(
                self.fetch_http,
                endpoint,
                upstream_path,
                scope.get("query_string", b"").decode("latin-1"),
                str(scope.get("method") or "GET"),
                self.proxy_request_headers(scope),
                body,
            )
            content = self.proxy_response_content(upstream_path, content)
            await Response(
                content,
                status_code=status,
                headers=self.proxy_response_headers(headers, token),
            )(scope, receive, send)
        except (http.client.HTTPException, OSError, asyncio.TimeoutError):
            await PlainTextResponse("Desktop proxy is unavailable.", status_code=502)(scope, receive, send)

    async def websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        websocket = WebSocket(scope, receive=receive, send=send)
        if not self.is_authorized(scope):
            await websocket.close(code=1008)
            return

        session_request = self.session_request(self.relative_path(scope))
        if not session_request:
            await websocket.close(code=1008)
            return
        token, upstream_path = session_request
        endpoint = virtual_desktop.proxy_for_token(token)
        if not endpoint:
            await websocket.close(code=1008)
            return

        target = self.upstream_target(upstream_path or "/", scope.get("query_string", b""))
        try:
            reader, writer, upstream, subprotocol = await self.open_websocket(
                endpoint,
                target,
                tuple(scope.get("subprotocols") or ()),
            )
            await websocket.accept(subprotocol=subprotocol)
            await asyncio.gather(
                self.browser_to_xpra(websocket, upstream, writer),
                self.xpra_to_browser(websocket, upstream, reader, writer),
            )
        except Exception:
            try:
                await websocket.close(code=1011)
            except Exception:
                pass

    async def open_websocket(
        self,
        endpoint: virtual_desktop.VirtualDesktopEndpoint,
        target: str,
        subprotocols: tuple[str, ...],
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter, WSConnection, str | None]:
        reader, writer = await asyncio.open_connection(endpoint.host, endpoint.port)
        upstream = WSConnection(ConnectionType.CLIENT)
        writer.write(
            upstream.send(
                WebSocketRequest(
                    host=f"{endpoint.host}:{endpoint.port}",
                    target=target,
                    subprotocols=list(subprotocols),
                ),
            ),
        )
        await writer.drain()

        while True:
            data = await asyncio.wait_for(reader.read(65536), timeout=10)
            if not data:
                raise ConnectionError("Xpra WebSocket handshake closed early.")
            upstream.receive_data(data)
            for event in upstream.events():
                if isinstance(event, AcceptConnection):
                    return reader, writer, upstream, event.subprotocol
                if isinstance(event, RejectConnection):
                    raise ConnectionError(f"Xpra rejected WebSocket handshake with HTTP {event.status_code}.")
                if isinstance(event, CloseConnection):
                    raise ConnectionError("Xpra closed WebSocket handshake.")

    async def browser_to_xpra(
        self,
        websocket: WebSocket,
        upstream: WSConnection,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    writer.write(upstream.send(CloseConnection(code=1000)))
                    await writer.drain()
                    return
                if message.get("bytes") is not None:
                    writer.write(upstream.send(BytesMessage(data=message["bytes"])))
                elif message.get("text") is not None:
                    writer.write(upstream.send(TextMessage(data=str(message["text"]))))
                await writer.drain()
        finally:
            writer.close()

    async def xpra_to_browser(
        self,
        websocket: WebSocket,
        upstream: WSConnection,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    return
                upstream.receive_data(data)
                for event in upstream.events():
                    if isinstance(event, BytesMessage):
                        await websocket.send_bytes(event.data)
                    elif isinstance(event, TextMessage):
                        await websocket.send_text(event.data)
                    elif isinstance(event, Ping):
                        writer.write(upstream.send(event.response()))
                        await writer.drain()
                    elif isinstance(event, CloseConnection):
                        writer.write(upstream.send(event.response()))
                        await writer.drain()
                        return
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
            writer.close()

    def session_request(self, path: str) -> tuple[str, str] | None:
        prefix = "/session/"
        if not path.startswith(prefix):
            return None
        rest = path[len(prefix):]
        token, separator, upstream_path = rest.partition("/")
        token = unquote(token)
        if not token:
            return None
        return token, f"/{upstream_path}" if separator else "/"

    def session_index_url(self, token: str) -> str:
        quoted_token = quote(str(token), safe="")
        base_path = f"{self.mount_path}/session/{quoted_token}/"
        return f"{base_path}index.html?path={quote(base_path, safe='')}"

    def fetch_http(
        self,
        endpoint: virtual_desktop.VirtualDesktopEndpoint,
        upstream_path: str,
        query: str,
        method: str,
        headers: dict[str, str],
        body: bytes,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(endpoint.host, endpoint.port, timeout=60)
        try:
            connection.request(
                method,
                self.upstream_target(upstream_path, query.encode("latin-1")),
                body=body or None,
                headers={**headers, "Connection": "close"},
            )
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def upstream_target(self, upstream_path: str, query_string: bytes) -> str:
        query = query_string.decode("latin-1")
        target = upstream_path or "/"
        return f"{target}?{query}" if query else target

    def proxy_request_headers(self, scope: Scope) -> dict[str, str]:
        headers: dict[str, str] = {}
        for raw_name, raw_value in scope.get("headers", []):
            name = raw_name.decode("latin-1")
            lower = name.lower()
            if lower in HOP_BY_HOP_HEADERS or lower == "origin" or lower.startswith("sec-websocket"):
                continue
            headers[name] = raw_value.decode("latin-1")
        return headers

    def proxy_response_headers(self, headers: dict[str, str], token: str) -> dict[str, str]:
        response_headers: dict[str, str] = {}
        for name, value in dict(headers).items():
            lower = name.lower()
            if lower in HOP_BY_HOP_HEADERS:
                continue
            if lower == "location":
                value = self.rewrite_location(str(value), token)
            response_headers[name] = str(value)
        return response_headers

    def proxy_response_content(self, upstream_path: str, content: bytes) -> bytes:
        if upstream_path.endswith("/index.html") and XPRA_WINDOW_SCRIPT in content:
            content = content.replace(XPRA_WINDOW_SCRIPT, XPRA_WINDOW_SCRIPT_PATCH)
        if upstream_path.endswith("/js/MenuCustom.js") and XPRA_MENU_CUSTOM_PATCH not in content:
            return content + XPRA_MENU_CUSTOM_PATCH
        if upstream_path.endswith("/js/Window.js") and XPRA_WINDOW_OFFSET_WARNING in content:
            return content.replace(XPRA_WINDOW_OFFSET_WARNING, XPRA_WINDOW_OFFSET_WARNING_PATCH)
        return content

    def rewrite_location(self, location: str, token: str) -> str:
        quoted_token = quote(str(token), safe="")
        prefix = f"{self.mount_path}/session/{quoted_token}"
        parsed = urlsplit(location)
        if parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost"}:
            path = parsed.path or "/"
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{prefix}{path}{query}"
        if location.startswith("/"):
            return f"{prefix}{location}"
        return location

    def relative_path(self, scope: Scope) -> str:
        raw_path = scope.get("raw_path")
        path = raw_path.decode("latin-1") if raw_path else str(scope.get("path") or "")
        if path.startswith(self.mount_path):
            path = path[len(self.mount_path):]
        return path or "/"

    def query(self, scope: Scope) -> dict[str, list[str]]:
        return parse_qs(scope.get("query_string", b"").decode("latin-1"), keep_blank_values=True)

    def is_authorized(self, scope: Scope) -> bool:
        credentials_hash = login.get_credentials_hash()
        if not credentials_hash:
            return True
        if not self.flask_app:
            return False
        serializer = SecureCookieSessionInterface().get_signing_serializer(self.flask_app)
        if not serializer:
            return False
        cookie_header = dict(scope.get("headers", [])).get(b"cookie", b"").decode("latin-1")
        if not cookie_header:
            return False
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        session_cookie = cookies.get(self.flask_app.config.get("SESSION_COOKIE_NAME", "session"))
        if not session_cookie:
            return False
        try:
            session_data = serializer.loads(session_cookie.value)
        except Exception:
            return False
        return session_data.get("authentication") == credentials_hash


def install_route_hooks() -> None:
    from helpers.ui_server import UiServerRuntime

    if getattr(UiServerRuntime, "_a0_virtual_desktop_route_hooks_installed", False):
        return

    original_build_asgi_app = UiServerRuntime.build_asgi_app

    def build_asgi_app(self, startup_monitor):
        from socketio import ASGIApp
        from starlette.applications import Starlette
        from starlette.routing import Mount
        from uvicorn.middleware.wsgi import WSGIMiddleware

        from helpers import fasta2a_server, mcp_server
        from plugins._desktop.helpers.gateway import TuxeeGateway
        from plugins._browser.helpers.viewer_gateway import BrowserVncGateway

        with startup_monitor.stage("wsgi.middleware.create"):
            wsgi_app = WSGIMiddleware(self.webapp)

        with startup_monitor.stage("mcp.proxy.init"):
            mcp_app = mcp_server.DynamicMcpProxy.get_instance()

        with startup_monitor.stage("a2a.proxy.init"):
            a2a_app = fasta2a_server.DynamicA2AProxy.get_instance()

        with startup_monitor.stage("starlette.app.create"):
            starlette_app = Starlette(
                routes=[
                    Mount("/browser/vnc", app=BrowserVncGateway(self.webapp)),
                    Mount("/desktop/tuxee", app=TuxeeGateway(self.webapp)),
                    Mount("/desktop", app=VirtualDesktopGateway(self.webapp, "/desktop")),
                    Mount("/mcp", app=mcp_app),
                    Mount("/a2a", app=a2a_app),
                    Mount("/", app=wsgi_app),
                ],
                lifespan=startup_monitor.lifespan(),
            )

        with startup_monitor.stage("socketio.asgi.create"):
            return ASGIApp(self.socketio_server, other_asgi_app=starlette_app)

    UiServerRuntime.build_asgi_app = build_asgi_app
    UiServerRuntime._a0_virtual_desktop_route_hooks_installed = True
    UiServerRuntime._a0_virtual_desktop_original_build_asgi_app = original_build_asgi_app


def is_installed() -> bool:
    from helpers.ui_server import UiServerRuntime

    return bool(getattr(UiServerRuntime, "_a0_virtual_desktop_route_hooks_installed", False))
