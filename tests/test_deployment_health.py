import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from python.helpers.deployment_health import check_http_endpoint


@pytest.mark.asyncio
async def test_health_check_success():
    """Test successful HTTP health check"""
    with (
        patch("python.helpers.deployment_health.aiohttp.ClientSession") as mock_session_cls,
        patch("python.helpers.deployment_health.aiohttp.TCPConnector"),
    ):
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get()
        mock_get = MagicMock(return_value=mock_response)

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession() constructor
        mock_session_cls.return_value = mock_session

        success, details = await check_http_endpoint("http://example.com/health")

        assert success is True
        assert details["status_code"] == 200
        assert "response_time_ms" in details


@pytest.mark.asyncio
async def test_health_check_wrong_status():
    """Test health check with unexpected status code"""
    with (
        patch("python.helpers.deployment_health.aiohttp.ClientSession") as mock_session_cls,
        patch("python.helpers.deployment_health.aiohttp.TCPConnector"),
    ):
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get()
        mock_get = MagicMock(return_value=mock_response)

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession() constructor
        mock_session_cls.return_value = mock_session

        success, details = await check_http_endpoint("http://example.com/health")

        assert success is False
        assert details["status_code"] == 500


@pytest.mark.asyncio
async def test_health_check_timeout():
    """Test health check timeout handling"""
    with (
        patch("python.helpers.deployment_health.aiohttp.ClientSession") as mock_session_cls,
        patch("python.helpers.deployment_health.aiohttp.TCPConnector"),
    ):
        # Mock session.get() to raise asyncio.TimeoutError
        mock_get = MagicMock(side_effect=asyncio.TimeoutError())

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession() constructor
        mock_session_cls.return_value = mock_session

        success, details = await check_http_endpoint("http://example.com/health", timeout=5)

        assert success is False
        assert "timeout" in details["error"].lower()


@pytest.mark.asyncio
async def test_health_check_connection_error():
    """Test health check connection error handling"""
    with (
        patch("python.helpers.deployment_health.aiohttp.ClientSession") as mock_session_cls,
        patch("python.helpers.deployment_health.aiohttp.TCPConnector"),
    ):
        # Mock session.get() to raise ClientError
        mock_get = MagicMock(side_effect=aiohttp.ClientError("Connection refused"))

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession() constructor
        mock_session_cls.return_value = mock_session

        success, details = await check_http_endpoint("http://example.com/health")

        assert success is False
        assert "error" in details


@pytest.mark.asyncio
async def test_health_check_custom_status():
    """Test health check with custom expected status"""
    with (
        patch("python.helpers.deployment_health.aiohttp.ClientSession") as mock_session_cls,
        patch("python.helpers.deployment_health.aiohttp.TCPConnector"),
    ):
        # Mock response
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session.get()
        mock_get = MagicMock(return_value=mock_response)

        # Mock session instance
        mock_session = MagicMock()
        mock_session.get = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        # Mock ClientSession() constructor
        mock_session_cls.return_value = mock_session

        success, details = await check_http_endpoint("http://example.com/health", expected_status=204)

        assert success is True
        assert details["status_code"] == 204
