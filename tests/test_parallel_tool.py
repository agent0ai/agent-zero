from __future__ import annotations

import json
import time
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import parallel_tools
from helpers.tool import Response


class _FakeLogItem:
    def __init__(self, type_, heading="", content="", kvps=None, id_=None, **kwargs) -> None:
        self.type = type_
        self.heading = heading
        self.content = content
        self.kvps = dict(kvps or {})
        self.kvps.update(kwargs)
        self.id = id_

    def update(self, content=None, kvps=None, **kwargs):
        if content is not None:
            self.content = content
        if kvps:
            self.kvps.update(kvps)
        self.kvps.update(kwargs)


class _FakeLog:
    def __init__(self) -> None:
        self.items = []

    def log(self, type, heading="", content="", kvps=None, id=None, **kwargs):
        item = _FakeLogItem(type, heading, content, kvps, id, **kwargs)
        self.items.append(item)
        return item


class _FakeContext:
    def __init__(self) -> None:
        self.id = "ctx"
        self.data = {}
        self.log = _FakeLog()

    def get_data(self, key: str, recursive: bool = True):
        return self.data.get(key)

    def set_data(self, key: str, value, recursive: bool = True):
        self.data[key] = value


class _FakeAgent:
    def __init__(self) -> None:
        self.context = _FakeContext()
        self.agent_name = "A0"


class _FakeDeferredTask:
    def __init__(self, *, ready: bool = False, alive: bool = True, result=None) -> None:
        self.ready = ready
        self.alive = alive
        self._result = result
        self.killed = 0

    def is_ready(self):
        return self.ready

    def is_alive(self):
        return self.alive

    async def result(self):
        return self._result

    def kill(self):
        self.killed += 1
        self.alive = False


def test_normalize_parallel_tool_calls_accepts_normal_tool_request_shapes() -> None:
    calls = parallel_tools.normalize_parallel_tool_calls(
        [
            {
                "tool_name": "text_editor:read",
                "tool_args": {"path": "README.md"},
            },
            {
                "tool": "scheduler",
                "args": {"method": "list_tasks"},
            },
        ]
    )

    assert calls[0].tool_name == "text_editor"
    assert calls[0].tool_args == {"path": "README.md", "action": "read"}
    assert calls[1].tool_name == "scheduler"
    assert calls[1].tool_args == {"method": "list_tasks", "action": "list_tasks"}


def test_normalize_parallel_tool_calls_accepts_json_string_array() -> None:
    calls = parallel_tools.normalize_parallel_tool_calls(
        json.dumps(
            [
                {
                    "tool_name": "call_subordinate",
                    "tool_args": {
                        "profile": "researcher",
                        "reset": True,
                        "message": "Research nuclear fusion news in French.",
                    },
                    "headline": "Researching nuclear fusion news in French",
                },
                {
                    "tool_name": "call_subordinate",
                    "tool_args": {
                        "profile": "researcher",
                        "reset": True,
                        "message": "Research nuclear fusion news in Italian.",
                    },
                    "headline": "Researching nuclear fusion news in Italian",
                },
            ]
        )
    )

    assert [call.tool_name for call in calls] == [
        "call_subordinate",
        "call_subordinate",
    ]
    assert calls[0].tool_args["profile"] == "researcher"
    assert calls[0].tool_args["reset"] is True
    assert calls[1].tool_args["message"] == "Research nuclear fusion news in Italian."


def test_normalize_parallel_tool_calls_rejects_nested_parallel() -> None:
    with pytest.raises(ValueError, match="cannot be nested"):
        parallel_tools.normalize_parallel_tool_calls(
            [{"tool_name": "parallel", "tool_args": {"tool_calls": []}}]
        )


def test_normalize_parallel_tool_calls_rejects_document_query() -> None:
    with pytest.raises(ValueError, match="document_query.*parallel"):
        parallel_tools.normalize_parallel_tool_calls(
            [
                {
                    "tool_name": "document_query",
                    "tool_args": {"document": "/tmp/report.pdf"},
                }
            ]
        )


@pytest.mark.asyncio
async def test_parallel_jobs_extras_lists_running_and_ready_jobs() -> None:
    agent = _FakeAgent()
    running = parallel_tools.ParallelJob(
        id="search-1234abcd",
        parent_context_id="ctx",
        index=0,
        tool_name="search_engine",
        tool_args={"query": "Agent Zero"},
        kind="tool",
        state="running",
        started_at=time.time() - 2,
    )
    ready = parallel_tools.ParallelJob(
        id="callsubordin-5678efgh",
        parent_context_id="ctx",
        index=1,
        tool_name="call_subordinate",
        tool_args={"message": "Summarize"},
        kind="subordinate",
        state="success",
        started_at=time.time() - 4,
        completed_at=time.time() - 1,
        result="done",
    )
    agent.context.set_data(
        parallel_tools.PARALLEL_JOBS_KEY,
        {running.id: running, ready.id: ready},
    )

    extras = await parallel_tools.build_parallel_jobs_extras(agent)  # type: ignore[arg-type]

    assert "search-1234abcd" in extras
    assert "callsubordin-5678efgh" in extras
    assert "ready to collect" in extras


@pytest.mark.asyncio
async def test_parallel_await_timeout_keeps_running_jobs_awaitable(monkeypatch) -> None:
    agent = _FakeAgent()
    task = _FakeDeferredTask(alive=True)
    job = parallel_tools.ParallelJob(
        id="wait-1234abcd",
        parent_context_id="ctx",
        index=0,
        tool_name="wait",
        tool_args={"seconds": 60},
        kind="tool",
        state="running",
        created_at=99.0,
        started_at=99.0,
        deferred_task=task,  # type: ignore[arg-type]
    )
    agent.context.set_data(parallel_tools.PARALLEL_JOBS_KEY, {job.id: job})
    times = iter([100.0, 102.0])
    monkeypatch.setattr(
        parallel_tools.time,
        "time",
        lambda: next(times, 102.0),
    )

    results = await parallel_tools.await_parallel_jobs(  # type: ignore[arg-type]
        agent,
        [job.id],
        timeout=1,
        collect=True,
        wait=True,
    )
    payload = json.loads(parallel_tools.format_parallel_results(results))

    assert results[0]["state"] == "running"
    assert results[0]["wait_timed_out"] is True
    assert payload["status"] == "waiting"
    assert payload["wait_timeout"] is True
    assert "await" in payload["instruction"]
    assert task.killed == 0
    assert agent.context.get_data(parallel_tools.PARALLEL_JOBS_KEY)[job.id] is job


@pytest.mark.asyncio
async def test_parallel_collect_returns_running_jobs_without_waiting_or_canceling() -> None:
    from tools.parallel import ParallelTool

    agent = _FakeAgent()
    task = _FakeDeferredTask(alive=True)
    job = parallel_tools.ParallelJob(
        id="wait-collect",
        parent_context_id="ctx",
        index=0,
        tool_name="wait",
        tool_args={"seconds": 60},
        kind="tool",
        state="running",
        deferred_task=task,  # type: ignore[arg-type]
    )
    agent.context.set_data(parallel_tools.PARALLEL_JOBS_KEY, {job.id: job})
    tool = ParallelTool(
        agent,  # type: ignore[arg-type]
        "parallel",
        None,
        {"action": "collect", "job_ids": [job.id]},
        "",
        None,
    )

    response = await tool.execute(**tool.args)
    payload = json.loads(response.message)

    assert payload["status"] == "running"
    assert payload["jobs"][0]["job_id"] == job.id
    assert "wait_timeout" not in payload
    assert task.killed == 0
    assert agent.context.get_data(parallel_tools.PARALLEL_JOBS_KEY)[job.id] is job


@pytest.mark.asyncio
async def test_parallel_cancel_still_stops_and_removes_running_jobs() -> None:
    agent = _FakeAgent()
    task = _FakeDeferredTask(alive=True)
    job = parallel_tools.ParallelJob(
        id="wait-cancel",
        parent_context_id="ctx",
        index=0,
        tool_name="wait",
        tool_args={"seconds": 60},
        kind="tool",
        state="running",
        deferred_task=task,  # type: ignore[arg-type]
    )
    agent.context.set_data(parallel_tools.PARALLEL_JOBS_KEY, {job.id: job})

    results = await parallel_tools.cancel_parallel_jobs(agent, [job.id])  # type: ignore[arg-type]
    payload = json.loads(parallel_tools.format_parallel_results(results))

    assert results[0]["state"] == "cancelled"
    assert payload["status"] == "cancelled"
    assert task.killed == 1
    assert job.id not in agent.context.get_data(parallel_tools.PARALLEL_JOBS_KEY)


@pytest.mark.asyncio
async def test_parallel_remove_context_deletes_persisted_worker_chat(monkeypatch) -> None:
    removed = []

    from helpers import persist_chat

    monkeypatch.setattr(persist_chat, "remove_chat", removed.append)

    await parallel_tools._remove_context("missing-worker")

    assert removed == ["missing-worker"]


@pytest.mark.asyncio
async def test_parallel_recursion_guard_allows_subordinate_children_but_blocks_tool_workers() -> None:
    from extensions.python.tool_execute_before._20_block_parallel_recursion import (
        BlockParallelRecursion,
    )
    from helpers.errors import RepairableException

    agent = _FakeAgent()
    agent.context.set_data(parallel_tools.PARALLEL_WORKER_JOB_KEY, "legacy-job")
    assert parallel_tools.is_parallel_worker(agent) is True  # type: ignore[arg-type]

    agent.context.set_data(parallel_tools.PARALLEL_WORKER_KIND_KEY, "subordinate")
    assert parallel_tools.is_parallel_worker(agent) is False  # type: ignore[arg-type]
    await BlockParallelRecursion(agent=agent).execute(tool_name="parallel")  # type: ignore[arg-type]

    agent.context.set_data(parallel_tools.PARALLEL_WORKER_KIND_KEY, "tool")
    assert parallel_tools.is_parallel_worker(agent) is True  # type: ignore[arg-type]
    with pytest.raises(RepairableException, match="cannot be used inside a parallel worker"):
        await BlockParallelRecursion(agent=agent).execute(tool_name="parallel")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_parallel_subordinate_jobs_are_visible_child_logs_not_scheduler_tasks(monkeypatch) -> None:
    class FakeDeferredTask:
        def __init__(self, thread_name=None) -> None:
            self.thread_name = thread_name
            self.started = None

        def start_task(self, func, *args):
            self.started = (func, args)
            return self

        def is_ready(self):
            return False

        def is_alive(self):
            return True

        def kill(self):
            pass

    monkeypatch.setattr(parallel_tools, "DeferredTask", FakeDeferredTask)
    agent = _FakeAgent()

    jobs = await parallel_tools.start_parallel_jobs(
        agent,  # type: ignore[arg-type]
        [
            parallel_tools.NormalizedToolCall(
                index=0,
                tool_name="call_subordinate",
                tool_args={
                    "profile": "developer",
                    "message": "Return ALPHA=1",
                    "reset": True,
                },
            )
        ],
    )

    assert jobs[0].kind == "subordinate"
    snapshot = parallel_tools._job_snapshot(jobs[0], include_result=False)
    assert "scheduler_task_uuid" not in snapshot
    assert agent.context.log.items[0].type == "subagent"
    assert agent.context.log.items[0].kvps == {
        "profile": "developer",
        "message": "Return ALPHA=1",
        "reset": True,
    }
    assert "id" not in agent.context.log.items[0].kvps
    assert "tool_name" not in agent.context.log.items[0].kvps
    assert "parallel_child" not in agent.context.log.items[0].kvps


@pytest.mark.asyncio
async def test_parallel_direct_tool_jobs_fallback_to_generic_tool_log_type(monkeypatch) -> None:
    class FakeDeferredTask:
        def __init__(self, thread_name=None) -> None:
            self.thread_name = thread_name
            self.started = None

        def start_task(self, func, *args):
            self.started = (func, args)
            return self

        def is_ready(self):
            return False

        def is_alive(self):
            return True

        def kill(self):
            pass

    monkeypatch.setattr(parallel_tools, "DeferredTask", FakeDeferredTask)
    monkeypatch.setattr(parallel_tools, "_resolve_parallel_tool", lambda *_args, **_kwargs: None)
    agent = _FakeAgent()

    jobs = await parallel_tools.start_parallel_jobs(
        agent,  # type: ignore[arg-type]
        [
            parallel_tools.NormalizedToolCall(
                index=0,
                tool_name="wait",
                tool_args={"seconds": 1},
            )
        ],
    )

    assert jobs[0].kind == "tool"
    assert agent.context.log.items[0].type == "tool"
    assert agent.context.log.items[0].kvps == {"seconds": 1, "_tool_name": "wait"}

    parallel_tools._finish_job(jobs[0], "success", result="done")

    assert agent.context.log.items[0].content == "done"
    assert agent.context.log.items[0].kvps == {"seconds": 1, "_tool_name": "wait"}


@pytest.mark.asyncio
async def test_parallel_code_execution_child_uses_code_exe_log_type(monkeypatch) -> None:
    class FakeDeferredTask:
        def __init__(self, thread_name=None) -> None:
            self.thread_name = thread_name

        def start_task(self, func, *args):
            return self

        def is_ready(self):
            return False

        def is_alive(self):
            return True

        def kill(self):
            pass

    class FakeCodeExecutionTool:
        def __init__(self, agent, args):
            self.agent = agent
            self.args = args

        def get_log_object(self):
            runtime = self.args.get("runtime", "unknown")
            session = self.args.get("session", None)
            session_text = f"[{session}] " if session or session == 0 else ""
            return self.agent.context.log.log(
                type="code_exe",
                heading=f"icon://terminal {session_text}code_execution_tool - {runtime}",
                content="",
                kvps=self.args,
            )

    monkeypatch.setattr(parallel_tools, "DeferredTask", FakeDeferredTask)
    monkeypatch.setattr(
        parallel_tools,
        "_resolve_parallel_tool",
        lambda _agent, _tool_name, args: FakeCodeExecutionTool(_agent, args),
    )
    agent = _FakeAgent()

    jobs = await parallel_tools.start_parallel_jobs(
        agent,  # type: ignore[arg-type]
        [
            parallel_tools.NormalizedToolCall(
                index=0,
                tool_name="code_execution_tool",
                tool_args={
                    "runtime": "terminal",
                    "session": 0,
                    "code": "pwd",
                },
            )
        ],
    )

    assert jobs[0].kind == "tool"
    assert agent.context.log.items[0].type == "code_exe"
    assert agent.context.log.items[0].heading == "icon://terminal [0] code_execution_tool - terminal"
    assert agent.context.log.items[0].kvps == {
        "runtime": "terminal",
        "session": 0,
        "code": "pwd",
    }


@pytest.mark.asyncio
async def test_parallel_wait_child_uses_wait_log_type(monkeypatch) -> None:
    class FakeDeferredTask:
        def __init__(self, thread_name=None) -> None:
            self.thread_name = thread_name

        def start_task(self, func, *args):
            return self

        def is_ready(self):
            return False

        def is_alive(self):
            return True

        def kill(self):
            pass

    class FakeWaitTool:
        def __init__(self, agent, args):
            self.agent = agent
            self.args = args

        def get_log_object(self):
            return self.agent.context.log.log(
                type="progress",
                heading="icon://timer Wait: Waiting...",
                content="",
                kvps=self.args,
            )

    monkeypatch.setattr(parallel_tools, "DeferredTask", FakeDeferredTask)
    monkeypatch.setattr(
        parallel_tools,
        "_resolve_parallel_tool",
        lambda _agent, _tool_name, args: FakeWaitTool(_agent, args),
    )
    agent = _FakeAgent()

    jobs = await parallel_tools.start_parallel_jobs(
        agent,  # type: ignore[arg-type]
        [
            parallel_tools.NormalizedToolCall(
                index=0,
                tool_name="wait",
                tool_args={"seconds": 1},
            )
        ],
    )

    assert jobs[0].kind == "tool"
    assert agent.context.log.items[0].type == "progress"
    assert agent.context.log.items[0].heading == "icon://timer Wait: Waiting..."
    assert agent.context.log.items[0].kvps == {"seconds": 1}


@pytest.mark.asyncio
async def test_parallel_execute_reuses_child_log_object(monkeypatch) -> None:
    class FakeTool:
        def __init__(self, agent, args):
            self.agent = agent
            self.args = args

        def get_log_object(self):
            return self.agent.context.log.log(
                type="tool",
                heading="generic tool log",
                content="",
                kvps=self.args,
            )

        async def before_execution(self, **kwargs):
            self.log = self.get_log_object()

        async def execute(self, **kwargs):
            return Response(message="done", break_loop=False)

        async def after_execution(self, response):
            self.log.update(content=response.message)

    class FakeWorkerAgent(_FakeAgent):
        def __init__(self) -> None:
            super().__init__()
            self.loop_data = SimpleNamespace(current_tool=None)

        def get_tool(self, **kwargs):
            return FakeTool(self, kwargs["args"])

        async def handle_intervention(self):
            pass

    async def noop_extensions(*_args, **_kwargs):
        pass

    monkeypatch.setattr(parallel_tools, "call_extensions_async", noop_extensions)

    agent = FakeWorkerAgent()
    child_log = agent.context.log.log(
        type="progress",
        heading="icon://timer Wait: Waiting...",
        content="",
        kvps={"seconds": 1},
    )

    result = await parallel_tools.execute_tool_call(
        agent,  # type: ignore[arg-type]
        "wait",
        {"seconds": 1},
        log_item=child_log,
    )

    assert result == "done"
    assert agent.context.log.items == [child_log]
    assert child_log.type == "progress"
    assert child_log.content == "done"


@pytest.mark.asyncio
async def test_parallel_tool_keeps_wrapper_out_of_visible_log() -> None:
    from tools.parallel import ParallelTool

    class HistoryAgent(_FakeAgent):
        def __init__(self) -> None:
            super().__init__()
            self.tool_results = []

        def hist_add_tool_result(self, tool_name, tool_result, **kwargs):
            self.tool_results.append((tool_name, tool_result, kwargs))

    agent = HistoryAgent()
    tool = ParallelTool(agent, "parallel", None, {}, "", None)  # type: ignore[arg-type]

    await tool.before_execution()
    await tool.after_execution(Response(message="done", break_loop=False, additional={"extra": "value"}))

    assert agent.context.log.items == []
    assert agent.tool_results == [("parallel", "done", {"extra": "value"})]


@pytest.mark.asyncio
async def test_parallel_child_contexts_are_chats_not_tasks(monkeypatch) -> None:
    from agent import AgentContext
    from initialize import initialize_agent
    from helpers import state_snapshot

    class NoTaskScheduler:
        def get_task_by_uuid(self, _task_id):
            return None

    monkeypatch.setattr(
        state_snapshot,
        "TaskScheduler",
        SimpleNamespace(get=lambda: NoTaskScheduler()),
    )

    parent_id = "ctx-par-parent"
    child_id = "ctx-par-child"
    parent = AgentContext(config=initialize_agent(), id=parent_id, name="Parent", set_current=False)
    child = AgentContext(config=initialize_agent(), id=child_id, name="Child", set_current=False)
    try:
        child.set_output_data(parallel_tools.CHILD_PARENT_CONTEXT_ID_KEY, parent.id)
        child.set_output_data(parallel_tools.CHILD_PARENT_CONTEXT_KIND_KEY, "parallel")
        child.set_output_data(parallel_tools.CHILD_PARENT_CONTEXT_LABEL_KEY, "Child task")
        child.set_output_data(parallel_tools.CHILD_PARALLEL_JOB_ID_KEY, "job-123")

        payload = await state_snapshot.build_snapshot(
            context=parent.id,
            log_from=0,
            notifications_from=0,
            timezone="UTC",
        )

        contexts_by_id = {ctx["id"]: ctx for ctx in payload["contexts"]}
        task_ids = {task["id"] for task in payload["tasks"]}
        assert parent_id in contexts_by_id
        assert child_id in contexts_by_id
        assert contexts_by_id[child_id]["parent_context_id"] == parent_id
        assert child_id not in task_ids
    finally:
        AgentContext.remove(parent_id)
        AgentContext.remove(child_id)


def test_chats_sidebar_projects_parallel_children_as_indented_accordion() -> None:
    store = (PROJECT_ROOT / "webui/components/sidebar/chats/chats-store.js").read_text(
        encoding="utf-8"
    )
    html = (PROJECT_ROOT / "webui/components/sidebar/chats/chats-list.html").read_text(
        encoding="utf-8"
    )

    assert "parent_context_id" in store
    assert "const nextExpandedParents = { ...this.expandedParents };" in store
    assert "nextExpandedParents[selectedId] === undefined" in store
    assert "nextExpandedParents[selectedId] = true;" in store
    assert "topLevelContexts()" in html
    assert "childContexts(context.id)" in html
    assert "chat-child-container" in html
    assert "keyboard_arrow_up" in html
    assert "keyboard_arrow_down" in html
    assert ".chats-config-list .chat-tree-item" in html
    assert ".chats-config-list .chat-child-list > li" in html
    assert 'x-show="$store.chats.hasChildren(context.id)"' in html
    assert "'chat-has-children': $store.chats.hasChildren(context.id)" in html
    assert ".chat-container.chat-has-children .chat-list-button" in html
    assert "left: 2px" in html
    assert "padding-left: 24px" in html
    assert "color: var(--color-text-muted)" in html
    assert "padding: 8px;" in html
