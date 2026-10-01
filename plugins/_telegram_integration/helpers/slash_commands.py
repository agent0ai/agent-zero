"""Resolve Agent Zero commands before Telegram adds its message envelope."""
from __future__ import annotations

import re
from copy import deepcopy

from agent import AgentContext
from helpers import integration_commands, plugins, projects
from helpers.persist_chat import save_tmp_chat
from plugins._commands.helpers import commands
from plugins._telegram_integration.helpers import command_ui, telegram_client as tc


# These names retain Telegram's existing behavior and pickers for bundled commands.
PICKERS = {"models": "model", "presets": "model", "chats": "sessions", "chat": "sessions"}


def available_commands(context=None) -> list[dict]:
    return commands.list_context_commands(context)


def menu_commands() -> list[tuple[str, str]]:
    menu = dict(integration_commands.telegram_menu_commands())
    menu["start"] = "Connect to Agent Zero."
    for item in available_commands():
        name = item["name"].replace("-", "_")
        if re.fullmatch(r"[a-z0-9_]{1,32}", name):
            menu.setdefault(name, str(item.get("description") or item["name"])[:256])
    return list(menu.items())[:100]


async def reply(token, chat_id, message_id, text, markup=None):
    # Plain text avoids treating command output as Telegram HTML.
    for chunk in tc._split_text(str(text), tc.MAX_MESSAGE_LENGTH):
        await tc.raw_send_text(token, chat_id, chunk, message_id, None, markup)
        markup = None


async def handle(context, token, chat_id, message_id, text) -> str | None:
    """Return agent input, or None when the command was handled without an LLM."""
    invocation = commands.parse_slash_invocation(text)
    name = invocation["command_name"]
    if not name:
        return text
    items = available_commands(context)
    item = next((c for c in items if c["name"] == name), None)
    if not item:
        item = next((c for c in items if c["name"].replace("-", "_") == name), None)
    args = invocation["raw_arguments"]
    name = item["name"] if item else name
    line = f"/{name} {args}".rstrip()
    custom = item and item.get("source_scope_key") != "builtin"
    try:
        if not custom:
            if name in {"commands", "help"}:
                await send_menu(context, token, chat_id, message_id)
                return None
            if name in PICKERS and (name != "chats" or not args):
                if name in {"models", "presets"} and args:
                    result = integration_commands.try_handle_command(context, f"/model {args}", integration="telegram")
                    await reply(token, chat_id, message_id, result or "Use /model to choose a preset.")
                    return None
                if name == "chat" and args:
                    target = AgentContext.get(args)
                    if not target:
                        raise ValueError("Chat not found. Use /sessions to choose a chat.")
                    await select_session(context, target)
                    await reply(token, chat_id, message_id, f"Switched to {target.name or target.id}.")
                else:
                    await command_ui.handle_command(context, token, chat_id, message_id, f"/{PICKERS[name]}")
                return None
            # Keep Telegram reset semantics; /new below uses a fresh context.
            if (name != "new" or not item) and (name != "queue" or not item):
                if await command_ui.handle_command(context, token, chat_id, message_id, line):
                    return None
                # /profile with arguments uses the shared command, including creation.
                if name != "profile" or not item:
                    result = integration_commands.try_handle_command(context, line, integration="telegram")
                    if result is not None:
                        await reply(token, chat_id, message_id, result)
                        return None
        if not item:
            if text.lstrip().startswith("/"):
                await reply(token, chat_id, message_id, f"Unknown command: /{name}. Use /commands to see commands for this chat.")
                return None
            return text
        resolution = await commands.resolve_command_invocation(
            path=item["path"], slash_text=line,
            project_name=projects.get_context_project_name(context) or "", context_id=context.id,
        )
        return await apply_result(context, token, chat_id, message_id, name, resolution["result"])
    except Exception as exc:
        await reply(token, chat_id, message_id, f"/{name} failed: {exc}")
        return None


async def apply_result(context, token, chat_id, message_id, name, result):
    text = str(result.get("text") or "")
    notes = []
    for effect in result.get("effects") or []:
        if not isinstance(effect, dict):
            continue
        kind = str(effect.get("type") or "").lower()
        if kind in {"replace_input", "send_message"}:
            text = str(effect.get("text") or (text if kind == "send_message" else ""))
        elif kind == "append_input":
            text = "\n".join(filter(None, (text, str(effect.get("text") or ""))))
        elif kind in {"toast", "show_markdown"}:
            notes.append(str(effect.get("message" if kind == "toast" else "content") or ""))
        elif kind == "goal_changed":
            pass
        elif kind == "new_chat":
            target = AgentContext(deepcopy(context.config))
            command_ui._copy_telegram_binding(context, target)
            for key in ("telegram_bot_cfg", "telegram_stream_enabled", "telegram_tools_enabled", "chat_model_override"):
                if key in context.data:
                    target.data[key] = deepcopy(context.data[key])
            project = projects.get_context_project_name(context)
            if project:
                projects.activate_project(target.id, project)
            command_ui._set_session_mapping(target)
            save_tmp_chat(target)
        elif kind == "select_chat":
            target = AgentContext.get(str(effect.get("context_id") or ""))
            if not target:
                raise ValueError("Chat not found.")
            await select_session(context, target)
        elif kind in {"pause_agent", "nudge_agent"}:
            action = "nudge" if kind == "nudge_agent" else ("pause" if effect.get("paused") else "resume")
            notes.append(integration_commands.try_handle_command(context, f"/{action}", integration="telegram") or "")
        elif kind in {"reset_chat", "clear_transcript"}:
            notes.append(integration_commands.try_handle_command(context, "/clear", integration="telegram") or "")
        elif kind == "compact_chat":
            await compact_menu(context, token, chat_id, message_id)
        elif kind == "attach_files":
            notes.append("Use Telegram's attachment button to send photos or files, with an optional command in the caption.")
        elif kind == "copy_transcript":
            from aiogram import Bot
            from aiogram.types import BufferedInputFile
            from helpers.history import output_text
            transcript = output_text(context.agent0.history.output(), ai_label="assistant", human_label="user")
            if not transcript:
                notes.append("This chat has no transcript yet.")
            else:
                async with Bot(token) as bot:
                    await bot.send_document(chat_id, BufferedInputFile(transcript.encode("utf-8"), filename="transcript.txt"))
        elif kind == "computer_use":
            notes.append(str(effect.get("fallback") or "Use Host access in A0 Launcher to change computer permissions."))
        elif kind == "test_agent_profile":
            notes.append(integration_commands.try_handle_command(context, f"/agent {effect.get('profile_id', '')}", integration="telegram") or "")
        elif kind == "open_modal" and effect.get("path") == "/components/projects/project-list.html":
            await command_ui.send_project_picker(context, token, chat_id, message_id, 0)
        elif kind == "open_modal" and effect.get("path") == "/plugins/_model_config/webui/main.html":
            await command_ui.send_model_picker(context, token, chat_id, message_id, 0)
        elif kind == "open_agent_editor" and effect.get("view") == "manage":
            await command_ui.send_agent_picker(context, token, chat_id, message_id, 0)
        elif kind == "open_modal" and effect.get("path") == "/plugins/_browser/webui/main.html":
            await reply(token, chat_id, message_id, "Browser runtime", {"inline_keyboard": [[
                {"text": label, "callback_data": f"a0:run:browser {action}"}
                for label, action in (("Status", "status"), ("Docker", "container"), ("Host", "host"))
            ]]})
        elif kind in {"open_modal", "open_plugin_config", "open_agent_editor"}:
            if name in {"plugins", "permissions"}:
                from plugins._telegram_integration.helpers import settings_ui
                await settings_ui.show(context, token, chat_id, message_id, name)
            else:
                notes.append(f"Open /{name} in the Agent Zero WebUI to edit these settings.")
        else:
            notes.append(f"/{name}: the '{kind}' action requires the Agent Zero WebUI.")
    if notes:
        await reply(token, chat_id, message_id, "\n\n".join(filter(None, notes)))
    elif not text.strip() and not result.get("effects"):
        await reply(token, chat_id, message_id, f"/{name} complete.")
    return text if text.strip() else None


async def select_session(context, target):
    if context.is_running() or target.is_running():
        raise ValueError("Stop the active run before switching sessions.")
    command_ui._copy_telegram_binding(context, target)
    command_ui._set_session_mapping(target)
    save_tmp_chat(target)


async def send_menu(context, token, chat_id, message_id, page=0):
    catalog = {c["name"]: (c.get("description", ""), c.get("argument_hint", "")) for c in available_commands(context)}
    for command in integration_commands.COMMAND_REGISTRY:
        if integration_commands.resolve_command(command.name, integration="telegram"):
            catalog.setdefault(command.name, (command.description, command.args_hint))
    items = sorted(catalog.items())
    page = min(max(0, page), max(0, (len(items) - 1) // 8))
    lines = [f"Commands for this chat ({page + 1}/{max(1, (len(items) + 7) // 8)})"]
    rows = []
    for name, (description, hint) in items[page * 8:page * 8 + 8]:
        lines.append(f"/{name}{' ' + hint if hint else ''} — {description}")
        callback = f"a0:command:{name}"
        if len(callback.encode()) <= 64:
            rows.append([{"text": f"/{name}", "callback_data": callback}])
    nav = []
    if page:
        nav.append({"text": "Prev", "callback_data": f"a0:page:{page - 1}"})
    if (page + 1) * 8 < len(items):
        nav.append({"text": "Next", "callback_data": f"a0:page:{page + 1}"})
    if nav:
        rows.append(nav)
    await reply(token, chat_id, message_id, "\n\n".join(lines), {"inline_keyboard": rows})


async def compact_menu(context, token, chat_id, message_id):
    from plugins._chat_compaction.helpers.compactor import MIN_COMPACTION_TOKENS, get_compaction_stats
    if "_chat_compaction" not in plugins.get_enabled_plugins(context.agent0):
        raise ValueError("Chat Compaction is disabled for this chat.")
    if context.is_running():
        raise ValueError("Stop the active run before compacting.")
    stats = await get_compaction_stats(context)
    if stats["token_count"] < MIN_COMPACTION_TOKENS:
        raise ValueError(f"Not enough content to compact (minimum {MIN_COMPACTION_TOKENS:,} tokens).")
    await reply(token, chat_id, message_id,
        f"Compact {stats['message_count']} messages (~{stats['token_count']:,} tokens)? The original conversation will be backed up.",
        {"inline_keyboard": [[{"text": "Compact", "callback_data": f"a0:compact:{context.id}"}]]})


async def handle_callback(context, token, chat_id, message_id, data):
    """Return (handled, agent text) for command menu callbacks."""
    if not data.startswith("a0:"):
        return False, None
    _, action, value = data.split(":", 2)
    from plugins._telegram_integration.helpers import settings_ui
    if await settings_ui.handle_callback(context, token, chat_id, message_id, action, value):
        return True, None
    if action == "page":
        await send_menu(context, token, chat_id, message_id, int(value))
    elif action == "command":
        items = available_commands(context)
        item = next((item for item in items if item["name"] == value), None)
        definition = integration_commands.resolve_command(value, integration="telegram")
        if not item and not definition:
            raise ValueError("This command is no longer available. Send /commands again.")
        hint = item.get("argument_hint", "") if item else (definition.args_hint if definition else "")
        # Selecting a command shows its usage; a separate Run button is explicit.
        await reply(token, chat_id, message_id, f"/{value}{' ' + hint if hint else ''}\nSend this command with any arguments, or run it now.",
            {"inline_keyboard": [[{"text": f"Run /{value}", "callback_data": f"a0:run:{value}"}]]})
    elif action == "run":
        return True, await handle(context, token, chat_id, message_id, f"/{value}")
    elif action == "compact":
        if value != context.id or context.is_running():
            raise ValueError("This confirmation is no longer current. Send /compact again.")
        if "_chat_compaction" not in plugins.get_enabled_plugins(context.agent0):
            raise ValueError("Chat Compaction is disabled for this chat.")
        await reply(token, chat_id, message_id, "Compacting chat…")
        context.run_task(_compact, context, token, chat_id, message_id)
    return True, None


async def _compact(context, token, chat_id, message_id):
    from plugins._chat_compaction.helpers.compactor import run_compaction
    try:
        await run_compaction(context)
        await reply(token, chat_id, message_id, "Chat compacted. The original conversation was backed up.")
    except Exception as exc:
        await reply(token, chat_id, message_id, f"Compaction failed: {exc}")
