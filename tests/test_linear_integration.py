"""Unit tests for Linear integration with mocked GraphQL responses."""

import os
import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── LinearDatabase tests ────────────────────────────────────────────


class TestLinearDatabase:
    def setup_method(self):
        from instruments.custom.linear_integration.linear_db import LinearDatabase

        self.tmp = tempfile.mkdtemp()
        self.db = LinearDatabase(os.path.join(self.tmp, "test.db"))

    def _make_issue(self, **overrides):
        base = {
            "id": "issue-1",
            "identifier": "AJB-1",
            "title": "Test issue",
            "description": "Desc",
            "url": "https://linear.app/test/issue/AJB-1",
            "priority": 2,
            "state": {"id": "state-1", "name": "In Progress"},
            "project": {"id": "proj-1", "name": "Test Project"},
            "assignee": {"name": "Aaron"},
            "labels": {"nodes": [{"id": "lbl-1", "name": "Bug"}]},
            "createdAt": "2026-03-14T00:00:00Z",
            "updatedAt": "2026-03-14T00:00:00Z",
        }
        base.update(overrides)
        return base

    def test_upsert_and_get_issue(self):
        issue = self._make_issue()
        self.db.upsert_issue(issue)
        results = self.db.get_issues()
        assert len(results) == 1
        assert results[0]["identifier"] == "AJB-1"
        assert results[0]["state_name"] == "In Progress"

    def test_upsert_issues_batch(self):
        issues = [
            self._make_issue(id="i1", identifier="AJB-1"),
            self._make_issue(id="i2", identifier="AJB-2", title="Second"),
        ]
        count = self.db.upsert_issues(issues)
        assert count == 2
        assert len(self.db.get_issues()) == 2

    def test_search_issues_cached(self):
        self.db.upsert_issue(self._make_issue(title="Login bug fix"))
        self.db.upsert_issue(self._make_issue(id="i2", title="Dashboard update"))
        results = self.db.search_issues_cached("login")
        assert len(results) == 1
        assert "Login" in results[0]["title"]

    def test_filter_by_project(self):
        self.db.upsert_issue(self._make_issue(id="i1", project={"id": "p1", "name": "P1"}))
        self.db.upsert_issue(self._make_issue(id="i2", project={"id": "p2", "name": "P2"}))
        results = self.db.get_issues(project_id="p1")
        assert len(results) == 1

    def test_upsert_project(self):
        self.db.upsert_project({"id": "proj-1", "name": "Alpha", "state": "started", "slugId": "alpha"})
        projects = self.db.get_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "Alpha"

    def test_sync_log(self):
        sync_id = self.db.start_sync("full")
        self.db.complete_sync(sync_id, 42)
        last = self.db.get_last_sync("full")
        assert last is not None
        assert last["items_synced"] == 42
        assert last["status"] == "completed"

    def test_dashboard_data(self):
        self.db.upsert_issue(self._make_issue(id="i1", priority=1))
        self.db.upsert_issue(self._make_issue(id="i2", priority=2, state={"id": "s2", "name": "Done"}))
        self.db.upsert_project({"id": "p1", "name": "P1", "state": "started", "slugId": "p1"})

        data = self.db.get_dashboard_data()
        assert data["total_issues"] == 2
        assert data["projects_count"] == 1
        assert "In Progress" in data["issues_by_state"]


# ── LinearClient tests (mocked HTTP) ────────────────────────────────


class TestLinearClient:
    @pytest.fixture
    def client(self):
        from python.helpers.linear_client import LinearClient

        return LinearClient(api_key="test-key")  # pragma: allowlist secret

    @pytest.mark.asyncio
    async def test_create_issue(self, client):
        mock_response = {
            "data": {
                "issueCreate": {
                    "success": True,
                    "issue": {
                        "id": "new-1",
                        "identifier": "AJB-99",
                        "title": "New issue",
                        "url": "https://linear.app/test/issue/AJB-99",
                        "state": {"name": "Triage"},
                        "priority": 2,
                    },
                }
            }
        }

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_ctx)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_session_cls.return_value = mock_session

            result = await client.create_issue(title="New issue", team_id="team-1", priority=2)
            assert result["success"] is True
            assert result["issue"]["identifier"] == "AJB-99"

    @pytest.mark.asyncio
    async def test_search_issues(self, client):
        mock_response = {
            "data": {
                "issues": {
                    "nodes": [
                        {"id": "i1", "identifier": "AJB-1", "title": "Auth bug"},
                    ]
                }
            }
        }

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_resp = AsyncMock()
            mock_resp.status = 200
            mock_resp.json = AsyncMock(return_value=mock_response)

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)

            mock_session = AsyncMock()
            mock_session.post = MagicMock(return_value=mock_ctx)
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_session_cls.return_value = mock_session

            results = await client.search_issues("auth")
            assert len(results) == 1
            assert results[0]["identifier"] == "AJB-1"

    def test_missing_api_key_raises(self):
        from python.helpers.linear_client import LinearClient

        with patch.dict(os.environ, {}, clear=True):
            # Remove LINEAR_API_KEY if set
            os.environ.pop("LINEAR_API_KEY", None)
            with pytest.raises(ValueError, match="Linear API key required"):
                LinearClient(api_key="")


# ── LinearManager tests ─────────────────────────────────────────────


class TestLinearManager:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        from instruments.custom.linear_integration.linear_manager import LinearManager

        self.manager = LinearManager(os.path.join(self.tmp, "test.db"), api_key="test-key")

    def test_get_dashboard_empty(self):
        data = self.manager.get_dashboard()
        assert data["total_issues"] == 0
        assert data["projects_count"] == 0

    @pytest.mark.asyncio
    async def test_create_issue_caches(self):
        mock_result = {
            "success": True,
            "issue": {
                "id": "new-1",
                "identifier": "AJB-1",
                "title": "Test",
                "url": "",
                "state": {"name": "Triage"},
                "priority": 0,
            },
        }

        with patch.object(self.manager, "_get_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.create_issue = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_client

            result = await self.manager.create_issue(title="Test", team_id="t1")
            assert result["success"] is True

            # Verify it was cached
            cached = self.manager.db.get_issues()
            assert len(cached) == 1
            assert cached[0]["identifier"] == "AJB-1"
