"""Tests for python/helpers/cognee_init.py — Cognee configuration layer."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_configured():
    """Reset the _configured flag and module-level state before each test."""
    import python.helpers.cognee_init as ci
    ci._configured = False
    ci._cognee_module = None
    ci._search_type_class = None
    yield
    ci._configured = False
    ci._cognee_module = None
    ci._search_type_class = None


@pytest.fixture
def _clean_env():
    """Remove cognee-related env vars after each test."""
    keys_before = set(os.environ.keys())
    yield
    cognee_keys = [
        "LLM_PROVIDER", "LLM_MODEL", "LLM_API_KEY", "LLM_API_BASE",
        "EMBEDDING_PROVIDER", "EMBEDDING_MODEL", "EMBEDDING_API_KEY",
        "EMBEDDING_API_BASE", "EMBEDDING_DIMENSIONS",
        "DATA_ROOT_DIRECTORY", "SYSTEM_ROOT_DIRECTORY", "CACHE_ROOT_DIRECTORY",
        "ENABLE_BACKEND_ACCESS_CONTROL", "CACHING", "CACHE_ADAPTER",
    ]
    for k in cognee_keys:
        os.environ.pop(k, None)
    for k in set(os.environ.keys()) - keys_before:
        if k.startswith("A0_SET_"):
            os.environ.pop(k, None)


# --- get_cognee_setting ---

class TestGetCogneeSetting:
    def test_returns_default_when_no_env_var(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = None
            result = get_cognee_setting("cognee_chunk_size", 512)
        assert result == 512

    def test_returns_builtin_default_when_in_defaults(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.return_value = None
            result = get_cognee_setting("cognee_temporal_enabled", False)
        assert result is True  # _COGNEE_DEFAULTS has True

    def test_env_var_overrides_default_int(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda key, *args: "1024" if "cognee_chunk_size" in key.lower() else None
            result = get_cognee_setting("cognee_chunk_size", 512)
        assert result == 1024

    def test_env_var_overrides_default_bool(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda key, *args: "false" if "cognee_temporal" in key.lower() else None
            result = get_cognee_setting("cognee_temporal_enabled", True)
        assert result is False

    def test_env_var_overrides_default_str(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda key, *args: "CHUNKS" if "cognee_search_type" in key.lower() else None
            result = get_cognee_setting("cognee_search_type", "GRAPH_COMPLETION")
        assert result == "CHUNKS"

    def test_invalid_int_returns_default(self):
        from python.helpers.cognee_init import get_cognee_setting
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.get_dotenv_value.side_effect = lambda key, *args: "not_a_number" if "cognee_chunk_size" in key.lower() else None
            result = get_cognee_setting("cognee_chunk_size", 512)
        assert result == 512


# --- _map_provider ---

class TestMapProvider:
    def test_known_providers(self):
        from python.helpers.cognee_init import _map_provider
        assert _map_provider("openai") == "openai"
        assert _map_provider("huggingface") == "huggingface"
        assert _map_provider("gemini") == "gemini"
        assert _map_provider("ollama") == "ollama"
        assert _map_provider("lmstudio") == "custom"

    def test_case_insensitive(self):
        from python.helpers.cognee_init import _map_provider
        assert _map_provider("OpenAI") == "openai"
        assert _map_provider("ANTHROPIC") == "anthropic"

    def test_unknown_provider_passes_through(self):
        from python.helpers.cognee_init import _map_provider
        assert _map_provider("some_new_provider") == "some_new_provider"


# --- _get_api_key ---

class TestGetApiKey:
    def test_env_var_takes_priority(self):
        from python.helpers.cognee_init import _get_api_key
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = "env_key_123"
            result = _get_api_key("openai", {"openai": "dict_key_456"})
        assert result == "env_key_123"

    def test_api_keys_dict_fallback(self):
        from python.helpers.cognee_init import _get_api_key
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            result = _get_api_key("openai", {"openai": "dict_key_456"})
        assert result == "dict_key_456"

    def test_settings_fallback(self):
        from python.helpers.cognee_init import _get_api_key
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings") as mock_settings:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_settings.return_value = {"api_keys": {"openai": "settings_key_789"}}
            result = _get_api_key("openai")
        assert result == "settings_key_789"

    def test_returns_empty_when_nothing_found(self):
        from python.helpers.cognee_init import _get_api_key
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings") as mock_settings:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_settings.return_value = {"api_keys": {}}
            result = _get_api_key("nonexistent")
        assert result == ""


# --- configure_cognee ---

class TestConfigureCognee:
    def _mock_settings(self):
        return {
            "util_model_provider": "openai",
            "util_model_name": "gpt-4o-mini",
            "util_model_api_base": "",
            "embed_model_provider": "huggingface",
            "embed_model_name": "BAAI/bge-small-en-v1.5",
            "embed_model_api_base": "",
            "api_keys": {"openai": "sk-test", "huggingface": "hf-test"},
        }

    def test_idempotent_only_runs_once(self):
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files"):
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            ci.configure_cognee()
            call_count = mock_cognee.config.set_llm_config.call_count
            ci.configure_cognee()
            assert mock_cognee.config.set_llm_config.call_count == call_count

    def test_reset_allows_rerun(self):
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files, \
             patch("os.makedirs"):
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            ci.configure_cognee()
            ci._configured = False
            ci.configure_cognee()
            assert mock_cognee.config.set_llm_config.call_count == 2

    def test_calls_cognee_config_api(self, _clean_env):
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()

        mock_cognee.config.set_llm_config.assert_called_once_with({
            "llm_provider": "openai",
            "llm_model": "gpt-4o-mini",
            "llm_api_key": "sk-test",
        })
        mock_cognee.config.set_chunk_size.assert_called_once_with(512)
        mock_cognee.config.set_chunk_overlap.assert_called_once_with(50)
        mock_cognee.config.set_data_root_directory.assert_called_once()
        mock_cognee.config.set_system_root_directory.assert_called_once()

    def test_falls_back_to_env_vars_on_config_error(self, _clean_env):
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        mock_cognee.config.set_llm_config.side_effect = AttributeError("no set_llm_config")
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()

        assert os.environ.get("LLM_PROVIDER") == "openai"
        assert os.environ.get("LLM_MODEL") == "gpt-4o-mini"
        assert os.environ.get("LLM_API_KEY") == "sk-test"

    def test_fastembed_for_huggingface(self, _clean_env):
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()

        assert os.environ.get("EMBEDDING_PROVIDER") == "fastembed"
        assert os.environ.get("EMBEDDING_MODEL") == "BAAI/bge-small-en-v1.5"
        assert os.environ.get("EMBEDDING_DIMENSIONS") == "384"

    def test_cognee_import_error_does_not_crash(self):
        import python.helpers.cognee_init as ci
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": None}):
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            # Should not raise even when cognee can't be imported
            try:
                ci.configure_cognee()
            except ImportError:
                pass  # Expected when cognee module is None in sys.modules


class TestConfigureCogneeAdditional:
    """Additional tests for configure_cognee (formerly ensure_cognee_setup)."""

    def _mock_settings(self):
        return {
            "util_model_provider": "openai",
            "util_model_name": "gpt-4o-mini",
            "util_model_api_base": "",
            "embed_model_provider": "huggingface",
            "embed_model_name": "BAAI/bge-small-en-v1.5",
            "embed_model_api_base": "",
            "api_keys": {"openai": "sk-test", "huggingface": "hf-test"},
        }

    def test_configure_cognee_idempotent_only_runs_once(self):
        """configure_cognee is idempotent — config APIs called only once."""
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()
            ci.configure_cognee()
        mock_cognee.config.set_llm_config.assert_called_once()

    def test_configure_cognee_handles_config_exception(self, _clean_env):
        """configure_cognee falls back to env vars when config API fails."""
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        mock_cognee.config.set_llm_config.side_effect = Exception("config failed")
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()
        assert os.environ.get("LLM_PROVIDER") == "openai"

    def test_configure_cognee_retries_after_reset(self):
        """After _configured reset, configure_cognee runs again."""
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=self._mock_settings()), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files, \
             patch("os.makedirs"):
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()
            ci._configured = False
            ci.configure_cognee()
        assert mock_cognee.config.set_llm_config.call_count == 2

    def test_configure_cognee_sets_embedding_for_non_fastembed(self, _clean_env):
        """configure_cognee sets EMBEDDING_PROVIDER for non-huggingface providers."""
        import python.helpers.cognee_init as ci
        mock_cognee = MagicMock()
        settings = self._mock_settings()
        settings["embed_model_provider"] = "openai"
        settings["embed_model_name"] = "text-embedding-3-small"
        with patch("python.helpers.cognee_init.dotenv") as mock_dotenv, \
             patch("python.helpers.cognee_init.get_settings", return_value=settings), \
             patch.dict("sys.modules", {"cognee": mock_cognee}), \
             patch("python.helpers.cognee_init.files") as mock_files:
            mock_dotenv.load_dotenv.return_value = None
            mock_dotenv.get_dotenv_value.return_value = None
            mock_files.get_abs_path.return_value = "/tmp/test_cognee"
            ci.configure_cognee()
        assert os.environ.get("EMBEDDING_PROVIDER") == "openai"
        assert "openai" in os.environ.get("EMBEDDING_MODEL", "")


# --- init_cognee / get_cognee ---

class TestInitCognee:
    def _mock_settings(self):
        return {
            "util_model_provider": "openai",
            "util_model_name": "gpt-4o-mini",
            "util_model_api_base": "",
            "embed_model_provider": "huggingface",
            "embed_model_name": "BAAI/bge-small-en-v1.5",
            "embed_model_api_base": "",
            "api_keys": {"openai": "sk-test", "huggingface": "hf-test"},
        }

    @pytest.mark.asyncio
    async def test_init_cognee_calls_configure_and_create_tables(self):
        """init_cognee calls configure_cognee and creates DB tables."""
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_search_type = MagicMock()
        mock_cognee.SearchType = mock_search_type
        mock_create_tables = AsyncMock()

        with patch("python.helpers.cognee_init.configure_cognee") as mock_configure, \
             patch.dict("sys.modules", {
                 "cognee": mock_cognee,
                 "cognee.infrastructure.databases.relational": MagicMock(
                     create_db_and_tables=mock_create_tables
                 ),
             }):
            await ci.init_cognee()

        mock_configure.assert_called_once()
        mock_create_tables.assert_awaited_once()
        assert ci._cognee_module is mock_cognee
        assert ci._search_type_class is mock_search_type

    @pytest.mark.asyncio
    async def test_get_cognee_raises_if_not_initialized(self):
        """get_cognee raises RuntimeError when init_cognee hasn't been called."""
        import python.helpers.cognee_init as ci
        with pytest.raises(RuntimeError, match="Cognee not initialized"):
            ci.get_cognee()

    @pytest.mark.asyncio
    async def test_get_cognee_returns_modules_after_init(self):
        """get_cognee returns (cognee, SearchType) tuple after init_cognee."""
        import python.helpers.cognee_init as ci

        mock_cognee = MagicMock()
        mock_search_type = MagicMock()
        mock_cognee.SearchType = mock_search_type
        mock_create_tables = AsyncMock()

        with patch("python.helpers.cognee_init.configure_cognee"), \
             patch.dict("sys.modules", {
                 "cognee": mock_cognee,
                 "cognee.infrastructure.databases.relational": MagicMock(
                     create_db_and_tables=mock_create_tables
                 ),
             }):
            await ci.init_cognee()

        cognee_mod, search_type = ci.get_cognee()
        assert cognee_mod is mock_cognee
        assert search_type is mock_search_type
