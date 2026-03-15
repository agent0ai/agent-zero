"""Tests for python/api/api_message.py — ApiMessage API handler."""

import base64
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.api_message import ApiMessage


def _make_handler(app=None, lock=None):
    return ApiMessage(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiMessage:
    @pytest.mark.asyncio
    async def test_empty_message_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({"message": ""}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400
        assert b"Message is required" in result.data

    @pytest.mark.asyncio
    async def test_missing_message_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({"context_id": "ctx-1"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400

    @pytest.mark.asyncio
    async def test_existing_context_processes_message(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"
        mock_ctx.log = MagicMock()
        mock_ctx.communicate = MagicMock(return_value=MagicMock(result=AsyncMock(return_value="Hello!")))

        with patch("python.api.api_message.AgentContext") as MockCtx:
            MockCtx.use.return_value = mock_ctx
            with patch.object(handler, "_chat_lifetimes", {}):
                with patch.object(handler, "_cleanup_lock"):
                    result = await handler.process({
                        "context_id": "ctx-123",
                        "message": "Hi",
                    }, MagicMock())

        assert result["context_id"] == "ctx-123"
        assert result["response"] == "Hello!"

    @pytest.mark.asyncio
    async def test_context_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.api_message.AgentContext") as MockCtx:
            MockCtx.use.return_value = None
            result = await handler.process({
                "context_id": "nonexistent",
                "message": "Hi",
            }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Context not found" in result.data

    @pytest.mark.asyncio
    async def test_agent_profile_mismatch_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.agent0 = MagicMock()
        mock_ctx.agent0.config.profile = "existing-profile"

        with patch("python.api.api_message.AgentContext") as MockCtx:
            MockCtx.use.return_value = mock_ctx
            result = await handler.process({
                "context_id": "ctx-1",
                "message": "Hi",
                "agent_profile": "different-profile",
            }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400
        assert b"Cannot override agent profile" in result.data

    @pytest.mark.asyncio
    async def test_project_mismatch_on_existing_context_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.agent0 = MagicMock()
        mock_ctx.get_data = MagicMock(return_value="existing-project")

        with patch("python.api.api_message.AgentContext") as MockCtx, \
             patch("python.api.api_message.projects") as mock_projects:
            MockCtx.use.return_value = mock_ctx
            mock_projects.CONTEXT_DATA_KEY_PROJECT = "project"
            result = await handler.process({
                "context_id": "ctx-1",
                "message": "Hi",
                "project_name": "different-project",
            }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400
        assert b"Project can only be set on first message" in result.data

    @pytest.mark.asyncio
    async def test_skips_invalid_attachments(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.log = MagicMock()
        mock_ctx.communicate = MagicMock(return_value=MagicMock(result=AsyncMock(return_value="ok")))

        with patch("python.api.api_message.AgentContext") as MockCtx, \
             patch.object(handler, "_chat_lifetimes", {}), \
             patch.object(handler, "_cleanup_lock", MagicMock()):
            MockCtx.use.return_value = mock_ctx
            # Invalid attachment (missing filename) - should be skipped
            result = await handler.process({
                "context_id": "ctx-1",
                "message": "Hi",
                "attachments": [{"base64": "abc"}],  # no filename
            }, MagicMock())

        assert result["response"] == "ok"

    @pytest.mark.asyncio
    async def test_communicate_exception_returns_500(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.log = MagicMock()
        mock_task = MagicMock()
        mock_task.result = AsyncMock(side_effect=Exception("LLM error"))
        mock_ctx.communicate = MagicMock(return_value=mock_task)

        with patch("python.api.api_message.AgentContext") as MockCtx:
            MockCtx.use.return_value = mock_ctx
            with patch.object(handler, "_chat_lifetimes", {}):
                with patch.object(handler, "_cleanup_lock"):
                    result = await handler.process({
                        "context_id": "ctx-1",
                        "message": "Hi",
                    }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 500
        assert b"LLM error" in result.data

    def test_requires_api_key_true(self):
        assert ApiMessage.requires_api_key() is True

    def test_requires_auth_false(self):
        assert ApiMessage.requires_auth() is False
