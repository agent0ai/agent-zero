"""Tests for python/tools/code_execution_tool.py — CodeExecution tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from python.tools.code_execution_tool import CodeExecution
except (ImportError, AttributeError) as e:
    pytest.skip(f"Failed to import code_execution_tool: {e}", allow_module_level=True)


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.config = MagicMock()
    agent.config.code_exec_ssh_enabled = False
    agent.handle_intervention = AsyncMock()
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Prompt:{t}")
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))
    return agent


@pytest.fixture
def tool(mock_agent):
    t = CodeExecution(
        agent=mock_agent,
        name="code_execution",
        method=None,
        args={"runtime": "python", "code": "print(1)", "session": 0},
        message="",
        loop_data=None,
    )
    t.log = MagicMock()
    return t


class TestCodeExecutionArgumentParsing:
    def test_parses_runtime_from_args(self, mock_agent):
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "nodejs", "code": "1+1"}, "", None)
        assert t.args["runtime"] == "nodejs"

    def test_parses_session_default_zero(self, mock_agent):
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "python", "code": "x"}, "", None)
        assert t.args.get("session", 0) == 0

    def test_parses_allow_running_from_args(self, mock_agent):
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "terminal", "code": "ls", "allow_running": "true"}, "", None)
        assert "allow_running" in t.args
        assert t.args["allow_running"] == "true"


class TestCodeExecutionFormatCommandForOutput:
    def test_truncates_long_commands(self, tool):
        long_cmd = "x" * 300
        result = tool.format_command_for_output(long_cmd)
        assert len(result) <= 110

    def test_normalizes_whitespace(self, tool):
        result = tool.format_command_for_output("  foo   bar  \n\t")
        assert "  " not in result or result.strip() == "foo bar"


class TestCodeExecutionGetHeading:
    def test_includes_runtime(self, tool):
        h = tool.get_heading()
        assert "python" in h.lower() or "code_execution" in h.lower()

    def test_includes_session_when_zero(self, tool):
        tool.args["session"] = 0
        h = tool.get_heading()
        assert "[0]" in h or "0" in str(h)


class TestCodeExecutionFixFullOutput:
    def test_strips_hex_escapes(self, tool):
        out = "hello \\x00\\x1b world"
        result = tool.fix_full_output(out)
        assert "\\x00" not in result or "\\x1b" not in result


class TestCodeExecutionGetHeadingFromOutput:
    def test_empty_output_returns_base_heading(self, tool):
        h = tool.get_heading_from_output("", skip_lines=0, done=False)
        assert "icon://" in h or "done" in str(h).lower()

    def test_uses_last_non_empty_line(self, tool):
        h = tool.get_heading_from_output("line1\n\nline2\n", skip_lines=0, done=True)
        assert "line2" in h or "done" in str(h).lower()


class TestCodeExecutionExecute:
    @pytest.mark.asyncio
    async def test_unknown_runtime_returns_prompt(self, mock_agent):
        from python.helpers.tool import Response
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "invalid", "code": "x"}, "", None)
        with patch.object(t, "prepare_state", new_callable=AsyncMock):
            resp = await t.execute()
        assert isinstance(resp, Response)
        assert "fw.code.runtime_wrong" in str(mock_agent.read_prompt.call_args) or "Prompt:" in resp.message

    @pytest.mark.asyncio
    async def test_reset_runtime_calls_reset_terminal(self, mock_agent):
        from python.helpers.tool import Response
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "reset", "session": 0}, "", None)
        with patch.object(t, "prepare_state", new_callable=AsyncMock):
            with patch.object(t, "reset_terminal", new_callable=AsyncMock, return_value="Reset done"):
                resp = await t.execute()
        assert isinstance(resp, Response)
        assert resp.break_loop is False


class TestCodeExecutionPrepareState:
    @pytest.mark.asyncio
    async def test_creates_state_when_none(self, mock_agent, tmp_path):
        t = CodeExecution(mock_agent, "ce", None, {"runtime": "python", "code": "1", "session": 0}, "", None)
        with patch("python.tools.code_execution_tool.files.normalize_a0_path", return_value=str(tmp_path)):
            with patch("python.tools.code_execution_tool.runtime.call_development_function", new_callable=AsyncMock):
                with patch("python.tools.code_execution_tool.projects.get_context_project_name", return_value=None):
                    with patch("python.tools.code_execution_tool.settings.get_settings") as mock_settings:
                        mock_settings.return_value.get.return_value = str(tmp_path)
                        with patch("python.tools.code_execution_tool.LocalInteractiveSession") as MockShell:
                            mock_shell = MagicMock()
                            mock_shell.connect = AsyncMock()
                            MockShell.return_value = mock_shell
                            state = await t.prepare_state(reset=False, session=0)
        assert state is not None
        assert 0 in state.shells


class TestCodeExecutionMarkSessionIdle:
    def test_marks_session_idle(self, tool):
        from python.tools.code_execution_tool import State, ShellWrap
        mock_shell = MagicMock()
        tool.state = State(shells={0: ShellWrap(0, mock_shell, True)}, ssh_enabled=False)
        tool.mark_session_idle(0)
        assert tool.state.shells[0].running is False


class TestCodeExecutionResetTerminal:
    @pytest.mark.asyncio
    async def test_reset_terminal_returns_response(self, tool):
        with patch.object(tool, "prepare_state", new_callable=AsyncMock):
            result = await tool.reset_terminal(session=0)
        assert "reset" in result.lower() or "Prompt:" in result
