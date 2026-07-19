from __future__ import annotations

from typing import Any

from agent import AgentContext
from helpers import message_queue as mq
from helpers import plugins, projects
from helpers.integration_commands import try_handle_command
from helpers.state_monitor_integration import mark_dirty_for_context

CLI_ONLY = {
    "quit": "Quit is an A0 CLI shell command. Close this browser tab or stop the WebUI session when you are done.",
}


def run(payload: dict[str, Any]) -> dict[str, Any]:
    invocation = payload.get("invocation") or {}
    raw_name = str(invocation.get("command_name") or "").strip().lower()
    command = raw_name
    raw_args = str(invocation.get("raw_arguments") or "").strip()
    arguments = invocation.get("arguments") if isinstance(invocation.get("arguments"), dict) else {}
    context_id = str((payload.get("context") or {}).get("context_id") or "").strip()
    context = _context(context_id)

    if command == "new":
        return _effects(_toast("Created a new chat."), {"type": "new_chat"})
    if command == "chat":
        return _handle_chat(arguments)
    if command == "chats":
        return _show_markdown("Chats", _chat_list(context, arguments))
    if command == "clear":
        return _effects(_toast("Visible transcript cleared."), {"type": "clear_transcript"})
    if command == "project":
        return _handle_project(context, raw_args)
    if command == "profile":
        return _handle_profile(context, raw_args)
    if command == "plugins":
        return _effects({"type": "open_modal", "path": "/components/plugins/list/plugin-list.html"})
    if command == "compact":
        return _effects({"type": "compact_chat"})
    if command == "pause":
        return _effects(_toast("Pause requested."), {"type": "pause_agent", "paused": True})
    if command == "resume":
        return _effects(_toast("Resume requested."), {"type": "pause_agent", "paused": False})
    if command == "nudge":
        return _effects(_toast("Nudge sent."), {"type": "nudge_agent"})
    if command == "send":
        return _handle_queue(context, ["send"])
    if command == "queue":
        return _handle_queue(context, list(arguments.get("tokens") or []))
    if command == "presets":
        return _effects({"type": "open_modal", "path": "/plugins/_model_config/webui/main.html"})
    if command == "models":
        return _handle_models(context, raw_args)
    if command == "browser":
        return _handle_browser(context, raw_args)
    if command == "attach":
        return _effects({"type": "attach_files"})
    if command == "computer-use":
        return _handle_computer_use(context_id, raw_args)
    if command == "copy":
        return _effects({"type": "copy_transcript"})
    if command == "status":
        return _show_markdown("Status", _status(context))
    if command in CLI_ONLY:
        return _effects(_toast(CLI_ONLY[command], level="info"))

    return _effects(_toast(f"Unknown command: /{raw_name or command}", level="error"))


def _context(context_id: str) -> AgentContext | None:
    if context_id:
        return AgentContext.get(context_id)
    return AgentContext.current() or AgentContext.first()


def _require_context(context: AgentContext | None) -> str | None:
    if context:
        return None
    return "Open or create a chat context first."


def _effects(*effects: dict[str, Any]) -> dict[str, Any]:
    return {"text": "", "effects": [effect for effect in effects if effect]}


def _toast(message: str, *, level: str = "success") -> dict[str, Any]:
    return {"type": "toast", "message": message, "level": level}


def _show_markdown(title: str, content: str) -> dict[str, Any]:
    return _effects({"type": "show_markdown", "title": title, "content": content})


def _handle_chat(arguments: dict[str, Any]) -> dict[str, Any]:
    selector = str((arguments.get("positional") or [""])[0] or "").strip()
    if not selector:
        return _effects(_toast("Usage: /chat <context_id>", level="error"))
    if not AgentContext.get(selector):
        return _effects(_toast(f"Chat context '{selector}' was not found.", level="error"))
    return _effects(_toast(f"Switched to {selector}."), {"type": "select_chat", "context_id": selector})


def _handle_project(context: AgentContext | None, raw_args: str) -> dict[str, Any]:
    if not raw_args:
        return _effects({"type": "open_modal", "path": "/components/projects/project-list.html"})
    error = _require_context(context)
    if error:
        return _effects(_toast(error, level="error"))
    return _show_markdown("Project", try_handle_command(context, f"/project {raw_args}") or "")


def _handle_profile(context: AgentContext | None, raw_args: str) -> dict[str, Any]:
    if not raw_args:
        return _effects({"type": "open_modal", "path": "/components/settings/settings.html"})
    error = _require_context(context)
    if error:
        return _effects(_toast(error, level="error"))
    return _show_markdown("Agent Profile", try_handle_command(context, f"/agent {raw_args}") or "")


def _handle_models(context: AgentContext | None, raw_args: str) -> dict[str, Any]:
    return _effects({"type": "open_plugin_config", "plugin": "_model_config"})


def _handle_browser(context: AgentContext | None, raw_args: str) -> dict[str, Any]:
    args = raw_args.strip().lower().replace("-", "_").split()
    action = args[0] if args else ""
    if not action:
        return _effects({"type": "open_modal", "path": "/plugins/_browser/webui/main.html"})
    if action in {"status", "state"}:
        return _show_markdown("Browser", _browser_status(context))
    if action not in {"host", "container", "docker"}:
        return _effects(_toast("Usage: /browser [host|container|status]", level="error"))

    project_name = projects.get_context_project_name(context) if context else ""
    settings = plugins.get_plugin_config("_browser", project_name=project_name or "", agent_profile="") or {}
    settings["runtime_backend"] = "host_required" if action == "host" else "container"
    plugins.save_plugin_config("_browser", project_name or "", "", settings)
    if context:
        mark_dirty_for_context(context.id, reason="plugins._commands.browser_runtime")
    label = "Host browser through A0 CLI" if settings["runtime_backend"] == "host_required" else "Internal Docker browser"
    return _effects(_toast(f"Browser runtime set to {label}."))


def _handle_computer_use(context_id: str, raw_args: str) -> dict[str, Any]:
    action = (
        "-".join(
            part.strip().lower().replace("_", "-") for part in raw_args.split()
        )
        or "status"
    )
    enabled = action in {"on", "enable", "enabled", "true", "yes", "1"}
    disabled = action in {"off", "disable", "disabled", "false", "no", "0"}
    if enabled or disabled:
        command = "on" if enabled else "off"
        return _effects(
            {
                "type": "computer_use",
                "enabled": enabled,
                "fallback": (
                    "Computer Use permissions are controlled on the connected host. "
                    "Use Host access in A0 Launcher, or run "
                    f"`/computer-use {command}` in the A0 CLI terminal."
                ),
            }
        )
    return _show_markdown("Computer Use", _computer_use_status(context_id))


def _browser_status(context: AgentContext | None) -> str:
    project_name = projects.get_context_project_name(context) if context else ""
    settings = plugins.get_plugin_config("_browser", project_name=project_name or "", agent_profile="") or {}
    runtime = str(settings.get("runtime_backend") or "container")
    label = "Host browser through A0 CLI" if runtime == "host_required" else "Internal Docker browser"
    return f"Browser runtime: {label}\n\nUse `/browser host` or `/browser container` to switch."


def _handle_queue(context: AgentContext | None, tokens: list[str]) -> dict[str, Any]:
    error = _require_context(context)
    if error:
        return _effects(_toast(error, level="error"))

    queue = mq.get_queue(context)
    if not tokens:
        return _show_markdown("Queue", _queue_summary(queue))

    action = str(tokens[0] or "").lower()
    if action in {"send", "all", "flush"}:
        if not queue:
            return _effects(_toast("No queued messages."))
        sent_count = mq.send_all_aggregated(context)
        mark_dirty_for_context(context.id, reason="plugins._commands.queue_send")
        noun = "message" if sent_count == 1 else "messages"
        return _effects(_toast(f"Sent {sent_count} queued {noun}."))

    if action in {"clear", "delete"} and len(tokens) == 1:
        mq.remove(context)
        mark_dirty_for_context(context.id, reason="plugins._commands.queue_clear")
        return _effects(_toast("Queue cleared."))

    if action in {"remove", "rm", "delete"}:
        if len(tokens) < 2:
            return _effects(_toast("Usage: /queue remove <number|id>", level="error"))
        item_id = _queue_selector_to_id(queue, str(tokens[1]))
        if not item_id:
            return _effects(_toast(f"No queued message matches '{tokens[1]}'.", level="error"))
        mq.remove(context, item_id)
        mark_dirty_for_context(context.id, reason="plugins._commands.queue_remove")
        return _effects(_toast("Queued message removed."))

    return _effects(_toast("Usage: /queue [send|clear|remove <number|id>]", level="error"))


def _queue_summary(queue: list[dict[str, Any]]) -> str:
    if not queue:
        return "No queued messages."
    lines = [f"Queued messages ({len(queue)}):"]
    for index, item in enumerate(queue, start=1):
        text = str(item.get("text") or "").strip() or "(attachment only)"
        if len(text) > 100:
            text = text[:97].rstrip() + "..."
        attachments = item.get("attachments") or []
        suffix = f" [{len(attachments)} files]" if attachments else ""
        lines.append(f"{index}. {text}{suffix}")
    return "\n".join(lines)


def _queue_selector_to_id(queue: list[dict[str, Any]], selector: str) -> str:
    value = selector.strip()
    if value.isdigit():
        index = int(value) - 1
        if 0 <= index < len(queue):
            return str(queue[index].get("id") or "")
        return ""
    return value


def _chat_list(context: AgentContext | None, arguments: dict[str, Any]) -> str:
    items = list(AgentContext.all())
    flags = arguments.get("flags") or {}
    active_project_only = bool(flags.get("project") or flags.get("active_project") or flags.get("p"))
    sort_by = str(flags.get("sort") or "").lower()
    positional = [str(item).lower() for item in (arguments.get("positional") or [])]
    if not sort_by:
        sort_by = next((item for item in positional if item in {"updated", "created", "name"}), "updated")
    if sort_by not in {"updated", "created", "name"}:
        return "Usage: /chats [--project|--all-projects] [--sort=updated|created|name]"

    if active_project_only and context:
        project_name = projects.get_context_project_name(context) or ""
        items = [item for item in items if (projects.get_context_project_name(item) or "") == project_name]

    def sort_key(item: AgentContext) -> Any:
        output = item.output()
        if sort_by == "name":
            return (item.name or item.id).casefold()
        if sort_by == "created":
            return str(output.get("created_at") or "")
        return str(output.get("last_message") or output.get("created_at") or "")

    items = sorted(items, key=sort_key, reverse=sort_by != "name")
    if not items:
        return "No chats found."

    lines = ["| Chat | Context | State |", "| --- | --- | --- |"]
    for item in items[:30]:
        marker = "current" if context and item.id == context.id else ("running" if item.is_running() else "idle")
        lines.append(f"| {_escape_cell(item.name or item.id)} | `{item.id}` | {marker} |")
    if len(items) > 30:
        lines.append(f"\nShowing 30 of {len(items)} chats.")
    return "\n".join(lines)


def _status(context: AgentContext | None) -> str:
    error = _require_context(context)
    if error:
        return error
    project_name = projects.get_context_project_name(context) or "none"
    profile = getattr(context.agent0.config, "profile", "default") if context.agent0 else "default"
    running = "running" if context.is_running() else "idle"
    if getattr(context, "paused", False):
        running = "paused"
    return "\n".join(
        [
            f"Context: `{context.id}`",
            f"State: {running}",
            f"Project: {project_name}",
            f"Agent profile: {profile}",
            f"Queued messages: {len(mq.get_queue(context))}",
        ]
    )


def _computer_use_status(context_id: str) -> str:
    from plugins._a0_connector.helpers import ws_runtime

    sids = (
        ws_runtime.remote_tool_sids_for_context(context_id)
        if context_id
        else sorted(ws_runtime.connected_sids())
    )
    if not sids:
        return (
            "No A0 CLI or Launcher host gateway is connected to this WebUI session.\n\n"
            "Open this Instance in A0 Launcher with Host access, or connect A0 CLI, then run `/computer-use on`."
        )

    lines = ["Connected host-control sessions:"]
    for sid in sids:
        metadata = ws_runtime.computer_use_metadata_for_sid(sid) or {}
        if not metadata:
            lines.append(f"- `{sid}`: connected, but not advertising Computer Use metadata.")
            continue
        state = "enabled" if metadata.get("enabled") else "disabled"
        supported = "supported" if metadata.get("supported") else "unsupported"
        status = str(metadata.get("status") or "unknown")
        detail = str(metadata.get("last_error") or metadata.get("support_reason") or "").strip()
        suffix = f" ({detail})" if detail else ""
        lines.append(f"- `{sid}`: {state}, {supported}, status: {status}{suffix}")
    lines.append(
        "\nUse `/computer-use on|off` in A0 Launcher or A0 CLI to change local Computer Use."
    )
    return "\n".join(lines)


def _escape_cell(value: str) -> str:
    return str(value).replace("|", "\\|")
