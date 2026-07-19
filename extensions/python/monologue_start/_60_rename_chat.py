from helpers import persist_chat, tokens
from helpers.extension import Extension
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
            new_name = await self.agent.call_utility_model(
                system=system, message=message, background=True
            )
            # update name
            if new_name:
                # trim name to max length if needed
                if len(new_name) > 40:
                    new_name = new_name[:40] + "..."
                # apply to context and save
                self.agent.context.name = new_name
                persist_chat.save_tmp_chat(self.agent.context)
        except Exception as e:
            pass  # non-critical
