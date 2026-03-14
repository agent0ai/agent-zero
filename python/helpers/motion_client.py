"""
Async REST client for the Motion API (api.usemotion.com/v1).

Rate limited: Motion caps at 30 req/min. Uses asyncio.sleep(2) between calls.
"""

import os
from typing import Any

import aiohttp

MOTION_API_URL = "https://api.usemotion.com/v1"


class MotionClient:
    """Thin async wrapper around Motion's REST API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MOTION_API_KEY", "")
        if not self.api_key:
            raise ValueError("Motion API key required. Set motion_api_key in settings or MOTION_API_KEY env var.")

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{MOTION_API_URL}{path}"

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=params, headers=headers) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise MotionAPIError(f"HTTP {resp.status}: {data}")
                return data

    # ── Task operations ──────────────────────────────────────────────

    async def create_task(
        self,
        name: str,
        workspace_id: str,
        description: str = "",
        priority: str = "MEDIUM",
        duration: int = 30,
        deadline: str | None = None,
        project_id: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new Motion task."""
        payload: dict[str, Any] = {
            "name": name,
            "workspaceId": workspace_id,
            "description": description,
            "priority": priority,
            "duration": duration,
        }
        if deadline:
            payload["dueDate"] = deadline
        if project_id:
            payload["projectId"] = project_id
        if labels:
            payload["labels"] = labels

        return await self._request("POST", "/tasks", json_data=payload)

    async def update_task(
        self,
        task_id: str,
        name: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing Motion task."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if priority is not None:
            payload["priority"] = priority
        if status is not None:
            payload["status"] = status

        return await self._request("PATCH", f"/tasks/{task_id}", json_data=payload)

    async def list_tasks(
        self,
        workspace_id: str,
        project_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """List tasks in a workspace."""
        params: dict[str, Any] = {"workspaceId": workspace_id}
        if project_id:
            params["projectId"] = project_id
        if status:
            params["status"] = status

        result = await self._request("GET", "/tasks", params=params)
        return result.get("tasks", [])

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Get a single task by ID."""
        return await self._request("GET", f"/tasks/{task_id}")

    async def delete_task(self, task_id: str) -> dict[str, Any]:
        """Delete a task."""
        return await self._request("DELETE", f"/tasks/{task_id}")

    # ── Schedule ─────────────────────────────────────────────────────

    async def get_schedule(self, workspace_id: str) -> list[dict[str, Any]]:
        """Get scheduled tasks/time blocks."""
        result = await self._request("GET", "/tasks", params={"workspaceId": workspace_id})
        return result.get("tasks", [])

    # ── Workspaces ───────────────────────────────────────────────────

    async def list_workspaces(self) -> list[dict[str, Any]]:
        """List available workspaces."""
        result = await self._request("GET", "/workspaces")
        return result.get("workspaces", [])


class MotionAPIError(Exception):
    """Raised when Motion API returns an error."""
