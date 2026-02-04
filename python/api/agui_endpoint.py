"""AG-UI Protocol ASGI endpoint for Agent Zero.

This module provides the Starlette ASGI application that handles
AG-UI SSE streaming requests, including A2UI protocol support for
agent-generated UIs.

A2UI Protocol: https://a2ui.org/specification/v0.8-a2ui/
"""

import json
import threading
from typing import Callable

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

from python.helpers.print_style import PrintStyle
from python.helpers import settings
from python.helpers.agui_server import AguiServer, is_available
from python.helpers.agui_validation import validate_agui_request

_PRINTER = PrintStyle(italic=True, font_color="cyan", padding=False)


def is_loopback_address(address: str) -> bool:
    """Check if address is a loopback address."""
    import socket
    import struct

    loopback_checker = {
        socket.AF_INET: lambda x: struct.unpack("!I", socket.inet_aton(x))[0]
        >> (32 - 8)
        == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }

    try:
        socket.inet_pton(socket.AF_INET, address)
        return loopback_checker[socket.AF_INET](address)
    except socket.error:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, address)
        return loopback_checker[socket.AF_INET6](address)
    except socket.error:
        pass

    # Hostname - resolve and check
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
            for fam, _, _, _, sockaddr in r:
                if not loopback_checker[fam](sockaddr[0]):
                    return False
        except socket.gaierror:
            continue
    return True


def validate_auth(request: Request) -> tuple[bool, str | None]:
    """Validate authentication for AG-UI requests.

    Returns:
        Tuple of (is_valid, error_message)
    """
    import os

    cfg = settings.get_settings()

    # Check if AG-UI is enabled
    if not cfg.get("agui_enabled", True):
        return False, "AG-UI server is disabled"

    # Get expected token (use agui_token or fall back to mcp_server_token)
    agui_token = cfg.get("agui_token")
    mcp_token = cfg.get("mcp_server_token")
    expected_token = agui_token or mcp_token

    _PRINTER.print(f"[AG-UI Auth] agui_token='{agui_token}', mcp_token='{mcp_token}', expected='{expected_token}'")

    if not expected_token:
        # No auth configured, allow
        _PRINTER.print("[AG-UI Auth] No token configured, allowing request")
        return True, None

    # Check loopback override
    if os.environ.get("AGUI_ALLOW_LOOPBACK", "").lower() in ("true", "1", "yes"):
        client_host = request.client.host if request.client else ""
        if client_host and is_loopback_address(client_host):
            return True, None

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        if token == expected_token:
            return True, None

    # Check X-API-KEY header
    api_key = request.headers.get("X-API-KEY")
    if api_key == expected_token:
        return True, None

    # Check api_key in query params
    api_key = request.query_params.get("api_key")
    if api_key == expected_token:
        return True, None

    # Will also check body later in the handler
    return False, None  # Defer to body check


def _cors_headers():
    """Return CORS headers for cross-origin requests."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-KEY",
    }


async def handle_agui_post(request: Request) -> Response:
    """Handle POST requests to /agui endpoint.

    Supports both:
    - JSON-RPC style: {"method": "info"} or {"method": "agent/run", "params": {...}}
    - Flat AG-UI style: {"threadId": "...", "runId": "...", "messages": [...]}
    """
    # Check if AG-UI SDK is available
    if not is_available():
        return Response(
            content="AG-UI SDK not available. Install with: pip install ag-ui",
            status_code=503,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    # Parse request body
    try:
        body = await request.body()
        data = json.loads(body)
    except json.JSONDecodeError as e:
        return Response(
            content=f"Invalid JSON: {e}",
            status_code=400,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    # Validate auth (check body api_key if header auth failed)
    is_valid, error = validate_auth(request)
    if not is_valid:
        cfg = settings.get_settings()
        expected_token = cfg.get("agui_token") or cfg.get("mcp_server_token")
        # If no token configured, allow the request
        if not expected_token:
            _PRINTER.print("[AG-UI Auth] No token configured (body check), allowing request")
        else:
            body_api_key = data.get("api_key")
            if body_api_key != expected_token:
                return Response(
                    content=error or "Unauthorized",
                    status_code=401,
                    media_type="text/plain",
                    headers=_cors_headers(),
                )

    # Check if this is a JSON-RPC style request (CopilotKit format)
    if "method" in data:
        method = data.get("method")
        params = data.get("params", {})

        _PRINTER.print(f"[AG-UI] JSON-RPC request: method={method}")

        # Handle "info" method - return runtime info
        if method == "info":
            cfg = settings.get_settings()
            # CopilotKit expects agents as an object keyed by name, not an array
            return Response(
                content=json.dumps({
                    "agents": {
                        "default": {
                            "name": "default",
                            "description": "Agent Zero - A general-purpose AI assistant",
                        }
                    },
                    "extensions": {},
                }),
                status_code=200,
                media_type="application/json",
                headers=_cors_headers(),
            )

        # Handle "agent/connect" method - return connection acknowledgment
        elif method == "agent/connect":
            agent_name = params.get("agentName", params.get("agent_name", "default"))
            _PRINTER.print(f"[AG-UI] agent/connect for agent: {agent_name}")
            return Response(
                content=json.dumps({
                    "connected": True,
                    "agentName": agent_name,
                    "threadId": params.get("threadId", f"thread-{id(request)}"),
                }),
                status_code=200,
                media_type="application/json",
                headers=_cors_headers(),
            )

        # Handle "agent/run" or "run" method - run the agent
        elif method in ("agent/run", "run", "agent/execute"):
            # Extract params into flat format
            data = {
                "threadId": params.get("threadId", params.get("thread_id", f"thread-{id(request)}")),
                "runId": params.get("runId", params.get("run_id", f"run-{id(request)}")),
                "agentName": params.get("agentName", params.get("agent_name", "default")),
                "messages": params.get("messages", []),
                "tools": params.get("tools", []),
                "context": params.get("context", params.get("state", {})),
                "api_key": data.get("api_key"),
            }

        # Handle unknown method - log and return error
        else:
            _PRINTER.print(f"[AG-UI] Unknown method: {method}, params: {params}")
            return Response(
                content=json.dumps({"error": f"Unknown method: {method}"}),
                status_code=400,
                media_type="application/json",
                headers=_cors_headers(),
            )

    # Validate request payload (flat AG-UI format)
    try:
        input_data = validate_agui_request(data)
    except Exception as e:
        return Response(
            content=f"Invalid request: {e}",
            status_code=400,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    _PRINTER.print(
        f"[AG-UI] Request: thread={input_data.thread_id}, run={input_data.run_id}, agent={input_data.agent_name}"
    )

    # Get server and stream response
    server = AguiServer.get_instance()

    return StreamingResponse(
        server.run_agent(input_data),
        media_type=server.get_content_type(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            **_cors_headers(),
        },
    )


async def handle_agui_options(request: Request) -> Response:
    """Handle OPTIONS preflight requests for CORS."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-KEY",
            "Access-Control-Max-Age": "86400",
        },
    )


async def handle_agui_get(request: Request) -> Response:
    """Handle GET requests - return info about the AG-UI endpoint."""
    cfg = settings.get_settings()
    return Response(
        content=json.dumps({
            "protocol": "AG-UI",
            "version": "1.0.0",
            "available": is_available(),
            "enabled": cfg.get("agui_enabled", True),
            "description": "Agent Zero AG-UI streaming endpoint",
            "methods": ["POST"],
            "docs": "https://docs.ag-ui.com",
        }),
        status_code=200,
        media_type="application/json",
        headers=_cors_headers(),
    )


async def handle_agui_info(request: Request) -> Response:
    """Handle GET /info requests - CopilotKit runtime info endpoint."""
    cfg = settings.get_settings()
    # CopilotKit expects agents as an object keyed by name, not an array
    return Response(
        content=json.dumps({
            "agents": {
                "default": {
                    "name": "default",
                    "description": "Agent Zero - A general-purpose AI assistant",
                }
            },
            "extensions": {},
        }),
        status_code=200,
        media_type="application/json",
        headers=_cors_headers(),
    )


# =============================================================================
# A2UI Protocol Endpoints
# =============================================================================

async def handle_a2ui_action(request: Request) -> Response:
    """Handle A2UI userAction messages from clients.

    A2UI clients send userAction messages when users interact with
    components that have actions defined (e.g., button clicks, form
    submissions).

    Per A2UI specification:
    - https://a2ui.org/specification/v0.8-a2ui/
    - https://github.com/google/A2UI

    Request format:
    {
        "userAction": {
            "name": "action_name",
            "surfaceId": "surface_id",
            "sourceComponentId": "component_id",
            "timestamp": "2025-01-01T12:00:00Z",
            "context": {...}
        }
    }
    """
    # Validate auth
    is_valid, error = validate_auth(request)
    if not is_valid and error:
        return Response(
            content=error,
            status_code=401,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    # Parse request body
    try:
        body = await request.body()
        data = json.loads(body)
    except json.JSONDecodeError as e:
        return Response(
            content=f"Invalid JSON: {e}",
            status_code=400,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    # Validate A2UI userAction message format
    if "userAction" not in data:
        return Response(
            content="Invalid A2UI message: missing 'userAction' key",
            status_code=400,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    action_data = data["userAction"]

    # Validate required fields per A2UI spec
    required_fields = ["name", "surfaceId", "sourceComponentId", "timestamp", "context"]
    missing = [f for f in required_fields if f not in action_data]
    if missing:
        return Response(
            content=f"Invalid userAction: missing required fields: {missing}",
            status_code=400,
            media_type="text/plain",
            headers=_cors_headers(),
        )

    _PRINTER.print(
        f"[A2UI] userAction: {action_data['name']} "
        f"from {action_data['sourceComponentId']} on {action_data['surfaceId']}"
    )

    # Find the active run for this surface
    # Note: In a full implementation, we'd track surface -> run mapping
    # For now, we acknowledge the action and log it
    server = AguiServer.get_instance()

    # Try to find an active run and process the action
    action_processed = False
    for run_key, run_data in server._active_runs.items():
        # Check if this run owns the surface
        agent = None
        try:
            from agent import AgentContext
            context = AgentContext.get(run_data.context_id)
            if context:
                agent = context.agent0
        except Exception:
            pass

        if agent:
            surface_manager = agent.get_data("_a2ui_surface_manager")
            if surface_manager and surface_manager.exists(action_data["surfaceId"]):
                # Process the action through the agent's extension system
                try:
                    from python.helpers.extension import execute_extensions
                    import asyncio

                    result = await execute_extensions(
                        agent,
                        "a2ui_action",
                        action_name=action_data["name"],
                        surface_id=action_data["surfaceId"],
                        source_component_id=action_data["sourceComponentId"],
                        timestamp=action_data["timestamp"],
                        context=action_data["context"],
                    )
                    action_processed = True
                    break
                except Exception as e:
                    _PRINTER.print(f"[A2UI] Extension error: {e}")

    # Return acknowledgment
    return Response(
        content=json.dumps({
            "status": "received",
            "action": action_data["name"],
            "surfaceId": action_data["surfaceId"],
            "processed": action_processed,
        }),
        status_code=200,
        media_type="application/json",
        headers=_cors_headers(),
    )


async def handle_a2ui_info(request: Request) -> Response:
    """Return A2UI capability information.

    Provides details about A2UI protocol support for client discovery.
    """
    return Response(
        content=json.dumps({
            "protocol": "A2UI",
            "version": "0.8",
            "catalog": "https://a2ui.dev/specification/0.8/standard_catalog.json",
            "description": "Agent Zero A2UI protocol support",
            "docs": "https://a2ui.org",
            "capabilities": {
                "surfaceUpdate": True,
                "dataModelUpdate": True,
                "beginRendering": True,
                "deleteSurface": True,
                "userAction": True,
            },
        }),
        status_code=200,
        media_type="application/json",
        headers=_cors_headers(),
    )


def create_agui_app(lock=None) -> Starlette:
    """Create the AG-UI ASGI application.

    Args:
        lock: Optional threading lock for request serialization

    Returns:
        Starlette ASGI application
    """
    routes = [
        # Handle both "/" and "" (empty path) for root endpoints
        Route("/", endpoint=handle_agui_post, methods=["POST"]),
        Route("/", endpoint=handle_agui_options, methods=["OPTIONS"]),
        Route("/", endpoint=handle_agui_get, methods=["GET"]),
        # CopilotKit runtime info endpoint
        Route("/info", endpoint=handle_agui_info, methods=["GET"]),
        Route("/info", endpoint=handle_agui_options, methods=["OPTIONS"]),
        # A2UI protocol endpoints
        Route("/a2ui/action", endpoint=handle_a2ui_action, methods=["POST"]),
        Route("/a2ui/action", endpoint=handle_agui_options, methods=["OPTIONS"]),
        Route("/a2ui/info", endpoint=handle_a2ui_info, methods=["GET"]),
        Route("/a2ui/info", endpoint=handle_agui_options, methods=["OPTIONS"]),
    ]

    from starlette.routing import Router, Mount
    from starlette.middleware import Middleware
    from starlette.middleware.base import BaseHTTPMiddleware

    # Custom middleware to handle empty path (when /agui is called without trailing slash)
    class EmptyPathMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # If path is empty, treat it as "/"
            if request.scope.get("path") == "" or request.scope.get("path") is None:
                request.scope["path"] = "/"
            return await call_next(request)

    app = Starlette(
        routes=routes,
        middleware=[Middleware(EmptyPathMiddleware)]
    )
    return app
