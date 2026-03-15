"""Tests for python/api/csrf_token.py — GetCsrfToken API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.csrf_token import GetCsrfToken


def _make_handler(app=None, lock=None):
    return GetCsrfToken(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetCsrfToken:
    def test_get_methods_returns_get(self):
        assert GetCsrfToken.get_methods() == ["GET"]

    def test_requires_csrf_returns_false(self):
        assert GetCsrfToken.requires_csrf() is False

    @pytest.mark.asyncio
    async def test_process_returns_ok_with_token_when_origin_allowed(self):
        handler = _make_handler()
        mock_session = {}
        with patch.object(handler, "check_allowed_origin", new_callable=AsyncMock, return_value={"ok": True}), \
             patch("python.api.csrf_token.session", mock_session):
            result = await handler.process({}, MagicMock())
        assert result["ok"] is True
        assert "token" in result
        assert "runtime_id" in result

    @pytest.mark.asyncio
    async def test_process_reuses_existing_session_token(self):
        handler = _make_handler()
        mock_session = {"csrf_token": "existing-token"}
        with patch.object(handler, "check_allowed_origin", new_callable=AsyncMock, return_value={"ok": True}), \
             patch("python.api.csrf_token.session", mock_session):
            with patch("python.api.csrf_token.runtime.get_runtime_id", return_value="rt-1"):
                result = await handler.process({}, MagicMock())
        assert result["ok"] is True
        assert result["token"] == "existing-token"

    @pytest.mark.asyncio
    async def test_process_returns_error_when_origin_not_allowed(self):
        handler = _make_handler()
        with patch.object(handler, "check_allowed_origin", new_callable=AsyncMock, return_value={
            "ok": False, "allowed_origins": ["*://localhost"]
        }), patch.object(handler, "get_origin_from_request", return_value="https://evil.com"):
            result = await handler.process({}, MagicMock())
        assert result["ok"] is False
        assert "not allowed" in result["error"]
        assert "evil.com" in result["error"]


class TestCheckAllowedOrigin:
    @pytest.mark.asyncio
    async def test_returns_ok_when_login_required(self):
        handler = _make_handler()
        with patch("python.api.csrf_token.login.is_login_required", return_value=True):
            result = await handler.check_allowed_origin(MagicMock())
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_checks_origin_when_login_not_required(self):
        handler = _make_handler()
        with patch("python.api.csrf_token.login.is_login_required", return_value=False), \
             patch.object(handler, "initialize_allowed_origins"), \
             patch.object(handler, "is_allowed_origin", new_callable=AsyncMock, return_value={"ok": True, "origin": "", "allowed_origins": ""}):
            result = await handler.check_allowed_origin(MagicMock())
        assert result["ok"] is True


class TestGetOriginFromRequest:
    def test_returns_origin_from_headers(self):
        handler = _make_handler()
        request = MagicMock()
        request.headers = {"Origin": "https://example.com:8080"}
        request.environ = {}
        request.referrer = None
        result = handler.get_origin_from_request(request)
        assert result == "https://example.com:8080"

    def test_returns_none_when_no_origin(self):
        handler = _make_handler()
        request = MagicMock()
        request.headers = {}
        request.environ = {}
        request.referrer = None
        result = handler.get_origin_from_request(request)
        assert result is None

    def test_uses_referer_when_origin_missing(self):
        handler = _make_handler()
        request = MagicMock()
        request.headers = {}
        request.environ = {"HTTP_REFERER": "https://app.example.com/page"}
        request.referrer = None
        result = handler.get_origin_from_request(request)
        assert result == "https://app.example.com"


class TestGetDefaultAllowedOrigins:
    def test_includes_localhost_and_127(self):
        handler = _make_handler()
        origins = handler.get_default_allowed_origins()
        assert "*://localhost" in origins
        assert "*://127.0.0.1" in origins
