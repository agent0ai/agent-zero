"""Unit tests for Motion integration with mocked API responses."""

import os
import sys
import tempfile
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMotionDatabase:
    def setup_method(self):
        from instruments.custom.motion_integration.motion_db import MotionDatabase

        self.tmp = tempfile.mkdtemp()
        self.db = MotionDatabase(os.path.join(self.tmp, "test.db"))

    def test_upsert_and_get_task(self):
        task = {
            "id": "task-1",
            "name": "Review PR",
            "description": "Check code",
            "priority": "HIGH",
            "status": "active",
            "duration": 60,
            "workspaceId": "ws-1",
        }
        self.db.upsert_task(task)
        results = self.db.get_tasks()
        assert len(results) == 1
        assert results[0]["name"] == "Review PR"

    def test_mapping_linear_to_motion(self):
        self.db.add_mapping("motion-1", "linear-1", "AJB-42")
        assert self.db.get_motion_id_for_linear("linear-1") == "motion-1"
        assert self.db.get_motion_id_for_linear("nonexistent") is None

    def test_mapping_idempotent(self):
        self.db.add_mapping("motion-1", "linear-1", "AJB-42")
        self.db.add_mapping("motion-1", "linear-1", "AJB-42")
        mappings = self.db.get_all_mappings()
        assert len(mappings) == 1

    def test_sync_log(self):
        sync_id = self.db.start_sync("linear_sync")
        self.db.complete_sync(sync_id, 5)
        last = self.db.get_last_sync("linear_sync")
        assert last["items_synced"] == 5
        assert last["status"] == "completed"

    def test_sync_log_error(self):
        sync_id = self.db.start_sync("linear_sync")
        self.db.complete_sync(sync_id, 0, error="Rate limited")
        last = self.db.get_last_sync()
        assert last["status"] == "error"
        assert "Rate limited" in last["error"]


class TestMotionClient:
    def test_missing_api_key_raises(self):
        from python.helpers.motion_client import MotionClient

        os.environ.pop("MOTION_API_KEY", None)
        with pytest.raises(ValueError, match="Motion API key required"):
            MotionClient(api_key="")


class TestMotionManager:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        from instruments.custom.motion_integration.motion_manager import MotionManager

        self.manager = MotionManager(os.path.join(self.tmp, "test.db"), api_key="test-key")

    @pytest.mark.asyncio
    async def test_create_task_caches(self):
        mock_result = {
            "id": "mt-1",
            "name": "Test task",
            "priority": "HIGH",
            "status": "active",
        }
        with patch.object(self.manager, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.create_task = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_client

            result = await self.manager.create_task(name="Test task", workspace_id="ws-1", priority="HIGH")
            assert result["id"] == "mt-1"

            cached = self.manager.db.get_tasks()
            assert len(cached) == 1

    @pytest.mark.asyncio
    async def test_sync_from_linear_creates_tasks(self):
        linear_issues = {
            "issues": {
                "nodes": [
                    {
                        "id": "li-1",
                        "identifier": "AJB-1",
                        "title": "Urgent fix",
                        "description": "Fix it",
                        "priority": 1,
                        "state": {"name": "In Progress"},
                        "labels": {"nodes": []},
                    }
                ]
            }
        }
        motion_task = {"id": "mt-1", "name": "[AJB-1] Urgent fix", "priority": "ASAP"}

        with patch("python.helpers.linear_client.LinearClient") as MockLinear:
            mock_linear = AsyncMock()
            mock_linear.execute = AsyncMock(return_value=linear_issues)
            MockLinear.return_value = mock_linear

            with patch.object(self.manager, "_get_client") as mock_get:
                mock_motion = AsyncMock()
                mock_motion.create_task = AsyncMock(return_value=motion_task)
                mock_get.return_value = mock_motion

                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await self.manager.sync_from_linear(
                        workspace_id="ws-1",
                        linear_api_key="test-linear-key",  # pragma: allowlist secret
                    )

                    assert result["success"] is True
                    assert result["created"] == 1
                    assert self.manager.db.get_motion_id_for_linear("li-1") == "mt-1"
