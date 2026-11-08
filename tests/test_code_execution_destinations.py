from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from plugins._code_execution.helpers import destinations as destination_helper
from plugins._code_execution.helpers.destinations import ExecutionDestination
from plugins._code_execution.tools import input as input_tool_module
from plugins._code_execution.tools.code_execution_tool import CodeExecution, State
from plugins._sandboxing.extensions.python.code_execution_destinations import (
    _10_sandboxes as sandbox_extension,
)
from plugins._sandboxing.extensions.python.code_execution_destinations import (
    _20_host as host_extension,
)


def test_named_missing_destination_is_lazy_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    async def only_local(agent):
        return [ExecutionDestination("local", "local", "Local", "Local")]

    monkeypatch.setattr(destination_helper, "get_code_execution_destinations", only_local)
    result = asyncio.run(
        destination_helper.resolve_code_execution_destination(None, "research")
    )
    assert result.kind == "sandbox"
    assert result.target == "research"
    assert result.status == "missing"


def test_unavailable_reserved_destinations_do_not_create_same_named_sandbox(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def only_local(agent):
        return [ExecutionDestination("local", "local", "Local", "Local")]

    monkeypatch.setattr(destination_helper, "get_code_execution_destinations", only_local)
    with pytest.raises(ValueError, match="not currently available"):
        asyncio.run(destination_helper.resolve_code_execution_destination(None, "host"))


def test_sandbox_extension_advertises_default_and_all_managed_sandboxes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sandbox_extension, "defaults", lambda agent=None: ("default", "temporary", "host"))
    monkeypatch.setattr(
        sandbox_extension,
        "get_manager",
        lambda agent=None: SimpleNamespace(
            list=lambda: [
                SimpleNamespace(name="default", sandbox_type="temporary", network="host", status="running"),
                SimpleNamespace(name="research", sandbox_type="permanent", network="none", status="stopped"),
            ]
        ),
    )
    values = [ExecutionDestination("local", "local", "Local", "Local")]
    asyncio.run(sandbox_extension.IncludeSandboxDestinations(None).execute(values))
    assert [value.id for value in values] == ["default", "local", "research"]
    assert values[-1].target == "research"
    assert values[-1].status == "stopped"


def test_host_extension_only_advertises_enabled_connector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import plugins._a0_connector.helpers.remote_tool_prompts as prompts

    agent = SimpleNamespace(context=SimpleNamespace(id="chat-1"))
    values: list[ExecutionDestination] = []
    monkeypatch.setattr(
        prompts,
        "remote_tool_prompt_availability",
        lambda context_id: {"code_execution_remote": False},
    )
    host_extension.IncludeConnectedHostDestination(agent).execute(values)
    assert values == []
    monkeypatch.setattr(
        prompts,
        "remote_tool_prompt_availability",
        lambda context_id: {"code_execution_remote": True},
    )
    host_extension.IncludeConnectedHostDestination(agent).execute(values)
    assert [(value.id, value.kind) for value in values] == [("host", "host")]


def test_code_execution_session_keys_include_destination() -> None:
    tool = object.__new__(CodeExecution)
    tool.destination = ExecutionDestination(
        "default", "sandbox", "Default", "Default sandbox", target="default"
    )
    tool.state = State(ssh_enabled=False, shells={})
    assert tool._session_key(0) == "default:0"
    tool.destination = ExecutionDestination("local", "local", "Local", "Local")
    assert tool._session_key(0) == 0


def test_local_python_execution_uses_depfix_store_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = object.__new__(CodeExecution)
    tool.destination = ExecutionDestination("local", "local", "Local", "Local")

    async def capture(_cfg, _session, command, _reset, _prefix):
        return command

    monkeypatch.setattr(tool, "terminal_session", capture)
    monkeypatch.setattr(tool, "format_command_for_output", lambda command: command)
    command = asyncio.run(tool.execute_python_code({}, 0, "import flask"))

    assert command == "depfix run -m IPython -- -c 'import flask'"


def test_input_uses_connector_input_operation_for_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCodeExecution:
        def __init__(self, agent, name, method, args, message, loop_data):
            captured["args"] = args
            self.log = None

        async def execute(self, **kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(message="ok")

    monkeypatch.setattr(input_tool_module, "CodeExecution", FakeCodeExecution)
    tool = object.__new__(input_tool_module.Input)
    tool.args = {"destination": "host", "session": 4}
    tool.agent = SimpleNamespace()
    tool.message = None
    tool.loop_data = None
    tool.log = None

    asyncio.run(tool.execute(keyboard="Y"))

    assert captured["args"] == {
        "runtime": "input",
        "keyboard": "Y",
        "session": 4,
        "destination": "host",
    }
