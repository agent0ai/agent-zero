# Operate Agent Zero

Agent Zero can use its local socket API to operate existing application features for the user: create and manage projects, create chats, select profiles, start work, manage scheduled tasks, and use plugin features. A request such as "create a project and start a research chat in it" can be completed directly through these APIs.

Use an available agent tool when it already handles the requested operation, such as scheduling. Use the application API for administration or features without a suitable tool. Follow the user's requested scope and existing permissions; socket access is not a way around blocked capabilities. Routine steps needed for an authorized outcome do not need separate confirmation.

Compose existing features to complete the outcome: a research workspace can combine project instructions, a Researcher chat, and a saved recurring task; a new custom profile can be created through Agent Editor, selected in a fresh chat, and given its assignment. Persist the returned IDs, verify each transition, and start execution only when the requested outcome includes it.

## Source Anchors

- Local transport: `/a0/helpers/socket_cli.py`, `/a0/helpers/socket_api.py`, `/a0/socket/`, `/a0/docs/developer/local-socket.md`.
- HTTP routing/auth/CSRF: `/a0/helpers/api.py`, `/a0/helpers/ui_server.py`, `/a0/api/csrf_token.py`.
- Projects: `/a0/api/projects.py`, `/a0/helpers/projects.py`.
- Chats: `/a0/api/chat_create.py`, `/a0/api/agent_profile_set.py`, `/a0/api/poll.py`, `/a0/helpers/state_snapshot.py`.
- Starting work: `/a0/api/message.py`, `/a0/api/message_async.py`, `/a0/api/api_message.py`.
- Tasks: `/a0/plugins/_scheduler/api/scheduler_task_create.py`, `/a0/plugins/_scheduler/api/scheduler_task_update.py`, `/a0/helpers/task_scheduler.py`.
- Other routes: `/a0/api/` and `/a0/plugins/<plugin>/api/`; inspect each handler and its nearest DOX before unfamiliar operations.

## Connect To The Correct Instance

Run the client inside the intended instance, from its framework root (`/a0` in Docker). The default socket is `/a0/tmp/socket/a0.sock`; `A0_SOCKET_PATH` or `--socket` selects another instance's socket. Filesystem permissions authorize access. A connected host or sandbox does not automatically have this socket mounted.

```bash
cd /a0
python -m helpers.socket_cli ping
python -m helpers.socket_cli projects '{"action":"list"}'
```

For composed operations, use the same standard-library client in a terminal Python script. It contacts the running framework without initializing another runtime:

```python
from helpers.socket_cli import call

def local(command, payload=None):
    response = call(command, payload if payload is not None else {})
    if not response["ok"]:
        raise RuntimeError("Socket operation failed; inspect response['error'] privately")
    return response["result"]
```

All examples below use `local()`. Commands map to files in `socket/` or a plugin's `socket/` directory; they have no `/api/` prefix. Arguments and successful operation results use the existing API shapes. Failures use `ok: false` with `error.code`/`error.message`; structured operation failures also retain their original fields in `error.details` (for example plugin-update conflicting files). CLI failures exit nonzero.

There is no default operation deadline, including scans and synchronous messages. An optional `call(..., timeout=seconds)` or CLI `--timeout` bounds the client's response wait. After a timeout or lost connection, inspect state before retrying a create or start request: it may already have succeeded. See the developer guide for payload and server limits.

For remote instances or features without a socket handler, use HTTP at the verified instance origin. Preserve its existing protections: authenticate through `/login` when enabled, keep the session cookie jar, GET `/api/csrf_token` with the origin, and send `X-CSRF-Token` on protected calls. Check HTTP status and body-level errors; login HTML is not success. Keep credentials out of output. Startup/update readiness checks use HTTP `/api/health`; `ping` checks only the local socket.

## Identify Scope Before Acting

Use `local("poll", {})` to discover `contexts` and `tasks`. Context records include `id`, `name`, `project`, `agent_profile`, `running`, and `paused`. Match the requested target or use an ID returned by your own earlier call. Do not assume the newest chat is the current/user-requested chat. If the target remains ambiguous, clarify it.

A separate shell Python process does not share the WebUI process's in-memory `AgentContext` objects. Importing `AgentContext` there is not a substitute for socket calls to the running server.

IDs are not interchangeable:

| Operation | Request ID field | Returned identity |
|---|---|---|
| `chat_create` | Optional `new_context`, `current_context` | `ctxid` |
| `projects` activate/deactivate | `context_id`; activate also needs project `name` | Verify through `poll` |
| `agent_profile_set` | `context_id`, `agent_profile` | `agent_profile` |
| `message_async`, `poll`, `history_get`, `pause`, `stop`, `chat_remove` | `context` | Context-dependent response |
| `chat_export` | `ctxid` | `ctxid`, `content` |
| `plugins/_scheduler/scheduler_task_update`, `plugins/_scheduler/scheduler_task_run`, `plugins/_scheduler/scheduler_task_delete` | `task_id` | Use `task.uuid` from creation/listing |

## Projects And Chats

Creating a project creates its workspace and metadata. Activating it assigns that project to a particular chat. There is no single global "active project" for every chat.

Project operations use the `projects` command:

| `action` | Other fields | Purpose |
|---|---|---|
| `list`, `list_options` | None | Discover project names/titles |
| `load` | `name` | Read editable project data |
| `create` | `project` object with `name`, title/instructions as needed | Create workspace |
| `clone` | `project` with `name`, `git_url`, optional `git_token` | Clone a repository as a project |
| `update` | `project` with existing `name` and edits | Update project metadata/instructions |
| `activate` | `context_id`, `name` | Assign project to chat |
| `deactivate` | `context_id` | Clear chat's project assignment |
| `file_structure` | `name`, optional `settings` | Inspect project tree |
| `delete` | `name` | Delete project files and detach its chats |

List before create; reuse a matching project when that is what the user wants. Choose a fresh, simple directory name for a new project. Load before updates and preserve unrelated fields, especially variables, secrets, MCP settings, and plugin-owned metadata. Do not print a whole loaded project object.

Example: ensure a project exists, then create an idle chat in it. Replace the illustrative name/title/instructions with the requested values.

```python
name = "research-workspace"
existing = local("projects", {"action": "list"})["data"]
if not any(project["name"] == name for project in existing):
    created = local("projects", {
        "action": "create",
        "project": {"name": name, "title": "Research Workspace",
                    "description": "Research and source notes",
                    "instructions": "Cite sources and distinguish evidence from inference."},
    })
    name = created["data"]["name"]

ctxid = local("chat_create", {})["ctxid"]
local("projects", {"action": "activate", "context_id": ctxid, "name": name})
snapshot = local("poll", {"context": ctxid, "log_from": 0, "notifications_from": 0})
chat = next(item for item in snapshot["contexts"] if item["id"] == ctxid)
assert chat["project"]["name"] == name
```

`chat_create` can inherit project and model override from `current_context`, subject to settings. Omit that field for an independent chat; activate the intended project explicitly. `new_context` may supply a fresh ID, but reusing an existing ID does not guarantee a new chat. Creation alone does not run a model or guarantee that the user's currently selected browser tab switches to it.

For a specialized chat, list available profiles and then call:

```python
local("agent_profile_set", {"context_id": ctxid, "agent_profile": "researcher"})
```

Use an available profile ID in that project's scope and verify `agent_profile` through `poll`. Select the profile in an idle chat before starting its assignment. Creating a profile and selecting it for a chat are separate operations.

## Start, Observe, And Control Chat Work

- `message_async` with `{"context": ctxid, "text": "<assigned work>"}` starts processing and returns acceptance plus `context`; it does not return task completion.
- `message` uses the same payload but waits for the model result. Do not synchronously call it against the same chat that is making the request.
- Poll the target with `context`, `log_from`, and `notifications_from`; inspect its `running` state and logs, then use `history_get` or `chat_export` for results. Reset cursors when log/notification GUIDs change. Use bounded polling rather than a tight loop.
- `pause` uses `{"context": ctxid, "paused": true}`; `false` resumes. `stop` terminates the current run. `chat_reset` resets the conversation; `chat_remove` deletes it and can remove tasks bound to that context.
- Message queue endpoints (`message_queue_add`, `message_queue_remove`, `message_queue_send`) support follow-ups. Inspect their handlers before use; queued messages may later be consumed by the running agent.

Starting a chat run or manually running a saved task consumes model resources and may execute tools. Do it when requested or needed for the user's assigned outcome, not as a side effect of merely creating or inspecting a chat. Send independent work to another chat and avoid recursive delegation back to the caller.

The external API is a different contract: `POST /api/api_message` uses `X-API-KEY` with `message`, optional `context_id`, `project_name`, `agent_profile`, and attachments. It waits for a result and returns `context_id`/`response`. Its project/profile options apply when creating a context; it is not the general WebUI session API. Check `/a0/api/api_message.py` rather than mixing its fields with `message_async`.

## Saved Tasks And Schedules

Prefer the `scheduler` tool when available; load `scheduled-tasks` for detailed scheduling. The socket API also manages the same saved tasks, including a project association selected at creation.

- List: `plugins/_scheduler/scheduler_tasks_list` with `{}`; result is `tasks`.
- Create: `plugins/_scheduler/scheduler_task_create` with `name`, `prompt`, optional `system_prompt`, `attachments`, and `project_name`.
- Type is selected by payload: a nonempty `schedule` creates a recurring task; otherwise a nonempty `plan` creates a planned task; neither creates an adhoc task. Do not send both.
- Recurring `schedule` is an object with cron strings `minute`, `hour`, `day`, `month`, `weekday`, plus an IANA `timezone`. Use the user's intended timezone.
- Socket/API planned shape is `{"plan": {"todo": ["<future ISO datetime with UTC offset>"]}}`, not the scheduler tool's list shorthand. Verify returned planned dates.
- Update: `plugins/_scheduler/scheduler_task_update` with `task_id` and changed fields such as `name`, `prompt`, `schedule`, `plan`, or `state`. `state: "disabled"` disables; `state: "idle"` re-enables.
- Run now: `plugins/_scheduler/scheduler_task_run` with `task_id`. Acceptance is not completion; check the returned task and later list state/results.
- Delete: `plugins/_scheduler/scheduler_task_delete` with `task_id`. This also handles a running task and its dedicated context.

Creation uses a dedicated context; `project_name` cannot be changed through the update endpoint. Top-level `timezone` also updates runtime localization, so use explicit planned offsets or `schedule.timezone` when that is the intended scope. Do not copy tool-only fields such as `dedicated_context` into socket/API payloads and assume they are honored.

For a saved draft that must not run automatically, create an adhoc task and disable it:

```python
task = local("plugins/_scheduler/scheduler_task_create", {
    "name": "Research draft", "prompt": "<work to run when requested>",
    "project_name": name,
})["task"]
task_id = task["uuid"]
local("plugins/_scheduler/scheduler_task_update", {"task_id": task_id, "state": "disabled"})
saved = next(t for t in local("plugins/_scheduler/scheduler_tasks_list", {})["tasks"] if t["uuid"] == task_id)
assert saved["state"] == "disabled"
```

Do not use a due recurring schedule as a draft and hope to disable it before execution. Do not reset/delete the caller's own active chat to manage another task.

## Other Application Features

These are discovery starting points, not interchangeable payloads. Read the handler and corresponding skill before changing state. Profile catalog/editor, plugins, and notifications have socket handlers. The remaining rows still use HTTP or their existing tools. Installed plugin handler discovery follows HTTP; feature handlers own any activation checks.

| Feature | Entry point | Guidance |
|---|---|---|
| Profile catalog and editor | `agents` (`action: list`); `plugins/_agent_editor/agent_editor` | Editor supports scoped list/load, quick_create, plan/save and lifecycle operations. Inspect its plan before applying complex edits. Use `a0-create-agent` for creation. |
| Skills (HTTP) | `skills`; `plugins/_skills/skills_catalog` | Catalog manages per-chat visibility and activation. Loading adds instructions to history; hiding is not unloading, and deactivate/clear are rejected. |
| Slash commands (HTTP) | `plugins/_commands/commands` | List effective commands by `context_id`; get/save/duplicate/delete in the intended scope. Use `commands-create-slash-command`. |
| Plugins | `plugins_list`, `plugins` | Inspect configuration and activation by plugin/project/profile. Use `a0-manage-plugin`; plugin execution/install/removal has wider effects than reading configuration. |
| Files (HTTP) | `get_work_dir_files`, `edit_work_dir_file`, upload/download/rename endpoints | Several reads use GET/query parameters; uploads use multipart. Use the appropriate file/Office tool when available. |
| Settings and MCP (HTTP) | `settings_get`, `settings_set`, `mcp_servers_status`, `mcp_servers_apply` | Scope changes carefully; preserve unowned settings and secrets. Do not treat a global settings update as a chat-only change. |
| Backups and updates (HTTP) | `backup_*`, `self_update_*`, `restart` | Inspect previews/defaults and source contracts. Restore, restart and self-update can disrupt other work; perform only for the requested maintenance outcome. |
| Notifications | `notification_create`, `notifications_history`, `notifications_mark_read` | Use the notification tool when available; avoid clearing other notifications as cleanup. |

For a feature not listed here, find the WebUI's actual request and read the matching handler. Do not guess routes from button labels or emulate state by editing scheduler/chat/project storage behind the running server.

## Verify And Report

Check the returned identity and read back the actual state: project name, chat project/profile, task UUID/state, or saved feature configuration. Distinguish created, activated, started, completed, and visible in the user's selected UI. Report what happened and provide the relevant names/IDs without dumping private state.

For smoke tests, use unique disposable records, avoid model execution unless required, and delete only records created by the test. Verify cleanup through the same listing endpoints. A successful CRUD test does not prove a model run, scheduled execution, external integration, or every listed feature works.
