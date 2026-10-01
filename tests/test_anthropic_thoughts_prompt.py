from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import files, responses_tools
from plugins._model_config.extensions.python._functions.agent.Agent.read_prompt.end import (
    _20_anthropic_thoughts as thoughts,
)


@pytest.mark.parametrize("provider,model,adapted", [
    ("anthropic", "claude-opus-5-5", True),
    ("openrouter", "Anthropic/claude-opus-5.5", True),
    ("bedrock", "us.anthropic.claude-opus", True),
    ("openrouter", "openai/gpt-5", False),
])
def test_scoped_prompt_rendering_preserves_templates_and_native_projection(
    monkeypatch, provider, model, adapted,
):
    root = Path(__file__).parents[1] / "prompts"
    monkeypatch.setattr(thoughts, "get_chat_model_config", lambda agent: {
        "provider": provider, "name": model,
    })
    agent = SimpleNamespace()
    hook = thoughts.AnthropicThoughts(agent)

    def read_prompt(name):
        original = files.read_prompt_file(name, _directories=[str(root)]).rstrip("\n")
        data = {"args": (agent,), "kwargs": {"file": name}, "result": original}
        hook.execute(data)
        assert (data["result"] != original) == (adapted and name != "agent.system.main.communication.native.md")
        return data["result"]

    agent.read_prompt = read_prompt
    main = read_prompt("agent.system.main.md")
    assert read_prompt("agent.system.main.communication.md") in main
    assert read_prompt("agent.system.main.solving.md") in main
    assert '"thoughts": [' in main
    assert ("explain each step in thoughts" not in main) == adapted
    loop = SimpleNamespace(params_temporary={})
    responses_tools.register_prompt(agent, loop, "main", main)
    native = responses_tools.project_system_prompt(
        [{"role": "system", "content": files.remove_code_fences(main, language="json")}],
        loop.params_temporary["responses_prompt_replacements"],
    )[0]["content"]
    assert "Use the provided native functions" in native

    for name in ("agent.system.main.md", "fw.initial_message.md"):
        custom = "Custom thoughts guidance."
        data = {"args": (agent, name), "kwargs": {}, "result": custom}
        hook.execute(data)
        assert data["result"] == custom
