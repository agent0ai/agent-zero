from __future__ import annotations

import re
from typing import TYPE_CHECKING

from helpers import message_queue as mq
from helpers import projects
from helpers.persist_chat import save_tmp_chat
from helpers.state_monitor_integration import mark_dirty_for_context
from plugins._model_config.helpers import model_config

if TYPE_CHECKING:
    from agent import AgentContext


_CLEAR_VALUES = {"", "default", "none", "clear", "off"}
_SUPPORTED_COMMANDS = {"/send", "/queue", "/project", "/config", "/preset"}


def extract_command_line(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        return stripped
    return ""


def parse_command(text: str) -> tuple[str, str] | None:
    line = extract_command_line(text)
    if not line.startswith("/"):
        return None

    command, _, args = line.partition(" ")
    command = command.strip().lower()
    if command not in _SUPPORTED_COMMANDS:
        return None

    return command, args.strip()


def try_handle_command(context: "AgentContext", text: str) -> str | None:
    parsed = parse_command(text)
    if not parsed:
        return None

    command, args = parsed
    if command == "/send":
        return _handle_queue(context, "send")
    if command == "/queue":
        return _handle_queue(context, args)
    if command == "/project":
        return _handle_project(context, args)
    if command in {"/config", "/preset"}:
        return _handle_config(context, args)
    return None


def _handle_queue(context: "AgentContext", args: str) -> str:
    queue = mq.get_queue(context)
    count = len(queue)
    action = args.strip().lower()

    if not action:
        noun = "message" if count == 1 else "messages"
        return (
            f"Queue has {count} {noun}.\n"
            "Use /send or /queue send to send everything as one batch."
        )

    if action not in {"send", "all"}:
        return "Unknown queue action. Use /queue send to flush the queue."

    if count == 0:
        return "Queue is empty."

    sent_count = mq.send_all_aggregated(context)
    mark_dirty_for_context(context.id, reason="integration_commands.queue_send")
    noun = "message" if sent_count == 1 else "messages"
    return f"Sent {sent_count} queued {noun} as one batch."


def _handle_project(context: "AgentContext", args: str) -> str:
    items = projects.get_active_projects_list() or []
    current_name = context.get_data("project") or ""

    if not args:
        current_label = _describe_project(items, current_name)
        available = ", ".join(_format_project_entry(item) for item in items) or "none"
        return (
            f"Current project: {current_label}\n"
            f"Available projects: {available}\n"
            "Use /project <name> to switch, or /project none to clear it."
        )

    desired = _strip_quotes(args)
    if _normalize_lookup(desired) in _CLEAR_VALUES:
        if not current_name:
            return "No project is active."
        projects.deactivate_project(context.id)
        return "Cleared the active project."

    match, ambiguous = _match_named_item(items, desired, keys=("name", "title"))
    if ambiguous:
        names = ", ".join(_format_project_entry(item) for item in ambiguous)
        return f"Project name is ambiguous. Matches: {names}"
    if not match:
        available = ", ".join(_format_project_entry(item) for item in items) or "none"
        return f"Project '{desired}' was not found. Available projects: {available}"

    if match.get("name") == current_name:
        return f"Already using project {match.get('title') or match.get('name')}."

    projects.activate_project(context.id, match["name"])
    return f"Switched project to {match.get('title') or match['name']}."


def _handle_config(context: "AgentContext", args: str) -> str:
    allowed = model_config.is_chat_override_allowed(context.agent0)
    presets = [preset for preset in model_config.get_presets() if preset.get("name")]
    current_override = context.get_data("chat_model_override")

    if not args:
        current_label = _describe_override(current_override)
        available = ", ".join(preset["name"] for preset in presets) or "none"
        suffix = "Use /config <name> to switch, or /config default to clear it."
        if not allowed:
            suffix = "Per-chat config switching is disabled in Model Configuration."
        return (
            f"Current config: {current_label}\n"
            f"Available configs: {available}\n"
            f"{suffix}"
        )

    if not allowed:
        return "Config switching is disabled in Model Configuration."

    desired = _strip_quotes(args)
    if _normalize_lookup(desired) in _CLEAR_VALUES:
        if not current_override:
            return "Already using the default config."
        context.set_data("chat_model_override", None)
        save_tmp_chat(context)
        mark_dirty_for_context(context.id, reason="integration_commands.config_clear")
        return "Switched back to the default config."

    match, ambiguous = _match_named_item(presets, desired, keys=("name",))
    if ambiguous:
        names = ", ".join(item["name"] for item in ambiguous)
        return f"Config name is ambiguous. Matches: {names}"
    if not match:
        available = ", ".join(preset["name"] for preset in presets) or "none"
        return f"Config '{desired}' was not found. Available configs: {available}"

    preset_name = match["name"]
    if isinstance(current_override, dict) and current_override.get("preset_name") == preset_name:
        return f"Already using config {preset_name}."

    context.set_data("chat_model_override", {"preset_name": preset_name})
    save_tmp_chat(context)
    mark_dirty_for_context(context.id, reason="integration_commands.config_set")
    return f"Switched config to {preset_name}."


def _format_project_entry(item: dict) -> str:
    title = str(item.get("title", "") or "").strip()
    name = str(item.get("name", "") or "").strip()
    if title and title.lower() != name.lower():
        return f"{title} ({name})"
    return name or title


def _describe_project(items: list[dict], current_name: str) -> str:
    if not current_name:
        return "none"
    for item in items:
        if item.get("name") == current_name:
            return item.get("title") or current_name
    return current_name


def _describe_override(override: dict | None) -> str:
    if not override:
        return "Default"
    if isinstance(override, dict) and override.get("preset_name"):
        return str(override["preset_name"])
    return "Custom override"


def _strip_quotes(value: str) -> str:
    trimmed = value.strip()
    if len(trimmed) >= 2 and trimmed[0] == trimmed[-1] and trimmed[0] in {'"', "'"}:
        return trimmed[1:-1].strip()
    return trimmed


def _normalize_lookup(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[\s_\-]+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9 ]+", "", lowered)
    return lowered.strip()


def _match_named_item(
    items: list[dict],
    desired: str,
    *,
    keys: tuple[str, ...],
) -> tuple[dict | None, list[dict]]:
    normalized = _normalize_lookup(desired)
    exact_matches: list[dict] = []

    for item in items:
        values = [str(item.get(key, "") or "") for key in keys]
        normalized_values = [_normalize_lookup(value) for value in values if value]
        if normalized in normalized_values:
            exact_matches.append(item)

    if len(exact_matches) == 1:
        return exact_matches[0], []
    if len(exact_matches) > 1:
        return None, exact_matches

    partial_matches: list[dict] = []
    for item in items:
        values = [str(item.get(key, "") or "") for key in keys]
        normalized_values = [_normalize_lookup(value) for value in values if value]
        if any(normalized and normalized in value for value in normalized_values):
            partial_matches.append(item)

    if len(partial_matches) == 1:
        return partial_matches[0], []
    if len(partial_matches) > 1:
        return None, partial_matches

    return None, []
