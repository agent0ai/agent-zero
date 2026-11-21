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
    configure = Mock(return_value={"ssh_enabled": False})
    monkeypatch.setattr(code, "_get_config", configure)
    tool.terminal_session = AsyncMock(
        side_effect=AssertionError("invalid code must not reach a shell")
    )

    with pytest.raises(RepairableException, match="code.*string"):
        await tool._execute(None)

    configure.assert_not_called()
    tool.terminal_session.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime", [None, 1, ["terminal"], {"name": "terminal"}, True])
async def test_wrong_runtime_type_falls_back_to_unknown_runtime_prompt(monkeypatch, runtime):
    tool = object.__new__(code.CodeExecution)
    read_prompt = Mock(return_value="wrong runtime")
    tool.agent = SimpleNamespace(
        handle_intervention=AsyncMock(),
        read_prompt=read_prompt,
    )
    tool.args = {"runtime": runtime, "code": "echo hi"}
    monkeypatch.setattr(code, "_get_config", lambda _: {"output_timeouts": {}})
    tool.terminal_session = AsyncMock(
        side_effect=AssertionError("wrong runtime must not reach a shell")
    )

    response = await tool._execute(None)

    assert response.message == "wrong runtime"
    assert response.break_loop is False
    read_prompt.assert_called_once()
    assert read_prompt.call_args.args[0] == "fw.code.runtime_wrong.md"
    assert read_prompt.call_args.kwargs["runtime"] == (
        "" if runtime is None else str(runtime).strip().lower()
    )
    tool.terminal_session.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("session", ["abc", [1], {"index": 1}, True])
async def test_invalid_session_type_is_repairable_before_shell_setup(monkeypatch, session):
    tool = object.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(
        handle_intervention=AsyncMock(),
        read_prompt=Mock(return_value="wrong runtime"),
    )
    tool.args = {"runtime": "terminal", "code": "echo hi", "session": session}
    configure = Mock(side_effect=AssertionError("invalid session must not configure a shell"))
    monkeypatch.setattr(code, "_get_config", configure)
    tool.terminal_session = AsyncMock(
        side_effect=AssertionError("invalid session must not reach a shell")
    )

    with pytest.raises(RepairableException, match="session.*integer"):
        await tool._execute(None)

    configure.assert_not_called()
    tool.terminal_session.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("session,expected", [(None, 0), ("", 0), ("3", 3), (4, 4)])
async def test_session_argument_accepts_missing_and_numeric_values(monkeypatch, session, expected):
    tool = object.__new__(code.CodeExecution)
    tool.agent = SimpleNamespace(handle_intervention=AsyncMock())
    tool.args = {"runtime": "reset", "session": session}
    monkeypatch.setattr(code, "_get_config", lambda _: {"output_timeouts": {}})
    reset = AsyncMock(return_value="reset done")
    tool.reset_terminal = reset

    response = await tool._execute(None)

    assert response.message == "reset done"
    reset.assert_awaited_once_with({"output_timeouts": {}}, session=expected)


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
    cfg = {"output_timeouts": {"first_output_timeout": 1}}
    monkeypatch.setattr(code, "_get_config", lambda _: cfg)
    dispatch = AsyncMock(return_value="done")
    setattr(tool, method, dispatch)

    response = await tool._execute(None)

    assert response.message == "done"
    assert response.break_loop is False
    expected = {"session": 2}
    if runtime in {"terminal", "python", "nodejs"}:
        expected["command" if runtime == "terminal" else "code"] = tool.args["code"]
        expected["reset"] = True
    elif runtime == "output":
        expected["timeouts"] = cfg["output_timeouts"]
    dispatch.assert_awaited_once_with(cfg, **expected)
