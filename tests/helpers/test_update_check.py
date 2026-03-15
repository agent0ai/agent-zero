"""Tests for python/helpers/update_check.py — check_version (mocked httpx)."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestCheckVersion:
    @pytest.mark.asyncio
    async def test_returns_version_from_api(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"latest": "v1.0.0", "url": "https://example.com"}
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("python.helpers.update_check.git") as mg, \
             patch("python.helpers.update_check.runtime") as mr:
            mg.get_version.return_value = "v0.9.0"
            mr.get_persistent_id.return_value = "test-id"

            from python.helpers.update_check import check_version
            result = await check_version()

        assert result["latest"] == "v1.0.0"
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_sends_current_version_and_anonymized_id(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_client), \
             patch("python.helpers.update_check.git") as mg, \
             patch("python.helpers.update_check.runtime") as mr:
            mg.get_version.return_value = "v0.9.8"
            mr.get_persistent_id.return_value = "abc123"

            from python.helpers.update_check import check_version
            await check_version()

        call_kw = mock_client.post.call_args[1]
        assert call_kw["json"]["current_version"] == "v0.9.8"
        assert "anonymized_id" in call_kw["json"]
