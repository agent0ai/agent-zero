import os
import asyncio
from typing import Annotated, Literal, Union
from urllib.parse import urlparse
from openai import BaseModel
from pydantic import Field
import fastmcp
from fastmcp import FastMCP
import contextvars
import re

from agent import AgentContext, AgentContextType, UserMessage
from helpers.persist_chat import remove_chat
from initialize import initialize_agent
from helpers.print_style import PrintStyle
from helpers import settings, projects, server_auth
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send
from fastmcp.server.http import create_sse_app, create_base_app, build_resource_metadata_url # type: ignore
from starlette.routing import Mount  # type: ignore
from starlette.requests import Request
import threading

_PRINTER = PrintStyle(italic=True, font_color="green", padding=False)

# Context variable to store project name from URL or header (per-request)
_mcp_project_name: contextvars.ContextVar[str | None] = contextvars.ContextVar('mcp_project_name', default=None)

# Proxy route: optional /t-{token} and /p-{project} segments, then the endpoint.
# The token may instead come from "Authorization: Bearer", the project from X-A0-Project.
_MCP_ROUTE = re.compile(
    r"^(?:/t-(?P<token>[^/]+))?(?:/p-(?P<project>[^/]+))?(?P<endpoint>/(?:sse|messages|http)(?:/.*)?)$"
)

mcp_server: FastMCP = FastMCP(
    name="Agent Zero integrated MCP Server",
    instructions="""
    Connect to remote Agent Zero instance.
    Agent Zero is a general AI assistant controlling it's linux environment.
    Agent Zero can install software, manage files, execute commands, code, use internet, etc.
    Agent Zero's environment is isolated unless configured otherwise.
    """,
)


class ToolResponse(BaseModel):
    status: Literal["success"] = Field(
        description="The status of the response", default="success"
    )
    response: str = Field(
        description="The response from the remote Agent Zero Instance"
    )
    chat_id: str = Field(description="The id of the chat this message belongs to.")


class ToolError(BaseModel):
    status: Literal["error"] = Field(
        description="The status of the response", default="error"
    )
    error: str = Field(
        description="The error message from the remote Agent Zero Instance"
    )
    chat_id: str = Field(description="The id of the chat this message belongs to.")


SEND_MESSAGE_DESCRIPTION = """
Send a message to the remote Agent Zero Instance.
This tool is used to send a message to the remote Agent Zero Instance connected remotely via MCP.
"""


@mcp_server.tool(
    name="send_message",
    description=SEND_MESSAGE_DESCRIPTION,
    tags={
        "agent_zero",
        "chat",
        "remote",
        "communication",
        "dialogue",
        "sse",
        "send",
        "message",
        "start",
        "new",
        "continue",
    },
    annotations={
        "remote": True,
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "title": SEND_MESSAGE_DESCRIPTION,
    },
)
async def send_message(
    message: Annotated[
        str,
        Field(
            description="The message to send to the remote Agent Zero Instance",
            title="message",
        ),
    ],
    attachments: (
        Annotated[
            list[str],
            Field(
                description="Optional: A list of attachments (file paths or web urls) to send to the remote Agent Zero Instance with the message. Default: Empty list",
                title="attachments",
            ),
        ]
        | None
    ) = None,
    chat_id: (
        Annotated[
            str,
            Field(
                description="Optional: ID of the chat. Used to continue a chat. This value is returned in response to sending previous message. Default: Empty string",
                title="chat_id",
            ),
        ]
        | None
    ) = None,
    persistent_chat: (
        Annotated[
            bool,
            Field(
                description="Optional: Whether to use a persistent chat. If true, the chat will be saved and can be continued later. Default: False.",
                title="persistent_chat",
            ),
        ]
        | None
    ) = None,
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(
        description="The response from the remote Agent Zero Instance", title="response"
    ),
]:
    # Get project name from context variable (set in proxy __call__)
    project_name = _mcp_project_name.get()

    context: AgentContext | None = None
    if chat_id:
        context = AgentContext.get(chat_id)
        if not context:
            return ToolError(error="Chat not found", chat_id=chat_id)
        else:
            # If the chat is found, we use the persistent chat flag to determine
            # whether we should save the chat or delete it afterwards
            # If we continue a conversation, it must be persistent
            persistent_chat = True

            # Validation: if the request names a project but context has different project
            if project_name:
                existing_project = context.get_data(projects.CONTEXT_DATA_KEY_PROJECT)
                if existing_project and existing_project != project_name:
                    return ToolError(
                        error=f"Chat belongs to project '{existing_project}' but the request specifies '{project_name}'",
                        chat_id=chat_id
                    )
    else:
        config = initialize_agent()
        context = AgentContext(config=config, type=AgentContextType.BACKGROUND)

        # Activate project if specified in the URL or the X-A0-Project header
        if project_name:
            try:
                projects.activate_project(context.id, project_name)
            except Exception as e:
                return ToolError(error=f"Failed to activate project: {str(e)}", chat_id="")

    if not message:
        return ToolError(
            error="Message is required", chat_id=context.id if persistent_chat else ""
        )

    try:
        response = await _run_chat(context, message, attachments)
        if not persistent_chat:
            context.reset()
            AgentContext.remove(context.id)
            remove_chat(context.id)
        return ToolResponse(
            response=response, chat_id=context.id if persistent_chat else ""
        )
    except Exception as e:
        return ToolError(error=str(e), chat_id=context.id if persistent_chat else "")


FINISH_CHAT_DESCRIPTION = """
Finish a chat with the remote Agent Zero Instance.
This tool is used to finish a persistent chat (send_message with persistent_chat=True) with the remote Agent Zero Instance connected remotely via MCP.
If you want to continue the chat, use the send_message tool instead.
Always use this tool to finish persistent chat conversations with remote Agent Zero.
"""


@mcp_server.tool(
    name="finish_chat",
    description=FINISH_CHAT_DESCRIPTION,
    tags={
        "agent_zero",
        "chat",
        "remote",
        "communication",
        "dialogue",
        "sse",
        "finish",
        "close",
        "end",
        "stop",
    },
    annotations={
        "remote": True,
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
        "title": FINISH_CHAT_DESCRIPTION,
    },
)
async def finish_chat(
    chat_id: Annotated[
        str,
        Field(
            description="ID of the chat to be finished. This value is returned in response to sending previous message.",
            title="chat_id",
        ),
    ]
) -> Annotated[
    Union[ToolResponse, ToolError],
    Field(
        description="The response from the remote Agent Zero Instance", title="response"
    ),
]:
    if not chat_id:
        return ToolError(error="Chat ID is required", chat_id="")

    context = AgentContext.get(chat_id)
    if not context:
        return ToolError(error="Chat not found", chat_id=chat_id)
    else:
        context.reset()
        AgentContext.remove(context.id)
        remove_chat(context.id)
        return ToolResponse(response="Chat finished", chat_id=chat_id)


async def _run_chat(
    context: AgentContext, message: str, attachments: list[str] | None = None
):
    try:
        _PRINTER.print("MCP Chat message received")

        # Attachment filenames for logging
        attachment_filenames = []
        if attachments:
            for attachment in attachments:
                if os.path.exists(attachment):
                    attachment_filenames.append(attachment)
                else:
                    try:
                        url = urlparse(attachment)
                        if url.scheme in ["http", "https", "ftp", "ftps", "sftp"]:
                            attachment_filenames.append(attachment)
                        else:
                            _PRINTER.print(f"Skipping attachment: [{attachment}]")
                    except Exception:
                        _PRINTER.print(f"Skipping attachment: [{attachment}]")

        _PRINTER.print("User message:")
        _PRINTER.print(f"> {message}")
        if attachment_filenames:
            _PRINTER.print("Attachments:")
            for filename in attachment_filenames:
                _PRINTER.print(f"- {filename}")

        task = context.communicate(
            UserMessage(
                message=message, system_message=[], attachments=attachment_filenames
            )
        )
        result = await task.result()

        # Success
        _PRINTER.print(f"MCP Chat message completed: {result}")

        return result

    except Exception as e:
        # Error
        _PRINTER.print(f"MCP Chat message failed: {e}")

        raise RuntimeError(f"MCP Chat message failed: {e}") from e


class DynamicMcpProxy:
    _instance: "DynamicMcpProxy | None" = None

    """A dynamic proxy that allows swapping the underlying MCP applications on the fly."""

    def __init__(self):
        cfg = settings.get_settings()
        self.token = ""
        self.sse_app: ASGIApp | None = None
        self.http_app: ASGIApp | None = None
        self.http_session_manager = None
        self.http_session_task_group = None
        self._lock = threading.RLock()  # Use RLock to avoid deadlocks
        self.reconfigure(cfg["mcp_server_token"])

    @staticmethod
    def get_instance():
        if DynamicMcpProxy._instance is None:
            DynamicMcpProxy._instance = DynamicMcpProxy()
        return DynamicMcpProxy._instance

    def reconfigure(self, token: str):
        if self.token == token:
            return

        self.token = token
        # The apps serve token-free paths; the proxy authenticates each request and
        # keeps a URL token in root_path, so the SSE endpoint event points the client
        # back to the form it connected with (/t-{token}/messages/ or /messages/).
        sse_path = "/sse"
        http_path = "/http"
        message_path = "/messages/"

        # Update settings in the MCP server instance if provided
        # Keep FastMCP settings synchronized so downstream helpers that read these
        # values (including deprecated accessors) resolve the runtime paths.
        fastmcp.settings.message_path = message_path
        fastmcp.settings.sse_path = sse_path
        fastmcp.settings.streamable_http_path = http_path

        # Create new MCP apps with updated settings
        with self._lock:
            middleware = [Middleware(BaseHTTPMiddleware, dispatch=mcp_middleware)]

            self.sse_app = create_sse_app(
                server=mcp_server,
                message_path=message_path,
                sse_path=sse_path,
                auth=mcp_server.auth,
                debug=fastmcp.settings.debug,
                middleware=list(middleware),
            )

            self.http_app = self._create_custom_http_app(
                http_path,
                middleware=list(middleware),
            )

    def _create_custom_http_app(
        self,
        streamable_http_path: str,
        *,
        middleware: list[Middleware],
    ) -> ASGIApp:
        """Create a Streamable HTTP app with manual session manager lifecycle."""

        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager  # type: ignore
        from mcp.server.auth.middleware.bearer_auth import RequireAuthMiddleware  # type: ignore
        import anyio

        server_routes = []
        server_middleware = []

        self.http_session_task_group = None
        self.http_session_manager = StreamableHTTPSessionManager(
            app=mcp_server._mcp_server,
            event_store=None,
            json_response=True,
            stateless=False,
        )

        async def handle_streamable_http(scope, receive, send):
            if self.http_session_task_group is None:
                self.http_session_task_group = anyio.create_task_group()
                await self.http_session_task_group.__aenter__()
                if self.http_session_manager:
                    self.http_session_manager._task_group = self.http_session_task_group

            if self.http_session_manager:
                await self.http_session_manager.handle_request(scope, receive, send)

        auth_provider = mcp_server.auth

        if auth_provider:
            server_routes.extend(auth_provider.get_routes(mcp_path=streamable_http_path))
            server_middleware.extend(auth_provider.get_middleware())

            resource_url = auth_provider._get_resource_url(streamable_http_path)
            resource_metadata_url = (
                build_resource_metadata_url(resource_url) if resource_url else None
            )

            server_routes.append(
                Mount(
                    streamable_http_path,
                    app=RequireAuthMiddleware(
                        handle_streamable_http,
                        auth_provider.required_scopes,
                        resource_metadata_url,
                    ),
                )
            )
        else:
            server_routes.append(
                Mount(
                    streamable_http_path,
                    app=handle_streamable_http,
                )
            )

        additional_routes = mcp_server._get_additional_http_routes()
        if additional_routes:
            server_routes.extend(additional_routes)

        server_middleware.extend(middleware)

        return create_base_app(
            routes=server_routes,
            middleware=server_middleware,
            debug=fastmcp.settings.debug,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Forward the ASGI calls to the appropriate app based on the URL path"""
        with self._lock:
            sse_app = self.sse_app
            http_app = self.http_app

        if not sse_app or not http_app:
            raise RuntimeError("MCP apps not initialized")

        # Route based on the path below the /mcp mount
        path = scope.get("path", "")
        root_path = scope.get("root_path", "")
        route_path = path[len(root_path):] if root_path and path.startswith(root_path) else path
        route = _MCP_ROUTE.match(route_path)
        if not route:
            raise StarletteHTTPException(status_code=403, detail="MCP forbidden")

        # Token in the path (/t-{token}/...) or in the Authorization: Bearer header
        url_token = route.group("token")
        if url_token is not None:
            authorized = server_auth.token_matches(url_token, self.token)
        else:
            authorized = server_auth.token_matches(
                server_auth.get_bearer_token(scope), self.token
            )
        if not authorized:
            raise StarletteHTTPException(status_code=403, detail="MCP forbidden")

        # Project from the path (/p-{project}/) or the X-A0-Project header
        try:
            project_name = server_auth.resolve_project(route.group("project"), scope)
        except server_auth.RequestRejected as e:
            raise StarletteHTTPException(status_code=e.status_code, detail=e.detail)
        if project_name:
            _PRINTER.print(f"[MCP] Proxy resolved project: {project_name}")

        # Store project in context variable (will be available in send_message)
        _mcp_project_name.set(project_name)

        # Drop the /p-{project} segment; keep a URL token in root_path so the
        # SSE transport announces /t-{token}/messages/ to URL-token clients and
        # a token-free /messages/ to header clients.
        prefix = root_path + (f"/t-{url_token}" if url_token is not None else "")
        endpoint = route.group("endpoint")
        modified_scope = dict(scope)
        modified_scope["root_path"] = prefix
        modified_scope["path"] = prefix + endpoint

        if endpoint.startswith(("/sse", "/messages")):
            await sse_app(modified_scope, receive, send)
        else:
            await http_app(modified_scope, receive, send)


async def mcp_middleware(request: Request, call_next):
    """Middleware to check if MCP server is enabled."""
    # check if MCP server is enabled
    cfg = settings.get_settings()
    if not cfg["mcp_server_enabled"]:
        PrintStyle.error("[MCP] Access denied: MCP server is disabled in settings.")
        raise StarletteHTTPException(
            status_code=403, detail="MCP server is disabled in settings."
        )

    return await call_next(request)
