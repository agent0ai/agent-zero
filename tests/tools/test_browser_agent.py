"""Tests for python/tools/browser_agent.py — BrowserAgent tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def patch_browser_use_config(tmp_path):
    """Patch browser_use config dir to avoid PermissionError in sandbox."""
    import os
    prev = os.environ.get("BROWSER_USE_CONFIG_DIR")
    os.environ["BROWSER_USE_CONFIG_DIR"] = str(tmp_path / "browseruse")
    yield
    if prev is not None:
        os.environ["BROWSER_USE_CONFIG_DIR"] = prev
    else:
        os.environ.pop("BROWSER_USE_CONFIG_DIR", None)


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.handle_intervention = AsyncMock()
    agent.config = MagicMock()
    agent.config.browser_model = MagicMock()
    agent.config.browser_model.vision = True
    agent.config.browser_http_headers = {}
    agent.context = MagicMock()
    agent.context.id = "test-ctx-001"
    agent.context.generate_id = MagicMock(return_value="guid-123")
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))
    agent.context.task = None
    agent.read_prompt = MagicMock(return_value="System prompt")
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.browser_agent import BrowserAgent
    return BrowserAgent(
        agent=mock_agent,
        name="browser_agent",
        method=None,
        args={"message": "Go to example.com", "reset": "false"},
        message="",
        loop_data=None,
    )


class TestBrowserAgentInit:
    def test_stores_args(self, tool):
        assert tool.args["message"] == "Go to example.com"
        assert tool.name == "browser_agent"


class TestBrowserAgentGetLogObject:
    def test_returns_log_with_browser_type(self, tool):
        log = tool.get_log_object()
        mock_agent = tool.agent
        mock_agent.context.log.log.assert_called_once()
        call_kw = mock_agent.context.log.log.call_args[1]
        assert call_kw.get("type") == "browser"


class TestBrowserAgentPrepareState:
    @pytest.mark.asyncio
    async def test_creates_state_when_none(self, tool):
        with patch("python.tools.browser_agent.State.create", new_callable=AsyncMock) as mock_create:
            mock_state = MagicMock()
            mock_create.return_value = mock_state
            await tool.prepare_state(reset=False)
        assert tool.state is mock_state
        tool.agent.set_data.assert_called_with("_browser_agent_state", mock_state)


class TestBrowserAgentUpdateProgress:
    def test_updates_log_and_context(self, tool):
        tool.log = MagicMock(update=MagicMock())
        tool.agent.context.log.set_progress = MagicMock()
        with patch("python.tools.browser_agent.get_secrets_manager") as mock_sm:
            mock_sm.return_value.mask_values = lambda x: x
            tool.update_progress("Loading page...")
        tool.log.update.assert_called()
        tool.agent.context.log.set_progress.assert_called()


class TestBrowserAgentMask:
    def test_masks_secrets(self, tool):
        with patch("python.tools.browser_agent.get_secrets_manager") as mock_sm:
            mock_sm.return_value.mask_values = lambda t: t.replace("secret", "***")
            result = tool._mask("password is secret")
        assert "***" in result

    def test_returns_empty_for_none(self, tool):
        with patch("python.tools.browser_agent.get_secrets_manager") as mock_sm:
            mock_sm.return_value.mask_values = lambda t: t or ""
            result = tool._mask(None)
        assert result == ""


class TestBrowserAgentExecute:
    @pytest.mark.asyncio
    async def test_execute_returns_response_on_timeout(self, tool):
        mock_state = MagicMock()
        mock_task = MagicMock()
        mock_task.is_ready = MagicMock(return_value=False)
        mock_state.start_task = MagicMock(return_value=mock_task)
        mock_state.use_agent = None
        mock_state.kill_task = MagicMock()

        async def mock_prepare_state(**kwargs):
            tool.state = mock_state

        with patch.object(tool, "prepare_state", new_callable=AsyncMock, side_effect=mock_prepare_state):
            with patch("python.tools.browser_agent.get_secrets_manager") as mock_sm:
                mock_sm.return_value.mask_values = lambda x, **kw: x
                with patch("python.tools.browser_agent.time.time", side_effect=[0, 400]):
                    resp = await tool.execute(message="test", reset="false")
        from python.helpers.tool import Response
        assert isinstance(resp, Response)
        assert resp.break_loop is False


class TestGetUseAgentLog:
    def test_returns_starting_when_no_agent(self):
        from python.tools.browser_agent import get_use_agent_log
        result = get_use_agent_log(None)
        assert "Starting" in result[0] or "🚦" in str(result)

    def test_includes_action_results_when_agent(self):
        from python.tools.browser_agent import get_use_agent_log
        mock_agent = MagicMock()
        mock_result = MagicMock()
        mock_result.is_done = True
        mock_result.success = True
        mock_result.error = None
        mock_result.extracted_content = None
        mock_agent.history = MagicMock()
        mock_agent.history.action_results = MagicMock(return_value=[mock_result])
        result = get_use_agent_log(mock_agent)
        assert len(result) >= 1
