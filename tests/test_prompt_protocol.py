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

    input_items = Agent._responses_prompt_input_items(
        agent,
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
