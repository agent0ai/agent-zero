"""Tests for python/tools/input.py — Input tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from python.tools.input import Input
except (ImportError, AttributeError) as e:
    pytest.skip(f"Failed to import input tool: {e}", allow_module_level=True)


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.handle_intervention = AsyncMock()
    agent.read_prompt = MagicMock(return_value="No output")
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    t = Input(
        agent=mock_agent,
        name="input",
        method=None,
        args={"keyboard": "yes\n", "session": 0},
        message="",
        loop_data=None,
    )
    t.log = MagicMock()
    return t


class TestInputExecute:
    @pytest.mark.asyncio
    async def test_forwards_to_code_execution(self, tool):
        from python.helpers.tool import Response
        with patch("python.tools.input.CodeExecution") as MockCET:
            mock_cet = MagicMock()
            mock_cet.execute = AsyncMock(return_value=Response(message="yes", break_loop=False))
            MockCET.return_value = mock_cet
            resp = await tool.execute(keyboard="yes")
        MockCET.assert_called_once()
        call_args = MockCET.call_args[0]
        args_dict = call_args[3]
        assert call_args[2] == ""  # method
        assert args_dict["runtime"] == "terminal"
        assert args_dict["allow_running"] is True
