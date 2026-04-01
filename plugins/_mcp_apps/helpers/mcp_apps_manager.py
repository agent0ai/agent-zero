"""
MCP Apps Manager — singleton that tracks UI-enabled tools, fetches UI resources,
manages active app sessions, and proxies tool calls from iframes back to MCP servers.

Proxy calls from iframes use persistent MCP sessions to avoid the per-call overhead
of creating new connections and running the MCP handshake each time.
"""

import asyncio
import threading
import uuid
from contextlib import AsyncExitStack
from datetime import timedelta
from typing import Any, Optional

from helpers.print_style import PrintStyle


class _ActiveApp:
    """Tracks a single active MCP App iframe instance."""

    def __init__(
        self,
        app_id: str,
        server_name: str,
        tool_name: str,
        resource_uri: str,
        html_content: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any] | None,
        ui_meta: dict[str, Any],
        tool_description: str = "",
        tool_input_schema: dict[str, Any] | None = None,
    ):
        self.app_id = app_id
        self.server_name = server_name
        self.tool_name = tool_name
        self.resource_uri = resource_uri
        self.html_content = html_content
        self.tool_args = tool_args
        self.tool_result = tool_result
        self.ui_meta = ui_meta
        self.tool_description = tool_description
        self.tool_input_schema = tool_input_schema or {"type": "object"}


class _ProxySession:
    """Maintains a persistent MCP ClientSession in a dedicated background task.

    anyio cancel scopes (used by streamablehttp_client) require enter/exit from
    the same asyncio Task.  We satisfy this by running the entire session
    lifecycle inside a single long-lived task and communicating via a queue.
    """

    def __init__(self):
        self.session = None
        self._queue: asyncio.Queue | None = None
        self._task: asyncio.Task | None = None
        self._ready = asyncio.Event()
        self._open_error: BaseException | None = None

    async def open(self, server):
        """Start the background task that owns the transport + session."""
        self._ready = asyncio.Event()
        self._open_error = None
        self._queue = asyncio.Queue()
        self._task = asyncio.create_task(self._run(server))
        await self._ready.wait()
        if self._open_error:
            raise self._open_error

    async def _run(self, server):
        """Background task — owns the full async-context-manager stack."""
        from mcp import ClientSession
        from helpers.mcp_handler import (
            MCPServerRemote,
            MCPServerLocal,
            _initialize_with_ui_ext,
            _is_streaming_http_type,
            CustomHTTPClientFactory,
        )
        from helpers import settings

        try:
            async with AsyncExitStack() as stack:
                if isinstance(server, MCPServerRemote):
                    set_ = settings.get_settings()
                    init_timeout = server.init_timeout or set_["mcp_client_init_timeout"] or 5
                    tool_timeout = server.tool_timeout or set_["mcp_client_tool_timeout"] or 60
                    client_factory = CustomHTTPClientFactory(verify=server.verify)

                    if _is_streaming_http_type(server.type):
                        from mcp.client.streamable_http import streamablehttp_client

                        read_stream, write_stream, _ = await stack.enter_async_context(
                            streamablehttp_client(
                                url=server.url,
                                headers=server.headers,
                                timeout=timedelta(seconds=init_timeout),
                                sse_read_timeout=timedelta(seconds=tool_timeout),
                                httpx_client_factory=client_factory,
                            )
                        )
                    else:
                        from mcp.client.sse import sse_client

                        read_stream, write_stream = await stack.enter_async_context(
                            sse_client(
                                url=server.url,
                                headers=server.headers,
                                timeout=init_timeout,
                                sse_read_timeout=tool_timeout,
                                httpx_client_factory=client_factory,
                            )
                        )
                elif isinstance(server, MCPServerLocal):
                    from mcp import StdioServerParameters
                    from mcp.client.stdio import stdio_client
                    from shutil import which

                    if not server.command or not which(server.command):
                        raise ValueError(f"Command '{server.command}' not found")

                    params = StdioServerParameters(
                        command=server.command,
                        args=server.args,
                        env=server.env,
                        encoding=server.encoding,
                        encoding_error_handler=server.encoding_error_handler,
                    )
                    read_stream, write_stream = await stack.enter_async_context(
                        stdio_client(params)
                    )
                else:
                    raise TypeError(f"Unsupported server type: {type(server)}")

                self.session = await stack.enter_async_context(
                    ClientSession(
                        read_stream,
                        write_stream,
                        read_timeout_seconds=timedelta(seconds=120),
                    )
                )
                await _initialize_with_ui_ext(self.session)

                # Signal that we are ready to accept requests
                self._ready.set()

                # Process requests until a None sentinel arrives
                while True:
                    item = await self._queue.get()
                    if item is None:
                        break
                    coro_factory, future = item
                    try:
                        result = await coro_factory(self.session)
                        if not future.done():
                            future.set_result(result)
                    except Exception as exc:
                        if not future.done():
                            future.set_exception(exc)
        except Exception as exc:
            # If we haven't signalled ready yet, store the error so open() can raise it
            if not self._ready.is_set():
                self._open_error = exc
                self._ready.set()
            else:
                PrintStyle(font_color="red", padding=True).print(
                    f"MCP Apps: Proxy session background task error: {exc}"
                )
        finally:
            self.session = None

    async def execute(self, coro_factory):
        """Submit work to the background task and wait for the result."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self._queue.put((coro_factory, future))
        return await future

    async def close(self):
        """Signal the background task to shut down and wait for it."""
        self.session = None
        if self._queue:
            try:
                await self._queue.put(None)
            except Exception:
                pass
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except (asyncio.TimeoutError, Exception):
                self._task.cancel()
        self._task = None
        self._queue = None


class MCPAppsManager:
    """Singleton managing MCP App lifecycle and communication."""

    _instance: Optional["MCPAppsManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._apps: dict[str, _ActiveApp] = {}
        self._resource_cache: dict[str, str] = {}
        self._proxy_sessions: dict[str, _ProxySession] = {}

    @classmethod
    def get_instance(cls) -> "MCPAppsManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_app(
        self,
        server_name: str,
        tool_name: str,
        resource_uri: str,
        html_content: str,
        tool_args: dict[str, Any],
        tool_result: dict[str, Any] | None,
        ui_meta: dict[str, Any],
        tool_description: str = "",
        tool_input_schema: dict[str, Any] | None = None,
    ) -> str:
        """Register a new active app instance. Returns the app_id."""
        app_id = str(uuid.uuid4())
        app = _ActiveApp(
            app_id=app_id,
            server_name=server_name,
            tool_name=tool_name,
            resource_uri=resource_uri,
            html_content=html_content,
            tool_args=tool_args,
            tool_result=tool_result,
            ui_meta=ui_meta,
            tool_description=tool_description,
            tool_input_schema=tool_input_schema,
        )
        with self._lock:
            self._apps[app_id] = app
        PrintStyle(font_color="cyan", padding=True).print(
            f"MCP Apps: Registered app '{app_id}' for tool '{server_name}.{tool_name}'"
        )
        return app_id

    def get_app(self, app_id: str) -> _ActiveApp | None:
        with self._lock:
            return self._apps.get(app_id)

    def remove_app(self, app_id: str) -> None:
        with self._lock:
            self._apps.pop(app_id, None)

    def get_app_data(self, app_id: str) -> dict[str, Any] | None:
        """Return serializable app data for the frontend."""
        app = self.get_app(app_id)
        if not app:
            return None
        return {
            "app_id": app.app_id,
            "server_name": app.server_name,
            "tool_name": app.tool_name,
            "resource_uri": app.resource_uri,
            "html_content": app.html_content,
            "tool_args": app.tool_args,
            "tool_result": app.tool_result,
            "ui_meta": app.ui_meta,
            "tool_description": app.tool_description,
            "tool_input_schema": app.tool_input_schema,
        }

    def cache_resource(self, uri: str, html: str) -> None:
        with self._lock:
            self._resource_cache[uri] = html

    def get_cached_resource(self, uri: str) -> str | None:
        with self._lock:
            return self._resource_cache.get(uri)

    @staticmethod
    def _find_mcp_server(server_name: str, tool_name: str | None = None):
        """Find an MCP server (and optionally verify it has a tool).
        Returns the server reference so callers can invoke async methods
        without holding MCPConfig's threading lock."""
        import helpers.mcp_handler as mcp_handler

        mcp_config = mcp_handler.MCPConfig.get_instance()
        for server in mcp_config.servers:
            if server.name == server_name:
                if tool_name is None or server.has_tool(tool_name):
                    return server
        return None

    async def fetch_ui_resource(self, server_name: str, resource_uri: str) -> str:
        """Fetch a ui:// resource from an MCP server. Uses cache if available."""
        cached = self.get_cached_resource(resource_uri)
        if cached:
            return cached

        import helpers.mcp_handler as mcp_handler

        mcp_config = mcp_handler.MCPConfig.get_instance()
        result = await mcp_config.read_resource(server_name, resource_uri)

        html_content = ""
        for content in result.contents:
            if hasattr(content, "text") and content.text:
                html_content = content.text
                break
            elif hasattr(content, "blob") and content.blob:
                import base64
                html_content = base64.b64decode(content.blob).decode("utf-8")
                break

        if not html_content:
            raise ValueError(
                f"UI resource '{resource_uri}' from server '{server_name}' returned no content"
            )

        self.cache_resource(resource_uri, html_content)
        return html_content

    async def _get_proxy_session(self, server_name: str) -> _ProxySession:
        """Get or create a persistent proxy session for the given server."""
        ps = self._proxy_sessions.get(server_name)
        if ps and ps.session is not None:
            return ps

        # Create a new persistent session
        server = self._find_mcp_server(server_name)
        if not server:
            raise ValueError(f"MCP server '{server_name}' not found")

        ps = _ProxySession()
        await ps.open(server)
        self._proxy_sessions[server_name] = ps
        PrintStyle(font_color="cyan", padding=True).print(
            f"MCP Apps: Opened persistent proxy session for '{server_name}'"
        )
        return ps

    async def _close_proxy_session(self, server_name: str):
        """Close and discard a persistent proxy session."""
        ps = self._proxy_sessions.pop(server_name, None)
        if ps:
            await ps.close()
            PrintStyle(font_color="cyan", padding=True).print(
                f"MCP Apps: Closed proxy session for '{server_name}'"
            )

    async def _proxy_with_retry(self, server_name: str, coro_factory):
        """Run coro_factory(session) via the background task, with one retry on failure."""
        for attempt in range(2):
            try:
                ps = await self._get_proxy_session(server_name)
                return await ps.execute(coro_factory)
            except Exception:
                if attempt == 0:
                    PrintStyle(font_color="yellow", padding=True).print(
                        f"MCP Apps: Proxy session error for '{server_name}', recreating..."
                    )
                    await self._close_proxy_session(server_name)
                else:
                    raise

    async def proxy_tool_call(
        self, app_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Proxy a tools/call request from an iframe back to the MCP server."""
        app = self.get_app(app_id)
        if not app:
            return {"error": {"code": -32000, "message": f"App '{app_id}' not found"}}

        try:
            from mcp.types import CallToolResult

            async def do_call(session):
                return await session.call_tool(tool_name, arguments)

            result: CallToolResult = await self._proxy_with_retry(app.server_name, do_call)
            content_list = []
            for item in result.content:
                if item.type == "text":
                    content_list.append({"type": "text", "text": item.text})
                elif item.type == "image":
                    content_list.append({
                        "type": "image",
                        "data": item.data,
                        "mimeType": item.mimeType,
                    })
            response = {"content": content_list, "isError": result.isError}
            if hasattr(result, "structuredContent") and result.structuredContent:
                response["structuredContent"] = result.structuredContent
            return response
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Apps: Proxy tool call failed for '{app.server_name}.{tool_name}': {e}"
            )
            return {"error": {"code": -32000, "message": str(e)}}

    async def proxy_resource_read(
        self, app_id: str, uri: str
    ) -> dict[str, Any]:
        """Proxy a resources/read request from an iframe back to the MCP server."""
        app = self.get_app(app_id)
        if not app:
            return {"error": {"code": -32000, "message": f"App '{app_id}' not found"}}

        try:
            async def do_read(session):
                return await session.read_resource(uri)

            result = await self._proxy_with_retry(app.server_name, do_read)
            contents = []
            for c in result.contents:
                entry: dict[str, Any] = {"uri": str(c.uri)}
                if hasattr(c, "mimeType") and c.mimeType:
                    entry["mimeType"] = c.mimeType
                if hasattr(c, "text") and c.text:
                    entry["text"] = c.text
                elif hasattr(c, "blob") and c.blob:
                    entry["blob"] = c.blob
                contents.append(entry)
            return {"contents": contents}
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Apps: Proxy resource read failed for '{uri}': {e}"
            )
            return {"error": {"code": -32000, "message": str(e)}}
