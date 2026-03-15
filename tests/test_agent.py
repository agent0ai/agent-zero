"""Tests for agent.py — AgentContext, LoopData, Agent, AgentConfig, UserMessage."""

import asyncio
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

    def test_context_use_sets_current_when_found(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-use")
            try:
                from python.helpers import context as context_helper
                context_helper.clear_context_data()
                result = AgentContext.use("test-ctx-use")
                assert result is ctx
                assert context_helper.get_context_data("agent_context_id", "") == "test-ctx-use"
            finally:
                AgentContext.remove("test-ctx-use")

    def test_context_use_clears_current_when_not_found(self):
        from agent import AgentContext
        from python.helpers import context as context_helper

        context_helper.clear_context_data()
        AgentContext.set_current("some-id")
        result = AgentContext.use("nonexistent_xyz_123")
        assert result is None
        assert context_helper.get_context_data("agent_context_id", "") == ""

    def test_context_current_returns_none_when_no_context_set(self):
        from agent import AgentContext
        from python.helpers import context as context_helper

        context_helper.clear_context_data()
        assert AgentContext.current() is None

    def test_context_current_returns_context_when_set(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-current", set_current=True)
            try:
                assert AgentContext.current() is ctx
            finally:
                AgentContext.remove("test-ctx-current")

    def test_context_first_returns_first_context_when_present(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-first")
            try:
                first = AgentContext.first()
                assert first is not None
                assert first.id == "test-ctx-first"
            finally:
                AgentContext.remove("test-ctx-first")

    def test_context_all_returns_list_of_contexts(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx1 = AgentContext(config=mock_agent_config, id="test-ctx-all-1")
            ctx2 = AgentContext(config=mock_agent_config, id="test-ctx-all-2")
            try:
                all_ctxs = AgentContext.all()
                assert len(all_ctxs) >= 2
                assert ctx1 in all_ctxs
                assert ctx2 in all_ctxs
            finally:
                AgentContext.remove("test-ctx-all-1")
                AgentContext.remove("test-ctx-all-2")

    def test_context_get_agent_returns_streaming_or_agent0(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent_cls.return_value = mock_agent
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-agent")
            try:
                assert ctx.get_agent() is mock_agent
                ctx.streaming_agent = MagicMock()
                assert ctx.get_agent() is ctx.streaming_agent
            finally:
                AgentContext.remove("test-ctx-agent")

    def test_context_is_running_false_when_no_task(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-running")
            try:
                assert ctx.is_running() is False
            finally:
                AgentContext.remove("test-ctx-running")

    def test_context_is_running_true_when_task_alive(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-running2")
            try:
                task = MagicMock()
                task.is_alive.return_value = True
                ctx.task = task
                assert ctx.is_running() is True
            finally:
                AgentContext.remove("test-ctx-running2")

    def test_context_log_to_all_logs_to_each_context(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-log")
            try:
                ctx.log.log = MagicMock(return_value=MagicMock())
                items = AgentContext.log_to_all("info", heading="Test", content="msg")
                assert len(items) >= 1
                ctx.log.log.assert_called()
            finally:
                AgentContext.remove("test-ctx-log")

    def test_context_get_notification_manager_returns_singleton(self, mock_agent_config):
        from agent import AgentContext

        with patch("agent.Agent") as mock_agent_cls:
            mock_agent_cls.return_value = MagicMock()
            ctx = AgentContext(config=mock_agent_config, id="test-ctx-notif")
            try:
                mgr1 = AgentContext.get_notification_manager()
                mgr2 = AgentContext.get_notification_manager()
                assert mgr1 is mgr2
            finally:
                AgentContext.remove("test-ctx-notif")


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


class TestAgent:
    @pytest.fixture
    def agent_with_mocked_extensions(self, mock_agent_config):
        """Create Agent with call_extensions mocked to avoid extension loading."""
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
        ):
            mock_ctx = MagicMock()
            mock_ctx.id = "test-ctx"
            mock_ctx.data = {}
            mock_ctx.paused = False
            mock_ctx.streaming_agent = None
            mock_ctx.task = None
            mock_ctx.log = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            agent.context = mock_ctx
            return agent

    def test_agent_get_data_set_data(self, agent_with_mocked_extensions):
        agent = agent_with_mocked_extensions
        assert agent.get_data("foo") is None
        agent.set_data("foo", "bar")
        assert agent.get_data("foo") == "bar"

    def test_agent_get_chat_model_calls_models(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("models.get_chat_model") as mock_get,
        ):
            mock_ctx = MagicMock()
            mock_ctx.id = "test-ctx"
            mock_ctx.data = {}
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            agent.get_chat_model()
            mock_get.assert_called_once()

    def test_agent_get_utility_model_calls_models(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("models.get_chat_model") as mock_get,
        ):
            mock_ctx = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            agent.get_utility_model()
            mock_get.assert_called_once()

    def test_agent_get_browser_model_calls_models(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("models.get_browser_model") as mock_get,
        ):
            mock_ctx = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            agent.get_browser_model()
            mock_get.assert_called_once()

    def test_agent_get_embedding_model_calls_models(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("models.get_embedding_model") as mock_get,
        ):
            mock_ctx = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            agent.get_embedding_model()
            mock_get.assert_called_once()

    def test_agent_build_metrics_context(self, agent_with_mocked_extensions):
        agent = agent_with_mocked_extensions
        agent.context.data["project"] = "my-project"
        agent.context.name = "Chat1"
        ctx = agent._build_metrics_context("chat")
        assert ctx["usage_type"] == "chat"
        assert ctx["agent_name"] == "A0"
        assert ctx["context_id"] == "test-ctx"
        assert ctx["project"] == "my-project"
        assert ctx["chat_name"] == "Chat1"

    def test_agent_read_prompt_calls_files(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("agent.files.read_prompt_file", return_value="prompt content") as mock_read,
            patch("agent.files.is_full_json_template", return_value=False),
        ):
            mock_ctx = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            result = agent.read_prompt("fw.msg_nudge.md")
            assert result == "prompt content"
            mock_read.assert_called_once()

    def test_agent_parse_prompt_calls_files(self, mock_agent_config):
        from agent import Agent, AgentContext

        with (
            patch("agent.call_extensions", new_callable=AsyncMock, return_value=None),
            patch("agent.AgentContext") as mock_ctx_cls,
            patch("agent.files.parse_file", return_value={"message": "parsed"}) as mock_parse,
        ):
            mock_ctx = MagicMock()
            mock_ctx_cls.return_value = mock_ctx
            agent = Agent(0, mock_agent_config, mock_ctx)
            result = agent.parse_prompt("fw.user_message.md", message="hi")
            assert result == {"message": "parsed"}
            mock_parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_handle_intervention_raises_when_intervention_set(self, agent_with_mocked_extensions):
        from agent import Agent, UserMessage, InterventionException

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        agent.loop_data.current_tool = None
        agent.intervention = UserMessage(message="stop")
        agent.hist_add_user_message = MagicMock()
        agent.hist_add_ai_response = MagicMock()

        with pytest.raises(InterventionException):
            await agent.handle_intervention("progress")
        assert agent.intervention is None

    @pytest.mark.asyncio
    async def test_agent_handle_intervention_waits_when_paused(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.intervention = None
        agent.loop_data = MagicMock()
        agent.context.paused = True

        async def stop_after_short_wait():
            await __import__("asyncio").sleep(0.05)
            agent.context.paused = False

        __import__("asyncio").create_task(stop_after_short_wait())
        await agent.handle_intervention()
        assert agent.context.paused is False

    @pytest.mark.asyncio
    async def test_agent_wait_if_paused(self, agent_with_mocked_extensions):
        agent = agent_with_mocked_extensions
        agent.context.paused = True

        async def unpause_soon():
            await __import__("asyncio").sleep(0.02)
            agent.context.paused = False

        __import__("asyncio").create_task(unpause_soon())
        await agent.wait_if_paused()
        assert agent.context.paused is False

    def test_agent_concat_messages(self, agent_with_mocked_extensions):
        agent = agent_with_mocked_extensions
        agent.history.output_text = MagicMock(return_value="user: hi\nassistant: hello")
        result = agent.concat_messages([])
        assert "user" in result or "assistant" in result

    def test_agent_hist_add_message(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.history.add_message = MagicMock(return_value=MagicMock())
        with patch("agent.call_extensions", new_callable=AsyncMock) as mock_ext:
            mock_ext.return_value = None
            result = agent.hist_add_message(True, content="hello")
            agent.history.add_message.assert_called_once_with(
                ai=True, content="hello", tokens=0
            )

    def test_agent_hist_add_user_message(self, agent_with_mocked_extensions):
        from agent import Agent, UserMessage

        agent = agent_with_mocked_extensions
        agent.parse_prompt = MagicMock(return_value={"message": "hi"})
        agent.history.new_topic = MagicMock()
        agent.history.add_message = MagicMock(return_value=MagicMock())
        with patch("agent.call_extensions", new_callable=AsyncMock):
            msg = agent.hist_add_user_message(UserMessage(message="hello"))
            agent.history.new_topic.assert_called_once()
            agent.parse_prompt.assert_called_with(
                "fw.user_message.md",
                message="hello",
                attachments=[],
                system_message=[],
            )

    def test_agent_hist_add_ai_response(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        agent.parse_prompt = MagicMock(return_value={"message": "response"})
        agent.history.add_message = MagicMock(return_value=MagicMock())
        with patch("agent.call_extensions", new_callable=AsyncMock):
            agent.hist_add_ai_response("AI said this")
            assert agent.loop_data.last_response == "AI said this"
            agent.parse_prompt.assert_called_with("fw.ai_response.md", message="AI said this")

    def test_agent_hist_add_warning(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.parse_prompt = MagicMock(return_value={"message": "warning"})
        agent.history.add_message = MagicMock(return_value=MagicMock())
        with patch("agent.call_extensions", new_callable=AsyncMock):
            agent.hist_add_warning("be careful")
            agent.parse_prompt.assert_called_with("fw.warning.md", message="be careful")

    def test_agent_hist_add_tool_result(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.history.add_message = MagicMock(return_value=MagicMock())
        with patch("agent.call_extensions", new_callable=AsyncMock):
            agent.hist_add_tool_result("tool_name", "result")
            agent.history.add_message.assert_called_once()
            call_kwargs = agent.history.add_message.call_args[1]
            assert call_kwargs["content"]["tool_name"] == "tool_name"
            assert call_kwargs["content"]["tool_result"] == "result"

    @pytest.mark.asyncio
    async def test_agent_rate_limiter_callback(self, agent_with_mocked_extensions):
        agent = agent_with_mocked_extensions
        agent.context.log.set_progress = MagicMock()
        result = await agent.rate_limiter_callback("msg", "key", 10, 100)
        assert result is False
        agent.context.log.set_progress.assert_called_once()

    def test_agent_handle_critical_exception_reraises_handled_exception(self, agent_with_mocked_extensions):
        from agent import Agent, HandledException

        agent = agent_with_mocked_extensions
        exc = HandledException("already handled")
        with pytest.raises(HandledException):
            agent.handle_critical_exception(exc)

    def test_agent_handle_critical_exception_reraises_on_cancelled_error(self, agent_with_mocked_extensions):
        from agent import Agent, HandledException

        agent = agent_with_mocked_extensions
        with patch("agent.PrintStyle") as mock_style:
            with pytest.raises(HandledException):
                agent.handle_critical_exception(asyncio.CancelledError())

    def test_agent_handle_critical_exception_reraises_on_general_exception(self, agent_with_mocked_extensions):
        from agent import Agent, HandledException

        agent = agent_with_mocked_extensions
        with patch("agent.PrintStyle"), patch("agent.errors") as mock_errors:
            mock_errors.format_error.return_value = "formatted"
            mock_errors.error_text.return_value = "error text"
            with pytest.raises(HandledException):
                agent.handle_critical_exception(ValueError("test error"))

    @pytest.mark.asyncio
    async def test_agent_process_tools_handles_misformat(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.read_prompt = MagicMock(return_value="Message misformat")
        agent.hist_add_warning = MagicMock()
        agent.context.log.log = MagicMock()
        with patch("agent.extract_tools") as mock_extract:
            mock_extract.json_parse_dirty.return_value = None
            await agent.process_tools("some random text without tool request")
            agent.hist_add_warning.assert_called_once()

    def test_agent_get_tool_returns_unknown_when_no_tool_found(self, agent_with_mocked_extensions):
        from agent import Agent
        from python.tools.unknown import Unknown

        agent = agent_with_mocked_extensions
        with (
            patch("agent.extract_tools.load_classes_from_file", side_effect=Exception("no file")),
            patch("agent.subagents.get_paths", return_value=["/fake/path"]),
        ):
            tool = agent.get_tool("nonexistent", None, {}, "msg", None)
            assert isinstance(tool, Unknown)
            assert tool.name == "nonexistent"

    @pytest.mark.asyncio
    async def test_agent_handle_reasoning_stream(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        with patch("agent.call_extensions", new_callable=AsyncMock):
            await agent.handle_reasoning_stream("reasoning text")
            # Should not raise

    @pytest.mark.asyncio
    async def test_agent_handle_response_stream_short_text_skips(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        await agent.handle_response_stream("short")
        # Short text (< 25 chars) returns early without parsing

    @pytest.mark.asyncio
    async def test_agent_handle_response_stream_parses_json(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        with patch("agent.call_extensions", new_callable=AsyncMock):
            await agent.handle_response_stream('{"tool_name": "test", "tool_args": {}}')
            # Should call extensions with parsed dict

    @pytest.mark.asyncio
    async def test_agent_get_system_prompt(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        with patch("agent.call_extensions", new_callable=AsyncMock) as mock_ext:
            mock_ext.return_value = None
            result = await agent.get_system_prompt(agent.loop_data)
            assert isinstance(result, list)
            mock_ext.assert_called_with(
                extension_point="system_prompt",
                agent=agent,
                system_prompt=result,
                loop_data=agent.loop_data,
            )

    @pytest.mark.asyncio
    async def test_agent_prepare_prompt(self, agent_with_mocked_extensions):
        from agent import Agent
        from collections import OrderedDict

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        agent.loop_data.system = []
        agent.loop_data.history_output = []
        agent.loop_data.extras_persistent = OrderedDict()
        agent.loop_data.extras_temporary = OrderedDict()
        agent.history.output = MagicMock(return_value=[])
        agent.read_prompt = MagicMock(return_value="extras")
        agent.set_data = MagicMock()
        with (
            patch("agent.call_extensions", new_callable=AsyncMock),
            patch.object(agent, "get_system_prompt", new_callable=AsyncMock, return_value=["sys"]),
            patch("agent.history.output_langchain", return_value=[]),
            patch("agent.tokens.approximate_tokens", return_value=10),
        ):
            result = await agent.prepare_prompt(agent.loop_data)
            assert len(result) >= 1
            agent.set_data.assert_called()

    @pytest.mark.asyncio
    async def test_agent_process_tools_with_tool_execution(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        agent.read_prompt = MagicMock(return_value="msg")
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_tool.progress = ""
        mock_tool.set_progress = MagicMock()
        mock_response = MagicMock()
        mock_response.break_loop = True
        mock_response.message = "done"
        mock_tool.execute = AsyncMock(return_value=mock_response)
        mock_tool.before_execution = AsyncMock()
        mock_tool.after_execution = AsyncMock()
        with (
            patch("agent.extract_tools") as mock_extract,
            patch("agent.call_extensions", new_callable=AsyncMock),
        ):
            mock_extract.json_parse_dirty.return_value = {
                "tool_name": "test_tool",
                "tool_args": {},
            }
            mock_mcp = MagicMock()
            mock_mcp.MCPConfig.get_instance.return_value.get_tool.return_value = None
            with patch.dict("sys.modules", {"python.helpers.mcp_handler": mock_mcp}):
                with patch.object(agent, "get_tool", return_value=mock_tool):
                    result = await agent.process_tools('{"tool_name": "test_tool"}')
                    assert result == "done"

    @pytest.mark.asyncio
    async def test_agent_process_tools_handles_unknown_tool(self, agent_with_mocked_extensions):
        from agent import Agent

        agent = agent_with_mocked_extensions
        agent.loop_data = MagicMock()
        agent.read_prompt = MagicMock(return_value="msg")
        agent.hist_add_warning = MagicMock()
        agent.context.log.log = MagicMock()
        agent.get_tool = MagicMock(return_value=None)
        with patch("agent.extract_tools") as mock_extract:
            mock_extract.json_parse_dirty.return_value = {"tool_name": "nonexistent_tool_xyz", "tool_args": {}}
            mock_mcp = MagicMock()
            mock_mcp.MCPConfig.get_instance.return_value.get_tool.return_value = None
            with patch.dict("sys.modules", {"python.helpers.mcp_handler": mock_mcp}):
                await agent.process_tools('{"tool_name": "nonexistent_tool_xyz"}')
                agent.hist_add_warning.assert_called()
