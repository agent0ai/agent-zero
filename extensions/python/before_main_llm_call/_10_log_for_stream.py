from helpers import persist_chat, tokens
from helpers.extension import Extension
from agent import LoopData
import asyncio
from helpers.log import LogItem
from helpers import log
import math
import uuid


class LogForStream(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), text: str = "", **kwargs):
        if not self.agent:
            return
        
        # create log message and store it in loop data temporary params
        if "log_item_generating" not in loop_data.params_temporary:
            loop_data.params_temporary["log_item_generating"] = (
                self.agent.context.log.log(
                    type="agent",
                    heading=build_default_heading(self.agent),
                    id=str(uuid.uuid4()),
                )
            )

def build_heading(agent, text: str, icon: str = "network_intelligence"):
    # Include agent identifier for all agents (A0:, A1:, A2:, etc.)
    agent_prefix = f"{agent.agent_name}: "
    return f"{agent_prefix}{text}"

def build_default_heading(agent):
    return build_heading(agent, "Calling LLM...") 