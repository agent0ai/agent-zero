"""ACP Server Implementation.

Implements Agent Client Protocol over stdio, translating between
ACP JSON-RPC messages and Agent Zero's HTTP API (polling-based).

Protocol: JSON-RPC 2.0 over stdio (newline-delimited).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from typing import Any

from a0.client.api import AgentZeroClient, LogItem
from a0.client.poller import Poller, PollEvent

logger = logging.getLogger(__name__)

# Log types that map to tool-like ACP updates
TOOL_TYPES = {"tool", "code_exe", "browser", "mcp"}

# Log types treated as agent thinking/progress
THINKING_TYPES = {"agent", "progress", "info", "hint", "util", "warning", "subagent"}


@dataclass
class ACPSession:
    """Tracks an active ACP session."""

    session_id: str
    context_id: str
    cwd: str
    mcp_servers: list[dict[str, Any]] = field(default_factory=list)
    poll_task: asyncio.Task[None] | None = None
    _tool_counter: int = 0

    def next_tool_id(self) -> str:
        self._tool_counter += 1
        return f"call_{self._tool_counter:04d}"


class ACPServer:
    """ACP Protocol Server bridging ACP clients to Agent Zero via stdio."""

    PROTOCOL_VERSION = 1

    def __init__(
        self,
        agent_url: str = "http://localhost:55080", # change from 8080
        api_key: str | None = None,
    ) -> None:
        self.agent_url = agent_url
        self.api_key = api_key
        self.client = AgentZeroClient(agent_url, api_key)
        self.poller = Poller(self.client, interval=0.3)

        self._sessions: dict[str, ACPSession] = {}
        self._initialized = False
        self._client_caps: dict[str, Any] = {}

        # Track pending prompt requests so we can respond when agent finishes
        self._pending_prompts: dict[str, int] = {}  # session_id -> request_id

    async def run(self) -> None:
        """Main server loop — read from stdin, write to stdout."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break

            try:
                message = json.loads(line.decode().strip())
                await self._handle_message(message)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON: %s", e)
            except Exception:
                logger.exception("Error handling message")

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Route incoming JSON-RPC message to handler."""
        method = message.get("method")
        msg_id = message.get("id")
        params = message.get("params", {})

        handlers: dict[str, Any] = {
            "initialize": self._handle_initialize,
            "session/new": self._handle_session_new,
            "session/load": self._handle_session_load,
            "session/prompt": self._handle_session_prompt,
            "session/cancel": self._handle_session_cancel,
        }

        handler = handlers.get(method)  # type: ignore[arg-type]
        if handler:
            try:
                result = await handler(params)
                if msg_id is not None:
                    await self._send_response(msg_id, result)
            except Exception as e:
                if msg_id is not None:
                    await self._send_error(msg_id, -32603, str(e))
        else:
            if msg_id is not None:
                await self._send_error(msg_id, -32601, f"Unknown method: {method}")

    # ── ACP Method Handlers ──────────────────────────────────────────

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle ACP initialize request."""
        client_version = params.get("protocolVersion", 1)
        self._client_caps = params.get("clientCapabilities", {})
        self._initialized = True

        return {
            "protocolVersion": min(self.PROTOCOL_VERSION, client_version),
            "agentCapabilities": {
                "loadSession": False,
                "promptCapabilities": {
                    "image": True,
                    "audio": False,
                    "embeddedContext": True,
                },
                "mcpCapabilities": {
                    "http": False,
                    "sse": False,
                },
            },
            "agentInfo": {
                "name": "agent-zero",
                "title": "Agent Zero",
                "version": "1.0.0",
            },
            "authMethods": [],
        }

    async def _handle_session_new(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a new Agent Zero session.

        We don't call /chat_create here because it requires CSRF/session auth.
        Instead we defer context creation to the first prompt — /api_message
        auto-creates a context when context_id is empty.
        """
        import uuid

        cwd = params.get("cwd", ".")
        mcp_servers = params.get("mcpServers", [])

        # Generate a local session ID; the real Agent Zero context_id
        # will be assigned on the first prompt via /api_message.
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = ACPSession(
            session_id=session_id,
            context_id="",  # filled on first prompt
            cwd=cwd,
            mcp_servers=mcp_servers,
        )
        self._sessions[session_id] = session

        return {"sessionId": session_id}

    async def _handle_session_load(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Load existing session."""
        session_id = params.get("sessionId", "")
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        return None

    async def _handle_session_prompt(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle user prompt — send to Agent Zero and poll for response."""
        session_id = params.get("sessionId", "")
        prompt_content = params.get("prompt", [])

        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Unknown session: {session_id}")

        # Convert ACP ContentBlocks to Agent Zero format
        message_text, attachments = self._convert_prompt(prompt_content)

        # Convert attachment dicts to Attachment models
        from a0.client.api import Attachment

        attachment_models = [
            Attachment(filename=a["filename"], base64=a["base64"])
            for a in attachments
        ] if attachments else None

        # Send message (this blocks until agent responds)
        response = await self.client.send_message(
            message=message_text,
            context_id=session.context_id,
            attachments=attachment_models,
        )

        # Update context_id in case it was auto-created
        session.context_id = response.context_id

        # Emit the response as agent_message_chunk
        await self._send_notification(
            "session/update",
            {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"type": "text", "text": response.response},
                },
            },
        )

        return {"stopReason": "end_turn"}

    async def _handle_session_cancel(self, params: dict[str, Any]) -> None:
        """Handle cancellation (notification, no response)."""
        session_id = params.get("sessionId", "")
        session = self._sessions.get(session_id)
        if session:
            await self.client.reset_chat(session.context_id)

    # ── Helpers ───────────────────────────────────────────────────────

    def _convert_prompt(
        self, content_blocks: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, str]]]:
        """Convert ACP ContentBlocks to Agent Zero message + attachments."""
        text_parts: list[str] = []
        attachments: list[dict[str, str]] = []

        for block in content_blocks:
            block_type = block.get("type")

            if block_type == "text":
                text_parts.append(block.get("text", ""))

            elif block_type == "resource":
                resource = block.get("resource", {})
                if "text" in resource:
                    uri = resource.get("uri", "file")
                    text_parts.append(f"\n--- {uri} ---\n{resource['text']}\n---\n")
                elif "blob" in resource:
                    attachments.append(
                        {
                            "filename": resource.get("uri", "attachment").split("/")[-1],
                            "base64": resource["blob"],
                        }
                    )

            elif block_type == "image":
                attachments.append(
                    {
                        "filename": "image.png",
                        "base64": block.get("data", ""),
                    }
                )

        return "\n".join(text_parts), attachments

    # ── JSON-RPC Transport ────────────────────────────────────────────

    async def _send_response(self, msg_id: int, result: Any) -> None:
        """Send JSON-RPC response."""
        await self._write({"jsonrpc": "2.0", "id": msg_id, "result": result})

    async def _send_error(self, msg_id: int, code: int, message: str) -> None:
        """Send JSON-RPC error."""
        await self._write(
            {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
        )

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send JSON-RPC notification (no id)."""
        await self._write({"jsonrpc": "2.0", "method": method, "params": params})

    async def _write(self, message: dict[str, Any]) -> None:
        """Write JSON-RPC message to stdout."""
        line = json.dumps(message, separators=(",", ":")) + "\n"
        sys.stdout.write(line)
        sys.stdout.flush()
