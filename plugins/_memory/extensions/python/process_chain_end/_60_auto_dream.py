from agent import AgentContextType
from helpers import persist_chat, plugins
from helpers.extension import Extension

from plugins._memory.helpers.auto_dream import schedule_auto_dream
from plugins._memory.helpers.memory import get_agent_memory_subdir


class AutoDream(Extension):

    async def execute(self, **kwargs):
        if not self.agent:
            return
        if self.agent.number != 0:
            return
        if self.agent.context.type == AgentContextType.BACKGROUND:
            return

        config = plugins.get_plugin_config("_memory", self.agent) or {}
        if not config.get("memory_memorize_enabled"):
            return
        if not config.get("memory_auto_dream_enabled"):
            return

        if self.agent.config.profile:
            self.agent.context.set_data("agent_profile", self.agent.config.profile)

        persist_chat.save_tmp_chat(self.agent.context)

        schedule_auto_dream(
            context_id=self.agent.context.id,
            project_name=self.agent.context.get_data("project"),
            agent_profile=self.agent.config.profile,
            memory_subdir=get_agent_memory_subdir(self.agent),
        )
