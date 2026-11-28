import json
from types import SimpleNamespace

import pytest

from extensions.python.response_stream._10_log_from_stream import (
    build_step_description,
)
from helpers import cache, extension
from helpers.log import Log
from test_tool_step_description import pin_bundled_plugins


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


async def _step(tool_name, tool_args):
    parsed = {"tool_name": tool_name, "tool_args": tool_args}
    return await build_step_description(_agent(), parsed)


def _suffix(tool_args) -> str:
    if isinstance(tool_args, dict) and tool_args:
        try:
            length = len(json.dumps(tool_args, separators=(",", ":"), ensure_ascii=False))
        except (TypeError, ValueError):
            length = len(repr(tool_args))
        return f" ({length})"
    return ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "tool_args", "expected"),
    [
        ("browser", {"action": "click"}, "Using browser... (18)"),
        ("browser", {"action": "keychord"}, "Using browser... (21)"),
        ("browser", {"action": "navigate", "url": "https://example.com/docs"}, "Using browser... (54)"),
        ("browser", {"action": "navigate"}, "Using browser... (21)"),
        ("browser", {"action": "evaluate", "code": "1+1"}, "Evaluating (34)"),
        ("browser", {"action": "unknown_action"}, "Using browser... (27)"),
        ("text_editor", {"action": "write", "path": "/tmp/dir/notes.md"}, "Writing file (45)"),
        ("text_editor", {"action": "patch"}, "Patching file (18)"),
        ("text_editor", {"action": "other"}, "Using text editor... (18)"),
        ("computer_use_remote", {"action": "click"}, "Using computer use remote... (18)"),
        ("computer_use_remote", {"action": "unknown_action"}, "Using computer use remote... (27)"),
    ],
)
async def test_plugin_tool_step_text(monkeypatch, tool_name, tool_args, expected):
    pin_bundled_plugins(monkeypatch)
    assert await _step(tool_name, tool_args) == expected


@pytest.mark.asyncio
async def test_plugin_hooks_leave_foreign_tools_alone():
    assert await _step("some_core_tool", {"action": "click"}) == "Using some core tool... (18)"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name",
    ["browser", "text_editor", "input", "input_remote", "code_execution_remote", "text_editor_remote", "computer_use_remote"],
)
@pytest.mark.parametrize("tool_args", [None, "raw", [1, 2], 5])
async def test_plugin_hooks_tolerate_malformed_arguments(tool_name, tool_args):
    # hooks that need no arguments still label the tool
    expected = f"Using {tool_name.replace('_', ' ')}..."
    assert await _step(tool_name, tool_args) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_name", "tool_args"),
    [
        ("text_editor_remote", {"action": ["x"]}),
    ],
)
async def test_plugin_tools_tolerate_odd_argument_shapes(tool_name, tool_args):
    assert await _step(tool_name, tool_args) == "Using text editor remote... (16)"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tool_args", "expected"),
    [
        ({"message": "go look", "profile": "developer"}, "Calling subordinate developer agent (43)"),
        ({"message": "go look"}, "Calling subordinate agent (21)"),
    ],
)
async def test_subordinate_step_names_the_profile(tool_args, expected):
    assert await _step("call_subordinate", tool_args) == expected


@pytest.mark.asyncio
async def test_parallel_step_labels_first_call_and_remaining_count():
    args = {"tool_calls": [{"tool_name": "browser", "action": "click"}, {"tool_name": "text_editor", "action": "write", "path": "/tmp/a.md"}]}
    assert await _step("parallel", args) == "Using in parallel browser and 1 more tools (121)"


@pytest.mark.asyncio
async def test_parallel_step_labels_single_call_without_count():
    args = {"tool_calls": [{"tool_name": "browser", "action": "click"}]}
    assert await _step("parallel", args) == "Using in parallel browser (57)"


@pytest.mark.asyncio
async def test_parallel_step_labels_string_calls_with_alias_names():
    args = {"calls": json.dumps([{"tool": "code_execution_tool"}, {"tool": "wait"}, {"tool": "memory"}])}
    assert await _step("parallel", args) == "Using in parallel code execution tool and 2 more tools (95)"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "args",
    [
        {},
        {"tool_calls": []},
        {"tool_calls": "not json ["},
        {"tool_calls": {"tool_name": "browser"}},
        {"tool_calls": ["raw"]},
        {"tool_calls": [None]},
    ],
)
async def test_parallel_step_falls_back_on_malformed_calls(args, monkeypatch):
    pin_bundled_plugins(monkeypatch)
    assert await _step("parallel", args) == f"Using parallel...{_suffix(args)}"
