from dataclasses import dataclass
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import TYPE_CHECKING
from uuid import uuid4

from flask import has_request_context, session

from helpers import login, projects
from helpers.team_store import ADMIN_ACTOR_ID, TeamAccount, get_store

if TYPE_CHECKING:
    from agent import AgentContext


_PROJECT_ID_FILE = "team-project-id"
_project_binding_lock = threading.Lock()
CHAT_PROJECT_ID = "team_project_id"
CHAT_CREATOR_ID = "team_creator_id"
CHAT_DRAFT_AT = "team_draft_at"
CHAT_STARTED = "team_started"
_DRAFT_TTL = 1800
TEAM_TOOL_IDS = {
    "response": "local:response",
    "goal": "plugin:_goal:goal",
    "text_editor": "plugin:_text_editor:text_editor",
    "memory": "plugin:_memory:memory",
}

# Both the operation and its resource must be permitted. Individual handlers resolve the resource.
MEMBER_API_ROUTES = frozenset({
    "banners", "chat_create", "csrf_token", "health", "logout", "message", "message_async", "poll", "projects", "stop",
    "message_queue_add", "message_queue_remove", "message_queue_send", "pause", "history_get", "ctx_window_get", "chat_reset", "nudge",
    "team_audit", "team_project_files", "team_surface",
    "plugins/_chat_compaction/compact_chat", "plugins/_model_config/model_override", "plugins/_model_config/model_presets",
    "plugins/_skills/skills_catalog",
    "plugins/_goal/goal",
    "plugins/_memory/memory_dashboard",
    "plugins/_scheduler/scheduler_task_create", "plugins/_scheduler/scheduler_task_delete",
    "plugins/_scheduler/scheduler_task_run", "plugins/_scheduler/scheduler_task_update",
    "plugins/_scheduler/scheduler_tasks_list",
})
MEMBER_UI_ROUTES = frozenset({
    "api_dispatch", "login_handler", "logout_handler", "static", "serve_index", "serve_app_index",
    "serve_bootstrap_index", "serve_safe", "serve_ui_asset_bundle", "serve_builtin_plugin_asset",
    "serve_plugin_asset", "serve_extension_asset", "serve_user_extension_asset",
})
_MEMBER_RENDER_POINTS = frozenset({"get_message_handler", "get_process_step_types", "get_tool_message_handler"})
_MEMBER_HTML = frozenset({
    "/extensions/webui/right-canvas-panels/files-panel.html",
    "/plugins/_editor/extensions/webui/right-canvas-panels/editor-panel.html",
    "/plugins/_memory/extensions/webui/page-head/memory-styles.html",
    "/plugins/_scheduler/extensions/webui/page-head/scheduler-styles.html",
    "/plugins/_scheduler/extensions/webui/sidebar-extensions/tasks-list.html",
    "/plugins/_chat_compaction/extensions/webui/chat-input-bottom-actions-start/compact-button.html",
    "/plugins/_model_config/extensions/webui/chat-input-progress-start/model-switcher.html",
    "/plugins/_commands/extensions/webui/chat-input-box-start/commands-menu.html",
    "/plugins/_goal/extensions/webui/page-head/goal-styles.html",
    "/plugins/_goal/extensions/webui/chat-input-progress-start/goal-strip.html",
})
_MEMBER_REQUIRED_HTML = {
    "sidebar-chats-list-view": (
        "/plugins/_sidebar_folders/extensions/webui/sidebar-chats-list-view/folders.html",
    ),
    "welcome-actions-start": (
        "/plugins/_memory/extensions/webui/welcome-actions-start/memory-card.html",
        "/plugins/_scheduler/extensions/webui/welcome-actions-start/tasks-card.html",
    ),
}
_MEMBER_JS = frozenset({
    "/extensions/webui/right_canvas_register_surfaces/register-files.js",
    "/extensions/webui/right_canvas_register_surfaces/register-project-viewers.js",
    "/plugins/_editor/extensions/webui/right_canvas_register_surfaces/register-editor.js",
    "/plugins/_editor/extensions/webui/surfaces_register/register-editor.js",
    "/plugins/_model_config/extensions/webui/apply_snapshot_before/refresh-switcher.js",
    "/plugins/_skills/extensions/webui/initFw_end/skills-menu-injector.js",
    "/plugins/_goal/extensions/webui/initFw_end/goal-menu-injector.js",
    "/plugins/_goal/extensions/webui/apply_snapshot_before/refresh-goal.js",
    "/plugins/_goal/extensions/webui/get_message_handler/goal-handler.js",
    "/plugins/_goal/extensions/webui/get_process_step_types/goal-types.js",
})


def member_webui_manifest(manifest: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
    html = {
        point: [path for path in paths if path in _MEMBER_HTML]
        for point, paths in manifest.get("html", {}).items()
    }
    for point, paths in _MEMBER_REQUIRED_HTML.items():
        html.setdefault(point, []).extend(paths)
    return {
        "html": html,
        "js": {
            point: [path for path in paths if path in _MEMBER_JS
                    or (point in _MEMBER_RENDER_POINTS and path.startswith("/extensions/webui/"))]
            for point, paths in manifest.get("js", {}).items()
        },
    }


def is_team_chat(context: "AgentContext | None") -> bool:
    get_data = getattr(context, "get_data", None)
    marker = get_data(CHAT_PROJECT_ID) if callable(get_data) else None
    return isinstance(marker, str) and bool(marker)


def is_team_chat_id(context_id: object) -> bool:
    if not isinstance(context_id, str):
        return False
    from agent import AgentContext

    return is_team_chat(AgentContext.get(context_id))


@dataclass(frozen=True)
class MemberScope:
    account_id: str
    project_ids: dict[str, str]

    def permits_chat(self, context: "AgentContext") -> bool:
        name = projects.get_context_project_name(context)
        project_id = self.project_ids.get(name or "")
        return bool(
            project_id
            and context.get_data(CHAT_PROJECT_ID) == project_id
        )


def has_chat_history(context: "AgentContext") -> bool:
    if context.get_data(CHAT_STARTED):
        return True
    for item in context.log.logs:
        if item.type == "user":
            values = item.kvps or {}
            if (item.content or "").strip() or values.get("attachments") or values.get("team_attachments"):
                return True
        if item.type == "response" and item.heading == "Context compacted":
            return True
    return False


def is_draft(context: "AgentContext") -> bool:
    return context.get_data(CHAT_DRAFT_AT) is not None


def can_send(scope: MemberScope, context: "AgentContext") -> bool:
    if not scope.permits_chat(context):
        return False
    created = context.get_data(CHAT_DRAFT_AT)
    return created is None or (
        context.get_data(CHAT_CREATOR_ID) == scope.account_id and time.monotonic() - created < _DRAFT_TTL
    )


def prune_drafts() -> None:
    from agent import AgentContext

    cutoff = time.monotonic() - _DRAFT_TTL
    for context in AgentContext.all():
        created = context.get_data(CHAT_DRAFT_AT)
        if created is not None and created < cutoff and not context.is_running():
            AgentContext.remove(context.id)


def _project_marker(name: str) -> Path:
    if projects.validate_project_name(name) != name:
        raise ValueError("Project not found.")
    root = Path(projects.get_projects_parent_folder()).resolve()
    metadata = root / name / projects.PROJECT_META_DIR
    header = metadata / projects.PROJECT_HEADER_FILE
    if metadata.resolve() != metadata or header.is_symlink() or not header.is_file():
        raise ValueError("Project not found.")
    return metadata / _PROJECT_ID_FILE


def _read_marker(marker: Path) -> str | None:
    try:
        if marker.is_symlink() or not marker.is_file():
            return None
        with marker.open(encoding="ascii") as stream:
            value = stream.read(33).strip()
        return value if len(value) == 32 else None
    except (OSError, UnicodeError):
        return None


def _matches_project(name: str, project_id: str) -> bool:
    try:
        return _read_marker(_project_marker(name)) == project_id
    except (OSError, ValueError):
        return False


def bound_project_id(name: str) -> str | None:
    project_id = get_store().project_id(name)
    return project_id if project_id and _matches_project(name, project_id) else None


def _write_marker(path: Path, project_id: str) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, encoding="ascii", delete=False) as stream:
        temp_path = Path(stream.name)
        try:
            stream.write(project_id)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)


def register_project(name: str) -> str:
    store = get_store()
    with _project_binding_lock:
        marker = _project_marker(name)
        project_id = store.project_id(name)
        if project_id and _read_marker(marker) == project_id:
            return project_id
        project_id = uuid4().hex
        _write_marker(marker, project_id)
        store.bind_project(name, project_id)
        return project_id


def adopt_project_chats(contexts: list["AgentContext"], name: str | None = None) -> None:
    """Record the already assigned native project on saved legacy conversations."""
    from agent import Agent, AgentContextType
    from helpers import message_queue, persist_chat, team_projects
    from helpers.task_scheduler import TaskScheduler

    bindings: dict[str, str | None] = {}
    scheduler = TaskScheduler.get()
    for context in contexts:
        native_name = projects.get_context_project_name(context)
        if (not native_name or (name is not None and native_name != name)
                or context.type != AgentContextType.USER or is_team_chat(context)
                or context.is_running() or not has_chat_history(context)
                or message_queue.has_queue(context) or scheduler.get_tasks_by_context_id(context.id)):
            continue
        if native_name not in bindings:
            bindings[native_name] = (
                None if get_store().project_has_predecessor(native_name) else bound_project_id(native_name)
            )
        project_id = bindings[native_name]
        if not project_id:
            continue
        agent = context.get_agent()
        previous_state = agent.get_data(Agent.DATA_NAME_RESPONSES_STATE)
        previous_window = agent.get_data(Agent.DATA_NAME_CTX_WINDOW)
        context.set_data(CHAT_PROJECT_ID, project_id)
        context.set_data(CHAT_CREATOR_ID, "legacy")
        agent.set_data(Agent.DATA_NAME_RESPONSES_STATE, None)
        agent.set_data(Agent.DATA_NAME_CTX_WINDOW, None)
        try:
            with team_projects.activity("chat.share_project", ADMIN_ACTOR_ID, project_id, context_id=context.id):
                persist_chat.save_tmp_chat(context)
        except BaseException:
            context.data.pop(CHAT_PROJECT_ID, None)
            context.data.pop(CHAT_CREATOR_ID, None)
            agent.set_data(Agent.DATA_NAME_RESPONSES_STATE, previous_state)
            agent.set_data(Agent.DATA_NAME_CTX_WINDOW, previous_window)
            raise


def set_project_membership(account_id: str, name: str, granted: bool, *, actor_id: str) -> None:
    from agent import AgentContext

    project_id = register_project(name) if granted else bound_project_id(name)
    if not project_id:
        return
    if granted:
        adopt_project_chats(AgentContext.all(), name)
    get_store().set_membership(account_id, project_id, granted, actor_id=actor_id)


def scope_for_account(account: TeamAccount) -> MemberScope:
    return MemberScope(account.id, assigned_projects(account.id))


def assigned_projects(account_id: str, *, include_disabled: bool = False) -> dict[str, str]:
    return {
        name: project_id
        for name, project_id in get_store().memberships(account_id, include_disabled=include_disabled).items()
        if _matches_project(name, project_id)
    }


def scope_for_session(token: object) -> MemberScope | None:
    account = login.team_account_for_session(token)
    return scope_for_account(account) if account else None


def request_scope() -> MemberScope | None:
    if has_request_context() and login.TEAM_SESSION_KEY in session:
        return scope_for_session(session[login.TEAM_SESSION_KEY]) or MemberScope("", {})
    return None


def admin_chat_scope(context: "AgentContext") -> MemberScope:
    name = projects.get_context_project_name(context)
    project_id = bound_project_id(name) if name else None
    return MemberScope(ADMIN_ACTOR_ID, {name: project_id} if name and project_id else {})


def request_chat_scope(context: "AgentContext") -> MemberScope | None:
    scope = request_scope()
    if scope is not None:
        return scope
    if is_team_chat(context) and has_request_context() and login.team_mode_enabled() and login.is_admin_session(session):
        return admin_chat_scope(context)
    return None


def bind_chat(context: "AgentContext", scope: MemberScope, name: str, *, draft: bool = False) -> None:
    context.set_data(CHAT_PROJECT_ID, scope.project_ids[name])
    context.set_data(CHAT_CREATOR_ID, scope.account_id)
    if draft:
        context.set_data(CHAT_DRAFT_AT, time.monotonic())
    projects.activate_project(context.id, name, mark_dirty=False)
