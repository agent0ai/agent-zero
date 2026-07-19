from types import SimpleNamespace

from agent import AgentContextType
from extensions.python.hist_add_tool_result._90_save_tool_call_file import SaveToolCallFile


def test_tool_result_file_persistence_skips_background_context(tmp_path, monkeypatch) -> None:
    target = tmp_path / "messages"
    agent = SimpleNamespace(
        context=SimpleNamespace(id="background-worker", type=AgentContextType.BACKGROUND)
    )
    data = {"tool_result": "x" * 501}

    monkeypatch.setattr(
        "extensions.python.hist_add_tool_result._90_save_tool_call_file.persist_chat.get_chat_msg_files_folder",
        lambda _ctxid: str(target),
    )

    SaveToolCallFile(agent=agent).execute(data=data)

    assert "file" not in data
    assert not target.exists()
