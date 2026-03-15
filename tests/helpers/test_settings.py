"""Tests for python/helpers/settings.py."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import python.helpers.settings as settings_module


@pytest.fixture(autouse=True)
def _reset_settings_module_state():
    settings_module._settings = None
    settings_module._runtime_settings_snapshot = None
    yield
    settings_module._settings = None
    settings_module._runtime_settings_snapshot = None


def _minimal_settings():
    with (
        patch("python.helpers.settings.files") as mock_files,
        patch("python.helpers.settings.runtime") as mock_runtime,
        patch("python.helpers.settings.git") as mock_git,
        patch("python.helpers.settings.dotenv") as mock_dotenv,
    ):
        mock_files.read_file.return_value = "# gitignore"
        mock_files.get_abs_path.side_effect = lambda *p: "/a0/" + "/".join(p)
        mock_files.get_abs_path_dockerized.side_effect = lambda *p: "/a0/" + "/".join(p)
        mock_runtime.is_dockerized.return_value = False
        mock_git.get_version.return_value = "v0.9.0"
        mock_dotenv.get_dotenv_value.return_value = None
        return dict(settings_module.get_default_settings())


class TestGetDefaultValue:
    def test_returns_default_when_env_not_set(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = None
            result = settings_module.get_default_value("foo", "default")
        assert result == "default"

    def test_returns_env_value_for_str(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "custom" if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", "default")
        assert result == "custom"

    def test_returns_env_value_for_int(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "42" if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", 0)
        assert result == 42

    def test_returns_env_value_for_bool_true(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "true" if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", False)
        assert result is True

    def test_returns_env_value_for_bool_yes(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "yes" if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", False)
        assert result is True

    def test_returns_env_value_for_bool_false(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "false" if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", True)
        assert result is False

    def test_returns_env_value_for_dict(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: '{"a": 1}' if "foo" in k.upper() else None
            result = settings_module.get_default_value("foo", {})
        assert result == {"a": 1}

    def test_invalid_value_returns_default_and_warns(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "not_a_number" if "foo" in k.upper() else None
            with patch("python.helpers.settings.PrintStyle") as mock_ps:
                result = settings_module.get_default_value("foo", 100)
        assert result == 100
        mock_ps.return_value.print.assert_called_once()

    def test_invalid_json_returns_default(self):
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda k, d=None: "{invalid" if "foo" in k.upper() else None
            with patch("python.helpers.settings.PrintStyle"):
                result = settings_module.get_default_value("foo", {})
        assert result == {}


class TestMergeSettings:
    def test_merges_delta_into_original(self):
        original = {"a": 1, "b": 2}
        delta = {"b": 20, "c": 3}
        result = settings_module.merge_settings(original, delta)
        assert result == {"a": 1, "b": 20, "c": 3}

    def test_does_not_mutate_original(self):
        original = {"a": 1}
        settings_module.merge_settings(original, {"b": 2})
        assert "b" not in original


class TestNormalizeSettings:
    def test_syncs_version(self):
        defs = _minimal_settings()
        defs["version"] = "v0.9.0"
        with patch("python.helpers.settings.get_default_settings", return_value=defs):
            s = {"version": "v0.8.0", "chat_model_provider": "openai"}
            result = settings_module.normalize_settings(s)
        assert result["version"] == "v0.9.0"

    def test_removes_unknown_keys(self):
        defs = _minimal_settings()
        with patch("python.helpers.settings.get_default_settings", return_value=defs):
            s = {"unknown_key": "x", "chat_model_provider": "openai"}
            result = settings_module.normalize_settings(s)
        assert "unknown_key" not in result

    def test_adds_missing_keys_from_default(self):
        defs = _minimal_settings()
        with patch("python.helpers.settings.get_default_settings", return_value=defs):
            s = {"chat_model_provider": "openai"}
            result = settings_module.normalize_settings(s)
        assert "version" in result
        assert "embed_model_name" in result

    def test_sets_mcp_server_token(self):
        defs = _minimal_settings()
        with patch("python.helpers.settings.get_default_settings", return_value=defs):
            s = {"chat_model_provider": "openai"}
            result = settings_module.normalize_settings(s)
        assert result["mcp_server_token"]
        assert len(result["mcp_server_token"]) == 16

    def test_adjusts_agent_profile_from_v08_default(self):
        defs = _minimal_settings()
        defs["agent_profile"] = "agent0"
        with patch("python.helpers.settings.get_default_settings", return_value=defs):
            s = {"version": "v0.8.0", "agent_profile": "default"}
            result = settings_module.normalize_settings(s)
        assert result["agent_profile"] == "agent0"


class TestGetDefaultSettings:
    def test_returns_settings_dict_with_required_keys(self):
        with patch("python.helpers.settings.files") as mock_files:
            mock_files.read_file.return_value = "# gitignore"
            mock_files.get_abs_path.side_effect = lambda *p: "/a0/" + "/".join(p)
            mock_files.get_abs_path_dockerized.side_effect = lambda *p: "/a0/" + "/".join(p)
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
        with patch("python.helpers.settings.git") as mock_git:
            mock_git.get_version.return_value = "v0.9.0"
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = None
        result = settings_module.get_default_settings()
        assert "version" in result
        assert "chat_model_provider" in result
        assert "api_keys" in result
        assert result["version"] == "v0.9.0"


class TestGetSettings:
    def test_returns_defaults_when_no_file(self):
        with patch("python.helpers.settings._read_settings_file", return_value=None):
            with patch("python.helpers.settings.get_default_settings") as mock_def:
                mock_def.return_value = _minimal_settings()
            with patch("python.helpers.settings._load_sensitive_settings"):
                result = settings_module.get_settings()
        assert result is not None
        assert "chat_model_provider" in result

    def test_returns_file_settings_when_file_exists(self):
        file_settings = _minimal_settings()
        file_settings["chat_model_provider"] = "openai"
        with patch("python.helpers.settings._read_settings_file", return_value=file_settings):
            with patch("python.helpers.settings.get_default_settings", return_value=_minimal_settings()):
                with patch("python.helpers.settings._load_sensitive_settings"):
                    result = settings_module.get_settings()
        assert result["chat_model_provider"] == "openai"

    def test_returns_cached_settings_on_second_call(self):
        with patch("python.helpers.settings._read_settings_file", return_value=None):
            with patch("python.helpers.settings.get_default_settings") as mock_def:
                mock_def.return_value = _minimal_settings()
            with patch("python.helpers.settings._load_sensitive_settings"):
                r1 = settings_module.get_settings()
                r2 = settings_module.get_settings()
        assert r1 is r2


class TestReloadSettings:
    def test_clears_cache_and_returns_fresh_settings(self):
        with patch("python.helpers.settings._read_settings_file", return_value=None):
            with patch("python.helpers.settings.get_default_settings") as mock_def:
                mock_def.return_value = _minimal_settings()
            with patch("python.helpers.settings._load_sensitive_settings"):
                settings_module.get_settings()
                result = settings_module.reload_settings()
        assert result is not None


class TestSetRuntimeSettingsSnapshot:
    def test_sets_snapshot(self):
        s = _minimal_settings()
        settings_module.set_runtime_settings_snapshot(s)
        assert settings_module._runtime_settings_snapshot is not None
        assert settings_module._runtime_settings_snapshot["chat_model_provider"] == s["chat_model_provider"]


class TestSetSettings:
    def test_writes_file_and_reloads(self):
        s = _minimal_settings()
        with patch("python.helpers.settings._write_settings_file") as mock_write:
            with patch("python.helpers.settings._apply_settings"):
                result = settings_module.set_settings(s, apply=False)
        mock_write.assert_called_once()
        assert result is not None

    def test_apply_true_calls_apply_settings(self):
        s = _minimal_settings()
        with patch("python.helpers.settings._write_settings_file"):
            with patch("python.helpers.settings._apply_settings") as mock_apply:
                settings_module.set_settings(s, apply=True)
        mock_apply.assert_called_once()


class TestSetSettingsDelta:
    def test_merges_delta_into_current(self):
        with patch("python.helpers.settings.get_settings") as mock_get:
            mock_get.return_value = _minimal_settings()
            with patch("python.helpers.settings.set_settings") as mock_set:
                settings_module.set_settings_delta({"chat_model_provider": "openai"}, apply=False)
        call_args = mock_set.call_args[0][0]
        assert call_args["chat_model_provider"] == "openai"


class TestConvertOut:
    def test_returns_settings_output_structure(self):
        s = _minimal_settings()
        with patch("python.helpers.settings.get_providers") as mock_prov:
            mock_prov.side_effect = lambda t: [{"value": "openrouter", "label": "OpenRouter"}] if t == "chat" else [{"value": "huggingface", "label": "HuggingFace"}]
        with patch("python.helpers.settings.files") as mock_files:
            mock_files.get_subdirectories.side_effect = lambda p, **kw: ["agent0", "default"] if p == "agents" else ["custom"]
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        with patch("python.helpers.settings.get_default_secrets_manager") as mock_sec:
            mock_sec.return_value.get_masked_secrets.return_value = ""
        with patch("python.helpers.settings.models") as mock_models:
            mock_models.get_api_key.return_value = ""
        result = settings_module.convert_out(s)
        assert "settings" in result
        assert "additional" in result
        assert "chat_providers" in result["additional"]
        assert "embedding_providers" in result["additional"]

    def test_masks_api_keys_in_output(self):
        s = _minimal_settings()
        s["api_keys"] = {"openai": "sk-secret"}
        with patch("python.helpers.settings.get_providers") as mock_prov:
            mock_prov.side_effect = lambda t: [{"value": "openai", "label": "OpenAI"}] if t == "chat" else []
        with patch("python.helpers.settings.files") as mock_files:
            mock_files.get_subdirectories.side_effect = lambda p, **kw: ["agent0"] if p == "agents" else ["custom"]
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        with patch("python.helpers.settings.get_default_secrets_manager") as mock_sec:
            mock_sec.return_value.get_masked_secrets.return_value = ""
        with patch("python.helpers.settings.models") as mock_models:
            mock_models.get_api_key.return_value = "sk-secret"
        result = settings_module.convert_out(s)
        assert result["settings"]["api_keys"].get("openai") == settings_module.API_KEY_PLACEHOLDER

    def test_ensures_option_present_for_missing_provider(self):
        s = _minimal_settings()
        s["chat_model_provider"] = "custom-provider"
        with patch("python.helpers.settings.get_providers") as mock_prov:
            mock_prov.side_effect = lambda t: [{"value": "openrouter", "label": "OpenRouter"}] if t == "chat" else []
        with patch("python.helpers.settings.files") as mock_files:
            mock_files.get_subdirectories.side_effect = lambda p, **kw: ["agent0"] if p == "agents" else ["custom"]
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        with patch("python.helpers.settings.get_default_secrets_manager") as mock_sec:
            mock_sec.return_value.get_masked_secrets.return_value = ""
        with patch("python.helpers.settings.models") as mock_models:
            mock_models.get_api_key.return_value = ""
        result = settings_module.convert_out(s)
        providers = result["additional"]["chat_providers"]
        assert any(p["value"] == "custom-provider" for p in providers)

    def test_converts_kwargs_dict_to_env_string_in_output(self):
        s = _minimal_settings()
        s["chat_model_kwargs"] = {"temperature": 0.7, "max_tokens": 100}
        with patch("python.helpers.settings.get_providers") as mock_prov:
            mock_prov.side_effect = lambda t: [{"value": "openrouter", "label": "OpenRouter"}] if t == "chat" else []
        with patch("python.helpers.settings.files") as mock_files:
            mock_files.get_subdirectories.side_effect = lambda p, **kw: ["agent0"] if p == "agents" else ["custom"]
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        with patch("python.helpers.settings.get_default_secrets_manager") as mock_sec:
            mock_sec.return_value.get_masked_secrets.return_value = ""
        with patch("python.helpers.settings.models") as mock_models:
            mock_models.get_api_key.return_value = ""
        result = settings_module.convert_out(s)
        kwargs_str = result["settings"]["chat_model_kwargs"]
        assert "temperature" in kwargs_str
        assert "0.7" in kwargs_str
        assert "max_tokens" in kwargs_str
        assert "100" in kwargs_str


class TestConvertIn:
    def test_converts_kwargs_string_to_dict(self):
        with patch("python.helpers.settings.get_settings") as mock_get:
            mock_get.return_value = _minimal_settings()
            incoming = {"chat_model_kwargs": "temperature=0.7\nmax_tokens=100"}
            result = settings_module.convert_in(incoming)
        assert result["chat_model_kwargs"] == {"temperature": 0.7, "max_tokens": 100}

    def test_converts_browser_http_headers_string_to_dict(self):
        with patch("python.helpers.settings.get_settings") as mock_get:
            mock_get.return_value = _minimal_settings()
            incoming = {"browser_http_headers": 'X-Custom="value"'}
            result = settings_module.convert_in(incoming)
        assert result["browser_http_headers"] == {"X-Custom": "value"}

    def test_preserves_non_kwargs_values(self):
        with patch("python.helpers.settings.get_settings") as mock_get:
            mock_get.return_value = _minimal_settings()
            incoming = {"chat_model_provider": "openai"}
            result = settings_module.convert_in(incoming)
        assert result["chat_model_provider"] == "openai"


class TestGetRuntimeConfig:
    def test_dockerized_returns_localhost_config(self):
        s = _minimal_settings()
        s["shell_interface"] = "ssh"
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = True
            result = settings_module.get_runtime_config(s)
        assert result["code_exec_ssh_enabled"] is True
        assert result["code_exec_ssh_addr"] == "localhost"
        assert result["code_exec_ssh_port"] == 22

    def test_non_dockerized_uses_rfc_url(self):
        s = _minimal_settings()
        s["shell_interface"] = "ssh"
        s["rfc_url"] = "localhost"
        s["rfc_port_ssh"] = 55022
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
            result = settings_module.get_runtime_config(s)
        assert result["code_exec_ssh_addr"] == "localhost"
        assert result["code_exec_ssh_port"] == 55022

    def test_strips_trailing_slash_from_host(self):
        s = _minimal_settings()
        s["rfc_url"] = "example.com/"
        s["rfc_port_ssh"] = 55022
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
            result = settings_module.get_runtime_config(s)
        assert result["code_exec_ssh_addr"] == "example.com"

    def test_strips_protocol_from_host(self):
        s = _minimal_settings()
        s["rfc_url"] = "http://example.com"
        s["rfc_port_ssh"] = 55022
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
            result = settings_module.get_runtime_config(s)
        assert result["code_exec_ssh_addr"] == "example.com"


class TestCreateAuthToken:
    def test_returns_16_char_token(self):
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.get_persistent_id.return_value = "id123"
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        result = settings_module.create_auth_token()
        assert len(result) == 16
        assert len(result) > 0

    def test_same_inputs_produce_same_token(self):
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.get_persistent_id.return_value = "id123"
        with patch("python.helpers.settings.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = ""
        r1 = settings_module.create_auth_token()
        r2 = settings_module.create_auth_token()
        assert r1 == r2


class TestSetRootPassword:
    def test_raises_when_not_dockerized(self):
        with patch("python.helpers.settings.runtime") as mock_runtime:
            mock_runtime.is_dockerized.return_value = False
            with pytest.raises(Exception, match="dockerized"):
                settings_module.set_root_password("secret")


class TestConstants:
    def test_password_placeholder_defined(self):
        assert settings_module.PASSWORD_PLACEHOLDER == "****PSWD****"

    def test_api_key_placeholder_defined(self):
        assert settings_module.API_KEY_PLACEHOLDER == "************"

    def test_settings_file_path_contains_usr(self):
        assert "usr" in settings_module.SETTINGS_FILE
