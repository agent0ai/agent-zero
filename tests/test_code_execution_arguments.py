from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from helpers.errors import RepairableException
from plugins._code_execution.tools import code_execution_tool as code


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime", ["terminal", "python", "nodejs"])
@pytest.mark.parametrize("arguments", [
    {}, {"code": None}, {"code": ["echo hi"]}, {"code": 42},
    {"code": {"command": "echo hi"}},
])
async def test_invalid_code_is_repairable_before_shell_setup(monkeypatch, runtime, arguments):
    tool = object.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(handle_intervention=AsyncMock())
    tool.args = {"runtime": runtime, "reset": True, **arguments}
    configure = Mock()
    monkeypatch.setattr(code.plugins, "get_plugin_config", configure)
    resolve = AsyncMock()
    monkeypatch.setattr(code, "resolve_code_execution_destination", resolve)
    tool.terminal_session = AsyncMock(
        side_effect=AssertionError("invalid code must not reach a shell")
    )

    with pytest.raises(RepairableException, match="code.*string"):
        await tool._execute(None)

    resolve.assert_not_awaited()
    configure.assert_not_called()
    tool.terminal_session.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime,method", [
    ("terminal", "execute_terminal_command"),
    ("python", "execute_python_code"),
    ("nodejs", "execute_nodejs_code"),
    ("output", "get_terminal_output"),
    ("reset", "reset_terminal"),
])
async def test_valid_dispatch_keeps_code_and_session_controls(monkeypatch, runtime, method):
    tool = object.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(handle_intervention=AsyncMock())
    tool.args = {"runtime": runtime, "session": 2, "reset": True}
    if runtime in {"terminal", "python", "nodejs"}:
        tool.args["code"] = "first line\nsecond line"
    config = {"output_first_output_timeout": 1}
    cfg = code._parse_config(config)
    monkeypatch.setattr(code.plugins, "get_plugin_config", Mock(return_value=config))
    destination = code.ExecutionDestination("default", "sandbox", "Default sandbox", "")
    resolve = AsyncMock(return_value=destination)
    monkeypatch.setattr(code, "resolve_code_execution_destination", resolve)
    dispatch = AsyncMock(return_value="done")
    setattr(tool, method, dispatch)

    response = await tool._execute(None)

    resolve.assert_awaited_once_with(tool.agent, "default")
    assert response.message == "done"
    assert response.break_loop is False
    expected = {"session": 2}
    if runtime in {"terminal", "python", "nodejs"}:
        expected["command" if runtime == "terminal" else "code"] = tool.args["code"]
        expected["reset"] = True
    elif runtime == "output":
        expected["timeouts"] = cfg["output_timeouts"]
    if runtime == "reset":
        dispatch.assert_awaited_once_with(**expected)
    else:
        dispatch.assert_awaited_once_with(cfg, **expected)
