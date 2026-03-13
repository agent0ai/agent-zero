"""Tests for OpenBao plugin configuration loading and validation."""
import json
import os
import pytest
from pathlib import Path

# Adjust import path for plugin structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers.config import OpenBaoConfig, load_config, validate_config


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def plugin_dir(tmp_path):
    """Empty plugin directory with no settings file."""
    return str(tmp_path)


@pytest.fixture
def plugin_dir_with_settings(tmp_path):
    """Plugin directory with a settings.json."""
    settings = {
        "enabled": True,
        "url": "https://bao.example.com:8200",
        "auth_method": "token",
        "token": "hvs.test-token-123",
        "mount_point": "kv",
        "secrets_path": "myapp",
        "timeout": 15.0,
        "cache_ttl": 600,
    }
    (tmp_path / "settings.json").write_text(json.dumps(settings))
    return str(tmp_path)


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all OPENBAO_ environment variables."""
    for key in list(os.environ.keys()):
        if key.startswith("OPENBAO_"):
            monkeypatch.delenv(key, raising=False)


# ── Defaults ──────────────────────────────────────────────────

class TestDefaults:
    def test_default_config_values(self):
        config = OpenBaoConfig()
        assert config.enabled is False
        assert config.url == "http://127.0.0.1:8200"
        assert config.auth_method == "approle"
        assert config.role_id == ""
        assert config.secret_id == ""
        assert config.token == ""
        assert config.mount_point == "secret"
        assert config.secrets_path == "agentzero"
        assert config.tls_verify is True
        assert config.tls_ca_cert == ""
        assert config.timeout == 10.0
        assert config.cache_ttl == 300
        assert config.retry_attempts == 3
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_recovery == 60
        assert config.fallback_to_env is True

    def test_load_config_returns_defaults_when_no_sources(self, plugin_dir, clean_env):
        config = load_config(plugin_dir)
        assert config.enabled is False
        assert config.url == "http://127.0.0.1:8200"


# ── Settings File Loading ─────────────────────────────────────

class TestSettingsFile:
    def test_load_from_settings_json(self, plugin_dir_with_settings, clean_env):
        config = load_config(plugin_dir_with_settings)
        assert config.enabled is True
        assert config.url == "https://bao.example.com:8200"
        assert config.auth_method == "token"
        assert config.token == "hvs.test-token-123"
        assert config.mount_point == "kv"
        assert config.secrets_path == "myapp"
        assert config.timeout == 15.0
        assert config.cache_ttl == 600

    def test_settings_preserves_defaults_for_missing_keys(self, tmp_path, clean_env):
        (tmp_path / "settings.json").write_text(json.dumps({"enabled": True}))
        config = load_config(str(tmp_path))
        assert config.enabled is True
        assert config.url == "http://127.0.0.1:8200"  # default preserved

    def test_settings_invalid_json(self, tmp_path, clean_env):
        (tmp_path / "settings.json").write_text("not json{{{")
        config = load_config(str(tmp_path))
        # Should fall back to defaults, not crash
        assert config.enabled is False

    def test_settings_non_dict_root(self, tmp_path, clean_env):
        (tmp_path / "settings.json").write_text(json.dumps([1, 2, 3]))
        config = load_config(str(tmp_path))
        assert config.enabled is False

    def test_settings_unknown_key_ignored(self, tmp_path, clean_env):
        (tmp_path / "settings.json").write_text(json.dumps({"unknown_key": "value"}))
        config = load_config(str(tmp_path))
        assert not hasattr(config, "unknown_key") or config.enabled is False


# ── Environment Variables ─────────────────────────────────────

class TestEnvVars:
    def test_env_vars_override_defaults(self, plugin_dir, monkeypatch, clean_env):
        monkeypatch.setenv("OPENBAO_ENABLED", "true")
        monkeypatch.setenv("OPENBAO_URL", "https://env-bao.com")
        monkeypatch.setenv("OPENBAO_AUTH_METHOD", "token")
        monkeypatch.setenv("OPENBAO_TOKEN", "hvs.env-token")
        config = load_config(plugin_dir)
        assert config.enabled is True
        assert config.url == "https://env-bao.com"
        assert config.auth_method == "token"
        assert config.token == "hvs.env-token"

    def test_env_vars_override_settings_file(self, plugin_dir_with_settings, monkeypatch, clean_env):
        # settings.json has url=https://bao.example.com:8200
        monkeypatch.setenv("OPENBAO_URL", "https://env-override.com")
        config = load_config(plugin_dir_with_settings)
        assert config.url == "https://env-override.com"  # env wins
        assert config.enabled is True  # from settings.json (not overridden)

    def test_bool_env_parsing(self, plugin_dir, monkeypatch, clean_env):
        for truthy in ("true", "True", "TRUE", "1", "yes", "Yes"):
            monkeypatch.setenv("OPENBAO_ENABLED", truthy)
            assert load_config(plugin_dir).enabled is True
        for falsy in ("false", "False", "0", "no", "anything"):
            monkeypatch.setenv("OPENBAO_ENABLED", falsy)
            assert load_config(plugin_dir).enabled is False

    def test_numeric_env_parsing(self, plugin_dir, monkeypatch, clean_env):
        monkeypatch.setenv("OPENBAO_TIMEOUT", "25.5")
        monkeypatch.setenv("OPENBAO_CACHE_TTL", "120")
        monkeypatch.setenv("OPENBAO_RETRY_ATTEMPTS", "5")
        monkeypatch.setenv("OPENBAO_CB_THRESHOLD", "10")
        monkeypatch.setenv("OPENBAO_CB_RECOVERY", "90")
        config = load_config(plugin_dir)
        assert config.timeout == 25.5
        assert config.cache_ttl == 120
        assert config.retry_attempts == 5
        assert config.circuit_breaker_threshold == 10
        assert config.circuit_breaker_recovery == 90

    def test_invalid_numeric_env_falls_back(self, plugin_dir, monkeypatch, clean_env):
        monkeypatch.setenv("OPENBAO_TIMEOUT", "not_a_number")
        config = load_config(plugin_dir)
        assert config.timeout == 10.0  # default preserved


# ── Validation ────────────────────────────────────────────────

class TestValidation:
    def test_valid_approle_config(self):
        config = OpenBaoConfig(
            enabled=True,
            auth_method="approle",
            role_id="role-123",
            secret_id="secret-456",
        )
        assert validate_config(config) == []

    def test_valid_token_config(self):
        config = OpenBaoConfig(
            enabled=True,
            auth_method="token",
            token="hvs.test-token",
        )
        assert validate_config(config) == []

    def test_invalid_url(self):
        config = OpenBaoConfig(url="ftp://bad-url")
        errors = validate_config(config)
        assert any("http://" in e for e in errors)

    def test_empty_url(self):
        config = OpenBaoConfig(url="")
        errors = validate_config(config)
        assert any("http://" in e for e in errors)

    def test_approle_requires_role_id(self):
        config = OpenBaoConfig(auth_method="approle", role_id="")
        errors = validate_config(config)
        assert any("role_id" in e for e in errors)

    def test_token_requires_token(self):
        config = OpenBaoConfig(auth_method="token", token="")
        errors = validate_config(config)
        assert any("token" in e.lower() for e in errors)

    def test_timeout_must_be_positive(self):
        config = OpenBaoConfig(timeout=0)
        errors = validate_config(config)
        assert any("timeout" in e for e in errors)

        config = OpenBaoConfig(timeout=-1)
        errors = validate_config(config)
        assert any("timeout" in e for e in errors)

    def test_cache_ttl_must_be_non_negative(self):
        config = OpenBaoConfig(cache_ttl=-1)
        errors = validate_config(config)
        assert any("cache_ttl" in e for e in errors)

        config = OpenBaoConfig(cache_ttl=0)
        assert validate_config(config) == [] or not any("cache_ttl" in e for e in validate_config(config))

    def test_retry_attempts_must_be_non_negative(self):
        config = OpenBaoConfig(retry_attempts=-1)
        errors = validate_config(config)
        assert any("retry_attempts" in e for e in errors)

    def test_circuit_breaker_threshold_must_be_positive(self):
        config = OpenBaoConfig(circuit_breaker_threshold=0)
        errors = validate_config(config)
        assert any("circuit_breaker_threshold" in e for e in errors)

    def test_circuit_breaker_recovery_must_be_positive(self):
        config = OpenBaoConfig(circuit_breaker_recovery=0)
        errors = validate_config(config)
        assert any("circuit_breaker_recovery" in e for e in errors)

    def test_tls_ca_cert_nonexistent_path(self):
        config = OpenBaoConfig(tls_ca_cert="/nonexistent/path/ca.crt")
        errors = validate_config(config)
        assert any("tls_ca_cert" in e for e in errors)

    def test_multiple_errors(self):
        config = OpenBaoConfig(
            url="bad",
            auth_method="approle",
            role_id="",
            timeout=-1,
            circuit_breaker_threshold=0,
        )
        errors = validate_config(config)
        assert len(errors) >= 3  # url + role_id + timeout + threshold
