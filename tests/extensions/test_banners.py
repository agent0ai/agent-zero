"""Tests for banner extensions: unsecured connection, missing API key, system resources."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestUnsecuredConnectionCheck:
    """Tests for _10_unsecured_connection.py."""

    @pytest.mark.asyncio
    async def test_adds_banner_for_non_local_without_credentials(self, mock_agent):
        banners = []
        frontend_context = {"hostname": "example.com", "protocol": "http:"}

        with patch(
            "python.extensions.banners._10_unsecured_connection.dotenv.get_dotenv_value",
            side_effect=lambda k, d: "",
        ):
            from python.extensions.banners._10_unsecured_connection import (
                UnsecuredConnectionCheck,
            )

            ext = UnsecuredConnectionCheck(agent=mock_agent)
            await ext.execute(banners=banners, frontend_context=frontend_context)

        assert len(banners) == 1
        assert banners[0]["id"] == "unsecured-connection"
        assert "Configure credentials" in banners[0]["html"]

    @pytest.mark.asyncio
    async def test_no_banner_for_localhost(self, mock_agent):
        banners = []
        frontend_context = {"hostname": "localhost", "protocol": "http:"}

        with patch(
            "python.extensions.banners._10_unsecured_connection.dotenv.get_dotenv_value",
            side_effect=lambda k, d: "",
        ):
            from python.extensions.banners._10_unsecured_connection import (
                UnsecuredConnectionCheck,
            )

            ext = UnsecuredConnectionCheck(agent=mock_agent)
            await ext.execute(banners=banners, frontend_context=frontend_context)

        assert len(banners) == 0

    @pytest.mark.asyncio
    async def test_adds_credentials_unencrypted_for_http_with_auth(self, mock_agent):
        banners = []
        frontend_context = {"hostname": "example.com", "protocol": "http:"}

        with patch(
            "python.extensions.banners._10_unsecured_connection.dotenv.get_dotenv_value",
            side_effect=lambda k, d: "user" if "LOGIN" in str(k) else "pass",
        ):
            from python.extensions.banners._10_unsecured_connection import (
                UnsecuredConnectionCheck,
            )

            ext = UnsecuredConnectionCheck(agent=mock_agent)
            await ext.execute(banners=banners, frontend_context=frontend_context)

        assert any(b["id"] == "credentials-unencrypted" for b in banners)


class TestMissingApiKeyCheck:
    """Tests for _20_missing_api_key.py."""

    @pytest.mark.asyncio
    async def test_no_banner_when_keys_configured(self, mock_agent):
        banners = []

        with patch(
            "python.extensions.banners._20_missing_api_key.settings_helper.get_settings",
            return_value={"chat_model_provider": "ollama"},
        ), patch(
            "python.extensions.banners._20_missing_api_key.models.get_api_key",
            return_value="key",
        ):
            from python.extensions.banners._20_missing_api_key import MissingApiKeyCheck

            ext = MissingApiKeyCheck(agent=mock_agent)
            await ext.execute(banners=banners)

        assert len(banners) == 0

    @pytest.mark.asyncio
    async def test_adds_banner_when_api_key_missing(self, mock_agent):
        banners = []

        with patch(
            "python.extensions.banners._20_missing_api_key.settings_helper.get_settings",
            return_value={"chat_model_provider": "openai"},
        ), patch(
            "python.extensions.banners._20_missing_api_key.models.get_api_key",
            return_value=None,
        ):
            from python.extensions.banners._20_missing_api_key import MissingApiKeyCheck

            ext = MissingApiKeyCheck(agent=mock_agent)
            await ext.execute(banners=banners)

        assert len(banners) == 1
        assert banners[0]["id"] == "missing-api-key"
        assert "API key" in banners[0]["title"]


class TestSystemResourcesCheck:
    """Tests for _30_system_resources.py."""

    @pytest.mark.asyncio
    async def test_adds_system_resources_banner(self, mock_agent):
        banners = []
        vm_mock = MagicMock()
        vm_mock.percent = 50.0
        vm_mock.total = 16 * 1024**3
        vm_mock.available = 8 * 1024**3

        with patch(
            "python.extensions.banners._30_system_resources.psutil.cpu_percent",
            return_value=25.0,
        ), patch(
            "python.extensions.banners._30_system_resources.psutil.cpu_count",
            return_value=8,
        ), patch(
            "python.extensions.banners._30_system_resources.psutil.virtual_memory",
            return_value=vm_mock,
        ), patch(
            "python.extensions.banners._30_system_resources.psutil.disk_usage",
            return_value=MagicMock(percent=40.0, used=50 * 1024**3, total=100 * 1024**3),
        ), patch(
            "python.extensions.banners._30_system_resources.psutil.net_io_counters",
            return_value=MagicMock(bytes_sent=1000, bytes_recv=2000),
        ), patch(
            "python.extensions.banners._30_system_resources.os.getloadavg",
            return_value=(1.0, 0.8, 0.6),
        ):
            from python.extensions.banners._30_system_resources import (
                SystemResourcesCheck,
            )

            ext = SystemResourcesCheck(agent=mock_agent)
            await ext.execute(banners=banners)

        assert len(banners) == 1
        assert banners[0]["id"] == "system-resources"
        assert "CPU" in banners[0]["html"]
