"""Tests for python/api/health.py — HealthCheck API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.health import HealthCheck


def _make_handler(app=None, lock=None):
    return HealthCheck(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestHealthCheck:
    def test_requires_auth_returns_false(self):
        assert HealthCheck.requires_auth() is False

    def test_requires_csrf_returns_false(self):
        assert HealthCheck.requires_csrf() is False

    def test_get_methods_returns_get_and_post(self):
        assert HealthCheck.get_methods() == ["GET", "POST"]

    @pytest.mark.asyncio
    async def test_process_returns_gitinfo_on_success(self):
        handler = _make_handler()
        mock_gitinfo = {"branch": "main", "commit": "abc123"}
        with patch("python.api.health.git.get_git_info", return_value=mock_gitinfo):
            result = await handler.process({}, MagicMock())
        assert result["gitinfo"] == mock_gitinfo
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_process_returns_error_when_git_fails(self):
        handler = _make_handler()
        with patch("python.api.health.git.get_git_info", side_effect=Exception("git not found")), \
             patch("python.api.health.errors.error_text", return_value="git not found"):
            result = await handler.process({}, MagicMock())
        assert result["gitinfo"] is None
        assert result["error"] == "git not found"
