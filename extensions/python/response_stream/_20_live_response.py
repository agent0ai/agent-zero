from helpers import persist_chat, tokens
from helpers.extension import Extension
from agent import LoopData
import asyncio
from helpers.log import LogItem
from helpers import log


class LiveResponse(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        text: str = "",
        parsed: dict = {},
        **kwargs,
    ):
        if not self.agent:
            return
            
        try:
            if (
                not "tool_name" in parsed
                or parsed["tool_name"] != "response"
                or "tool_args" not in parsed
                or "text" not in parsed["tool_args"]
                or not parsed["tool_args"]["text"]
            ):
                return  # not a response

            # create log message and store it in loop data temporary params
            if "log_item_response" not in loop_data.params_temporary:
                # Share id with the agent log item so branching covers the response bubble
                gen_item = loop_data.params_temporary.get("log_item_generating")
                shared_id = gen_item.id if gen_item and gen_item.id else ""
                loop_data.params_temporary["log_item_response"] = (
                    self.agent.context.log.log(
                        type="response",
                        heading=f"icon://chat {self.agent.agent_name}: Responding",
                        id=shared_id,
                    )
                )

            # update log message
            log_item = loop_data.params_temporary["log_item_response"]
            log_item.update(content=parsed["tool_args"]["text"])
        except Exception as e:
            pass
