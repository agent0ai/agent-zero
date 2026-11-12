from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent import Agent, LoopData
from helpers import extension, history
from extensions.python.system_prompt import _14_project_prompt as project_prompt


class _DummyLog:
    def set_progress(self, _message: str) -> None:
        return None


@pytest.mark.asyncio
async def test_cache_boundaries_survive_tool_turns_with_changing_extras(monkeypatch):
    from copy import deepcopy

    import models
    from helpers import litellm_transport

    project_rule = "Project rule."
    turn = 0

    async def fake_extensions(point, agent=None, **kwargs):
        if point == "message_loop_prompts_after":
            loop = kwargs["loop_data"]
            loop.protocol_persistent["project_instructions"] = project_rule
            loop.extras_temporary["current_datetime"] = f"time-{turn}"

    monkeypatch.setattr(extension, "call_extensions_async", fake_extensions)
    monkeypatch.setattr(history.History, "_get_max_embeds", lambda self: 0)
    agent = object.__new__(Agent)
    agent.loop_data = LoopData()
    agent.context = SimpleNamespace(log=_DummyLog())
    agent.history = history.History(agent)
    agent.data = {}
    agent.read_prompt = lambda name, **values: (
        "[PROTOCOL]\n" + values["protocol"]
        if name == "agent.context.protocol.md"
        else "[EXTRAS]\n" + values["extras"]
    )

    async def system_prompt(_loop):
        return ["Stable system instructions."]

    agent.get_system_prompt = system_prompt
    agent.history.add_message(False, "User task.")
    wrapper = models.LiteLLMChatWrapper(
        model="claude-sonnet-4-5", provider="anthropic", model_config=None
    )
    requests = []

    def completion(**request):
        requests.append(request)
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(litellm_transport, "completion", completion)

    async def cache_boundaries():
        stored_history = agent.history.serialize()
        prompt = await Agent.prepare_prompt(agent, agent.loop_data)
        messages = wrapper._convert_messages(prompt)
        original = deepcopy(messages)
        transport = litellm_transport.LiteLLMTransport(
            model=wrapper.model_name,
            messages=messages,
            kwargs={"a0_explicit_prompt_caching": True},
        )
        assert transport.complete()["response_delta"] == "ok"
        assert messages == original
        assert agent.history.serialize() == stored_history

        prefix = []
        boundaries = {}
        for index, message in enumerate(requests[-1]["messages"]):
            prefix.append((message["role"], litellm_transport._content_to_text(message["content"])))
            if litellm_transport._has_cache_control(message):
                boundaries[index] = tuple(prefix)
        assert len(boundaries) <= 3  # Reserve the fourth provider breakpoint for tools.
        assert all("[EXTRAS]" not in text for prefix in boundaries.values() for _, text in prefix)
        return boundaries

    previous = await cache_boundaries()
    assert list(previous) == [0]
    for turn in range(1, 5):
        agent.history.add_message(True, f"Assistant tool call {turn}.")
        agent.history.add_message(False, f"Tool result {turn}.")
        current = await cache_boundaries()
        assert current[max(previous)] == previous[max(previous)]
        assert current[max(current)][-1] == ("assistant", f"Assistant tool call {turn}.")
        previous = current

    project_rule = "Changed project rule."
    changed = await cache_boundaries()
    assert changed[0] == previous[0]
    assert changed[max(changed)] != previous[max(previous)]


@pytest.mark.asyncio
async def test_prepare_prompt_places_protocol_before_history_and_extras(monkeypatch):
    async def fake_call_extensions(extension_point: str, agent=None, **kwargs):
        if extension_point == "message_loop_prompts_after":
            loop_data = kwargs["loop_data"]
            loop_data.protocol_persistent["project_instructions"] = "Project rule."
            loop_data.extras_temporary["current_datetime"] = "Today."

    monkeypatch.setattr(extension, "call_extensions_async", fake_call_extensions)
    monkeypatch.setattr(history.History, "_get_max_embeds", lambda self: 0)

    agent = object.__new__(Agent)
    loop_data = LoopData()
    agent.loop_data = loop_data
    agent.context = SimpleNamespace(log=_DummyLog())
    agent.history = history.History(agent)
    agent.data = {}

    agent.history.add_message(False, "User asks.")
    agent.history.add_message(True, "Assistant answers.")

    async def get_system_prompt(_loop_data):
        return ["System root."]

    def read_prompt(prompt_file: str, **kwargs) -> str:
        if prompt_file == "agent.context.protocol.md":
            return "[PROTOCOL]\n" + kwargs["protocol"]
        if prompt_file == "agent.context.extras.md":
            return "[EXTRAS]\n" + kwargs["extras"]
        raise AssertionError(f"Unexpected prompt file: {prompt_file}")

    agent.get_system_prompt = get_system_prompt
    agent.read_prompt = read_prompt
    agent.set_data = lambda key, value: agent.data.__setitem__(key, value)

    prompt = await Agent.prepare_prompt(agent, loop_data)

    assert isinstance(prompt[0], SystemMessage)
    assert prompt[0].content == "System root."
    assert isinstance(prompt[1], HumanMessage)
    assert str(prompt[1].content).startswith("[PROTOCOL]")
    assert str(prompt[1].content).index("Project rule.") < str(prompt[1].content).index(
        "User asks."
    )
    assert isinstance(prompt[2], AIMessage)
    assert prompt[2].content == "Assistant answers."
    assert isinstance(prompt[3], HumanMessage)
    assert str(prompt[3].content).startswith("[EXTRAS]")
    assert "Today." in str(prompt[3].content)
    assert '{"current_datetime":"Today."' in str(prompt[3].content)

    serialized_history = agent.history.serialize()
    assert "Project rule." not in serialized_history
    assert "Today." not in serialized_history
    assert "protocol" not in serialized_history.lower()
    assert loop_data.protocol_temporary == {}
    assert loop_data.extras_temporary == {}

    class FakeResponsesModel:
        def _convert_messages(self, messages):
            role_by_type = {"system": "system", "human": "user", "ai": "assistant"}
            return [
                {"role": role_by_type[message.type], "content": message.content}
                for message in messages
            ]

    from helpers.litellm_transport import ResponsesTransport

    input_items = ResponsesTransport.input_from_model_messages(
        FakeResponsesModel(),
        prompt,
    )
    assert input_items[1]["role"] == "user"
    assert "[PROTOCOL]" in input_items[1]["content"]
    assert "[EXTRAS]" in input_items[-1]["content"]


@pytest.mark.asyncio
async def test_project_prompt_moves_project_instructions_to_protocol(monkeypatch):
    project_vars = {
        "project_name": "Demo",
        "project_description": "",
        "project_instructions": "Project rule.",
        "include_agents_md": True,
        "project_path": "/a0/usr/projects/demo",
        "project_git_url": "",
    }
    loop_data = LoopData()

    class FakeContext:
        def get_data(self, key):
            assert key == project_prompt.projects.CONTEXT_DATA_KEY_PROJECT
            return "demo"

    class FakeAgent:
        context = FakeContext()

        def read_prompt(self, prompt_file: str, **kwargs) -> str:
            if prompt_file == "agent.system.projects.main.md":
                return "project context may be active"
            if prompt_file == "agent.system.projects.active.md":
                return f"active project: {kwargs['project_path']}"
            if prompt_file == "agent.protocol.projects.instructions.md":
                return "protocol project instructions:\n" + kwargs["project_instructions"]
            raise AssertionError(f"Unexpected prompt file: {prompt_file}")

    monkeypatch.setattr(
        project_prompt.projects,
        "build_system_prompt_vars",
        lambda _name: project_vars,
    )
    monkeypatch.setattr(
        project_prompt.projects,
        "build_agents_md_protocol",
        lambda _name: "AGENTS path rule.",
    )

    prompt = await project_prompt.build_prompt.__wrapped__(  # type: ignore[attr-defined]
        FakeAgent(),
        loop_data=loop_data,
    )

    assert "Project rule." not in prompt
    assert "AGENTS path rule." not in prompt
    assert list(loop_data.protocol_persistent) == [
        "agents_md_instructions",
        "project_instructions",
    ]
    assert "AGENTS path rule." in loop_data.protocol_persistent["agents_md_instructions"]
    assert "Project rule." in loop_data.protocol_persistent["project_instructions"]


@pytest.mark.asyncio
async def test_project_prompt_does_not_load_agents_md_without_project(monkeypatch):
    loop_data = LoopData()

    class FakeContext:
        def get_data(self, key):
            assert key == project_prompt.projects.CONTEXT_DATA_KEY_PROJECT
            return None

    class FakeAgent:
        context = FakeContext()

        def read_prompt(self, prompt_file: str, **kwargs) -> str:
            if prompt_file == "agent.system.projects.main.md":
                return "project context may be active"
            if prompt_file == "agent.system.projects.inactive.md":
                return "no active project"
            raise AssertionError(f"Unexpected prompt file: {prompt_file}")

    monkeypatch.setattr(
        project_prompt.projects,
        "build_agents_md_protocol",
        lambda _name: (_ for _ in ()).throw(AssertionError("unexpected AGENTS load")),
    )

    await project_prompt.build_prompt.__wrapped__(  # type: ignore[attr-defined]
        FakeAgent(),
        loop_data=loop_data,
    )

    assert "agents_md_instructions" not in loop_data.protocol_persistent
    assert "project_instructions" not in loop_data.protocol_persistent


@pytest.mark.asyncio
async def test_native_communication_projection_preserves_custom_main_sections():
    from pathlib import Path
    from helpers import files, responses_tools
    from extensions.python.system_prompt._10_main_prompt import MainPrompt

    prompt_root = Path(__file__).parents[1] / 'prompts'
    legacy = files.read_prompt_file('agent.system.main.communication.md', _directories=[str(prompt_root)]).rstrip('\n')
    native = files.read_prompt_file('agent.system.main.communication.native.md', _directories=[str(prompt_root)]).rstrip('\n')
    original = f'Custom role instructions.\n{legacy}\nCustom project constraints.'
    mapping = {
        'agent.system.main.md': original,
        'agent.system.main.communication.md': legacy,
        'agent.system.main.communication.native.md': native,
    }
    agent = SimpleNamespace(read_prompt=lambda name: mapping[name])
    loop_data = LoopData()
    sections = []
    await MainPrompt(agent).execute(system_prompt=sections, loop_data=loop_data)
    assert sections == [original]
    rendered = files.remove_code_fences(original, language='json')
    result = responses_tools.project_system_prompt(
        [{'role':'system','content':rendered}], loop_data.params_temporary["responses_prompt_replacements"],
    )[0]['content']
    assert result.startswith('Custom role instructions.')
    assert result.endswith('Custom project constraints.')
    assert 'Use the provided native functions' in result
    assert 'treat the closing' not in result.lower()
    assert '"tool_name":' not in result
    assert 'closing `}`' in legacy
    assert '[PROTOCOL]' in result and '[EXTRAS]' in result
