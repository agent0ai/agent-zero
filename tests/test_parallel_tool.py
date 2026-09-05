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
        self.task = None

    def get_data(self, key: str, recursive: bool = True):
        return self.data.get(key)

    def set_data(self, key: str, value, recursive: bool = True):
        self.data[key] = value


class _FakeAgent:
    def __init__(self) -> None:
        self.context = _FakeContext()
        self.agent_name = "A0"
        self.number = 0


class _FakeDeferredTask:
    def __init__(
        self,
        *,
        ready: bool = False,
        alive: bool = True,
        result=None,
        thread_name=None,
    ) -> None:
        self.ready = ready
        self.alive = alive
        self._result = result
        self.killed = 0
        self.thread_name = thread_name
        self.started = None
        self.children = []

    def start_task(self, func, *args):
        self.started = (func, args)
        return self

    def is_ready(self):
        return self.ready

    def is_alive(self):
        return self.alive

    async def result(self):
        return self._result

    def kill(self):
        self.killed += 1
        self.alive = False
        for child in self.children:
            child.kill()
        self.children = []

    def add_child_task(self, task, terminate_thread=False):
        self.children.append(task)


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


def test_subordinate_prompts_share_reusable_tree_contract() -> None:
    call_prompt = (PROJECT_ROOT / "prompts/agent.system.tool.call_sub.md").read_text(
        encoding="utf-8"
    )
    parallel_prompt = (PROJECT_ROOT / "prompts/agent.system.tool.parallel.md").read_text(
        encoding="utf-8"
    )

    assert "A0 creates A1 children, A1 creates A2 children" in call_prompt
    assert "stable child ID" in call_prompt
    assert "same child lifecycle here as it does top-level" in parallel_prompt
    assert "each job's `context_id`" in parallel_prompt


def test_normalize_parallel_tool_calls_rejects_nested_parallel() -> None:
    with pytest.raises(ValueError, match="cannot be nested"):
        parallel_tools.normalize_parallel_tool_calls(
            [{"tool_name": "parallel", "tool_args": {"tool_calls": []}}]
        )


@pytest.mark.parametrize("tool_name", ["document_query", "response"])
def test_normalize_parallel_tool_calls_rejects_disallowed_tools(tool_name: str) -> None:
    with pytest.raises(ValueError, match=rf"{tool_name}.*parallel"):
        parallel_tools.normalize_parallel_tool_calls(
            [
                {
                    "tool_name": tool_name,
                    "tool_args": {},
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
async def test_direct_parallel_worker_inherits_chat_model_override(monkeypatch) -> None:
    from agent import AgentConfig, AgentContext

    parent_id = "ctx-parallel-model-override"
    AgentContext.remove(parent_id)
    parent = AgentContext(
        AgentConfig(mcp_servers="", profile="agent0"),
        id=parent_id,
        set_current=False,
    )
    override = {"preset_name": "Text only"}
    parent.set_data("chat_model_override", override)
    current_user_message = object()
    parent.agent0.last_user_message = current_user_message
    observed = {}

    async def fake_execute_tool_call(agent, *_args, **_kwargs):
        observed["override"] = agent.context.get_data("chat_model_override")
        observed["last_user_message"] = agent.last_user_message
        return "done"

    async def remove_context(context_id):
        AgentContext.remove(context_id)

    monkeypatch.setattr(parallel_tools, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(parallel_tools, "_remove_context", remove_context)
    job = parallel_tools.ParallelJob(
        id="vision-load-override",
        parent_context_id=parent_id,
        index=0,
        tool_name="vision_load",
        tool_args={"paths": ["/tmp/example.png"]},
        kind="tool",
    )

    try:
        assert await parallel_tools._run_direct_tool_job(parent_id, job) == "done"
        assert observed["override"] == override
        assert observed["last_user_message"] is current_user_message
    finally:
        AgentContext.remove(parent_id)


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
async def test_parallel_subordinate_enforces_parent_delegation_policy(
    monkeypatch,
) -> None:
    from agent import AgentContext
    from helpers import tool_policy
    from helpers.errors import RepairableException

    parent_agent = SimpleNamespace(
        config=SimpleNamespace(profile="restricted"),
        context=_FakeContext(),
    )
    parent_context = SimpleNamespace(agent0=parent_agent)
    monkeypatch.setattr(
        AgentContext,
        "get",
        staticmethod(lambda _context_id: parent_context),
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "custom",
            "default": "allow",
            "allowed": [],
            "blocked": ["local:call_subordinate"],
        },
    )
    job = parallel_tools.ParallelJob(
        id="callsubordin-blocked",
        parent_context_id="ctx",
        index=0,
        tool_name="call_subordinate",
        tool_args={"profile": "developer", "message": "Work"},
        kind="subordinate",
    )

    with pytest.raises(
        RepairableException,
        match='Tool "call_subordinate" is blocked for agent profile "restricted"',
    ):
        await parallel_tools._run_subordinate_context_job("ctx", job)


@pytest.mark.asyncio
async def test_parallel_subordinate_reuses_profile_validation(monkeypatch) -> None:
    from agent import AgentContext
    from helpers import tool_policy
    from helpers.errors import RepairableException
    from tools import call_subordinate

    parent_agent = SimpleNamespace(
        config=SimpleNamespace(profile="agent0"),
        context=_FakeContext(),
    )
    parent_context = SimpleNamespace(agent0=parent_agent)
    monkeypatch.setattr(
        AgentContext,
        "get",
        staticmethod(lambda _context_id: parent_context),
    )
    monkeypatch.setattr(tool_policy.subagents, "get_paths", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "inherit",
            "default": "allow",
            "allowed": [],
            "blocked": [],
        },
    )
    monkeypatch.setattr(
        call_subordinate.subagents,
        "get_available_agents_dict",
        lambda project_name: {"developer": SimpleNamespace(title="Developer")},
    )
    job = parallel_tools.ParallelJob(
        id="callsubordin-invalid",
        parent_context_id="ctx",
        index=0,
        tool_name="call_subordinate",
        tool_args={"profile": "ghost", "message": "Work"},
        kind="subordinate",
    )

    with pytest.raises(RepairableException, match="Agent profile 'ghost' not found"):
        await parallel_tools._run_subordinate_context_job("ctx", job)


@pytest.mark.asyncio
async def test_parallel_subordinates_are_distinct_reusable_a1_children(monkeypatch) -> None:
    from agent import Agent, AgentConfig, AgentContext
    from helpers import message_queue, persist_chat, tool_policy

    parent_id = "ctx-parallel-a1-tree"
    AgentContext.remove(parent_id)
    parent = AgentContext(
        AgentConfig(mcp_servers="", profile="agent0"),
        id=parent_id,
        set_current=False,
    )

    async def fake_monologue(agent):
        return agent.agent_name

    monkeypatch.setattr(Agent, "monologue", fake_monologue)
    monkeypatch.setattr(tool_policy, "ensure_tool_allowed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(message_queue, "log_user_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(persist_chat, "save_tmp_chat", lambda _context: None)

    child_ids = []
    try:
        jobs = await parallel_tools.start_parallel_jobs(
            parent.agent0,
            [
                parallel_tools.NormalizedToolCall(
                    index=0,
                    tool_name="call_subordinate",
                    tool_args={"message": "left branch", "reset": True},
                ),
                parallel_tools.NormalizedToolCall(
                    index=1,
                    tool_name="call_subordinate",
                    tool_args={"message": "right branch", "reset": True},
                ),
            ],
        )
        results = await parallel_tools.await_parallel_jobs(
            parent.agent0,
            [job.id for job in jobs],
            timeout=10,
        )
        child_ids = [result["context_id"] for result in results]

        assert [result["state"] for result in results] == ["success", "success"]
        assert [result["result"] for result in results] == ["A1", "A1"]
        assert len(set(child_ids)) == 2
        assert set(parent.agent0.get_data("_subordinates")) == set(child_ids)
        for child_id in child_ids:
            child = AgentContext.get(child_id)
            assert child is not None
            assert child.agent0.number == 1
            assert child.get_output_data("parent_context_id") == parent.id
            assert child.get_output_data("parent_agent_number") == 0
            assert child.get_output_data("parent_context_kind") == "subordinate"
    finally:
        for child_id in child_ids:
            AgentContext.remove(child_id)
        AgentContext.remove(parent_id)


@pytest.mark.asyncio
async def test_failed_parallel_subordinate_continues_directly_or_in_parallel(
    monkeypatch,
) -> None:
    from agent import Agent, AgentConfig, AgentContext
    from helpers import message_queue, persist_chat, tool_policy
    from tools.call_subordinate import Delegation

    parent_id = "ctx-parallel-resume-tree"
    AgentContext.remove(parent_id)
    parent = AgentContext(
        AgentConfig(mcp_servers="", profile="agent0"),
        id=parent_id,
        set_current=False,
    )
    calls = {}

    async def flaky_monologue(agent):
        count = calls.get(agent.context.id, 0) + 1
        calls[agent.context.id] = count
        if count == 1:
            raise RuntimeError("simulated API failure")
        return f"{agent.agent_name} continuation {count}"

    monkeypatch.setattr(Agent, "monologue", flaky_monologue)
    monkeypatch.setattr(tool_policy, "ensure_tool_allowed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(message_queue, "log_user_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(persist_chat, "save_tmp_chat", lambda _context: None)

    child_id = ""
    try:
        failed = parallel_tools.ParallelJob(
            id="callsubordin-failed",
            parent_context_id=parent.id,
            index=0,
            tool_name="call_subordinate",
            tool_args={"message": "remember ALPHA", "reset": True},
            kind="subordinate",
            parent_agent=parent.agent0,
        )
        parallel_tools._jobs_for_context(parent)[failed.id] = failed
        await parallel_tools._run_parallel_job(parent.id, failed.id)
        child_id = failed.worker_context_id or ""

        assert failed.state == "error"
        assert failed.error == "simulated API failure"
        assert child_id
        assert AgentContext.get(child_id).agent0.number == 1  # type: ignore[union-attr]

        direct = Delegation(
            parent.agent0,
            "call_subordinate",
            None,
            {},
            "",
            None,
        )
        direct_result = await direct.execute(
            message="continue after the API failure",
            context_id=child_id,
            reset=False,
        )
        assert direct_result.message == "A1 continuation 2"
        assert direct_result.additional == {"context_id": child_id}

        continued = parallel_tools.ParallelJob(
            id="callsubordin-continued",
            parent_context_id=parent.id,
            index=0,
            tool_name="call_subordinate",
            tool_args={
                "message": "continue once more",
                "context_id": child_id,
                "reset": False,
            },
            kind="subordinate",
            parent_agent=parent.agent0,
        )
        parallel_tools._jobs_for_context(parent)[continued.id] = continued
        await parallel_tools._run_parallel_job(parent.id, continued.id)

        assert continued.state == "success"
        assert continued.worker_context_id == child_id
        assert continued.result == "A1 continuation 3"
        assert calls == {child_id: 3}
    finally:
        if child_id:
            AgentContext.remove(child_id)
        AgentContext.remove(parent_id)


@pytest.mark.asyncio
async def test_parallel_a1_spawns_a2_with_same_lifecycle(monkeypatch) -> None:
    from agent import Agent, AgentConfig, AgentContext
    from helpers import message_queue, persist_chat, tool_policy

    parent_id = "ctx-parallel-a2-tree"
    AgentContext.remove(parent_id)
    parent = AgentContext(
        AgentConfig(mcp_servers="", profile="agent0"),
        id=parent_id,
        set_current=False,
    )

    async def fake_monologue(agent):
        return agent.agent_name

    monkeypatch.setattr(Agent, "monologue", fake_monologue)
    monkeypatch.setattr(tool_policy, "ensure_tool_allowed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(message_queue, "log_user_message", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(persist_chat, "save_tmp_chat", lambda _context: None)

    child_ids = []
    try:
        a1_job = parallel_tools.ParallelJob(
            id="callsubordin-a1",
            parent_context_id=parent.id,
            index=0,
            tool_name="call_subordinate",
            tool_args={"message": "be A1", "reset": True},
            kind="subordinate",
            parent_agent=parent.agent0,
        )
        a1_result = await parallel_tools._run_subordinate_context_job(parent.id, a1_job)
        a1 = AgentContext.get(a1_job.worker_context_id or "").agent0  # type: ignore[union-attr]
        child_ids.append(a1.context.id)

        a2_job = parallel_tools.ParallelJob(
            id="callsubordin-a2",
            parent_context_id=a1.context.id,
            index=0,
            tool_name="call_subordinate",
            tool_args={"message": "be A2", "reset": True},
            kind="subordinate",
            parent_agent=a1,
        )
        a2_result = await parallel_tools._run_subordinate_context_job(
            a1.context.id, a2_job
        )
        a2_context = AgentContext.get(a2_job.worker_context_id or "")
        child_ids.append(a2_context.id)  # type: ignore[union-attr]

        assert a1_result == "A1"
        assert a1.number == 1
        assert a2_result == "A2"
        assert a2_context.agent0.number == 2  # type: ignore[union-attr]
        assert a2_context.get_output_data("parent_context_id") == a1.context.id  # type: ignore[union-attr]
        assert a2_context.get_output_data("parent_agent_number") == 1  # type: ignore[union-attr]
    finally:
        for child_id in reversed(child_ids):
            AgentContext.remove(child_id)
        AgentContext.remove(parent_id)


@pytest.mark.asyncio
async def test_parallel_subordinate_owns_nested_parallel_tasks(monkeypatch) -> None:
    monkeypatch.setattr(parallel_tools, "DeferredTask", _FakeDeferredTask)
    agent = _FakeAgent()
    parent_task = _FakeDeferredTask()
    agent.context.task = parent_task
    agent.context.set_data(parallel_tools.PARALLEL_WORKER_KIND_KEY, "subordinate")

    jobs = await parallel_tools.start_parallel_jobs(
        agent,  # type: ignore[arg-type]
        [
            parallel_tools.NormalizedToolCall(
                index=0,
                tool_name="call_subordinate",
                tool_args={"message": "nested", "reset": True},
            )
        ],
    )

    assert parent_task.children == [jobs[0].deferred_task]
    parent_task.kill()
    assert jobs[0].deferred_task.killed == 1  # type: ignore[union-attr]


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


def test_parallel_child_log_keeps_streamed_user_content() -> None:
    agent = _FakeAgent()
    job = parallel_tools.ParallelJob(
        id="job-streamed",
        parent_context_id=agent.context.id,
        index=0,
        tool_name="code_execution_tool",
        tool_args={},
        kind="tool",
    )
    job.log_item = agent.context.log.log(
        type="code_exe",
        heading="icon://terminal code_execution_tool - terminal",
        content="streamed output visible to user",
        kvps={},
    )

    parallel_tools._finish_job(job, "success", result="agent-view result")
    assert job.log_item.content == "streamed output visible to user"

    parallel_tools._finish_job(job, "error", error="boom")
    assert job.log_item.content == "streamed output visible to user"


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
async def test_parallel_collect_promotes_history_after_wrapper_result() -> None:
    from tools.parallel import ParallelTool

    class HistoryAgent(_FakeAgent):
        def __init__(self) -> None:
            super().__init__()
            self.history_events = []

        def hist_add_tool_result(self, tool_name, tool_result, **kwargs):
            self.history_events.append(("tool", tool_name, tool_result, kwargs))

        def hist_add_message(self, ai, content, tokens=0, **kwargs):
            self.history_events.append(("message", ai, content, tokens, kwargs))

    agent = HistoryAgent()
    job = parallel_tools.ParallelJob(
        id="vision-ready",
        parent_context_id=agent.context.id,
        index=0,
        tool_name="vision_load",
        tool_args={"paths": ["/image.png"]},
        kind="tool",
        state="success",
        result="Loaded images (1)",
        parent_history=[("raw-image-message", 1500)],
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

    assert job.id in agent.context.get_data(parallel_tools.PARALLEL_JOBS_KEY)
    assert agent.history_events == []

    await tool.after_execution(response)

    assert agent.history_events[0][0] == "tool"
    assert agent.history_events[1] == (
        "message",
        False,
        "raw-image-message",
        1500,
        {},
    )
    assert job.id not in agent.context.get_data(parallel_tools.PARALLEL_JOBS_KEY)


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
    assert "this.expandedParents[selectedId] === undefined" in store
    assert "...this.expandedParents," in store
    assert "[selectedId]: true," in store
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


def test_parallel_result_json_is_compact() -> None:
    result = parallel_tools.format_parallel_results(
        [{"job_id": "wait-1", "tool_name": "wait", "state": "success"}]
    )

    assert result == '{"status":"success","jobs":[{"job_id":"wait-1","tool_name":"wait","state":"success"}]}'
