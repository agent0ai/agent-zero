import asyncio
import threading
from types import SimpleNamespace


from plugins._sidebar_folders.api import layout, move_chat


def test_layout_persists_independent_lists_and_rejects_bad_input(monkeypatch):
    saved = {}
    monkeypatch.setattr(layout.kvp, "get_persistent", lambda *args: saved)
    monkeypatch.setattr(layout.kvp, "set_persistent", lambda key, value: saved.update(value))
    handler = layout.Layout(None, None)

    def call(**data):
        return asyncio.run(handler.process(data, None))

    assert call(action="save", kind="project", ids=["b", "", "a"])["ok"]
    assert call(action="save", kind="chat", ids=["c2", "c1"])["ok"]
    assert call()["order"] == {"project": ["b", "", "a"], "chat": ["c2", "c1"], "task": []}
    for ids in (["a", "a"], [None], "a", ["x" * 513]):
        assert call(action="save", kind="chat", ids=ids).status_code == 400
    assert call(action="save", kind="invalid", ids=[]).status_code == 400


def test_chat_moves_keep_parallel_family_and_restore_failed_moves(monkeypatch):
    def context(id, parent=None, background=False):
        item = SimpleNamespace(
            id=id, data={"project": "old"}, output_data={"project": {"name": "old"}},
            config=object(), agent0=SimpleNamespace(config=None), running=False,
            type=move_chat.AgentContextType.USER,
        )
        if parent:
            (item.data if background else item.output_data)[
                "_parallel_parent_context_id" if background else "parent_context_id"
            ] = parent
        item.get_data = item.data.get
        item.get_output_data = lambda key: item.output_data.get(key)
        item.is_running = lambda: item.running
        return item

    root, child, worker, other = context("root"), context("child", "root"), context("worker", "child", True), context("other")
    contexts = {item.id: item for item in [root, child, worker, other]}
    monkeypatch.setattr(move_chat.AgentContext, "all", lambda: list(contexts.values()))
    monkeypatch.setattr(move_chat.AgentContext, "get", contexts.get)
    task_ids = set()
    monkeypatch.setattr(move_chat.TaskScheduler, "get", lambda: SimpleNamespace(get_task_by_uuid=lambda id: id in task_ids))
    monkeypatch.setattr(move_chat.projects, "load_basic_project_data", lambda name: {})
    persisted = []
    monkeypatch.setattr(move_chat.persist_chat, "save_tmp_chat", lambda item: persisted.append(item.id))
    monkeypatch.setattr(move_chat, "mark_dirty_all", lambda **kwargs: None)

    def assign(id, name, **kwargs):
        contexts[id].data["project"] = name
        contexts[id].output_data["project"] = {"name": name} if name else None
        persisted.append(id)

    monkeypatch.setattr(move_chat.projects, "activate_project", assign)
    monkeypatch.setattr(move_chat.projects, "deactivate_project", lambda id, **kwargs: assign(id, None))
    handler = move_chat.MoveChat(None, threading.RLock())

    def move(id="child", project="new"):
        return asyncio.run(handler.process({"context_id": id, "project_name": project}, None))

    assert move()["context_ids"] == ["root", "child", "worker"]
    assert [item.data["project"] for item in [root, child, worker, other]] == ["new", "new", "new", "old"]
    assert child.output_data["parent_context_id"] == "root"
    assert move(project="")["project"] is None
    child.running = True
    persisted.clear()
    assert move().status_code == 409
    assert persisted == []
    child.running = False
    task_ids.add("root")
    assert move().status_code == 409
    task_ids.clear()
    assert move(id="missing").status_code == 404
    assert move(project="../escape").status_code == 400

    def failing_assign(id, name, **kwargs):
        assign(id, name)
        if id == "child":
            raise OSError("test write failure")

    monkeypatch.setattr(move_chat.projects, "activate_project", failing_assign)
    assert move().status_code == 500
    assert all(item.data["project"] is None for item in [root, child, worker])
