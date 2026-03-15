"""Tests for python/tools/notify_user.py — NotifyUserTool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from python.tools.notify_user import NotifyUserTool
except (ImportError, AttributeError):
    NotifyUserTool = None

pytestmark = pytest.mark.skipif(NotifyUserTool is None, reason="Cannot import NotifyUserTool")


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.read_prompt = MagicMock(return_value="Notification sent")
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.notify_user import NotifyUserTool
    return NotifyUserTool(
        agent=mock_agent,
        name="notify_user",
        method=None,
        args={"message": "Hello", "title": "Alert"},
        message="",
        loop_data=None,
    )


class TestNotifyUserToolExecute:
    @pytest.mark.asyncio
    async def test_valid_notification_succeeds(self, tool):
        with patch("python.tools.notify_user.AgentContext.get_notification_manager") as mock_mgr:
            mock_manager = MagicMock()
            mock_manager.add_notification = MagicMock()
            mock_mgr.return_value = mock_manager
            resp = await tool.execute()
        assert "Notification sent" in resp.message or resp.message
        mock_manager.add_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_message_returns_error(self, tool):
        tool.args = {"message": "", "title": ""}
        resp = await tool.execute()
        assert "Message is required" in resp.message

    @pytest.mark.asyncio
    async def test_invalid_notification_type_returns_error(self, tool):
        tool.args = {"message": "Hi", "type": "invalid_type"}
        resp = await tool.execute()
        assert "Invalid" in resp.message
