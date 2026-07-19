import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentConfig, AgentContext, AgentContextType
from helpers import runtime, tokens


def _iter_prompt_files():
    yield from (PROJECT_ROOT / "prompts").rglob("*.md")
    yield from (PROJECT_ROOT / "agents" / "agent0" / "prompts").rglob("*.md")
    yield from (PROJECT_ROOT / "knowledge" / "main").rglob("*.md")
    for prompts_dir in (PROJECT_ROOT / "plugins").glob("*/prompts"):
        yield from prompts_dir.rglob("*.md")


async def _build_system_text(profile: str = "agent0") -> str:
    old_args = dict(runtime.args)
    runtime.args.clear()
    runtime.args["dockerized"] = "true"

    ctx = AgentContext(
        config=AgentConfig(
            profile=profile,
            knowledge_subdirs=["custom", "default"],
            mcp_servers='{"mcpServers": {}}',
        ),
        type=AgentContextType.USER,
        set_current=False,
    )
    try:
        system = await ctx.agent0.get_system_prompt(ctx.agent0.loop_data)
        return "\n\n".join(system)
    finally:
        AgentContext.remove(ctx.id)
        runtime.args.clear()
        runtime.args.update(old_args)


@pytest.mark.asyncio
async def test_default_agent0_prompt_budget_and_guardrails():
    system_text = await _build_system_text()

    # The default prompt now intentionally includes the compact always-on tool
    # surface plus skill metadata. Keep the guardrail close to the observed
    # budget so prompt creep remains visible without pretending this surface is
    # a tiny single-tool prompt.
    assert tokens.approximate_tokens(system_text) <= 8500
    assert "`tool_name` must be one listed tool name" in system_text
    assert "- tool_args: key value pairs tool arguments" in system_text
    assert '"tool_name": "call_subordinate"' in system_text
    assert '"reset": true' in system_text
    assert '"tool_name": "text_editor"' in system_text
    assert '"action": "read"' in system_text
    assert '"tool_name": "code_execution_tool"' in system_text
    assert '"tool_name": "memory_load"' in system_text
    assert "informative but tight" in system_text
    assert '"tool_name": "code_execution_remote"' in system_text
    assert '"tool_name": "text_editor_remote"' in system_text
    assert '"tool_name": "computer_use_remote"' not in system_text
    assert "host-computer-use" in system_text


def test_a0_small_profile_removed_and_prompt_text_generic():
    assert not (PROJECT_ROOT / "agents" / "a0_small").exists()
    assert not (PROJECT_ROOT / "knowledge" / "main" / "a0_small_tool_call_examples.md").exists()
    assert not (PROJECT_ROOT / "knowledge" / "main" / "tool_call_reference_examples.md").exists()

    for path in _iter_prompt_files():
        assert "a0_small" not in path.read_text(encoding="utf-8")
