"""Tests for python/api/banners.py — GetBanners API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.banners import GetBanners


def _make_handler(app=None, lock=None):
    return GetBanners(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetBanners:
    def test_get_methods_returns_post(self):
        assert GetBanners.get_methods() == ["POST"]

    @pytest.mark.asyncio
    async def test_process_returns_banners_from_extensions(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        banners = []

        with patch(
            "python.api.banners.call_extensions",
            new_callable=AsyncMock,
        ) as mock_call:
            result = await handler.process(
                {"banners": banners, "context": {}}, MagicMock()
            )

        mock_call.assert_called_once_with(
            "banners", agent=None, banners=banners, frontend_context={}
        )
        assert result["banners"] is banners

    @pytest.mark.asyncio
    async def test_process_extensions_can_append_to_banners(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        banners = []

        def append_banner(*args, **kwargs):
            kwargs["banners"].append({"id": "b1", "title": "Welcome"})

        with patch(
            "python.api.banners.call_extensions",
            new_callable=AsyncMock,
            side_effect=append_banner,
        ):
            result = await handler.process(
                {"banners": banners, "context": {"key": "val"}}, MagicMock()
            )

        assert len(result["banners"]) == 1
        assert result["banners"][0]["title"] == "Welcome"
