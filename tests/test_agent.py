"""Tests for agent.py — AgentContext, LoopData, Agent, AgentConfig, UserMessage."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import agent as _agent_mod
except (ImportError, AttributeError, Exception):
    _agent_mod = None

pytestmark = pytest.mark.skipif(_agent_mod is None, reason="Cannot import agent module")


@pytest.fixture
def mock_model_config():
    cfg = MagicMock()
    cfg.provider = "openai"
    cfg.name = "gpt-4"
    cfg.build_kwargs.return_value = {}
    return cfg


@pytest.fixture
def mock_agent_config(mock_model_config):
    from agent import AgentConfig

    return AgentConfig(
        chat_model=mock_model_config,
        utility_model=mock_model_config,
        embeddings_model=mock_model_config,
        browser_model=mock_model_config,
        mcp_servers="",
    )


class TestAgentContextType:
    def test_enum_values(self):
        from agent import AgentContextType

        assert AgentContextType.USER.value == "user"
        assert AgentContextType.TASK.value == "task"
        assert AgentContextType.BACKGROUND.value == "background"


class TestAgentConfig:
    def test_agent_config_stores_model_configs(self, mock_agent_config):
        assert mock_agent_config.chat_model is not None
        assert mock_agent_config.utility_model is not None
        assert mock_agent_config.embeddings_model is not None
        assert mock_agent_config.browser_model is not None
        assert mock_agent_config.mcp_servers == ""

    def test_agent_config_defaults(self, mock_agent_config):
        assert mock_agent_config.profile == ""
        assert mock_agent_config.memory_subdir == ""
        assert mock_agent_config.knowledge_subdirs == ["default", "custom"]
        assert mock_agent_config.code_exec_ssh_enabled is True
        assert mock_agent_config.code_exec_ssh_addr == "localhost"
        assert mock_agent_config.code_exec_ssh_port == 55022


class TestUserMessage:
    def test_user_message_defaults(self):
        from agent import UserMessage

        msg = UserMessage(message="hello")
        assert msg.message == "hello"
        assert msg.attachments == []
        assert msg.system_message == []

    def test_user_message_with_attachments(self):
        from agent import UserMessage

        msg = UserMessage(
            message="hi",
            attachments=["file1.txt"],
            system_message=["system prompt"],
        )
        assert msg.attachments == ["file1.txt"]
        assert msg.system_message == ["system prompt"]


class TestLoopData:
    def test_loop_data_defaults(self):
        from agent import LoopData

        ld = LoopData()
        assert ld.iteration == -1
        assert ld.system == []
        assert ld.user_message is None
        assert ld.history_output == []
        assert ld.last_response == ""
        assert ld.params_temporary == {}
        assert ld.params_persistent == {}
        assert ld.current_tool is None

    def test_loop_data_kwargs_override(self):
        from agent import LoopData

        ld = LoopData(iteration=5, last_response="test")
        assert ld.iteration == 5
        assert ld.last_response == "test"


class TestAgentContext:
    def test_generate_id_returns_unique_strings(self):
        from agent import AgentContext

        ids = {AgentContext.generate_id() for _ in range(20)}
        assert len(ids) == 20
        for id in ids:
            assert len(id) == 8
            assert id.isalnum()

    def test_get_returns_none_for_unknown_id(self):
        from agent import AgentContext

        assert AgentContext.get("nonexistent_id_xyz") is None

    def test_set_current_and_get_current(self):
        from agent import AgentContext
        from python.helpers import context as context_helper

        context_helper.clear_context_data()
        AgentContext.set_current("ctx-1")
        assert context_helper.get_context_data("agent_context_id", "") == "ctx-1"
        AgentContext.set_current("")
        assert context_helper.get_context_data("agent_context_id", "") == ""

    def test_context_creation_registers_in_contexts(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-1")
            try:
                assert AgentContext.get("test-ctx-1") is ctx
                assert ctx.id == "test-ctx-1"
                assert ctx.config == mock_agent_config
                assert ctx.paused is False
                assert ctx.data == {}
                assert ctx.output_data == {}
            finally:
                AgentContext.remove("test-ctx-1")

    def test_context_get_data_set_data(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-2")
            try:
                assert ctx.get_data("foo") is None
                ctx.set_data("foo", "bar")
                assert ctx.get_data("foo") == "bar"
            finally:
                AgentContext.remove("test-ctx-2")

    def test_context_get_output_data_set_output_data(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-3")
            try:
                assert ctx.get_output_data("out") is None
                ctx.set_output_data("out", 42)
                assert ctx.get_output_data("out") == 42
            finally:
                AgentContext.remove("test-ctx-3")

    def test_context_output_contains_expected_keys(self, mock_agent_config):
        from agent import AgentContext
        from datetime import datetime, timezone

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(
                config=mock_agent_config,
                id="test-ctx-4",
                name="TestChat",
                created_at=datetime.now(timezone.utc),
            )
            try:
                out = ctx.output()
                assert "id" in out
                assert out["id"] == "test-ctx-4"
                assert "name" in out
                assert out["name"] == "TestChat"
                assert "no" in out
                assert "paused" in out
                assert "type" in out
                assert "running" in out
            finally:
                AgentContext.remove("test-ctx-4")

    def test_context_remove_returns_context(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-5")
            removed = AgentContext.remove("test-ctx-5")
            assert removed is ctx
            assert AgentContext.get("test-ctx-5") is None


class TestInterventionException:
    def test_intervention_exception_is_exception(self):
        from agent import InterventionException

        exc = InterventionException("test")
        assert isinstance(exc, Exception)
        assert str(exc) == "test"


class TestHandledException:
    def test_handled_exception_is_exception(self):
        from agent import HandledException

        exc = HandledException("test")
        assert isinstance(exc, Exception)


class TestAgentConstants:
    def test_data_name_constants(self):
        from agent import Agent

        assert Agent.DATA_NAME_SUPERIOR == "_superior"
        assert Agent.DATA_NAME_SUBORDINATE == "_subordinate"
        assert Agent.DATA_NAME_CTX_WINDOW == "ctx_window"
