"""
Async REST client for the Notion API (api.notion.com/v1).

Uses aiohttp (already installed) — no new dependencies.
"""

import os
from typing import Any

import aiohttp

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionClient:
    """Thin async wrapper around Notion's REST API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY", "")
        if not self.api_key:
            raise ValueError("Notion API key required. Set notion_api_key in settings or NOTION_API_KEY env var.")

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }
        url = f"{NOTION_API_URL}{path}"

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=params, headers=headers) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise NotionAPIError(f"HTTP {resp.status}: {data}")
                return data

    # ── Page operations ──────────────────────────────────────────────

    async def create_page(
        self,
        parent_database_id: str,
        title: str,
        properties: dict[str, Any] | None = None,
        content_blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new page in a database."""
        payload: dict[str, Any] = {
            "parent": {"database_id": parent_database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                **(properties or {}),
            },
        }
        if content_blocks:
            payload["children"] = content_blocks

        return await self._request("POST", "/pages", json_data=payload)

    async def update_page(
        self,
        page_id: str,
        properties: dict[str, Any] | None = None,
        archived: bool | None = None,
    ) -> dict[str, Any]:
        """Update page properties."""
        payload: dict[str, Any] = {}
        if properties:
            payload["properties"] = properties
        if archived is not None:
            payload["archived"] = archived

        return await self._request("PATCH", f"/pages/{page_id}", json_data=payload)

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """Get a page by ID."""
        return await self._request("GET", f"/pages/{page_id}")

    # ── Database operations ──────────────────────────────────────────

    async def query_database(
        self,
        database_id: str,
        filter_obj: dict[str, Any] | None = None,
        sorts: list[dict[str, Any]] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """Query a Notion database with optional filter and sort."""
        payload: dict[str, Any] = {"page_size": page_size}
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts

        result = await self._request("POST", f"/databases/{database_id}/query", json_data=payload)
        return result.get("results", [])

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Get database metadata."""
        return await self._request("GET", f"/databases/{database_id}")

    # ── Block operations ─────────────────────────────────────────────

    async def append_blocks(
        self,
        page_id: str,
        blocks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Append content blocks to a page."""
        return await self._request(
            "PATCH",
            f"/blocks/{page_id}/children",
            json_data={"children": blocks},
        )

    # ── Search ───────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        filter_type: str | None = None,
        page_size: int = 25,
    ) -> list[dict[str, Any]]:
        """Search across all pages and databases."""
        payload: dict[str, Any] = {"query": query, "page_size": page_size}
        if filter_type:
            payload["filter"] = {"value": filter_type, "property": "object"}

        result = await self._request("POST", "/search", json_data=payload)
        return result.get("results", [])


class NotionAPIError(Exception):
    """Raised when Notion API returns an error."""
