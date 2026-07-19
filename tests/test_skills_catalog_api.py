import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._skills.api import skills_catalog


class FakeHistory:
    def __init__(self):
        self.messages = []

    def output(self):
        return self.messages


class FakeContext:
    def __init__(self):
        self.id = "ctx"
        self.data = {}
        self.agent = FakeAgent(self)

    def get_agent(self):
        return self.agent

    def get_data(self, key, recursive=True):
        return self.data.get(key)

    def set_data(self, key, value, recursive=True):
        self.data[key] = value


class FakeAgent:
    def __init__(self, context):
        self.context = context
        self.history = FakeHistory()
        self.tool_results = []

    def hist_add_tool_result(self, tool_name, tool_result, **kwargs):
        content = {"tool_name": tool_name, "tool_result": tool_result, **kwargs}
        message = {"ai": False, "content": content}
        self.tool_results.append(content)
        self.history.messages.append(message)
        return SimpleNamespace(output=lambda: [message])


def _patch_catalog(monkeypatch, context):
    skill = {
        "name": "demo-skill",
        "description": "Demo skill.",
        "path": "/a0/skills/demo-skill",
        "origin": "Built-in",
        "hidden": False,
    }

    monkeypatch.setattr(
        skills_catalog.AgentContext,
        "get",
        staticmethod(lambda context_id: context if context_id == context.id else None),
    )
    monkeypatch.setattr(
        skills_catalog.projects,
        "get_context_project_name",
        lambda _context: "",
    )
    monkeypatch.setattr(
        skills_catalog.skills,
        "list_skill_catalog",
        lambda *args, **kwargs: [skill],
    )
    monkeypatch.setattr(
        skills_catalog.skills,
        "load_skill_for_agent",
        lambda skill_name, agent: f"Skill: {skill_name}\n\nInstructions:\nUse it.",
    )
    monkeypatch.setattr(
        skills_catalog.skills,
        "add_loaded_skill_name",
        lambda agent, skill_name: agent.context.set_data("loaded_skills", [skill_name]),
    )
    monkeypatch.setattr(
        skills_catalog.skills,
        "get_loaded_skill_entries",
        lambda agent: [
            {"name": name} for name in (agent.context.get_data("loaded_skills") or [])
        ] if agent else [],
    )
    monkeypatch.setattr(skills_catalog.skills, "get_scope_active_skills", lambda agent: [])
    monkeypatch.setattr(skills_catalog.skills, "get_scope_hidden_skills", lambda agent: [])
    monkeypatch.setattr(skills_catalog.skills, "get_chat_active_skills", lambda context: [])
    monkeypatch.setattr(skills_catalog.skills, "get_chat_disabled_skills", lambda context: [])
    monkeypatch.setattr(skills_catalog.skills, "get_chat_visible_skills", lambda context: [])
    monkeypatch.setattr(skills_catalog.skills, "get_hidden_skills", lambda agent: [])
    monkeypatch.setattr(skills_catalog.skills, "get_max_active_skills", lambda **kwargs: 20)

    saved = []
    monkeypatch.setattr(skills_catalog, "save_tmp_chat", lambda ctx: saved.append(ctx.id))
    return saved


def test_skills_catalog_activate_loads_skill_into_chat_history(monkeypatch):
    context = FakeContext()
    saved = _patch_catalog(monkeypatch, context)
    handler = skills_catalog.SkillsCatalog(None, None)

    response = asyncio.run(
        handler.process(
            {
                "action": "activate",
                "context_id": "ctx",
                "skill": {"name": "demo-skill", "path": "/a0/skills/demo-skill"},
            },
            None,
        )
    )

    assert response["ok"] is True, response
    assert context.get_data("loaded_skills") == ["demo-skill"]
    assert len(context.agent.tool_results) == 1
    assert "Skill: demo-skill" in context.agent.tool_results[0]["tool_result"]
    assert response["active_skills"][0]["state_source"] == "Loaded in chat history"
    assert saved == ["ctx"]

    duplicate = asyncio.run(
        handler.process(
            {
                "action": "activate",
                "context_id": "ctx",
                "skill": {"name": "demo-skill", "path": "/a0/skills/demo-skill"},
            },
            None,
        )
    )

    assert duplicate["ok"] is True
    assert len(context.agent.tool_results) == 1


def test_skills_catalog_deactivate_does_not_remove_loaded_skill(monkeypatch):
    context = FakeContext()
    _patch_catalog(monkeypatch, context)
    context.set_data("loaded_skills", ["demo-skill"])
    handler = skills_catalog.SkillsCatalog(None, None)

    response = asyncio.run(
        handler.process(
            {
                "action": "deactivate",
                "context_id": "ctx",
                "skill": {"name": "demo-skill"},
            },
            None,
        )
    )

    assert response["ok"] is False
    assert "cannot be removed" in response["error"]
    assert context.get_data("loaded_skills") == ["demo-skill"]
    assert context.agent.tool_results == []
