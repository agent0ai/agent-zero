"""Tests for python/helpers/state_monitor_integration.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- mark_dirty_all ---


class TestMarkDirtyAll:
    def test_mark_dirty_all_delegates_to_state_monitor(self):
        from python.helpers.state_monitor_integration import mark_dirty_all

        with patch("python.helpers.state_monitor_integration.get_state_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mark_dirty_all(reason="test_reason")
            mock_monitor.mark_dirty_all.assert_called_once_with(reason="test_reason")

    def test_mark_dirty_all_can_be_called_without_reason(self):
        from python.helpers.state_monitor_integration import mark_dirty_all

        with patch("python.helpers.state_monitor_integration.get_state_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mark_dirty_all()
            mock_monitor.mark_dirty_all.assert_called_once_with(reason=None)


# --- mark_dirty_for_context ---


class TestMarkDirtyForContext:
    def test_mark_dirty_for_context_delegates_to_state_monitor(self):
        from python.helpers.state_monitor_integration import mark_dirty_for_context

        with patch("python.helpers.state_monitor_integration.get_state_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mark_dirty_for_context("ctx-123", reason="notification")
            mock_monitor.mark_dirty_for_context.assert_called_once_with(
                "ctx-123",
                reason="notification",
            )

    def test_mark_dirty_for_context_can_be_called_without_reason(self):
        from python.helpers.state_monitor_integration import mark_dirty_for_context

        with patch("python.helpers.state_monitor_integration.get_state_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mark_dirty_for_context("ctx-1")
            mock_monitor.mark_dirty_for_context.assert_called_once_with(
                "ctx-1",
                reason=None,
            )
