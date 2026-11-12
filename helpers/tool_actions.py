"""Action contracts for bundled tools, shared by policy and discovery."""

from dataclasses import dataclass, field
from typing import Any


MEMORY_TOOL_ID = "plugin:_memory:memory"
MEMORY_ACTIONS = ("load", "save", "delete", "forget")


@dataclass(frozen=True)
class ToolActions:
    actions: tuple[str, ...]
    argument: str = "action"
    default: str = ""
    aliases: dict[str, str] = field(default_factory=dict)

    def normalize(self, value: Any) -> str:
        action = str(value or "").strip().lower().replace("-", "_")
        return self.aliases.get(action, action)


_EDITOR = ToolActions(("read", "write", "patch"))
_CODE = ToolActions(("terminal", "python", "nodejs", "output", "reset"), argument="runtime")
BUNDLED_ACTIONS = {
    MEMORY_TOOL_ID: ToolActions(MEMORY_ACTIONS),
    "plugin:_scheduler:scheduler": ToolActions((
        "list_tasks", "find_task_by_name", "show_task", "run_task", "delete_task",
        "update_task", "create_scheduled_task", "create_adhoc_task",
        "create_planned_task", "wait_for_task",
    )),
    "plugin:_text_editor:text_editor": _EDITOR,
    "plugin:_a0_connector:text_editor_remote": _EDITOR,
    "plugin:_code_execution:code_execution_tool": _CODE,
    "plugin:_a0_connector:code_execution_remote": _CODE,
    "plugin:_browser:browser": ToolActions((
        "open", "list", "state", "set_active", "navigate", "back", "forward", "reload",
        "content", "detail", "screenshot", "click", "type", "submit", "type_submit",
        "scroll", "evaluate", "key_chord", "hover", "double_click", "right_click",
        "drag", "wheel", "keyboard", "clipboard", "set_viewport", "select_option",
        "set_checked", "upload_file", "mouse", "multi", "close", "close_all",
    ), default="state", aliases={
        "setactive": "set_active", "activate": "set_active", "focus": "set_active",
        "typesubmit": "type_submit", "keychord": "key_chord",
        "copy": "clipboard", "cut": "clipboard", "paste": "clipboard",
    }),
    "plugin:_a0_connector:computer_use_remote": ToolActions((
        "start_session", "status", "capture", "list_windows", "get_window_state",
        "element_action", "ax_snapshot", "ax_action", "uia_snapshot", "uia_action",
        "move", "click", "scroll", "key", "type", "stop_session",
    )),
    "plugin:_office:office_artifact": ToolActions((
        "create", "open", "read", "edit", "inspect", "version_history",
        "restore_version", "export", "status",
    ), default="status", aliases={"extract": "read", "update": "edit", "patch": "edit"}),
    "plugin:_goal:goal": ToolActions(
        ("get", "create", "update"), default="get",
        aliases={"show": "get", "status": "get", "set": "create", "complete": "update", "blocked": "update"},
    ),
    "local:skills_tool": ToolActions(("list", "search", "load", "read_file"), default="list"),
    "local:parallel": ToolActions(
        ("start", "await", "collect", "cancel"),
        aliases={"background": "start", "wait": "await"},
    ),
}


def bundled_path(tool_id: str) -> str:
    parts = tool_id.split(":")
    return f"plugins/{parts[1]}/tools/{parts[2]}.py" if parts[0] == "plugin" else f"tools/{parts[1]}.py"


def action_policy_id(tool_id: str, action: str) -> str:
    # The four former memory tools already have durable permission IDs.
    separator = "_" if tool_id == MEMORY_TOOL_ID else ":"
    return f"{tool_id}{separator}{action}"


def requested_actions(tool_id: str, args: dict[str, Any]) -> list[str]:
    """Include compound operations, so wrappers cannot hide a denied action."""
    spec = BUNDLED_ACTIONS[tool_id]
    value = args.get(spec.argument)
    if tool_id == "local:skills_tool":
        value = value or args.get("method")
    action = spec.normalize(value or spec.default)
    result = [action]

    if tool_id == "plugin:_browser:browser" and action == "multi":
        calls = args.get("calls")
        if isinstance(calls, list):
            for call in calls:
                if isinstance(call, dict):
                    result.extend(requested_actions(tool_id, call))
    elif spec.argument == "runtime":
        from helpers.tool import coerce_bool

        if coerce_bool(args.get("reset"), False):
            result.append("reset")
    elif tool_id == "local:parallel" and action != "cancel":
        from helpers.parallel_tools import extract_tool_calls
        from helpers.tool import coerce_bool

        result = []
        if extract_tool_calls(args) is not None:
            result.append("start")
        wait = coerce_bool(args.get("wait"), action not in {"start", "collect"})
        if action == "await" or wait:
            result.append("await")
        elif args.get("job_ids"):
            result.append("collect")
        if not result:
            result.append(action)
    return list(dict.fromkeys(result))
