from datetime import datetime, timedelta, timezone

from agent import Agent, AgentConfig, AgentContext, LoopData, UserMessage
from helpers import extension, localization, persist_chat
from helpers.localization import Localization


def test_history_activity_updates_its_context_and_survives_reload(monkeypatch):
    monkeypatch.setattr(localization, "get_dotenv_value", lambda key, default=None: default)
    monkeypatch.setattr(localization, "save_dotenv_value", lambda *args: None)
    monkeypatch.setattr(Localization, "apply_process_timezone", lambda self: None)
    monkeypatch.setattr(Localization, "_instance", Localization("UTC"))
    monkeypatch.setattr(extension, "call_extensions_sync", lambda *args, **kwargs: None)
    monkeypatch.setattr(AgentContext, "_contexts", {})
    monkeypatch.setattr(Agent, "parse_prompt", lambda self, name, **kwargs: kwargs)
    config = AgentConfig(mcp_servers="")
    monkeypatch.setattr(persist_chat, "initialize_agent", lambda **kwargs: config)
    now = datetime(2026, 9, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(Localization, "now", lambda self: now)
    parent = Agent(0, config)
    child = Agent(1, config)

    for current, other in ((parent, child), (child, parent)):
        created = current.context.created_at
        other_activity = other.context.last_message
        current.loop_data = LoopData()
        writes = (
            lambda: current.hist_add_user_message(UserMessage("hello")),
            lambda: current.hist_add_ai_response("hello back"),
            lambda: current.hist_add_tool_result("test_tool", "done"),
            lambda: current.hist_add_warning("warning"),
        )
        for write in writes:
            now += timedelta(minutes=1)
            write()
            assert current.context.last_message == now
            assert current.context.created_at == created
            assert other.context.last_message == other_activity
            assert datetime.fromisoformat(current.context.output()["last_message"]) == now

        serialized = persist_chat.export_json_chat(current.context)
        AgentContext.remove(current.context.id)
        restored_id = persist_chat.load_json_chats([serialized])[0]
        restored = AgentContext.get(restored_id)
        assert restored.last_message == now
        assert restored.created_at == created
        now += timedelta(minutes=1)
        restored.agent0.hist_add_user_message(UserMessage("continued after reload"))
        assert restored.last_message == now
        assert datetime.fromisoformat(restored.output()["last_message"]) == now
