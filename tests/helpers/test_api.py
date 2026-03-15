"""Tests for python/helpers/api.py — ApiHandler base class."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.api import ApiHandler


class ConcreteApiHandler(ApiHandler):
    async def process(self, input, request):
        return {"result": input.get("x", "default")}


class TestApiHandlerClassMethods:
    def test_requires_loopback_default_false(self):
        assert ApiHandler.requires_loopback() is False

    def test_requires_api_key_default_false(self):
        assert ApiHandler.requires_api_key() is False

    def test_requires_auth_default_true(self):
        assert ApiHandler.requires_auth() is True

    def test_get_methods_default_post(self):
        assert ApiHandler.get_methods() == ["POST"]

    def test_requires_csrf_defaults_to_requires_auth(self):
        assert ApiHandler.requires_csrf() == ApiHandler.requires_auth()


class TestApiHandlerHandleRequest:
    @pytest.fixture
    def handler(self):
        app = MagicMock()
        lock = MagicMock()
        return ConcreteApiHandler(app, lock)

    @pytest.mark.asyncio
    async def test_handle_request_json_input(self, handler):
        request = MagicMock()
        request.is_json = True
        request.data = b'{"x": "hello"}'
        request.get_json = MagicMock(return_value={"x": "hello"})
        response = await handler.handle_request(request)
        assert response.status_code == 200
        assert b"hello" in response.data

    @pytest.mark.asyncio
    async def test_handle_request_empty_json_uses_empty_dict(self, handler):
        request = MagicMock()
        request.is_json = True
        request.data = b""
        request.get_json = MagicMock(return_value=None)
        response = await handler.handle_request(request)
        assert response.status_code == 200
        assert b"default" in response.data

    @pytest.mark.asyncio
    async def test_handle_request_non_json_uses_empty_input(self, handler):
        request = MagicMock()
        request.is_json = False
        response = await handler.handle_request(request)
        assert response.status_code == 200
        assert b"default" in response.data

    @pytest.mark.asyncio
    async def test_handle_request_returns_json_error_on_exception(self, handler):
        class FailingHandler(ApiHandler):
            async def process(self, input, request):
                raise ValueError("test error")

        h = FailingHandler(MagicMock(), MagicMock())
        request = MagicMock()
        request.is_json = True
        request.data = b"{}"
        request.get_json = MagicMock(return_value={})
        response = await h.handle_request(request)
        assert response.status_code == 500
        assert b"test error" in response.data or b"ValueError" in response.data
