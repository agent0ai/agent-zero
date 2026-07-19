from __future__ import annotations

from typing import Any

from helpers.extension import Extension
from plugins._commands.helpers import commands


class ResolveSlashCommand(Extension):
    async def execute(self, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        if not isinstance(data, dict):
            return

        args = data.get("args")
        if not isinstance(args, tuple) or len(args) < 3:
            return

        context, message = args[0], args[2]
        raw_message = getattr(message, "message", None)
        if not isinstance(raw_message, str):
            return

        resolution = await commands.resolve_message_command(
            raw_message,
            context_id=str(getattr(context, "id", "") or ""),
        )
        if not resolution:
            return

        result = resolution.get("result") or {}
        next_text = str(result.get("text") or "")
        notes: list[str] = []
        unsupported = False

        for effect in result.get("effects") or []:
            if not isinstance(effect, dict):
                continue
            effect_type = str(effect.get("type") or "").strip().lower()
            if effect_type == "replace_input":
                next_text = str(effect.get("text") or "")
            elif effect_type == "append_input":
                chunk = str(effect.get("text") or "")
                next_text = f"{next_text}\n{chunk}" if next_text else chunk
            elif effect_type == "send_message":
                next_text = str(effect.get("text") or next_text)
            elif effect_type == "toast":
                notes.append(str(effect.get("message") or ""))
            elif effect_type == "show_markdown":
                notes.append(str(effect.get("content") or ""))
            elif effect_type != "goal_changed":
                unsupported = True

        command_name = str((resolution.get("command") or {}).get("name") or "command")
        if unsupported:
            data["result"] = f"/{command_name} requires the WebUI."
        elif next_text.strip():
            message.message = next_text
        else:
            data["result"] = "\n\n".join(note for note in notes if note) or f"/{command_name} complete."
