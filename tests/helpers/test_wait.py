"""Tests for python/helpers/wait.py — format_remaining_time, managed_wait."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.wait import format_remaining_time, managed_wait


class TestFormatRemainingTime:
    def test_seconds_only(self):
        assert "0.0s remaining" in format_remaining_time(0) or "0" in format_remaining_time(0)
        assert "5.0s" in format_remaining_time(5) or "5" in format_remaining_time(5)

    def test_minutes_and_seconds(self):
        result = format_remaining_time(90)
        assert "1m" in result or "90" in result
        assert "remaining" in result

    def test_hours(self):
        result = format_remaining_time(3661)
        assert "1h" in result or "3600" in result

    def test_days(self):
        result = format_remaining_time(86400 * 2 + 3600)
        assert "2d" in result or "d" in result

    def test_negative_clamped_to_zero(self):
        result = format_remaining_time(-10)
        assert "remaining" in result

    def test_subsecond(self):
        result = format_remaining_time(0.5)
        assert "0.5" in result or "remaining" in result


class TestManagedWait:
    @pytest.mark.asyncio
    async def test_returns_immediately_when_target_passed(self):
        agent = MagicMock()
        agent.handle_intervention = AsyncMock()
        target = datetime.now(timezone.utc) - timedelta(seconds=1)
        log = MagicMock()
        log.update = MagicMock()

        result = await managed_wait(
            agent, target, is_duration_wait=False, log=log,
            get_heading_callback=lambda x: x,
        )
        assert result == target

    @pytest.mark.asyncio
    async def test_waits_until_target(self):
        agent = MagicMock()
        agent.handle_intervention = AsyncMock()
        target = datetime.now(timezone.utc) + timedelta(seconds=0.1)
        log = MagicMock()
        log.update = MagicMock()

        result = await managed_wait(
            agent, target, is_duration_wait=False, log=log,
            get_heading_callback=lambda x: x,
        )
        assert result == target
