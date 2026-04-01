import asyncio
from helpers.extension import Extension
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

        if task and not task.done():

            # if memory recall is set to delayed mode, do not await on the iteration it was called
            if set["memory_recall_delayed"]:
                if iter == loop_data.iteration:
                    # insert info about delayed memory to extras
                    delay_text = self.agent.read_prompt("memory.recall_delay_msg.md")
                    loop_data.extras_temporary["memory_recall_delayed"] = delay_text
                    return

            # otherwise await the task with error handling
            try:
                await task
            except asyncio.TimeoutError:
                self.agent.context.log.log(
                    type="warning",
                    heading="Memory recall timed out",
                    content="The memory search took too long and was cancelled. Continuing without memory context.",
                )
            except asyncio.CancelledError:
                self.agent.context.log.log(
                    type="warning",
                    heading="Memory recall cancelled",
                    content="The memory search was cancelled. Continuing without memory context.",
                )
            except Exception as e:
                from helpers import errors
                self.agent.context.log.log(
                    type="warning",
                    heading="Memory recall error",
                    content=errors.format_error(e),
                )
