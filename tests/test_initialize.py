"""Tests for initialize.py — initialization functions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _minimal_settings():
    return {
        "chat_model_provider": "openai",
        "chat_model_name": "gpt-4",
        "chat_model_api_base": "",
        "chat_model_ctx_length": 4096,
        "chat_model_vision": False,
        "chat_model_rl_requests": 0,
        "chat_model_rl_input": 0,
        "chat_model_rl_output": 0,
        "chat_model_kwargs": {},
        "util_model_provider": "openai",
        "util_model_name": "gpt-4",
        "util_model_api_base": "",
        "util_model_ctx_length": 4096,
        "util_model_rl_requests": 0,
        "util_model_rl_input": 0,
        "util_model_rl_output": 0,
        "util_model_kwargs": {},
        "embed_model_provider": "openai",
        "embed_model_name": "text-embedding-3-small",
        "embed_model_api_base": "",
        "embed_model_rl_requests": 0,
        "embed_model_kwargs": {},
        "browser_model_provider": "openai",
        "browser_model_name": "gpt-4",
        "browser_model_api_base": "",
        "browser_model_vision": False,
        "browser_model_kwargs": {},
        "agent_profile": "",
        "agent_memory_subdir": "",
        "agent_knowledge_subdir": "default",
        "mcp_servers": "",
        "browser_http_headers": {},
    }


class TestInitializeAgent:
    def test_initialize_agent_returns_agent_config(self):
        from initialize import initialize_agent

        with (
            patch("initialize.settings.get_settings", return_value=_minimal_settings()),
            patch("initialize.settings.get_runtime_config", return_value={}),
            patch("initialize.runtime.args", {}),
        ):
            config = initialize_agent()
            assert config is not None
            assert config.chat_model is not None
            assert config.utility_model is not None
            assert config.embeddings_model is not None
            assert config.browser_model is not None
            assert config.mcp_servers == ""

    def test_initialize_agent_uses_override_settings(self):
        from initialize import initialize_agent

        base = _minimal_settings()
        with (
            patch("initialize.settings.get_settings", return_value=base.copy()),
            patch("initialize.settings.merge_settings") as mock_merge,
            patch("initialize.settings.get_runtime_config", return_value={}),
            patch("initialize.runtime.args", {}),
        ):
            mock_merge.return_value = {**base, "agent_profile": "custom"}
            config = initialize_agent(override_settings={"agent_profile": "custom"})
            mock_merge.assert_called_once()
            assert config.profile == "custom"

    def test_initialize_agent_normalizes_model_kwargs_string_numbers(self):
        from initialize import initialize_agent

        base = _minimal_settings()
        base["chat_model_kwargs"] = {"temperature": "0.7", "max_tokens": "1024"}
        with (
            patch("initialize.settings.get_settings", return_value=base),
            patch("initialize.settings.get_runtime_config", return_value={}),
            patch("initialize.runtime.args", {}),
        ):
            config = initialize_agent()
            assert config.chat_model.kwargs["temperature"] == 0.7
            assert config.chat_model.kwargs["max_tokens"] == 1024


class TestArgsOverride:
    def test_args_override_sets_config_attributes(self):
        from initialize import _args_override

        mock_cfg = MagicMock()
        mock_cfg.profile = "original"
        mock_cfg.chat_model = None
        mock_cfg.utility_model = None
        mock_cfg.embeddings_model = None
        mock_cfg.browser_model = None
        mock_cfg.mcp_servers = ""

        with patch("initialize.runtime") as mock_runtime:
            mock_runtime.args = {"profile": "overridden"}
            _args_override(mock_cfg)
            assert mock_cfg.profile == "overridden"

    def test_args_override_converts_bool(self):
        from initialize import _args_override

        mock_cfg = MagicMock()
        mock_cfg.code_exec_ssh_enabled = True
        mock_cfg.chat_model = None
        mock_cfg.utility_model = None
        mock_cfg.embeddings_model = None
        mock_cfg.browser_model = None
        mock_cfg.mcp_servers = ""

        with patch("initialize.runtime") as mock_runtime:
            mock_runtime.args = {"code_exec_ssh_enabled": "false"}
            _args_override(mock_cfg)
            assert mock_cfg.code_exec_ssh_enabled is False

    def test_args_override_converts_int(self):
        from initialize import _args_override

        mock_cfg = MagicMock()
        mock_cfg.code_exec_ssh_port = 55022
        mock_cfg.chat_model = None
        mock_cfg.utility_model = None
        mock_cfg.embeddings_model = None
        mock_cfg.browser_model = None
        mock_cfg.mcp_servers = ""

        with patch("initialize.runtime") as mock_runtime:
            mock_runtime.args = {"code_exec_ssh_port": "12345"}
            _args_override(mock_cfg)
            assert mock_cfg.code_exec_ssh_port == 12345


class TestInitializeChats:
    def test_initialize_chats_returns_deferred_task(self):
        from initialize import initialize_chats

        with patch("python.helpers.persist_chat.load_tmp_chats"):
            result = initialize_chats()
            assert result is not None
            assert hasattr(result, "start_task")


class TestInitializeMcp:
    def test_initialize_mcp_returns_deferred_task(self):
        from initialize import initialize_mcp

        result = initialize_mcp()
        assert result is not None
        assert hasattr(result, "start_task")


class TestInitializeJobLoop:
    def test_initialize_job_loop_returns_deferred_task(self):
        from initialize import initialize_job_loop

        with patch("initialize.run_loop", AsyncMock()):
            result = initialize_job_loop()
            assert result is not None
            assert hasattr(result, "start_task")


class TestInitializePreload:
    def test_initialize_preload_returns_deferred_task(self):
        from initialize import initialize_preload

        with patch("initialize.preload") as mock_preload_mod:
            mock_preload_mod.preload = MagicMock()
            result = initialize_preload()
            assert result is not None
            assert hasattr(result, "start_task")


class TestInitializeCognee:
    def test_initialize_cognee_calls_configure_and_starts_task(self):
        from initialize import initialize_cognee

        with (
            patch("python.helpers.cognee_init.configure_cognee") as mock_configure,
            patch("python.helpers.cognee_background.CogneeBackgroundWorker") as mock_worker,
        ):
            mock_instance = MagicMock()
            mock_worker.get_instance.return_value = mock_instance
            # Patch migration module so deferred task can import it
            mock_migrate_mod = MagicMock()
            mock_migrate_mod.run_migration = AsyncMock(return_value=True)
            with patch.dict(
                "sys.modules",
                {
                    "scripts": MagicMock(),
                    "scripts.migrate_faiss_to_cognee": mock_migrate_mod,
                },
            ):
                result = initialize_cognee()
            mock_configure.assert_called_once()
            assert result is not None


class TestInitializeMigration:
    def test_initialize_migration_calls_migrate_and_reload(self):
        from initialize import initialize_migration

        with (
            patch("python.helpers.migration.migrate_user_data") as mock_migrate,
            patch("python.helpers.dotenv.load_dotenv") as mock_dotenv,
            patch("python.helpers.settings.reload_settings") as mock_reload,
        ):
            initialize_migration()
            mock_migrate.assert_called_once()
            mock_dotenv.assert_called_once()
            mock_reload.assert_called_once()
