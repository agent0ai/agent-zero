import base64
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, SystemMessage


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models
from agent import Agent, LoopData
from helpers import extension, extract_tools, history, litellm_transport
from helpers.llm_result import LLMResult
from plugins._context_window.api.context_window import ContextWindow
from plugins._context_window.helpers import usage


class _Log:
    def set_progress(self, _message: str) -> None:
        pass


@pytest.mark.asyncio
async def test_usage_follows_prompt_sources_and_reconciles_to_total(monkeypatch):
    agent = object.__new__(Agent)
    loop_data = LoopData()
    agent.loop_data = loop_data
    agent.context = SimpleNamespace(log=_Log())
    agent.history = history.History(agent)
    agent.data = {}
    agent.history.add_message(False, "User asks a question.")
    agent.history.add_message(True, "Assistant answers.")
    agent.history.add_message(
        False,
        {
            "tool_name": "skills_tool",
            "tool_result": "Skill instructions without a special heading.",
            "skill_instructions": {
                "name": "test-skill",
                "content_included": True,
            },
        },
    )

    system_parts = {
        "system_prompt": "Main instructions without a special heading.",
        "system_tools": "Tool definitions without a special heading.",
        "mcp_tools": "Remote definitions without a special heading.",
        "skills": "Available skill names without a special heading.",
    }

    async def get_system_prompt(_loop_data):
        for key in ("system_tools", "mcp_tools", "skills"):
            usage.record_prompt(agent, key, system_parts[key])
        return list(system_parts.values())

    def read_prompt(prompt_file: str, **kwargs) -> str:
        if prompt_file == "agent.context.protocol.md":
            return "[PROTOCOL]\n" + kwargs["protocol"]
        if prompt_file == "agent.context.extras.md":
            return "[EXTRAS]\n" + kwargs["extras"]
        raise AssertionError(f"Unexpected prompt: {prompt_file}")

    async def call_extensions(extension_point: str, agent=None, **kwargs):
        if extension_point == "message_loop_prompts_after":
            current = kwargs["loop_data"]
            current.protocol_persistent["project"] = "Project instructions."
            current.extras_temporary["time"] = "Current time."
            usage.capture_context(agent, current)

    agent.get_system_prompt = get_system_prompt
    agent.read_prompt = read_prompt
    monkeypatch.setattr(extension, "call_extensions_async", call_extensions)
    monkeypatch.setattr(history.History, "_get_max_embeds", lambda self: 0)

    usage.reset(agent)
    await Agent.prepare_prompt.__wrapped__(agent, loop_data)
    usage.finalize(agent)

    window = agent.get_data(Agent.DATA_NAME_CTX_WINDOW)
    breakdown = window["usage"]
    assert tuple(breakdown) == usage.USAGE_KEYS
    assert sum(breakdown.values()) == window["tokens"]
    assert all(breakdown[key] > 0 for key in usage.USAGE_KEYS)
    assert usage.PARTS_KEY not in loop_data.params_temporary
    assert "history_messages" not in agent.data[usage.CACHE_KEY]


@pytest.mark.asyncio
async def test_api_returns_only_counts_and_effective_limit(monkeypatch):
    agent = SimpleNamespace(
        DATA_NAME_CTX_WINDOW="ctx_window",
        get_data=lambda _key: {
            "text": "private prompt",
            "tokens": 120,
            "usage": {"messages": 42},
        },
    )
    handler = object.__new__(ContextWindow)
    handler.use_context = lambda _context_id: SimpleNamespace(
        streaming_agent=None,
        agent0=agent,
    )
    monkeypatch.setattr(
        "plugins._context_window.api.context_window.get_chat_model_config",
        lambda _agent: {"ctx_length": 128_000},
    )

    result = await handler.process({"context": "ctx-1"}, SimpleNamespace())

    assert result == {
        "tokens": 120,
        "context_window": 128_000,
        "usage": {
            "messages": 42,
            "system_tools": 0,
            "skills": 0,
            "mcp_tools": 0,
            "system_prompt": 0,
            "extras": 0,
        },
        "provider_usage": {},
    }
    assert "text" not in result


def test_webui_and_accounting_are_plugin_owned():
    model_switcher = (
        ROOT
        / "plugins/_model_config/extensions/webui/chat-input-progress-start/model-switcher.html"
    ).read_text(encoding="utf-8")
    model_store = (ROOT / "plugins/_model_config/webui/switcher-mixin.js").read_text(
        encoding="utf-8"
    )
    component = (
        ROOT
        / "plugins/_context_window/extensions/webui/model-context-strip-end/context-window.html"
    ).read_text(encoding="utf-8")
    context_store = (
        ROOT / "plugins/_context_window/webui/context-window-store.js"
    ).read_text(encoding="utf-8")
    helper = (ROOT / "plugins/_context_window/helpers/usage.py").read_text(
        encoding="utf-8"
    )
    refresh_hook = (
        ROOT
        / "plugins/_context_window/extensions/webui/apply_snapshot_before/refresh-context-window.js"
    ).read_text(encoding="utf-8")

    assert 'id="model-context-strip-end"' in model_switcher
    assert "contextWindowUsage" not in model_switcher
    assert "contextUsage" not in model_store
    assert "Context window" in component
    assert "position: static" in component
    assert "min-width: min(19rem, calc(100vw - 2rem))" in component
    assert "min-width: min(calc(17rem + 1.25rem), calc(100vw - 2.5rem))" in component
    assert "width: min(19rem, calc(100vw - 2rem))" in component
    assert "right: 1.25rem" in component
    assert "width: min(17rem, calc(100vw - 3rem))" in component
    assert 'label: "Free space"' in context_store
    assert "Last model call" not in component
    assert ">Price<" in component
    assert ">Cache hit<" in component
    assert ">Tokens In/Out<" in component
    assert "context-window-cache-meter" not in component
    assert "price: {" in context_store
    assert "hasData: cost !== null" in context_store
    assert 'label: cost === null ? "" : formatCost(cost)' in context_store
    assert "usage.provider.price.hasData" in component
    assert "usage.provider.price.label" in component
    assert 'value < 0.001 ? "<$0.001"' in context_store
    assert "maximumSignificantDigits: 3" in context_store
    assert "border-top: 1px solid var(--color-border)" in component
    assert " → " in context_store
    assert "summaryTokens" in context_store
    assert 'summaryPercent: `${percentLabel} used`' in context_store
    assert "formatTokens(output)} tok" not in context_store
    assert "context-window-summary-tokens" in component
    assert "context-window-summary-percent" in component
    assert "font-family: var(--font-family-main)" in component
    assert "<details" not in component
    assert "Reasoning" not in component
    assert "Images sent" not in component
    assert "provider did not split out their token cost" not in context_store
    assert "cached / input" in context_store
    assert "Math.round(cachePercent)" in context_store
    assert "context-window-dot" not in component
    assert "dotStyle" not in context_store
    assert "Breakdown available after the next message." in component
    assert "startswith(" not in helper
    assert "rpartition(" not in helper
    assert 'item?.type !== "agent"' in refresh_hook
    assert "Number(item.agentno || 0) !== 0" in refresh_hook
    assert 'const logGuid = String(snapshot?.log_guid || "")' in refresh_hook
    assert "logGuid !== lastLogGuid" in refresh_hook
    assert "generationKey === lastGenerationKey" in refresh_hook
    assert "TOOL_REFRESH_INTERVAL = 4" in refresh_hook
    assert 'watch("$store.chats.selectedContext?.running"' in context_store


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is required")
def test_webui_refreshes_after_four_distinct_root_tool_calls():
    source = (
        ROOT
        / "plugins/_context_window/extensions/webui/apply_snapshot_before/refresh-context-window.js"
    ).read_text(encoding="utf-8")
    source = source.replace(
        'import { store as contextWindowStore } from "/plugins/_context_window/webui/context-window-store.js";',
        "const contextWindowStore = { refresh: async id => globalThis.refreshes.push(id) };",
    )
    module_url = "data:text/javascript;base64," + base64.b64encode(
        source.encode("utf-8")
    ).decode("ascii")
    script = f"""
globalThis.refreshes = [];
const {{ default: refresh }} = await import({module_url!r});
const snapshot = (logs) => ({{
  context: "chat-1",
  contexts: [{{ id: "chat-1" }}],
  log_guid: "log-1",
  logs,
}});
const call = (logs) => refresh({{ snapshot: snapshot(logs) }});
const assertCount = expected => {{
  if (globalThis.refreshes.length !== expected) throw new Error(
    `expected ${{expected}} refreshes, got ${{globalThis.refreshes.length}}`
  );
}};

await call([]);
assertCount(1);
await call([{{ no: 1, type: "tool", agentno: 0 }}]);
await call([{{ no: 1, type: "tool", agentno: 0, content: "updated" }}]);
await call([{{ no: 2, type: "mcp", agentno: 0 }}]);
await call([{{ no: 3, type: "code_exe", agentno: 0 }}]);
await call([{{ no: 4, type: "text_editor", agentno: 0 }}]);
assertCount(2);
await call([{{ no: 5, type: "agent", agentno: 0, id: "gen-1" }}]);
assertCount(3);
await call([{{ no: 6, type: "tool", agentno: 0 }}]);
await call([{{ no: 7, type: "mcp", agentno: 1 }}]);
await call([{{ no: 8, type: "subagent", agentno: 0 }}]);
await call([{{ no: 9, type: "text_editor", agentno: 0 }}]);
assertCount(3);
await call([{{ no: 10, type: "code_exe", agentno: 0 }}]);
assertCount(4);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)


def test_source_prompt_extensions_are_registered():
    expected = {
        "_functions/agent/Agent/prepare_prompt/start": "ResetContextUsage",
        "_functions/agent/Agent/prepare_prompt/end": "StoreContextUsage",
        "_functions/agent/Agent/call_chat_model_turn/end": "RecordProviderUsage",
        "_functions/models/LiteLLMChatWrapper/unified_turn/start": "DrainProviderUsage",
        "_functions/models/LiteLLMChatWrapper/unified_turn/end": "RestoreProviderResponse",
        "message_loop_prompts_after": "CaptureContextUsage",
    }
    for point, class_name in expected.items():
        classes = extension._get_extension_classes(point)  # type: ignore[attr-defined]
        assert any(cls.__name__ == class_name for cls in classes)

    system_prompt_classes = {
        cls.__name__: cls
        for cls in extension._get_extension_classes("system_prompt")  # type: ignore[attr-defined]
    }
    for owner, recorder in {
        "ToolsPrompt": "RecordSystemToolsUsage",
        "MCPToolsPrompt": "RecordMcpToolsUsage",
        "SkillsPrompt": "RecordSkillsUsage",
    }.items():
        builder = system_prompt_classes[owner].execute.__globals__["build_prompt"]
        module = builder.__wrapped__.__module__.replace(".", "/")
        point = f"_functions/{module}/build_prompt/end"
        classes = extension._get_extension_classes(point)  # type: ignore[attr-defined]
        assert any(cls.__name__ == recorder for cls in classes)


@pytest.mark.asyncio
async def test_chat_stream_drains_terminal_provider_usage(monkeypatch):
    response = '{"tool_name":"response","tool_args":{"text":"done"}}'
    chunks = [
        {"choices": [{"delta": {"content": response}, "message": {}}]},
        {"choices": [{"delta": {"content": " ignored"}, "message": {}}]},
        {
            "choices": [],
            "usage": {
                "prompt_tokens": 12_000,
                "prompt_tokens_details": {"cached_tokens": 9_000},
                "completion_tokens": 80,
            },
            "_hidden_params": {"response_cost": 0.0042},
        },
    ]
    consumed = []

    async def stream():
        for chunk in chunks:
            consumed.append(chunk)
            yield chunk

    async def fake_acompletion(*args, **kwargs):
        assert kwargs["stream_options"] == {"include_usage": True}
        return stream()

    async def fake_rate_limiter(*args, **kwargs):
        return None

    callback_calls = []

    async def response_callback(chunk: str, full: str):
        callback_calls.append((chunk, full))
        return full if extract_tools.extract_tool_request(full) else None

    monkeypatch.setattr(litellm_transport, "acompletion", fake_acompletion)
    monkeypatch.setattr(models, "apply_rate_limiter", fake_rate_limiter)
    wrapper = models.LiteLLMChatWrapper(
        model="test-model",
        provider="openrouter",
        model_config=None,
        api_base="https://openrouter.ai/api/v1",
    )

    result = await wrapper.unified_turn(
        messages=[
            SystemMessage(content="stable instructions"),
            HumanMessage(content="question"),
        ],
        response_callback=response_callback,
        explicit_caching=True,
    )

    assert consumed == chunks
    assert callback_calls == [
        (response, response),
        (" ignored", response + " ignored"),
    ]
    assert result.response == response
    assert result.output_items[0].type == "message"
    assert result.usage == {
        "prompt_tokens": 12_000,
        "prompt_tokens_details": {"cached_tokens": 9_000},
        "completion_tokens": 80,
        "cost": 0.0042,
    }


def test_prompt_fragment_cache_is_bounded_and_content_addressed(monkeypatch):
    calls = []
    agent = SimpleNamespace(data={}, loop_data=LoopData())
    monkeypatch.setattr(
        usage.tokens,
        "approximate_prompt_tokens",
        lambda text: calls.append(text) or len(text),
    )

    usage.reset(agent)
    usage.record_prompt(agent, "system_tools", "same prompt")
    usage.record_prompt(agent, "system_tools", "same prompt")
    usage.record_prompt(agent, "system_tools", "changed prompt")

    assert calls == ["same prompt", "changed prompt"]
    cache = agent.data[usage.CACHE_KEY]
    assert len(cache) == 1
    assert cache["prompt:system_tools"][1] == len("changed prompt")
    assert all(len(value[0]) == 64 for value in cache.values())


def test_history_ledger_changes_without_invalidating_fragment_cache(monkeypatch):
    calls = []
    history_tokens = 1_000
    agent = SimpleNamespace(
        data={},
        loop_data=LoopData(),
        history=SimpleNamespace(get_tokens=lambda: history_tokens),
        _build_context_message=lambda *args, **kwargs: [],
    )
    skill_message = {
        "ai": False,
        "content": {
            "tool_name": "skills_tool",
            "tool_result": "Loaded skill body.",
            "skill_instructions": {
                "name": "test-skill",
                "content_included": True,
            },
        },
    }
    loop_data = SimpleNamespace(
        history_output=[skill_message],
        protocol_persistent={},
        protocol_temporary={},
        extras_persistent={},
        extras_temporary={},
    )
    monkeypatch.setattr(
        usage.tokens,
        "approximate_prompt_tokens",
        lambda text: calls.append(text) or len(text),
    )

    usage.reset(agent)
    usage.record_prompt(agent, "system_tools", "stable tools")
    usage.capture_context(agent, loop_data)
    first = dict(agent.loop_data.params_temporary[usage.PARTS_KEY])

    history_tokens = 400
    agent.loop_data.params_temporary = {}
    usage.reset(agent)
    usage.record_prompt(agent, "system_tools", "stable tools")
    usage.capture_context(agent, loop_data)
    second = agent.loop_data.params_temporary[usage.PARTS_KEY]

    assert first["messages"] == 1_000 - first["skills"]
    assert second["messages"] == 400 - second["skills"]
    assert calls.count("stable tools") == 1
    assert len(agent.data[usage.CACHE_KEY]) == 3


def test_rendered_history_fallback_preserves_system_prompt_bucket(monkeypatch):
    data = {}
    output = [{"ai": False, "content": "short message"}]
    agent = SimpleNamespace(
        DATA_NAME_CTX_WINDOW="ctx_window",
        data=data,
        loop_data=LoopData(),
        history=SimpleNamespace(get_tokens=lambda: 10_000),
        _build_context_message=lambda *args, **kwargs: [],
        get_data=lambda key: data.get(key),
        set_data=lambda key, value: data.__setitem__(key, value),
    )
    loop_data = SimpleNamespace(
        history_output=output,
        protocol_persistent={},
        protocol_temporary={},
        extras_persistent={},
        extras_temporary={},
    )
    monkeypatch.setattr(
        usage.tokens,
        "approximate_prompt_tokens",
        lambda text: len(text),
    )

    usage.reset(agent)
    usage.capture_context(agent, loop_data)
    data[agent.DATA_NAME_CTX_WINDOW] = {"tokens": 100}
    usage.finalize(agent)

    breakdown = data[agent.DATA_NAME_CTX_WINDOW]["usage"]
    assert breakdown["messages"] == len("user: short message")
    assert breakdown["system_prompt"] > 0
    assert sum(breakdown.values()) == 100


def test_provider_usage_is_optional():
    data = {}
    agent = SimpleNamespace(
        data=data,
        history=SimpleNamespace(all_messages=lambda: []),
        set_data=lambda key, value: data.__setitem__(key, value),
    )
    result = LLMResult.from_chat(
        response="done",
        usage={
            "prompt_tokens": 12_000,
            "prompt_tokens_details": {"cached_tokens": 9_000},
            "completion_tokens": 80,
            "cost": 0.0123,
        },
    )

    usage.capture_provider_usage(agent, result)

    assert usage.latest_provider_usage(agent) == {
        "input_tokens": 12_000,
        "cached_tokens": 9_000,
        "output_tokens": 80,
        "cost": 0.0123,
    }

    usage.capture_provider_usage(agent, LLMResult.from_chat(response="no usage"))
    assert usage.latest_provider_usage(agent) == {}
    assert usage.provider_usage_snapshot(
        {"input_tokens": 100, "cached_tokens": None, "cost": None}
    ) == {"input_tokens": 100}
