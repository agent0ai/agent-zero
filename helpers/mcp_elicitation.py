import asyncio
import threading
import uuid
from typing import Any, Optional

from mcp.shared.context import RequestContext
from mcp.client.session import ClientSession
import mcp.types as types

from helpers.print_style import PrintStyle


class _PendingElicitation:
    """Tracks a single in-flight elicitation request awaiting a frontend response."""

    def __init__(
        self,
        request_id: str,
        message: str,
        requested_schema: dict[str, Any],
        server_name: str,
        loop: asyncio.AbstractEventLoop,
    ):
        self.request_id = request_id
        self.message = message
        self.requested_schema = requested_schema
        self.server_name = server_name
        self.loop = loop
        self.event = asyncio.Event()
        self.result: Optional[types.ElicitResult] = None


class ElicitationManager:
    """Singleton that bridges MCP elicitation callbacks with the WebSocket frontend.

    Flow:
    1. MCP SDK invokes the elicitation callback during a tool call session.
    2. The callback registers a _PendingElicitation and broadcasts the request
       to the frontend via WebSocket.
    3. The callback awaits the asyncio.Event until the frontend responds.
    4. The WS extension receives the frontend response, resolves the pending
       elicitation, and sets the Event.
    5. The callback returns the ElicitResult to the MCP SDK.
    """

    _instance: Optional["ElicitationManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._pending: dict[str, _PendingElicitation] = {}
        self._pending_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ElicitationManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def create_elicitation_callback(self, server_name: str):
        """Create an elicitation callback bound to a specific MCP server name."""

        async def elicitation_callback(
            context: RequestContext[ClientSession, Any],
            params: types.ElicitRequestParams,
        ) -> types.ElicitResult | types.ErrorData:
            request_id = str(uuid.uuid4())

            loop = asyncio.get_running_loop()
            pending = _PendingElicitation(
                request_id=request_id,
                message=params.message,
                requested_schema=params.requestedSchema,
                server_name=server_name,
                loop=loop,
            )

            with self._pending_lock:
                self._pending[request_id] = pending

            PrintStyle(font_color="cyan", padding=True).print(
                f"MCP Elicitation: Server '{server_name}' requests input: {params.message}"
            )

            self._log_to_contexts(
                request_id=request_id,
                heading=f"icon://input MCP Server '{server_name}' requests input",
                content=params.message,
                kvps={
                    "server_name": server_name,
                    "request_id": request_id,
                    "status": "pending",
                },
            )

            try:
                await self._broadcast_elicitation_request(pending)

                # Wait for the frontend to respond (timeout after 5 minutes)
                try:
                    await asyncio.wait_for(pending.event.wait(), timeout=300)
                except asyncio.TimeoutError:
                    PrintStyle(font_color="orange", padding=True).print(
                        f"MCP Elicitation: Request '{request_id}' timed out after 5 minutes"
                    )
                    return types.ElicitResult(
                        action="cancel",
                        content=None,
                    )

                if pending.result is not None:
                    return pending.result

                return types.ElicitResult(action="cancel", content=None)
            finally:
                with self._pending_lock:
                    self._pending.pop(request_id, None)

        return elicitation_callback

    def resolve(
        self,
        request_id: str,
        action: str,
        content: dict[str, Any] | None = None,
    ) -> bool:
        """Resolve a pending elicitation with the frontend's response.

        Returns True if the request was found and resolved, False otherwise.
        """
        with self._pending_lock:
            pending = self._pending.get(request_id)

        if pending is None:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Elicitation: No pending request found for id '{request_id}'"
            )
            return False

        if action not in ("accept", "decline", "cancel"):
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Elicitation: Invalid action '{action}' for request '{request_id}'"
            )
            return False

        pending.result = types.ElicitResult(
            action=action,
            content=content if action == "accept" else None,
        )
        # Signal the event on its originating loop for thread-safety.
        pending.loop.call_soon_threadsafe(pending.event.set)

        PrintStyle(font_color="green", padding=True).print(
            f"MCP Elicitation: Request '{request_id}' resolved with action='{action}'"
        )

        self._log_to_contexts(
            request_id=request_id,
            heading=f"icon://input MCP Elicitation '{pending.server_name}': {action}",
            content=f"User responded with: {action}",
            kvps={
                "server_name": pending.server_name,
                "request_id": request_id,
                "action": action,
                "status": "resolved",
            },
        )

        return True

    def get_pending(self, request_id: str) -> Optional[_PendingElicitation]:
        """Get a pending elicitation by request_id."""
        with self._pending_lock:
            return self._pending.get(request_id)

    def get_all_pending(self) -> list[dict[str, Any]]:
        """Get all pending elicitation requests as serializable dicts."""
        with self._pending_lock:
            return [
                {
                    "request_id": p.request_id,
                    "message": p.message,
                    "requested_schema": p.requested_schema,
                    "server_name": p.server_name,
                }
                for p in self._pending.values()
            ]

    @staticmethod
    def _log_to_contexts(
        request_id: str,
        heading: str,
        content: str,
        kvps: dict[str, Any],
    ):
        """Log an elicitation event to all active agent contexts."""
        try:
            from agent import AgentContext
            AgentContext.log_to_all(
                type="mcp_elicitation",
                heading=heading,
                content=content,
                kvps=kvps,
                id=request_id,
            )
        except Exception as e:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Elicitation: Failed to log to contexts: {e}"
            )

    async def _broadcast_elicitation_request(self, pending: _PendingElicitation):
        """Broadcast an elicitation request to all connected WebSocket clients."""
        from helpers.ws_manager import get_shared_ws_manager
        from helpers.ws import NAMESPACE

        payload = {
            "request_id": pending.request_id,
            "message": pending.message,
            "requested_schema": pending.requested_schema,
            "server_name": pending.server_name,
        }

        try:
            manager = get_shared_ws_manager()
            await manager.broadcast(
                NAMESPACE,
                "mcp_elicitation_request",
                payload,
                handler_id="helpers.mcp_elicitation.ElicitationManager",
            )
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Elicitation: Failed to broadcast request: {e}"
            )
