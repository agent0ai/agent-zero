"""Tests for python/helpers/rfc_exchange.py."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- get_root_password ---


@pytest.mark.asyncio
class TestGetRootPassword:
    async def test_get_root_password_dockerized_uses_dotenv(self):
        from python.helpers.rfc_exchange import get_root_password

        with patch("python.helpers.rfc_exchange.runtime.is_dockerized", return_value=True):
            with patch("python.helpers.rfc_exchange._get_root_password") as mock_get:
                mock_get.return_value = "docker-pass"
                result = await get_root_password()
                assert result == "docker-pass"
                mock_get.assert_called_once()

    async def test_get_root_password_non_docker_uses_crypto_exchange(self):
        from python.helpers.rfc_exchange import get_root_password

        with patch("python.helpers.rfc_exchange.runtime.is_dockerized", return_value=False):
            with patch("python.helpers.rfc_exchange.crypto") as mock_crypto:
                mock_crypto._generate_private_key = MagicMock(return_value="priv")
                mock_crypto._generate_public_key = MagicMock(return_value="pub")
                mock_crypto.decrypt_data = MagicMock(return_value="decrypted")
                with patch("python.helpers.rfc_exchange.runtime.call_development_function", new_callable=AsyncMock) as mock_call:
                    mock_call.return_value = "encrypted"
                    result = await get_root_password()
                    assert result == "decrypted"
                    mock_call.assert_called_once()


# --- _provide_root_password ---


class TestProvideRootPassword:
    def test_provide_root_password_returns_encrypted(self):
        from python.helpers.rfc_exchange import _provide_root_password

        with patch("python.helpers.rfc_exchange._get_root_password", return_value="secret"):
            with patch("python.helpers.rfc_exchange.crypto.encrypt_data") as mock_enc:
                mock_enc.return_value = "encrypted_secret"
                result = _provide_root_password("public_key_pem")
                assert result == "encrypted_secret"
                mock_enc.assert_called_once_with("secret", "public_key_pem")


# --- _get_root_password ---


class TestGetRootPassword:
    def test_get_root_password_returns_dotenv_value(self):
        from python.helpers.rfc_exchange import _get_root_password

        with patch("python.helpers.rfc_exchange.dotenv.get_dotenv_value") as mock_get:
            mock_get.return_value = "stored-pass"
            result = _get_root_password()
            assert result == "stored-pass"
            mock_get.assert_called_once()

    def test_get_root_password_returns_empty_when_not_set(self):
        from python.helpers.rfc_exchange import _get_root_password

        with patch("python.helpers.rfc_exchange.dotenv.get_dotenv_value", return_value=None):
            result = _get_root_password()
            assert result == ""
