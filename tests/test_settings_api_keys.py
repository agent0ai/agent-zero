import json

import pytest

import models
from helpers import dotenv, settings
from helpers.errors import RepairableException
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


def test_settings_editor_does_not_present_secret_read_failures_as_empty_fields(tmp_path, monkeypatch):
    path = tmp_path / "secrets.env"
    stored = b"TOKEN=synthetic-existing-value\n# invalid UTF-8: \xff\n"
    path.write_bytes(stored)
    manager = SecretsManager(str(path))
    monkeypatch.setattr(settings, "get_default_secrets_manager", lambda: manager)
    monkeypatch.setattr(settings, "get_providers", lambda _: [])
    monkeypatch.setattr(settings.dotenv, "get_dotenv_value", lambda _: None)
    monkeypatch.setattr(settings, "get_default_settings", lambda: {"uvicorn_access_logs_enabled": False})
    monkeypatch.setattr(settings.runtime, "is_dockerized", lambda: False)
    monkeypatch.setattr(settings.subagents, "get_available_agents_dict", lambda _: {})
    monkeypatch.setattr(settings.files, "get_subdirectories", lambda *args, **kwargs: [])
    monkeypatch.setattr(settings, "_timezone_options", lambda: [])
    monkeypatch.setattr(settings, "_resolve_runtime_timezone", lambda _: "UTC")
    configured = {"api_keys": {}, "timezone": "UTC"}

    with pytest.raises(RepairableException):
        settings.convert_out(configured)
    assert path.read_bytes() == stored


@pytest.mark.parametrize("failure", ["permission", "encoding"])
@pytest.mark.parametrize("recover_before_save", [False, True])
def test_unavailable_secrets_allow_unrelated_settings_without_data_loss(
    tmp_path, monkeypatch, failure, recover_before_save
):
    path = tmp_path / "secrets.env"
    original = b"TOKEN=synthetic-existing-value\n"
    stored = original + b"# invalid UTF-8: \xff\n" if failure == "encoding" else original
    path.write_bytes(stored)
    manager = SecretsManager(str(path))
    monkeypatch.setattr(settings, "get_default_secrets_manager", lambda: manager)
    monkeypatch.setattr(settings, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.setattr(settings, "_settings", None)
    monkeypatch.setattr(settings, "get_providers", lambda _: [])
    monkeypatch.setattr(settings.dotenv, "get_dotenv_value", lambda key, default=None: default)
    monkeypatch.setattr(settings.dotenv, "save_dotenv_value", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings.git, "get_version", lambda: "v1")
    monkeypatch.setattr(settings.runtime, "get_persistent_id", lambda: "test-runtime")
    monkeypatch.setattr(settings.runtime, "is_dockerized", lambda: False)
    read_file = settings.files.read_file

    with monkeypatch.context() as patch:
        if failure == "permission":
            def unreadable(filename, *args, **kwargs):
                if filename == str(path):
                    raise PermissionError("synthetic read failure")
                return read_file(filename, *args, **kwargs)
            patch.setattr(settings.files, "read_file", unreadable)

        current = settings.get_settings()
        assert current["secrets"] is None
        updated = settings.set_settings_delta({"workdir_show": False}, apply=False)
        assert updated["workdir_show"] is False
        assert updated["secrets"] is None
        assert path.read_bytes() == stored

        with pytest.raises(RepairableException):
            settings.set_settings_delta({"secrets": ""}, apply=False)
        assert path.read_bytes() == stored

        if recover_before_save:
            path.write_bytes(original)
            patch.setattr(settings.files, "read_file", read_file)
        current["workdir_show"] = False
        settings.set_settings(current, apply=False)
        assert path.read_bytes() == (original if recover_before_save else stored)
        persisted = json.loads((tmp_path / "settings.json").read_text())
        assert persisted["workdir_show"] is False
        assert persisted["secrets"] == ""

    path.write_bytes(original)
    assert settings.get_settings()["secrets"] == original.decode()
    settings.set_settings_delta({"secrets": ""}, apply=False)
    assert path.read_text() == ""
