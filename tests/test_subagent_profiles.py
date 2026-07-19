from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent import Agent, AgentConfig, AgentContext
from helpers import persist_chat
from helpers.errors import RepairableException


class _FakeContext:
    id = "ctx"

    def get_data(self, key: str, recursive: bool = True):
        return None


class _FakeParentAgent:
    def __init__(self) -> None:
        self.number = 0
        self.agent_name = "A0"
        self.config = AgentConfig(mcp_servers="", profile="agent0")
        self.context = _FakeContext()
        self.data = {}

    def get_data(self, key: str):
        return self.data.get(key)

    def set_data(self, key: str, value):
        self.data[key] = value

    def read_prompt(self, _file: str, **_kwargs) -> str:
        return ""


class _FakeSubAgent:
    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"

    def __init__(self, number: int, config: AgentConfig, context) -> None:
        self.number = number
        self.config = config
        self.context = context
        self.data = {}
        self.history = SimpleNamespace(new_topic=lambda: None)
        self.messages = []

    def set_data(self, key: str, value):
        self.data[key] = value

    def hist_add_user_message(self, message):
        self.messages.append(message)

    async def monologue(self):
        return "delegated"


@pytest.mark.asyncio
async def test_call_subordinate_rejects_unknown_profile(monkeypatch) -> None:
    import tools.call_subordinate as call_subordinate

    monkeypatch.setattr(
        call_subordinate,
        "_subordinate_profile_labels",
        lambda _agent: {"developer": "Developer", "researcher": "Researcher"},
    )
    parent = _FakeParentAgent()
    tool = call_subordinate.Delegation(
        parent,  # type: ignore[arg-type]
        "call_subordinate",
        None,
        {"profile": "ghost", "message": "work"},
        "",
        None,
    )

    with pytest.raises(RepairableException, match="Agent profile 'ghost' not found"):
        await tool.execute(message="work", profile="ghost", reset=True)

    assert parent.data == {}


@pytest.mark.asyncio
async def test_call_subordinate_uses_valid_profile(monkeypatch) -> None:
    import tools.call_subordinate as call_subordinate

    monkeypatch.setattr(call_subordinate, "Agent", _FakeSubAgent)
    monkeypatch.setattr(
        call_subordinate,
        "_subordinate_profile_labels",
        lambda _agent: {"developer": "Developer"},
    )
    monkeypatch.setattr(
        call_subordinate,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "agent0"),
        ),
    )

    parent = _FakeParentAgent()
    tool = call_subordinate.Delegation(
        parent,  # type: ignore[arg-type]
        "call_subordinate",
        None,
        {"profile": "developer", "message": "work"},
        "",
        None,
    )

    response = await tool.execute(message="work", profile="developer", reset=True)
    child = parent.get_data(_FakeSubAgent.DATA_NAME_SUBORDINATE)

    assert response.message == "delegated"
    assert child.config.profile == "developer"
    assert child.messages[0].message == "work"


@pytest.mark.asyncio
async def test_call_subordinate_requires_reset_to_change_existing_profile(monkeypatch) -> None:
    import tools.call_subordinate as call_subordinate

    monkeypatch.setattr(
        call_subordinate,
        "_subordinate_profile_labels",
        lambda _agent: {"developer": "Developer", "researcher": "Researcher"},
    )

    parent = _FakeParentAgent()
    existing = SimpleNamespace(config=AgentConfig(mcp_servers="", profile="developer"))
    parent.set_data(_FakeSubAgent.DATA_NAME_SUBORDINATE, existing)
    tool = call_subordinate.Delegation(
        parent,  # type: ignore[arg-type]
        "call_subordinate",
        None,
        {"profile": "researcher", "message": "work"},
        "",
        None,
    )

    with pytest.raises(RepairableException, match="Set reset=true"):
        await tool.execute(message="work", profile="researcher", reset=False)


def test_persist_chat_roundtrip_preserves_each_agent_profile(monkeypatch) -> None:
    monkeypatch.setattr(
        persist_chat,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "agent0"),
        ),
    )

    context_id = "ctx-subagent-profile"
    AgentContext.remove(context_id)
    context = AgentContext(
        config=AgentConfig(mcp_servers="", profile="agent0"),
        id=context_id,
        set_current=False,
    )
    child = Agent(1, AgentConfig(mcp_servers="", profile="developer"), context)
    context.agent0.set_data(Agent.DATA_NAME_SUBORDINATE, child)
    child.set_data(Agent.DATA_NAME_SUPERIOR, context.agent0)

    try:
        serialized = persist_chat._serialize_context(context)
        assert serialized["agent_profile"] == "agent0"
        assert serialized["agents"][0]["agent_profile"] == "agent0"
        assert serialized["agents"][1]["agent_profile"] == "developer"

        AgentContext.remove(context_id)
        restored = persist_chat._deserialize_context(serialized)
        restored_child = restored.agent0.get_data(Agent.DATA_NAME_SUBORDINATE)

        assert restored.config.profile == "agent0"
        assert restored.agent0.config.profile == "agent0"
        assert restored_child.config.profile == "developer"
    finally:
        AgentContext.remove(context_id)


@pytest.mark.asyncio
async def test_agent_profile_set_preserves_subagent_profile(monkeypatch) -> None:
    import api.agent_profile_set as agent_profile_set

    monkeypatch.setattr(
        agent_profile_set,
        "_agent_profile_labels",
        lambda: {"researcher": "Researcher"},
    )
    monkeypatch.setattr(
        agent_profile_set,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "agent0"),
        ),
    )
    monkeypatch.setattr(agent_profile_set, "save_tmp_chat", lambda _context: None)
    monkeypatch.setattr(
        agent_profile_set,
        "mark_dirty_for_context",
        lambda *_args, **_kwargs: None,
    )

    context_id = "ctx-profile-switch"
    AgentContext.remove(context_id)
    context = AgentContext(
        config=AgentConfig(mcp_servers="", profile="agent0"),
        id=context_id,
        set_current=False,
    )
    child = Agent(1, AgentConfig(mcp_servers="", profile="developer"), context)
    context.agent0.set_data(Agent.DATA_NAME_SUBORDINATE, child)
    child.set_data(Agent.DATA_NAME_SUPERIOR, context.agent0)

    try:
        handler = agent_profile_set.SetAgentProfile.__new__(
            agent_profile_set.SetAgentProfile
        )
        response = await handler.process(
            {"context_id": context_id, "agent_profile": "researcher"},
            request=None,  # type: ignore[arg-type]
        )

        assert response["ok"] is True
        assert context.config.profile == "researcher"
        assert context.agent0.config.profile == "researcher"
        assert child.config.profile == "developer"
    finally:
        AgentContext.remove(context_id)
