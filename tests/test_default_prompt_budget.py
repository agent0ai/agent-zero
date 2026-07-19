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
    assert tokens.approximate_tokens(system_text) <= 10000
    assert "`tool_name` must be one listed tool name" in system_text
    assert "- tool_args: key value pairs tool arguments" in system_text
    assert '"tool_name": "call_subordinate"' in system_text
    assert '"tool_name": "parallel"' in system_text
    assert "Each `tool_calls` item is a normal tool request object" in system_text
    assert '"reset": true' in system_text
    assert '"tool_name": "text_editor"' in system_text
    assert '"action": "read"' in system_text
    assert '"tool_name": "code_execution_tool"' in system_text
    assert '"tool_name": "memory_load"' in system_text
    assert "informative but tight" in system_text
    assert "# code_execution_remote tool" not in system_text
    assert "# text_editor_remote tool" not in system_text
    assert "### computer_use_remote" not in system_text
    assert '"tool_name": "code_execution_remote"' not in system_text
    assert '"tool_name": "text_editor_remote"' not in system_text
    assert '"tool_name": "computer_use_remote"' not in system_text
    assert "Computer Use enablement is scoped to the current CLI session" not in system_text


@pytest.mark.asyncio
async def test_tiny_local_profile_prompt_is_action_first_json_contract():
    system_text = await _build_system_text("tiny-local")
    communication_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "agent.system.main.communication.md"
    ).read_text(encoding="utf-8")
    code_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "agent.system.tool.code_exe.md"
    ).read_text(encoding="utf-8")
    response_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "agent.system.tool.response.md"
    ).read_text(encoding="utf-8")
    repeat_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "fw.msg_repeat.md"
    ).read_text(encoding="utf-8")
    text_editor_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "agent.system.tool.text_editor.md"
    ).read_text(encoding="utf-8")
    solving_prompt = (
        PROJECT_ROOT / "agents" / "tiny-local" / "prompts" / "agent.system.main.solving.md"
    ).read_text(encoding="utf-8")

    assert "You are Agent Zero. Act on the user's behalf." in system_text
    assert "Your visible assistant message must be exactly one valid JSON object." in system_text
    assert 'Use exactly these top-level fields: `"tool_name"` and `"tool_args"`.' in system_text
    assert 'For a final user-facing answer, use the `response` tool.' in system_text
    assert "Use `response` only when the work is complete, blocked, or the user is only acknowledging completed work." in system_text
    assert "If the user says \"proceed\", \"continue\", \"go ahead\", \"do it\", \"excellent proceed\"" in system_text
    assert "Do not explain what command the user could run manually." in system_text
    assert "output a corrected JSON tool request immediately" in system_text
    assert "do not resend the same JSON" in system_text
    assert "## Tiny Local Output Rule" in system_text
    assert "~~~json" not in communication_prompt
    assert "~~~json" not in code_prompt
    assert "~~~json" not in response_prompt
    assert "~~~json" not in text_editor_prompt
    assert "No JSON in markdown fences" not in communication_prompt
    assert "thoughts: array thoughts before execution" not in communication_prompt
    assert "headline: short headline summary" not in communication_prompt
    assert "explain each step in thoughts" not in solving_prompt
    assert "Continuation words" in solving_prompt
    assert "Do not respond by saying you will begin, continue, start, proceed, or investigate." in solving_prompt
    assert "Do not use this tool for \"proceed\", \"continue\", \"go ahead\"" in response_prompt
    assert "Your repeated JSON was recorded, but it did not execute another tool." in repeat_prompt
    assert "replace it with the next real tool call" in repeat_prompt
    assert "do not repeat the same status response or exact tool request" in solving_prompt
    assert "do not repeat the same exact tool call" in solving_prompt
    assert '"open_in_canvas":true' in text_editor_prompt
    assert "do not repeat the same tool call" in text_editor_prompt
    assert '"headline"' not in code_prompt
    assert '"headline"' not in response_prompt
    assert '"headline"' not in text_editor_prompt


def test_tiny_local_profile_is_discoverable():
    from helpers import subagents

    profiles = {
        str(item.get("key") or ""): str(item.get("label") or "")
        for item in subagents.get_all_agents_list()
    }

    assert profiles["tiny-local"] == "Tiny Local"


def test_removed_small_profile_and_prompt_text_generic():
    removed_profile = "a0" + "_" + "small"

    assert not (PROJECT_ROOT / "agents" / removed_profile).exists()
    assert not (
        PROJECT_ROOT / "knowledge" / "main" / f"{removed_profile}_tool_call_examples.md"
    ).exists()
    assert not (PROJECT_ROOT / "knowledge" / "main" / "tool_call_reference_examples.md").exists()

    for path in _iter_prompt_files():
        assert removed_profile not in path.read_text(encoding="utf-8")


def test_prompt_token_estimate_omits_embedded_image_data_urls():
    embedded_png = "data:image/png;base64," + ("ABCDabcd0123+/==" * 20_000)
    prompt_text = f"user: please inspect this screenshot {embedded_png}"

    sanitized = tokens.sanitize_embedded_image_data_urls(prompt_text)

    assert "ABCDabcd0123+/==" not in sanitized
    assert "data:image/png;base64," in sanitized
    assert tokens.EMBEDDED_IMAGE_DATA_PLACEHOLDER in sanitized
    assert tokens.approximate_prompt_tokens(prompt_text) < 100
    assert tokens.approximate_prompt_tokens(prompt_text) < tokens.approximate_tokens(prompt_text) / 100
