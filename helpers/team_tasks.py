"""Project-bound native scheduler tasks and their run identities."""

import asyncio
from concurrent.futures import CancelledError as FutureCancelled
import secrets
from uuid import uuid4

from helpers import login, message_queue, persist_chat, projects, team_access, team_projects, team_runs
from helpers.team_store import get_store


def scope_for_task(task, account_id: str | None):
    if not login.team_mode_enabled() or not account_id or not task.team_project_id or not task.project_name:
        return None
    scope = team_access.MemberScope(account_id, team_access.assigned_projects(account_id))
    return scope if scope.project_ids.get(task.project_name) == task.team_project_id else None


def permits_task(task, scope: team_access.MemberScope | None) -> bool:
    if scope is None:
        return not task.team_project_id
    return bool(task.team_project_id and scope.project_ids.get(task.project_name) == task.team_project_id)


def validate_fields(data: dict):
    if data.get("attachments") or data.get("token"):
        raise ValueError("Project tasks accept text prompts through the team scheduler.")
    for field, limit in (("name", 200), ("prompt", 80_000), ("system_prompt", 30_000)):
        if field in data and (not isinstance(data[field], str) or len(data[field]) > limit):
            raise ValueError(f"Invalid task {field}.")
    if data.get("state") not in (None, "idle", "disabled"):
        raise ValueError("Choose an enabled or disabled state.")


async def create_task(data: dict, scope: team_access.MemberScope):
    from helpers.task_scheduler import (
        AdHocTask, PlannedTask, ScheduledTask, TaskScheduler, TaskState,
        parse_task_plan, parse_task_schedule, serialize_task,
    )

    validate_fields(data)
    name, prompt, project = data.get("name", ""), data.get("prompt", ""), data.get("project_name")
    if not isinstance(project, str) or project not in scope.project_ids:
        raise PermissionError("Select an assigned project for the task.")
    if not name.strip() or not prompt.strip():
        raise ValueError("Enter a task name and prompt.")
    with team_projects.project_lock(project, scope) as project_id:
        color = projects.load_basic_project_data(project).get("color")
    common = {
        "name": name, "prompt": prompt, "system_prompt": data.get("system_prompt", ""),
        "project_name": project, "project_color": color,
    }
    if schedule := data.get("schedule"):
        if not isinstance(schedule, dict):
            raise ValueError("Use the native schedule fields.")
        schedule = parse_task_schedule(schedule)
        task = ScheduledTask.create(**common, schedule=schedule, timezone=schedule.timezone or data.get("timezone"))
    elif plan := data.get("plan"):
        if not isinstance(plan, dict):
            raise ValueError("Use the native project task plan.")
        task = PlannedTask.create(**common, plan=parse_task_plan(plan))
    else:
        task = AdHocTask(**common, token=secrets.token_urlsafe(32))
    task.team_project_id = project_id
    task.team_owner_id = scope.account_id
    task.state = TaskState(data.get("state", TaskState.IDLE))
    with team_projects.activity("task.create", scope.account_id, project_id, context_id=task.context_id):
        await TaskScheduler.get().add_task(task)
    return {"success": True, "task": serialize_task(task, include_team_data=True)}


async def execute_task(task, context, actor_id: str):
    from agent import UserMessage

    scope = scope_for_task(task, actor_id)
    if not scope or not scope.permits_chat(context):
        raise PermissionError("The task no longer has access to this project.")
    run, _ = team_runs.reserve(context, actor_id, uuid4().hex, task.prompt)
    try:
        context.set_data("scheduler_task_uuid", task.uuid)
        message_queue.log_user_message(context, task.prompt, [], run.request_id, author=run.username)
        persist_chat.save_tmp_chat(context)
        with team_runs.authorized_dispatch(run):
            turn = context.communicate(UserMessage(
                message=task.prompt, system_message=[task.system_prompt], id=run.request_id,
            ))
    except BaseException:
        get_store().finish_run(run, "failed")
        raise
    try:
        result = await turn.result()
    except (asyncio.CancelledError, FutureCancelled):
        team_runs.request_stop(run, actor_id)
        raise asyncio.CancelledError
    if result is None:
        raise RuntimeError("The project task did not return a response.")
    return result
