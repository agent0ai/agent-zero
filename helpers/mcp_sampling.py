import asyncio
import threading
import uuid
from typing import Any, Optional

from mcp.shared.context import RequestContext
from mcp.client.session import ClientSession
import mcp.types as types

from helpers.print_style import PrintStyle


class _PendingSampling:
    """Tracks a single in-flight sampling request awaiting user approval."""

    def __init__(
        self,
        request_id: str,
        server_name: str,
        messages: list[dict[str, Any]],
        system_prompt: str | None,
        max_tokens: int,
        temperature: float | None,
        model_preferences: dict[str, Any] | None,
        stop_sequences: list[str] | None,
        metadata: dict[str, Any] | None,
        include_context: str | None,
        loop: asyncio.AbstractEventLoop,
    ):
        self.request_id = request_id
        self.server_name = server_name
        self.messages = messages
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model_preferences = model_preferences
        self.stop_sequences = stop_sequences
        self.metadata = metadata
        self.include_context = include_context
        self.loop = loop
        self.event = asyncio.Event()
        # Set by resolve(): "approve", "reject", or "cancel"
        self.action: str | None = None


class SamplingManager:
    """Singleton that bridges MCP sampling callbacks with the WebSocket frontend.

    Flow:
    1. MCP SDK invokes the sampling callback during a tool call session.
    2. The callback registers a _PendingSampling and broadcasts the request
       to the frontend via WebSocket for human-in-the-loop approval.
    3. The callback awaits the asyncio.Event until the user responds.
    4. On approval, the manager calls LiteLLM with the provided messages
       using the configured utility model.
    5. The callback returns the CreateMessageResult to the MCP SDK.
    """

    _instance: Optional["SamplingManager"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._pending: dict[str, _PendingSampling] = {}
        self._pending_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "SamplingManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def create_sampling_callback(self, server_name: str):
        """Create a sampling callback bound to a specific MCP server name."""

        async def sampling_callback(
            context: RequestContext[ClientSession, Any],
            params: types.CreateMessageRequestParams,
        ) -> types.CreateMessageResult | types.ErrorData:
            request_id = str(uuid.uuid4())

            # Serialize SamplingMessage list to plain dicts for WS transport
            messages = []
            for msg in params.messages:
                m: dict[str, Any] = {"role": msg.role}
                if isinstance(msg.content, types.TextContent):
                    m["content"] = msg.content.text
                    m["content_type"] = "text"
                elif isinstance(msg.content, types.ImageContent):
                    m["content"] = msg.content.data
                    m["content_type"] = "image"
                    m["mime_type"] = msg.content.mimeType
                elif isinstance(msg.content, types.AudioContent):
                    m["content"] = msg.content.data
                    m["content_type"] = "audio"
                    m["mime_type"] = msg.content.mimeType
                else:
                    m["content"] = str(msg.content)
                    m["content_type"] = "unknown"
                messages.append(m)

            model_prefs = None
            if params.modelPreferences:
                model_prefs = params.modelPreferences.model_dump(exclude_none=True)

            loop = asyncio.get_running_loop()
            pending = _PendingSampling(
                request_id=request_id,
                server_name=server_name,
                messages=messages,
                system_prompt=params.systemPrompt,
                max_tokens=params.maxTokens,
                temperature=params.temperature,
                model_preferences=model_prefs,
                stop_sequences=params.stopSequences,
                metadata=params.metadata,
                include_context=params.includeContext,
                loop=loop,
            )

            with self._pending_lock:
                self._pending[request_id] = pending

            PrintStyle(font_color="cyan", padding=True).print(
                f"MCP Sampling: Server '{server_name}' requests LLM sampling "
                f"({len(messages)} messages, max_tokens={params.maxTokens})"
            )

            self._log_to_contexts(
                request_id=request_id,
                heading=f"icon://smart_toy MCP Server '{server_name}' requests LLM sampling",
                content=f"{len(messages)} message(s), max_tokens={params.maxTokens}",
                kvps={
                    "server_name": server_name,
                    "request_id": request_id,
                    "status": "pending_approval",
                    "max_tokens": params.maxTokens,
                    "message_count": len(messages),
                },
            )

            try:
                await self._broadcast_sampling_request(pending)

                # Wait for the user to approve/reject (timeout after 5 minutes)
                try:
                    await asyncio.wait_for(pending.event.wait(), timeout=300)
                except asyncio.TimeoutError:
                    PrintStyle(font_color="orange", padding=True).print(
                        f"MCP Sampling: Request '{request_id}' timed out after 5 minutes"
                    )
                    return types.ErrorData(
                        code=types.INVALID_REQUEST,
                        message="Sampling request timed out waiting for user approval",
                    )

                if pending.action == "approve":
                    return await self._execute_sampling(pending)
                elif pending.action == "reject":
                    return types.ErrorData(
                        code=types.INVALID_REQUEST,
                        message="User rejected the sampling request",
                    )
                else:
                    return types.ErrorData(
                        code=types.INVALID_REQUEST,
                        message="Sampling request was cancelled",
                    )
            finally:
                with self._pending_lock:
                    self._pending.pop(request_id, None)

        return sampling_callback

    def resolve(self, request_id: str, action: str) -> bool:
        """Resolve a pending sampling request with the user's decision.

        Returns True if the request was found and resolved, False otherwise.
        """
        with self._pending_lock:
            pending = self._pending.get(request_id)

        if pending is None:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Sampling: No pending request found for id '{request_id}'"
            )
            return False

        if action not in ("approve", "reject", "cancel"):
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Sampling: Invalid action '{action}' for request '{request_id}'"
            )
            return False

        pending.action = action
        # Signal the event on its originating loop for thread-safety.
        pending.loop.call_soon_threadsafe(pending.event.set)

        PrintStyle(font_color="green", padding=True).print(
            f"MCP Sampling: Request '{request_id}' resolved with action='{action}'"
        )

        self._log_to_contexts(
            request_id=request_id,
            heading=f"icon://smart_toy MCP Sampling '{pending.server_name}': {action}",
            content=f"User responded with: {action}",
            kvps={
                "server_name": pending.server_name,
                "request_id": request_id,
                "action": action,
                "status": "resolved",
            },
        )

        return True

    def get_all_pending(self) -> list[dict[str, Any]]:
        """Get all pending sampling requests as serializable dicts."""
        with self._pending_lock:
            return [
                {
                    "request_id": p.request_id,
                    "server_name": p.server_name,
                    "messages": p.messages,
                    "system_prompt": p.system_prompt,
                    "max_tokens": p.max_tokens,
                    "temperature": p.temperature,
                    "model_preferences": p.model_preferences,
                    "stop_sequences": p.stop_sequences,
                    "include_context": p.include_context,
                }
                for p in self._pending.values()
            ]

    async def _execute_sampling(
        self, pending: _PendingSampling
    ) -> types.CreateMessageResult | types.ErrorData:
        """Call the utility model with the sampling request messages."""
        try:
            from plugins._model_config.helpers.model_config import build_utility_model

            model = build_utility_model()
            model_name = model.model_name

            # Build the user message from the sampling messages
            user_parts = []
            for msg in pending.messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    user_parts.append(content)
                else:
                    user_parts.append(f"[{role}]: {content}")
            user_message = "\n\n".join(user_parts)

            call_kwargs: dict[str, Any] = {}
            if pending.max_tokens:
                call_kwargs["max_tokens"] = pending.max_tokens
            if pending.temperature is not None:
                call_kwargs["temperature"] = pending.temperature
            if pending.stop_sequences:
                call_kwargs["stop"] = pending.stop_sequences

            PrintStyle(font_color="cyan", padding=True).print(
                f"MCP Sampling: Calling utility model '{model_name}' "
                f"with {len(pending.messages)} messages"
            )

            response_text, _reasoning = await model.unified_call(
                system_message=pending.system_prompt or "",
                user_message=user_message,
                **call_kwargs,
            )

            PrintStyle(font_color="green", padding=True).print(
                f"MCP Sampling: LLM response received ({len(response_text)} chars)"
            )

            self._log_to_contexts(
                request_id=pending.request_id,
                heading=f"icon://smart_toy MCP Sampling '{pending.server_name}': completed",
                content=response_text[:200] + ("..." if len(response_text) > 200 else ""),
                kvps={
                    "server_name": pending.server_name,
                    "request_id": pending.request_id,
                    "model": model_name,
                    "status": "completed",
                },
            )

            return types.CreateMessageResult(
                role="assistant",
                content=types.TextContent(type="text", text=response_text),
                model=model_name,
                stopReason="endTurn",
            )
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Sampling: LLM call failed: {e}"
            )
            return types.ErrorData(
                code=types.INTERNAL_ERROR,
                message=f"LLM call failed: {e}",
            )

    @staticmethod
    def _log_to_contexts(
        request_id: str,
        heading: str,
        content: str,
        kvps: dict[str, Any],
    ):
        """Log a sampling event to all active agent contexts."""
        try:
            from agent import AgentContext
            AgentContext.log_to_all(
                type="mcp_sampling",
                heading=heading,
                content=content,
                kvps=kvps,
                id=request_id,
            )
        except Exception as e:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Sampling: Failed to log to contexts: {e}"
            )

    async def _broadcast_sampling_request(self, pending: _PendingSampling):
        """Broadcast a sampling request to all connected WebSocket clients."""
        from helpers.ws_manager import get_shared_ws_manager
        from helpers.ws import NAMESPACE

        payload = {
            "request_id": pending.request_id,
            "server_name": pending.server_name,
            "messages": pending.messages,
            "system_prompt": pending.system_prompt,
            "max_tokens": pending.max_tokens,
            "temperature": pending.temperature,
            "model_preferences": pending.model_preferences,
            "stop_sequences": pending.stop_sequences,
            "include_context": pending.include_context,
        }

        try:
            manager = get_shared_ws_manager()
            await manager.broadcast(
                NAMESPACE,
                "mcp_sampling_request",
                payload,
                handler_id="helpers.mcp_sampling.SamplingManager",
            )
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Sampling: Failed to broadcast request: {e}"
            )
