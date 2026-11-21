import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from agent import Agent, LoopData
from helpers import cache, extension, mcp_handler, parallel_tools, secrets, subagents, tool_policy
from helpers.errors import RepairableException
from helpers.llm_result import LLMResult
from helpers.tool import Response, Tool


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tool_agent(monkeypatch, tmp_path):
    def paths(_agent, *parts, **kwargs):
        if parts == ("extensions/python", "tool_execute_before"):
            return [str(ROOT.joinpath(*parts)), str(ROOT / "plugins/_tool_access" / Path(*parts))]
        if parts[0] == "tools":
            return [str(ROOT.joinpath(*parts))]
        return []

    monkeypatch.setattr(cache, "_cache", {})
    monkeypatch.setattr(subagents, "get_paths", paths)
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: {"mode": "inherit"})
    secret_file = tmp_path / "secrets.env"
    secret_file.write_text("TOKEN=resolved-token\n", encoding="utf-8")
    manager = secrets.SecretsManager(str(secret_file))
    monkeypatch.setattr(secrets, "get_secrets_manager", lambda _context: manager)
    monkeypatch.setattr(
        mcp_handler.MCPConfig, "get_instance",
        lambda: SimpleNamespace(get_tool=lambda *_args: None),
    )
    agent = object.__new__(Agent)
    agent.data = {}
    agent.config = SimpleNamespace(profile="default")
    agent.context = SimpleNamespace(get_data=lambda _key: None)
    agent.loop_data = LoopData()
    agent.handle_intervention = AsyncMock()
    return agent


@pytest.mark.asyncio
@pytest.mark.parametrize("dispatch", ["chat", "responses", "parallel"])
async def test_tools_receive_expanded_includes_without_streaming(tool_agent, tmp_path, dispatch):
    content = 'File contents: "quotes", \\backslash, caffè\nsecond line\n'
    source = tmp_path / "source.txt"
    source.write_text(content, encoding="utf-8")
    placeholder = f"§§include({source})"
    args = {"text": f"before {placeholder} after", "nested": [{"value": placeholder}, 7, None, False]}
    expected = {"text": f"before {content} after", "nested": [{"value": content}, 7, None, False]}

    class CaptureTool(Tool):
        async def before_execution(self, **kwargs):
            self.original_args = self.args
            assert kwargs == args

        async def execute(self, **kwargs):
            assert self.args is self.original_args
            assert self.args == kwargs == expected
            return Response(message="done", break_loop=True)

        async def after_execution(self, response):
            pass

    tool_agent.get_tool = lambda **kwargs: CaptureTool(agent=tool_agent, **kwargs)
    if dispatch == "chat":
        result = await tool_agent.process_tools(json.dumps({"tool_name": "capture", "tool_args": args}))
    elif dispatch == "responses":
        result = await tool_agent.process_llm_result_tools(LLMResult.from_response({"output": [{
            "type": "function_call", "name": "capture", "call_id": "call_include",
            "arguments": json.dumps(args),
        }]}))
    else:
        result = await parallel_tools.execute_tool_call(tool_agent, "capture", args)

    assert result == "done"
    assert tool_agent.loop_data.current_tool is None


@pytest.mark.asyncio
async def test_include_expansion_preserves_keys_tuples_and_unreadable_files(tool_agent, tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("included", encoding="utf-8")
    empty = tmp_path / "empty.txt"
    empty.touch()
    placeholder = f"§§include({source})"
    missing = f"§§include({tmp_path / 'missing.txt'})"
    unreadable = f"§§include({tmp_path})"
    args = {placeholder: (placeholder, {"values": [missing, unreadable, "", 0, True, None]}),
            "text": f"{placeholder} + {placeholder}", "empty": f"§§include({empty})"}

    await extension.call_extensions_async("tool_execute_before", tool_agent, tool_name="capture", tool_args=args)

    assert args == {placeholder: ("included", {"values": [missing, unreadable, "", 0, True, None]}),
                    "text": "included + included", "empty": ""}


@pytest.mark.asyncio
async def test_included_secret_placeholders_are_unmasked_before_execution(tool_agent, tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Bearer §§secret(TOKEN)", encoding="utf-8")
    args = {"text": f"§§include({source})"}

    await extension.call_extensions_async("tool_execute_before", tool_agent, tool_name="capture", tool_args=args)

    assert args == {"text": "Bearer resolved-token"}


@pytest.mark.asyncio
async def test_included_action_cannot_bypass_tool_policy(tool_agent, monkeypatch, tmp_path):
    source = tmp_path / "action.txt"
    source.write_text("load", encoding="utf-8")
    monkeypatch.setattr(tool_policy, "get_policy", lambda _agent: tool_policy.normalize_policy({
        "mode": "custom", "default": "allow", "blocked": ["local:skills_tool:load"],
    }))

    with pytest.raises(RepairableException, match='Tool "skills_tool" is blocked'):
        await extension.call_extensions_async(
            "tool_execute_before", tool_agent, tool_name="skills_tool",
            tool_args={"action": f"§§include({source})"},
        )
