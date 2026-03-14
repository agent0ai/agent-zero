"""Unit tests for Notion integration with mocked API responses."""

import os
import sys
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNotionDatabase:
    def setup_method(self):
        from instruments.custom.notion_integration.notion_db import NotionDatabase

        self.tmp = tempfile.mkdtemp()
        self.db = NotionDatabase(os.path.join(self.tmp, "test.db"))

    def test_upsert_and_get_page(self):
        page = {
            "id": "page-1",
            "properties": {
                "Name": {"title": [{"text": {"content": "Test Page"}}]},
            },
            "url": "https://notion.so/test-page",
            "parent": {"database_id": "db-1"},
            "created_time": "2026-03-14T00:00:00Z",
            "last_edited_time": "2026-03-14T00:00:00Z",
        }
        self.db.upsert_page(page)
        results = self.db.get_pages()
        assert len(results) == 1
        assert results[0]["title"] == "Test Page"

    def test_filter_by_database(self):
        self.db.upsert_page(
            {
                "id": "p1",
                "properties": {},
                "parent": {"database_id": "db-1"},
                "created_time": "",
                "last_edited_time": "",
                "_title": "Page 1",
            }
        )
        self.db.upsert_page(
            {
                "id": "p2",
                "properties": {},
                "parent": {"database_id": "db-2"},
                "created_time": "",
                "last_edited_time": "",
                "_title": "Page 2",
            }
        )
        results = self.db.get_pages(database_id="db-1")
        assert len(results) == 1

    def test_linear_mapping(self):
        self.db.add_linear_mapping("notion-1", "linear-1", "AJB-42", "spec")
        assert self.db.get_notion_id_for_linear("linear-1", "spec") == "notion-1"
        assert self.db.get_notion_id_for_linear("nonexistent") is None

    def test_crm_mapping(self):
        self.db.add_crm_mapping("notion-1", 1, "John Smith")
        assert self.db.get_notion_id_for_customer(1) == "notion-1"
        assert self.db.get_notion_id_for_customer(999) is None

    def test_sync_log(self):
        sync_id = self.db.start_sync("spec_sync")
        self.db.complete_sync(sync_id, 3)
        last = self.db.get_last_sync("spec_sync")
        assert last["items_synced"] == 3
        assert last["status"] == "completed"


class TestNotionClient:
    def test_missing_api_key_raises(self):
        from python.helpers.notion_client import NotionClient

        os.environ.pop("NOTION_API_KEY", None)
        with pytest.raises(ValueError, match="Notion API key required"):
            NotionClient(api_key="")


class TestNotionManager:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        from instruments.custom.notion_integration.notion_manager import NotionManager

        self.manager = NotionManager(os.path.join(self.tmp, "test.db"), api_key="test-key")

    @pytest.mark.asyncio
    async def test_create_page_caches(self):
        mock_result = {
            "id": "page-1",
            "url": "https://notion.so/test",
            "properties": {"Name": {"title": [{"text": {"content": "Test"}}]}},
            "parent": {"database_id": "db-1"},
            "created_time": "2026-03-14",
            "last_edited_time": "2026-03-14",
        }

        with patch.object(self.manager, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.create_page = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_client

            result = await self.manager.create_page(database_id="db-1", title="Test")
            assert result["id"] == "page-1"
            assert len(self.manager.db.get_pages()) == 1

    @pytest.mark.asyncio
    async def test_sync_specs_creates_pages(self):
        linear_issues = {
            "issues": {
                "nodes": [
                    {
                        "id": "li-1",
                        "identifier": "AJB-1",
                        "title": "Auth Spec",
                        "description": "Auth specification",
                        "labels": {"nodes": [{"name": "Spec"}]},
                        "project": {"name": "Auth"},
                        "state": {"name": "In Progress"},
                    }
                ]
            }
        }
        notion_page = {
            "id": "np-1",
            "url": "https://notion.so/np-1",
            "properties": {},
            "parent": {"database_id": "db-1"},
            "created_time": "2026-03-14",
            "last_edited_time": "2026-03-14",
        }

        with patch("python.helpers.linear_client.LinearClient") as MockLinear:
            mock_linear = AsyncMock()
            mock_linear.execute = AsyncMock(return_value=linear_issues)
            MockLinear.return_value = mock_linear

            with patch.object(self.manager, "_get_client") as mock_get:
                mock_notion = AsyncMock()
                mock_notion.create_page = AsyncMock(return_value=notion_page)
                mock_get.return_value = mock_notion

                result = await self.manager.sync_specs(
                    notion_database_id="db-1",
                    linear_api_key="test-key",  # pragma: allowlist secret
                )

                assert result["success"] is True
                assert result["created"] == 1
                assert self.manager.db.get_notion_id_for_linear("li-1", "spec") == "np-1"

    @pytest.mark.asyncio
    async def test_sync_specs_idempotent(self):
        """Second sync should skip already-mapped issues."""
        self.manager.db.add_linear_mapping("np-1", "li-1", "AJB-1", "spec")

        linear_issues = {"issues": {"nodes": [{"id": "li-1", "identifier": "AJB-1", "title": "Already synced"}]}}

        with patch("python.helpers.linear_client.LinearClient") as MockLinear:
            mock_linear = AsyncMock()
            mock_linear.execute = AsyncMock(return_value=linear_issues)
            MockLinear.return_value = mock_linear

            with patch.object(self.manager, "_get_client"):
                result = await self.manager.sync_specs(
                    notion_database_id="db-1",
                    linear_api_key="test-key",  # pragma: allowlist secret
                )
                assert result["created"] == 0
                assert result["skipped"] == 1
