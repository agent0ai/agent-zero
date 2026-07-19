from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from helpers import files
from plugins._goal.api.goal import Goal
from plugins._goal.commands import goal_command
from plugins._goal.helpers import goals
from plugins._goal.tools.create_goal import CreateGoal
from plugins._goal.tools.get_goal import GetGoal
from plugins._goal.tools.response import ResponseTool
from plugins._goal.tools.update_goal import UpdateGoal


@pytest.fixture()
def context_id():
    context_id = f"goal-test-{uuid.uuid4().hex}"
    yield context_id
    goals.delete_goal(context_id)


def _payload(context_id: str, command_text: str) -> dict:
    from plugins._commands.helpers.commands import parse_slash_invocation

    return {
        "invocation": parse_slash_invocation(command_text),
        "context": {"context_id": context_id},
    }


def test_goal_storage_round_trip(context_id: str):
    goal = goals.create_goal(context_id, "Ship the goal plugin", token_budget=1200)

    loaded = goals.get_goal(context_id)
    assert loaded == goal
    assert loaded["status"] == "active"
    assert loaded["token_budget"] == 1200
    assert loaded["active_since"]
    assert loaded["elapsed_seconds"] == 0

    updated = goals.update_goal(context_id, status="paused", objective="Polish the goal strip")
    assert updated["status"] == "paused"
    assert updated["objective"] == "Polish the goal strip"
    assert updated["active_since"] == ""
    paused_seconds = updated["elapsed_seconds"]

    resumed = goals.update_goal(context_id, status="active")
    assert resumed["status"] == "active"
    assert resumed["active_since"]
    assert resumed["elapsed_seconds"] == paused_seconds

    goals.delete_goal(context_id)
    assert goals.get_goal(context_id) is None


def test_goal_command_sets_pauses_resumes_and_deletes(context_id: str):
    created = goal_command.run(_payload(context_id, "/goal Add current goal support"))
    assert created["effects"][0]["message"] == "Goal set."
    assert created["effects"][2] == {"type": "send_message", "text": "Add current goal support"}
    assert goals.get_goal(context_id)["objective"] == "Add current goal support"

    paused = goal_command.run(_payload(context_id, "/goal pause"))
    assert paused["effects"][0]["message"] == "Goal paused."
    assert goals.get_goal(context_id)["status"] == "paused"

    resumed = goal_command.run(_payload(context_id, "/goal resume"))
    assert resumed["effects"][0]["message"] == "Goal resumed."
    assert goals.get_goal(context_id)["status"] == "active"

    deleted = goal_command.run(_payload(context_id, "/goal delete"))
    assert deleted["effects"][0]["message"] == "Goal deleted."
    assert goals.get_goal(context_id) is None


def test_goal_auto_fills_prompt(context_id: str):
    result = goal_command.run(_payload(context_id, "/goal auto keep this tight"))

    assert "Please create and manage a goal" in result["text"]
    assert "User hint: keep this tight" in result["text"]
    assert result["effects"] == []


def test_goal_files_stay_under_user_plugin_state(context_id: str):
    goals.create_goal(context_id, "Keep state in usr")
    goal_path = files.get_abs_path(
        files.USER_DIR,
        files.PLUGINS_DIR,
        goals.PLUGIN_NAME,
        goals.GOALS_DIR,
        f"{context_id}.json",
    )

    assert files.exists(goal_path)


@pytest.mark.asyncio
async def test_goal_api_and_agent_tools(context_id: str):
    handler = object.__new__(Goal)
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
    get_tool = GetGoal(fake_agent, "get_goal", None, {}, "", None)
    get_response = await get_tool.execute()
    assert "Exercise API path" in get_response.message

    update_tool = UpdateGoal(fake_agent, "update_goal", None, {}, "", None)
    update_response = await update_tool.execute(status="complete")
    assert "Status: complete" in update_response.message

    create_tool = CreateGoal(fake_agent, "create_goal", None, {}, "", None)
    create_response = await create_tool.execute(objective="Exercise tool path")
    assert "Goal created: Exercise tool path" == create_response.message
    assert goals.get_goal(context_id)["created_by"] == "model"


@pytest.mark.parametrize("terminal_status", ["blocked", "complete"])
@pytest.mark.asyncio
async def test_editing_terminal_goal_requests_agent_reactivation(
    context_id: str,
    terminal_status: str,
):
    goals.create_goal(context_id, "Initial goal")
    goals.update_goal(context_id, status=terminal_status)

    response = await object.__new__(Goal).process(
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
    goals.create_goal(context_id, "Keep going")
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

    goals.update_goal(context_id, status="complete")
    response = await tool.execute()
    assert response.break_loop is True
    assert response.message == "Can you decide?"
