import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from helpers import parallel_tools
from plugins._code_execution.tools import code_execution_tool as code


@pytest.mark.asyncio
@pytest.mark.parametrize("parallel,cancel", [(False, False), (True, False), (True, True)])
async def test_code_job_keeps_polling_after_output_timeout_without_reexecuting(monkeypatch, parallel, cancel):
    shell = SimpleNamespace(running=True, session=SimpleNamespace(close=AsyncMock()))
    job = SimpleNamespace(result=None) if parallel else None
    agent = SimpleNamespace(handle_intervention=AsyncMock())
    tool = object.__new__(code.CodeExecution)
    tool.agent = agent
    tool.args = {"runtime": "terminal", "session": 0, "code": "long command"}
    tool.state = SimpleNamespace(shells={0: shell})
    cfg = {"output_timeouts": {"first_output_timeout": 1}}
    monkeypatch.setattr(code, "_get_config", lambda _: cfg)
    monkeypatch.setattr(parallel_tools, "get_parallel_worker_job", lambda _: job)
    tool.execute_terminal_command = AsyncMock(return_value="START; output timeout")

    async def poll(*args, **kwargs):
        assert job.result == "START; output timeout"
        if cancel:
            raise asyncio.CancelledError()
        shell.running = False
        return "START; DONE"

    tool.get_terminal_output = AsyncMock(side_effect=poll)
    if cancel:
        with pytest.raises(asyncio.CancelledError):
            await tool.execute()
    else:
        result = await tool.execute()
        assert result.message == ("START; DONE" if parallel else "START; output timeout")
    tool.execute_terminal_command.assert_awaited_once()
    if parallel:
        tool.get_terminal_output.assert_awaited_once_with(
            cfg, session=0, reset_full_output=False, timeouts=cfg["output_timeouts"],
        )
        shell.session.close.assert_awaited_once()
    else:
        tool.get_terminal_output.assert_not_called()
        shell.session.close.assert_not_called()


@pytest.mark.parametrize("tool_name,args", [
    ("input", {"session": 0, "keyboard": "yes"}),
    ("input_remote", {"session": 0, "keyboard": "yes"}),
    ("code_execution_remote", {"runtime": "output", "session": 0}),
    ("code_execution_remote", {"runtime": "reset", "session": 0}),
    ("code_execution_tool", {"runtime": "output", "session": 0}),
    ("code_execution_tool", {"runtime": " RESET ", "session": 0}),
])
def test_parallel_session_followups_cannot_open_unrelated_workers(tool_name, args):
    with pytest.raises(ValueError, match="sequentially"):
        parallel_tools.normalize_parallel_tool_calls([{"tool": tool_name, "args": args}])


@pytest.mark.asyncio
async def test_cancelled_shell_connection_closes_partial_resources(monkeypatch):
    shell = SimpleNamespace(connect=AsyncMock(side_effect=asyncio.CancelledError()), close=AsyncMock())
    monkeypatch.setattr(code, "LocalInteractiveSession", lambda **kwargs: shell)
    tool = object.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(get_data=lambda _: None)
    tool.ensure_cwd = AsyncMock(return_value=None)
    with pytest.raises(asyncio.CancelledError):
        await tool.prepare_state({"ssh_enabled": False}, session=0)
    shell.close.assert_awaited_once()
