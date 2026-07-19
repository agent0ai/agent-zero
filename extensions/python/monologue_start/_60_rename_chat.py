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
