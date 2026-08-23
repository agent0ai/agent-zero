import asyncio

from helpers.extension import Extension
from helpers.errors import HandledException
from agent import LoopData
from plugins._memory.extensions.python.message_loop_prompts_after._50_recall_memories import DATA_NAME_TASK as DATA_NAME_TASK_MEMORIES, DATA_NAME_ITER as DATA_NAME_ITER_MEMORIES
from helpers import plugins

class RecallWait(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):

        if not self.agent:
            return

        set = plugins.get_plugin_config("_memory", self.agent)
        if not set:
            return None

        task = self.agent.get_data(DATA_NAME_TASK_MEMORIES)
        iter = self.agent.get_data(DATA_NAME_ITER_MEMORIES) or 0

        if task:

            # if memory recall is set to delayed mode, do not await on the iteration it was called
            if set["memory_recall_delayed"]:
                if iter == loop_data.iteration:
                    # insert info about delayed memory to extras
                    delay_text = self.agent.read_prompt("memory.recall_delay_msg.md")
                    loop_data.extras_temporary["memory_recall_delayed"] = delay_text
                    return

            # otherwise await the task
            try:
                await task
            except asyncio.TimeoutError as error:
                self.agent.context.log.log(
                    type="error",
                    heading="Memory recall timed out",
                    content=(
                        "No response was generated because required memory recall did "
                        "not finish within 30 seconds. Retry the request after the "
                        "memory service recovers."
                    ),
                )
                self.agent.set_data(DATA_NAME_TASK_MEMORIES, None)
                raise HandledException(
                    "Required memory recall timed out; agent response blocked."
                ) from error
