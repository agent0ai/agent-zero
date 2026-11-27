from __future__ import annotations

import asyncio
import shlex
import sys
from types import SimpleNamespace

import pytest

from helpers import runtime
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
                SimpleNamespace(service=False, name="default", sandbox_type="temporary", network="host", status="running"),
                SimpleNamespace(service=False, name="research", sandbox_type="permanent", network="none", status="stopped"),
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
    tool.state = State(shells={})
    assert tool._session_key(0) == "default:0"
    tool.destination = ExecutionDestination("local", "local", "Local", "Local")
    assert tool._session_key(0) == 0


@pytest.mark.parametrize("destination,windows", [
    ("local", False), ("sandbox", False), ("local", True),
])
def test_python_execution_uses_destination_interpreter(
    monkeypatch: pytest.MonkeyPatch, destination: str, windows: bool,
) -> None:
    tool = object.__new__(CodeExecution)
    tool.destination = ExecutionDestination(destination, destination, destination, destination)
    monkeypatch.setattr(sys, "executable", "/runtime with spaces/bin/python")
    monkeypatch.setattr(runtime, "is_windows", lambda: windows)

    async def capture(_cfg, _session, command, _reset, _prefix):
        return command

    monkeypatch.setattr(tool, "terminal_session", capture)
    monkeypatch.setattr(tool, "format_command_for_output", lambda command: command)
    command = asyncio.run(tool.execute_python_code({}, 0, "import flask"))

    assert shlex.split(command) == (
        [sys.executable, "-m", "IPython"]
        if destination == "local" and not windows else ["ipython"]
    ) + ["-c", "import flask"]


def test_host_input_reuses_terminal_transport_without_model_supplied_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeCodeExecution:
        def __init__(self, agent, name, method, args, message, loop_data):
            captured["args"] = args
            self.log = None

        async def execute(self, **kwargs):
            captured["kwargs"] = kwargs
            captured["allow_running"] = self.allow_running
            return SimpleNamespace(message="ok")

    monkeypatch.setattr(input_tool_module, "CodeExecution", FakeCodeExecution)
    tool = object.__new__(input_tool_module.Input)
    tool.args = {"destination": "host", "session": 4}
    from helpers import tool_policy
    monkeypatch.setattr(tool_policy, "ensure_tool_allowed", lambda *args, **kwargs: None)
    monkeypatch.setattr(tool_policy, "ensure_retired_host_tool_allowed", lambda *args, **kwargs: None)
    tool.agent = SimpleNamespace()
    tool.message = None
    tool.loop_data = None
    tool.log = None

    asyncio.run(tool.execute(keyboard="Y"))

    assert captured["args"] == {
        "runtime": "terminal",
        "code": "Y",
        "session": 4,
        "destination": "host",
    }
    assert captured["allow_running"] is True


@pytest.mark.parametrize(
    "destination, session, expected",
    [
        (ExecutionDestination("default", "sandbox", "Default", "", target="work"), None, ("Sandbox work", 0)),
        (ExecutionDestination("research", "sandbox", "Research", "", target="research"), 3, ("Sandbox research", 3)),
        (ExecutionDestination("local", "local", "Agent Zero system", ""), 0, ("Agent Zero system", 0)),
    ],
)
def test_execution_logs_resolved_destination_and_session(monkeypatch, destination, session, expected):
    from helpers.log import Log
    from plugins._code_execution.tools import code_execution_tool

    async def resolve(agent, requested):
        return destination

    async def execute_terminal(*args, **kwargs):
        return "done"

    agent = SimpleNamespace(handle_intervention=lambda: asyncio.sleep(0))
    tool = object.__new__(CodeExecution)
    tool.agent = agent
    tool.args = {"runtime": "terminal", "code": "echo test"}
    if session is not None:
        tool.args["session"] = session
    tool.log = Log().log(type="code_exe", kvps=tool.args)
    monkeypatch.setattr(code_execution_tool, "resolve_code_execution_destination", resolve)
    monkeypatch.setattr(code_execution_tool.plugins, "get_plugin_config", lambda *args, **kwargs: {})
    monkeypatch.setattr(code_execution_tool, "_parse_config", lambda config: {})
    monkeypatch.setattr(tool, "execute_terminal_command", execute_terminal)

    asyncio.run(tool._execute(None))

    assert (tool.log.kvps["execution_destination"], tool.log.kvps["session"]) == expected
    assert tool.log.kvps["code"] == "echo test"
