import asyncio
from types import SimpleNamespace


def test_explicit_new_chat_project_overrides_inheritance_and_validates_first(monkeypatch):
    from api import chat_create
    from helpers import state_monitor_integration

    current = SimpleNamespace(get_data=lambda key: "old" if key == "project" else None,
                              get_output_data=lambda key: {"name": "old"})
    new = SimpleNamespace(id="new", set_data=lambda *args: None, set_output_data=lambda *args: None)
    monkeypatch.setattr(chat_create.AgentContext, "get", lambda id: current)
    monkeypatch.setattr(chat_create.settings, "get_settings", lambda: {"chat_inherit_project": True})
    monkeypatch.setattr(chat_create.projects, "load_basic_project_data", lambda name: {})
    monkeypatch.setattr(chat_create.projects, "get_context_project_name", lambda context: None)
    monkeypatch.setattr(chat_create.projects, "reconcile_agent_profile", lambda *args: None)
    monkeypatch.setattr(state_monitor_integration, "mark_dirty_all", lambda **kwargs: None)
    created, assigned = [], []
    handler = chat_create.CreateChat(None, None)
    monkeypatch.setattr(handler, "use_context", lambda id: created.append(id) or new)
    monkeypatch.setattr(chat_create.projects, "activate_project", lambda id, name, **kwargs: assigned.append(name))
    monkeypatch.setattr(chat_create.projects, "deactivate_project", lambda id, **kwargs: assigned.append(""))

    for name in ("project-b", ""):
        result = asyncio.run(handler.process({"current_context": "old", "project_name": name}, None))
        assert result["ctxid"] == "new"
    assert assigned == ["project-b", ""]
    created.clear()
    for name in ("../escape", None, {}):
        result = asyncio.run(handler.process({"project_name": name}, None))
        assert result.status_code == 400
    assert created == []
