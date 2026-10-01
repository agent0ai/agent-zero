import json

import pytest

import models
from helpers import dotenv, settings
from helpers.secrets import SecretsManager


@pytest.mark.parametrize("env_key", ["API_KEY_TEST_PROVIDER", "TEST_PROVIDER_API_KEY", "TEST_PROVIDER_API_TOKEN"])
def test_settings_delta_preserves_full_provider_key_list(tmp_path, monkeypatch, env_key):
    env_path = tmp_path / ".env"
    env_path.write_text(f"{env_key}=first-key,second-key\nAUTH_PASSWORD=test-password\n")
    for key in ("API_KEY_TEST_PROVIDER", "TEST_PROVIDER_API_KEY", "TEST_PROVIDER_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(env_key, "first-key,second-key")
    # Track the canonical key so dotenv reloads are undone after each test.
    if env_key != "API_KEY_TEST_PROVIDER":
        monkeypatch.setenv("API_KEY_TEST_PROVIDER", "")
    for key in ("AUTH_LOGIN", "AUTH_PASSWORD", "RFC_PASSWORD", "ROOT_PASSWORD"):
        monkeypatch.setenv(key, "test-password" if key == "AUTH_PASSWORD" else "")
    monkeypatch.setattr(dotenv, "get_dotenv_file_path", lambda: str(env_path))
    monkeypatch.setattr(settings, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.setattr(settings, "_settings", None)
    monkeypatch.setattr(settings.git, "get_version", lambda: "v1")
    monkeypatch.setattr(settings.runtime, "get_persistent_id", lambda: "test-runtime")
    monkeypatch.setattr(settings.runtime, "is_dockerized", lambda: False)
    monkeypatch.setattr(settings, "get_providers", lambda _: [{"value": "test_provider"}])
    monkeypatch.setattr(settings, "get_default_secrets_manager", lambda: SecretsManager.get_instance(str(tmp_path / "secrets.env")))
    monkeypatch.setattr(SecretsManager, "_instances", {})
    monkeypatch.setattr(models, "api_keys_round_robin", {})

    assert settings.get_settings()["api_keys"]["test_provider"] == "first-key,second-key"
    assert models.api_keys_round_robin == {}
    settings.set_settings_delta({"workdir_show": False}, apply=False)
    assert dotenv.get_dotenv_value("API_KEY_TEST_PROVIDER") == "first-key,second-key"
    assert settings.get_settings()["auth_password"] == "test-password"
    assert json.loads((tmp_path / "settings.json").read_text())["api_keys"] == {}
    assert models.get_api_key("test_provider") == "first-key"
    assert models.get_api_key("test_provider") == "second-key"


def test_raw_keys_do_not_include_runtime_oauth_placeholders(monkeypatch):
    from helpers import extension
    from plugins._oauth.extensions.python._functions.models.get_api_key.end import (
        _20_oauth_account_dummy_key as oauth_key,
    )
    from plugins._oauth.helpers.providers import CODEX_PROVIDER_ID, DUMMY_API_KEY

    provider = CODEX_PROVIDER_ID
    for key in (f"API_KEY_{provider.upper()}", f"{provider.upper()}_API_KEY", f"{provider.upper()}_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(oauth_key, "oauth_provider_is_connected", lambda _: True)
    monkeypatch.setattr(
        extension, "_get_extension_classes",
        lambda point, **_: [oauth_key.OAuthAccountDummyKey] if point == "_functions/models/get_api_key/end" else [],
    )

    assert models.get_api_key_raw(provider) == "None"
    assert models.get_api_key(provider) == DUMMY_API_KEY
