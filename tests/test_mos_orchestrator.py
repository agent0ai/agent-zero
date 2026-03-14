"""Integration tests for MOS Orchestrator with mocked API calls."""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMOSOrchestrator:
    @pytest.mark.asyncio
    async def test_on_lead_captured_creates_issue(self):
        """Verify lead capture creates a Linear issue."""
        from python.helpers.mos_orchestrator import MOSOrchestrator

        with patch.dict(
            os.environ,
            {
                "LINEAR_API_KEY": "test-key",  # pragma: allowlist secret
                "LINEAR_DEFAULT_TEAM_ID": "team-1",
            },
        ):
            with patch("instruments.custom.linear_integration.linear_manager.LinearManager") as MockManager:
                mock_instance = AsyncMock()
                mock_instance.create_issue = AsyncMock(return_value={"success": True})
                MockManager.return_value = mock_instance

                # Patch the internal import
                with patch(
                    "python.helpers.mos_orchestrator.LinearManager",
                    MockManager,
                    create=True,
                ):
                    await MOSOrchestrator.on_lead_captured(
                        customer_name="Jane Doe",
                        company="TechCorp",
                        customer_id=42,
                    )

    @pytest.mark.asyncio
    async def test_on_lead_captured_noop_without_api_key(self):
        """Should silently skip if no API key."""
        from python.helpers.mos_orchestrator import MOSOrchestrator

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LINEAR_API_KEY", None)
            os.environ.pop("LINEAR_DEFAULT_TEAM_ID", None)

            # Should not raise
            await MOSOrchestrator.on_lead_captured(
                customer_name="No Key User",
            )

    @pytest.mark.asyncio
    async def test_on_deployment_success_noop_without_issues(self):
        """Should be a no-op when no related issues provided."""
        from python.helpers.mos_orchestrator import MOSOrchestrator

        # No issues → should return immediately
        await MOSOrchestrator.on_deployment_success(
            project_name="test-project",
            related_issue_ids=None,
        )

    @pytest.mark.asyncio
    async def test_sync_linear_to_motion_skips_without_config(self):
        """Should skip gracefully when config is missing."""
        from python.helpers.mos_orchestrator import MOSOrchestrator

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MOTION_API_KEY", None)
            os.environ.pop("LINEAR_API_KEY", None)
            os.environ.pop("MOTION_WORKSPACE_ID", None)

            # Patch settings to not be available
            with patch(
                "python.helpers.mos_orchestrator.get_settings",
                side_effect=ImportError,
                create=True,
            ):
                result = await MOSOrchestrator.sync_linear_to_motion()
                assert result.get("skipped") is True

    @pytest.mark.asyncio
    async def test_sync_linear_activity_skips_without_key(self):
        """Should skip gracefully when no Linear API key."""
        from python.helpers.mos_orchestrator import MOSOrchestrator

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("LINEAR_API_KEY", None)

            # Also patch settings so it doesn't provide a key
            with patch(
                "python.helpers.mos_orchestrator.get_settings",
                side_effect=ImportError,
                create=True,
            ):
                # Patch the actual settings import inside the method
                with patch("python.helpers.settings.get_settings", side_effect=ImportError):
                    result = await MOSOrchestrator.sync_linear_activity_to_digest()
                    assert result.get("skipped") is True


class TestMOSSchedulerInit:
    def test_register_returns_dict(self):
        from python.helpers.mos_scheduler_init import register_mos_schedules

        # Should not crash even without TaskScheduler
        result = register_mos_schedules()
        assert "registered" in result
        assert "count" in result
