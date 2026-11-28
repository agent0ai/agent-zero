from pathlib import Path
from types import SimpleNamespace

import pytest

from agent import LoopData
from extensions.python.response_stream._10_log_from_stream import (
    LogFromStream as StreamLog,
    build_step_description,
)
from helpers import cache, extension, files, subagents
from helpers.log import Log


def pin_bundled_plugins(monkeypatch) -> None:
    def paths(agent, *subpaths):
        root = files.get_abs_path("plugins")
        found = []
        for plugin_dir in sorted(Path(root).iterdir()):
            candidate = files.get_abs_path(str(plugin_dir), *subpaths)
            if files.exists(candidate):
                found.append(candidate)
        return found

    monkeypatch.setattr(subagents, "get_paths", paths)
    cache.clear(extension._CLASSES_CACHE_AREA)
    cache.clear(extension._EXTENSIONS_CACHE_AREA)


@pytest.fixture(autouse=True)
def restore_extension_caches():
    yield
    cache.clear(extension._CLASSES_CACHE_AREA)
    cache.clear(extension._EXTENSIONS_CACHE_AREA)


def _agent():
    return SimpleNamespace(
        context=SimpleNamespace(log=Log(), get_data=lambda *args, **kwargs: None),
        config=SimpleNamespace(profile=None),
        agent_name="A0",
    )


@pytest.mark.asyncio
async def test_step_description_defaults_to_using_tool():
    parsed = {"tool_name": "some_new_tool", "tool_args": {"a": 1}}
    assert await build_step_description(_agent(), parsed) == "Using some new tool... (7)"


@pytest.mark.asyncio
async def test_step_description_dispatches_mutable_contract(monkeypatch):
    seen = {}

    async def capture(name, agent, **kwargs):
        seen["name"] = name
        seen["ctx"] = dict(kwargs["ctx"])
        kwargs["ctx"]["step"] = "Custom step"

    monkeypatch.setattr(extension, "call_extensions_async", capture)

    parsed = {"tool_name": "any_tool", "tool_args": {"k": "v"}}
    assert await build_step_description(_agent(), parsed) == "Custom step (9)"
    assert seen["name"] == "tool_step_description"
    assert seen["ctx"]["tool_name"] == "any_tool"
    assert seen["ctx"]["tool_args"] == {"k": "v"}
    assert seen["ctx"]["step"] == "Using any tool..."


@pytest.mark.asyncio
async def test_step_description_ignores_missing_tool_args():
    assert await build_step_description(_agent(), {"tool_name": "any_tool"}) == "Using any tool..."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_args", "expected"),
    [
        ({"runtime": "python", "code": "print(1)"}, "Writing Python code... (38)"),
        ({"runtime": "nodejs", "code": "1"}, "Writing Node.js code... (31)"),
        ({"runtime": "terminal", "code": "ls"}, "Writing terminal command... (34)"),
        ({"runtime": "python"}, "Writing Python code... (20)"),
        ({"runtime": "output", "code": "print(1)"}, "Writing code... (38)"),
        ({"code": "print(1)"}, "Using code execution tool... (19)"),
        ({"session": 1}, "Using code execution tool... (13)"),
        ({}, "Using code execution tool..."),
    ],
)
async def test_code_execution_plugin_refines_step_text(monkeypatch, tool_args, expected):
    pin_bundled_plugins(monkeypatch)
    parsed = {"tool_name": "code_execution_tool", "tool_args": tool_args}
    assert await build_step_description(_agent(), parsed) == expected


@pytest.mark.asyncio
async def test_stream_log_writes_hook_step_text(monkeypatch):
    async def custom(name, agent, **kwargs):
        kwargs["ctx"]["step"] = "Refined step"

    monkeypatch.setattr(extension, "call_extensions_async", custom)

    loop_data = LoopData()
    await StreamLog(agent=_agent()).execute(
        loop_data=loop_data,
        text='{"tool_name":"any_tool"}',
        parsed={"tool_name": "any_tool"},
    )

    assert loop_data.params_temporary["log_item_generating"].kvps["step"] == "Refined step"


@pytest.mark.asyncio
async def test_step_description_falls_back_when_hook_raises(monkeypatch):
    async def boom(name, agent, **kwargs):
        raise RuntimeError("hook exploded")

    monkeypatch.setattr(extension, "call_extensions_async", boom)

    parsed = {"tool_name": "any_tool", "tool_args": {"k": "v"}}
    assert await build_step_description(_agent(), parsed) == "Using any tool... (9)"


@pytest.mark.asyncio
async def test_stream_log_keeps_chunk_when_hook_raises(monkeypatch):
    async def boom(name, agent, **kwargs):
        raise RuntimeError("hook exploded")

    monkeypatch.setattr(extension, "call_extensions_async", boom)

    loop_data = LoopData()
    await StreamLog(agent=_agent()).execute(
        loop_data=loop_data,
        text='{"tool_name":"any_tool"}',
        parsed={"tool_name": "any_tool"},
    )

    assert loop_data.params_temporary["log_item_generating"].kvps["step"] == "Using any tool..."
