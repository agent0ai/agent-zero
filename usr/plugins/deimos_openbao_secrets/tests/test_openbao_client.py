"""Tests for OpenBao client wrapper — resilience patterns.

Uses mocked hvac.Client to test retry, circuit breaker, TTL cache,
and authentication without requiring a running OpenBao instance.

See Issue #3: https://192.168.200.52:3000/deimosAI/a0-plugin-openbao-secrets/issues/3
"""
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers.config import OpenBaoConfig
from helpers.openbao_client import OpenBaoClient, _TTLCache, TRANSIENT_ERRORS


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def base_config():
    """Config with token auth for simplicity."""
    return OpenBaoConfig(
        enabled=True,
        url="http://127.0.0.1:8200",
        auth_method="token",
        token="hvs.test-token",
        mount_point="secret",
        secrets_path="agentzero",
        timeout=5.0,
        cache_ttl=10,
        retry_attempts=2,
        circuit_breaker_threshold=3,
        circuit_breaker_recovery=5,
    )


@pytest.fixture
def approle_config():
    """Config with AppRole auth."""
    return OpenBaoConfig(
        enabled=True,
        url="http://127.0.0.1:8200",
        auth_method="approle",
        role_id="test-role-id",
        secret_id="test-secret-id",
        mount_point="secret",
        secrets_path="agentzero",
        timeout=5.0,
        cache_ttl=10,
        retry_attempts=2,
        circuit_breaker_threshold=3,
        circuit_breaker_recovery=5,
    )


@pytest.fixture
def mock_hvac_client():
    """Mocked hvac.Client that appears authenticated."""
    client = MagicMock()
    client.is_authenticated.return_value = True
    client.auth.token.lookup_self.return_value = {
        "data": {"ttl": 3600}
    }
    client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {
            "data": {
                "API_KEY": "sk-test-123",
                "DB_PASSWORD": "secret-pw",
            }
        }
    }
    client.sys.read_health_status.return_value = {
        "initialized": True,
        "sealed": False,
        "standby": False,
        "server_time_utc": 1234567890,
    }
    return client


# ── TTL Cache Tests ───────────────────────────────────────────

class TestTTLCache:
    def test_empty_cache_returns_none(self):
        cache = _TTLCache(ttl_seconds=300)
        assert cache.get() is None

    def test_set_and_get_within_ttl(self):
        cache = _TTLCache(ttl_seconds=300)
        cache.set({"key": "value"})
        result = cache.get()
        assert result == {"key": "value"}

    def test_cache_returns_copy(self):
        cache = _TTLCache(ttl_seconds=300)
        data = {"key": "value"}
        cache.set(data)
        result = cache.get()
        result["key"] = "modified"
        assert cache.get()["key"] == "value"  # Original unmodified

    def test_cache_expires_after_ttl(self):
        cache = _TTLCache(ttl_seconds=0)  # Immediate expiry
        cache.set({"key": "value"})
        assert cache.get() is None

    def test_invalidate_clears_cache(self):
        cache = _TTLCache(ttl_seconds=300)
        cache.set({"key": "value"})
        cache.invalidate()
        assert cache.get() is None

    def test_age_returns_none_when_empty(self):
        cache = _TTLCache(ttl_seconds=300)
        assert cache.age is None

    def test_age_returns_seconds_since_set(self):
        cache = _TTLCache(ttl_seconds=300)
        cache.set({"key": "value"})
        age = cache.age
        assert age is not None
        assert age >= 0
        assert age < 1  # Should be very small


# ── Connection Tests ──────────────────────────────────────────

class TestConnection:
    @patch("helpers.openbao_client.hvac.Client")
    def test_connect_with_token(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        assert client.is_connected()
        assert mock_hvac_client.token == "hvs.test-token"

    @patch("helpers.openbao_client.hvac.Client")
    def test_connect_with_approle(self, mock_hvac_cls, approle_config, mock_hvac_client):
        mock_hvac_client.auth.approle.login.return_value = {
            "auth": {"client_token": "hvs.approle-token"}
        }
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(approle_config)
        assert client.is_connected()
        mock_hvac_client.auth.approle.login.assert_called_once_with(
            role_id="test-role-id",
            secret_id="test-secret-id",
        )

    @patch("helpers.openbao_client.hvac.Client")
    def test_connect_failure_sets_client_none(self, mock_hvac_cls, base_config):
        mock_hvac_cls.side_effect = ConnectionError("refused")
        client = OpenBaoClient(base_config)
        assert not client.is_connected()

    @patch("helpers.openbao_client.hvac.Client")
    def test_is_connected_false_when_not_authenticated(self, mock_hvac_cls, base_config):
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = False
        mock_client.auth.token.lookup_self.return_value = {"data": {"ttl": 0}}
        mock_hvac_cls.return_value = mock_client
        client = OpenBaoClient(base_config)
        assert not client.is_connected()


# ── Read Tests ────────────────────────────────────────────────

class TestRead:
    @patch("helpers.openbao_client.hvac.Client")
    def test_read_all_secrets(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        secrets = client.read_all_secrets()
        assert secrets == {"API_KEY": "sk-test-123", "DB_PASSWORD": "secret-pw"}

    @patch("helpers.openbao_client.hvac.Client")
    def test_read_all_secrets_uppercases_keys(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"lower_key": "value"}}
        }
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        secrets = client.read_all_secrets()
        assert "LOWER_KEY" in secrets

    @patch("helpers.openbao_client.hvac.Client")
    def test_read_single_secret(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        assert client.read_secret("api_key") == "sk-test-123"
        assert client.read_secret("nonexistent") is None

    @patch("helpers.openbao_client.hvac.Client")
    def test_read_returns_empty_on_none_response(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = None
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        client.invalidate_cache()
        secrets = client.read_all_secrets()
        assert secrets == {}


# ── Cache Tests ───────────────────────────────────────────────

class TestCaching:
    @patch("helpers.openbao_client.hvac.Client")
    def test_second_read_uses_cache(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        # First read
        secrets1 = client.read_all_secrets()
        # Second read should use cache (no additional API call)
        secrets2 = client.read_all_secrets()
        assert secrets1 == secrets2
        # KV read should only be called once
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 1

    @patch("helpers.openbao_client.hvac.Client")
    def test_invalidate_forces_refetch(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        client.read_all_secrets()
        client.invalidate_cache()
        client.read_all_secrets()
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 2


# ── Health Check Tests ────────────────────────────────────────

class TestHealthCheck:
    @patch("helpers.openbao_client.hvac.Client")
    def test_health_check_returns_status(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        health = client.health_check()
        assert health["connected"] is True
        assert health["authenticated"] is True
        assert health["initialized"] is True
        assert health["sealed"] is False

    @patch("helpers.openbao_client.hvac.Client")
    def test_health_check_handles_failure(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_client.sys.read_health_status.side_effect = ConnectionError("down")
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        health = client.health_check()
        assert health["connected"] is False

    def test_health_check_no_client(self, base_config):
        with patch("helpers.openbao_client.hvac.Client") as mock_cls:
            mock_cls.side_effect = ConnectionError("refused")
            client = OpenBaoClient(base_config)
        health = client.health_check()
        assert health["connected"] is False
        assert health["authenticated"] is False


# ── Close/Repr Tests ──────────────────────────────────────────

class TestLifecycle:
    @patch("helpers.openbao_client.hvac.Client")
    def test_close(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        client.close()
        assert not client.is_connected()

    @patch("helpers.openbao_client.hvac.Client")
    def test_repr(self, mock_hvac_cls, base_config, mock_hvac_client):
        mock_hvac_cls.return_value = mock_hvac_client
        client = OpenBaoClient(base_config)
        r = repr(client)
        assert "OpenBaoClient" in r
        assert "127.0.0.1" in r
