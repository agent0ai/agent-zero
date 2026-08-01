from helpers import persist_chat, tokens
from helpers.extension import Extension
from helpers.notification import NotificationManager, NotificationPriority, NotificationType
from helpers.state_monitor_integration import mark_dirty_all
from agent import LoopData
import asyncio


class RenameChat(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        asyncio.create_task(self.change_name())

    async def change_name(self):
        if not self.agent:
            return

        try:
            # prepare history
            from plugins._model_config.helpers.model_config import get_utility_model_config
            util_cfg = get_utility_model_config(self.agent)
            history_text = self.agent.history.output_text()
            ctx_length = min(
                int(util_cfg.get("ctx_length", 128000) * 0.7), 5000
            )
            history_text = tokens.trim_to_tokens(history_text, ctx_length, "start")
            # prepare system and user prompt
            system = self.agent.read_prompt("fw.rename_chat.sys.md")
            current_name = self.agent.context.name
            message = self.agent.read_prompt(
                "fw.rename_chat.msg.md", current_name=current_name, history=history_text
            )
            # call utility model
            try:
                new_name = await self.agent.call_utility_model(
                    system=system, message=message, background=True
                )
            except Exception:
                NotificationManager.send_notification(
                    type=NotificationType.ERROR,
                    priority=NotificationPriority.NORMAL,
                    title="Chat Rename Failed",
                    message="Automatic chat renaming failed because the Utility Model was not reachable.",
                    detail=(
                        "Automatic chat renaming uses the Utility Model. Check Settings > Models > "
                        "Utility Model, provider/API key, and network reachability."
                    ),
                    display_time=10,
                    group="chat_rename",
                    id=f"chat_rename_failed_{self.agent.context.id}",
                )
                return
            # update name
            if new_name:
                new_name = " ".join(str(new_name).split())
                # P028: Guard against JSON-looking names (utility model echoes)
                stripped = new_name.lstrip()
                if stripped and stripped[0] in "{[":
                    import json as _json
                    extracted = None
                    # Step 1: Try to parse JSON and extract headline (best quality)
                    try:
                        parsed = _json.loads(stripped)
                        headline = parsed.get("headline")
                        if isinstance(headline, str) and headline.strip():
                            extracted = headline.strip()
                        else:
                            thoughts = parsed.get("thoughts")
                            if isinstance(thoughts, list) and thoughts:
                                first = thoughts[0]
                                if isinstance(first, str) and first.strip():
                                    extracted = first.strip()
                    except (_json.JSONDecodeError, ValueError, AttributeError):
                        pass
                    # Step 2: Fall back to first user message topic
                    if not extracted:
                        try:
                            msgs = self.agent.history.output()
                            for msg in msgs:
                                if not msg.ai and msg.content:
                                    content = str(msg.content)
                                    first_line = content.split(chr(10))[0].split(".")[0].strip()
                                    if first_line:
                                        extracted = first_line[:40]
                                        if len(first_line) > 40:
                                            extracted += "..."
                                        break
                        except Exception:
                            pass
                    # Step 3: Last resort
                    new_name = extracted or "Conversation"
                if len(new_name) > 40:
                    new_name = new_name[:40] + "..."
                if not new_name:
                    return
                # apply to context and save
                self.agent.context.name = new_name
                persist_chat.save_tmp_chat(self.agent.context)
                mark_dirty_all(reason="monologue_start.RenameChat.change_name")
        except Exception:
            pass  # non-critical
