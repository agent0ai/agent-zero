"""Agent Zero HTTP API Client.

Wraps Agent Zero's REST endpoints with proper error handling
and type-safe responses. Uses the /api_* endpoints (API key auth).

Available API-key endpoints:
  /api_message        - Send message (auto-creates context)
  /api_log_get        - Get log items for a context
  /api_files_get      - Get files from context
  /api_reset_chat     - Reset chat history
  /api_terminate_chat - Terminate a context
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from pydantic import BaseModel


class Attachment(BaseModel):
    filename: str
    base64: str


class MessageResponse(BaseModel):
    context_id: str
    response: str


class LogItem(BaseModel):
    no: int
    id: Optional[str] = None
    type: str
    heading: str = ""
    content: str = ""
    kvps: dict[str, Any] = {}
    timestamp: float = 0.0
    agentno: int = 0


class LogResponse(BaseModel):
    """Response from /api_log_get."""

    context_id: str
    log: LogData


class LogData(BaseModel):
    guid: str = ""
    total_items: int = 0
    returned_items: int = 0
    start_position: int = 0
    progress: str | int = 0
    progress_active: bool = False
    items: list[dict[str, Any]] = []


class AgentZeroClient:
    """HTTP client for Agent Zero API (API-key authenticated endpoints only)."""

    def __init__(
        self,
        base_url: str = "http://localhost:55080", # change from 8080
        api_key: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    async def send_message(
        self,
        message: str,
        *,
        context_id: str = "",
        attachments: list[Attachment] | None = None,
        project_name: str | None = None,
        agent_profile: str | None = None,
    ) -> MessageResponse:
        """Send a message via /api_message.

        Auto-creates a new context if context_id is empty.
        Blocks until the agent has finished responding.
        """
        payload: dict[str, Any] = {
            "message": message,
            "context_id": context_id,
            "attachments": [a.model_dump() for a in (attachments or [])],
        }
        if project_name:
            payload["project_name"] = project_name
        if agent_profile:
            payload["agent_profile"] = agent_profile

        response = await self._client.post("/api_message", json=payload)
        response.raise_for_status()
        return MessageResponse.model_validate(response.json())

    async def get_logs(
        self,
        context_id: str,
        length: int = 100,
    ) -> LogResponse:
        """Get log items for a context via /api_log_get."""
        response = await self._client.post(
            "/api_log_get",
            json={"context_id": context_id, "length": length},
        )
        response.raise_for_status()
        return LogResponse.model_validate(response.json())

    async def get_files(
        self,
        context_id: str,
        filenames: list[str],
    ) -> dict[str, str]:
        """Retrieve files from context via /api_files_get."""
        response = await self._client.post(
            "/api_files_get",
            json={"context_id": context_id, "filenames": filenames},
        )
        response.raise_for_status()
        return response.json().get("files", {})

    async def reset_chat(self, context_id: str) -> bool:
        """Reset chat history via /api_reset_chat."""
        response = await self._client.post(
            "/api_reset_chat",
            json={"context_id": context_id},
        )
        return response.is_success

    async def terminate_chat(self, context_id: str) -> bool:
        """Terminate a context via /api_terminate_chat."""
        response = await self._client.post(
            "/api_terminate_chat",
            json={"context_id": context_id},
        )
        return response.is_success

    async def health(self) -> bool:
        """Check if Agent Zero is running."""
        try:
            response = await self._client.get("/")
            return response.is_success
        except httpx.ConnectError:
            return False

    async def close(self) -> None:
        await self._client.aclose()
