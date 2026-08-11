from __future__ import annotations

import base64
import shutil
import subprocess
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent import Agent, LoopData
from helpers import extension, files, mcp_handler
from helpers.llm_result import LLMResult
from helpers.log import Log
from plugins._goal.api.goal import Goal as GoalApi
from plugins._goal.commands import goal_command
from plugins._goal.tools import goal
from plugins._goal.tools.goal import GoalTool
from plugins._goal.tools.response import ResponseTool


@pytest.fixture()
def context_id():
    context_id = f"goal-test-{uuid.uuid4().hex}"
    yield context_id
    goal.delete_goal(context_id)


def _payload(context_id: str, command_text: str) -> dict:
    from plugins._commands.helpers.commands import parse_slash_invocation

    return {
        "invocation": parse_slash_invocation(command_text),
        "context": {"context_id": context_id},
    }


def test_goal_storage_round_trip(context_id: str):
    current_goal = goal.create_goal(context_id, "Ship the goal plugin", token_budget=1200)

    loaded = goal.get_goal(context_id)
    assert loaded == current_goal
    assert loaded["status"] == "active"
    assert loaded["token_budget"] == 1200
    assert loaded["active_since"]
    assert loaded["elapsed_seconds"] == 0

    updated = goal.update_goal(context_id, status="paused", objective="Polish the goal strip")
    assert updated["status"] == "paused"
    assert updated["objective"] == "Polish the goal strip"
    assert updated["active_since"] == ""
    paused_seconds = updated["elapsed_seconds"]

    resumed = goal.update_goal(context_id, status="active")
    assert resumed["status"] == "active"
    assert resumed["active_since"]
    assert resumed["elapsed_seconds"] == paused_seconds

    goal.delete_goal(context_id)
    assert goal.get_goal(context_id) is None


def test_goal_changes_publish_state_revision(context_id: str, monkeypatch):
    from agent import AgentContext
    from helpers import state_monitor_integration

    revisions = iter([1.0, 2.0, 3.0])
    output_data = {}
    dirty = []
    context = SimpleNamespace(
        set_output_data=lambda key, value: output_data.__setitem__(key, value)
    )
    monkeypatch.setattr(AgentContext, "get", lambda _context_id: context)
    monkeypatch.setattr(goal.time, "time", lambda: next(revisions))
    monkeypatch.setattr(
        state_monitor_integration,
        "mark_dirty_for_context",
        lambda context_id, *, reason: dirty.append((context_id, reason)),
    )

    goal.create_goal(context_id, "Publish changes")
    goal.update_goal(context_id, status="paused")
    goal.delete_goal(context_id)

    assert output_data["_goal_revision"] == 3.0
    assert dirty == [(context_id, "plugins._goal")] * 3


def test_goal_webui_uses_state_revisions_instead_of_polling():
    plugin_root = Path(__file__).resolve().parents[1]
    store = (plugin_root / "webui" / "goal-store.js").read_text()
    strip = (
        plugin_root
        / "extensions"
        / "webui"
        / "chat-input-progress-start"
        / "goal-strip.html"
    ).read_text()
    refresh = (
        plugin_root
        / "extensions"
        / "webui"
        / "apply_snapshot_before"
        / "refresh-goal.js"
    ).read_text()

    assert "setInterval(() => this.refresh" not in store
    assert "$watch('$store.chats.selected'" not in strip
    assert "_goal_revision" in refresh
    assert "goalStore.refresh(true)" in refresh


@pytest.mark.skipif(not shutil.which("node"), reason="node is required")
def test_goal_webui_uses_shared_hour_aware_duration_formatter():
    project_root = Path(__file__).resolve().parents[3]
    time_utils = (project_root / "webui" / "js" / "time-utils.js").read_bytes()
    module_url = "data:text/javascript;base64," + base64.b64encode(time_utils).decode("ascii")
    script = f"""
import {{ formatDuration }} from {module_url!r};
if (formatDuration(3_782_000) !== "1h3m2s") throw new Error("hours");
if (formatDuration(62_000) !== "1m2s") throw new Error("minutes");
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True)

    store = (project_root / "plugins" / "_goal" / "webui" / "goal-store.js").read_text()
    assert 'import { formatDuration } from "/js/time-utils.js";' in store
    assert "return formatDuration(this.elapsedSeconds * 1000);" in store


def test_goal_command_sets_pauses_resumes_and_deletes(context_id: str):
    created = goal_command.run(_payload(context_id, "/goal Add current goal support"))
    assert created["effects"][0]["message"] == "Goal set."
    assert created["effects"][2] == {"type": "send_message", "text": "Add current goal support"}
    assert goal.get_goal(context_id)["objective"] == "Add current goal support"

    paused = goal_command.run(_payload(context_id, "/goal pause"))
    assert paused["effects"][0]["message"] == "Goal paused."
    assert goal.get_goal(context_id)["status"] == "paused"

    resumed = goal_command.run(_payload(context_id, "/goal resume"))
    assert resumed["effects"][0]["message"] == "Goal resumed."
    assert goal.get_goal(context_id)["status"] == "active"

    deleted = goal_command.run(_payload(context_id, "/goal delete"))
    assert deleted["effects"][0]["message"] == "Goal deleted."
    assert goal.get_goal(context_id) is None


def test_goal_auto_fills_prompt(context_id: str):
    result = goal_command.run(_payload(context_id, "/goal auto keep this tight"))

    assert "Please create and manage a goal" in result["text"]
    assert "User hint: keep this tight" in result["text"]
    assert result["effects"] == []


def test_goal_files_stay_under_user_plugin_state(context_id: str):
    goal.create_goal(context_id, "Keep state in usr")
    goal_path = files.get_abs_path(
        files.USER_DIR,
        files.PLUGINS_DIR,
        goal.PLUGIN_NAME,
        goal.GOALS_DIR,
        f"{context_id}.json",
    )

    assert files.exists(goal_path)


@pytest.mark.asyncio
async def test_goal_api_and_agent_tools(context_id: str):
    handler = object.__new__(GoalApi)
    created = await handler.process(
        {
            "action": "set",
            "context_id": context_id,
            "objective": "Exercise API path",
        },
        None,
    )
    assert created["ok"] is True
    assert created["goal"]["objective"] == "Exercise API path"

    fake_agent = SimpleNamespace(context=SimpleNamespace(id=context_id))
    get_tool = GoalTool(fake_agent, "goal", None, {}, "", None)
    get_response = await get_tool.execute()
    assert "Exercise API path" in get_response.message

    update_tool = GoalTool(fake_agent, "goal", None, {}, "", None)
    update_response = await update_tool.execute(action="update", status="complete")
    assert "Status: complete" in update_response.message

    create_tool = GoalTool(fake_agent, "goal", None, {}, "", None)
    create_response = await create_tool.execute(action="create", objective="Exercise tool path")
    assert "Goal created: Exercise tool path" == create_response.message
    assert goal.get_goal(context_id)["created_by"] == "model"


@pytest.mark.parametrize("terminal_status", ["blocked", "complete"])
@pytest.mark.asyncio
async def test_editing_terminal_goal_requests_agent_reactivation(
    context_id: str,
    terminal_status: str,
):
    goal.create_goal(context_id, "Initial goal")
    goal.update_goal(context_id, status=terminal_status)

    response = await object.__new__(GoalApi).process(
        {
            "action": "update",
            "context_id": context_id,
            "objective": "Continue with the edited goal",
            "status": "active",
        },
        None,
    )

    assert response["reactivated"] is True
    assert response["goal"]["objective"] == "Continue with the edited goal"
    assert response["goal"]["status"] == "active"


@pytest.mark.asyncio
async def test_active_goal_keeps_response_tool_running(context_id: str):
    goal.create_goal(context_id, "Keep going")
    recorded = []
    fake_agent = SimpleNamespace(
        context=SimpleNamespace(id=context_id),
        hist_add_tool_result=lambda *args, **kwargs: recorded.append((args, kwargs)),
    )
    loop_data = SimpleNamespace(params_temporary={})
    tool = ResponseTool(
        fake_agent,
        "response",
        None,
        {"text": "Can you decide?"},
        "",
        loop_data,
    )

    response = await tool.execute()
    assert response.break_loop is False
    response.additional["_responses_output_item"] = {"type": "function_call_output"}
    await tool.after_execution(response)
    assert recorded == [
        (
            ("response", response.message),
            {"_responses_output_item": {"type": "function_call_output"}},
        )
    ]

    goal.update_goal(context_id, status="complete")
    response = await tool.execute()
    assert response.break_loop is True
    assert response.message == "Can you decide?"


@pytest.mark.asyncio
async def test_native_responses_text_uses_active_goal_response_override(
    context_id: str,
    monkeypatch,
):
    goal.create_goal(context_id, "Keep going")
    recorded = []

    async def no_op(*args, **kwargs):
        return None

    class NoMcpTools:
        def get_tool(self, agent, tool_name):
            return None

    agent = object.__new__(Agent)
    agent.context = SimpleNamespace(id=context_id, log=Log())
    agent.loop_data = LoopData()
    agent.data = {}
    agent.handle_intervention = no_op
    agent._log_response_builtin_items = no_op
    agent.hist_add_tool_result = lambda *args, **kwargs: recorded.append((args, kwargs))

    def get_tool(name, method, args, message, loop_data, **kwargs):
        return ResponseTool(agent, name, method, args, message, loop_data)

    agent.get_tool = get_tool
    monkeypatch.setattr(extension, "call_extensions_async", no_op)
    monkeypatch.setattr(mcp_handler.MCPConfig, "get_instance", lambda: NoMcpTools())

    result = await Agent.process_llm_result_tools(
        agent,
        LLMResult(response="Checkpoint for the user."),
    )

    assert result is None
    assert recorded[0][0][0] == "response"
    assert recorded[0][0][1].startswith("Goal still active.")
    assert recorded[0][1] == {}

    goal.update_goal(context_id, status="complete")
    result = await Agent.process_llm_result_tools(
        agent,
        LLMResult(response="Finished."),
    )

    assert result == "Finished."
