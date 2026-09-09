import asyncio
from helpers.extension import Extension
from agent import LoopData
from plugins._memory.extensions.python.message_loop_prompts_after._50_recall_memories import (
    DATA_NAME_ITER as DATA_NAME_ITER_MEMORIES,
    DATA_NAME_RESULT as DATA_NAME_RESULT_MEMORIES,
    DATA_NAME_RESULT_SCOPE as DATA_NAME_RESULT_SCOPE_MEMORIES,
    DATA_NAME_TASK as DATA_NAME_TASK_MEMORIES,
    apply_recall_result,
    get_recall_scope,
)
from helpers import plugins

RECALL_WAIT_TIMEOUT_S = 20


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
                if iter == loop_data.iteration and not task.done():
                    # insert info about delayed memory to extras
                    delay_text = self.agent.read_prompt("memory.recall_delay_msg.md")
                    loop_data.extras_temporary["memory_recall_delayed"] = delay_text
                    return

            # otherwise await the task, bounded so a hung recall task
            # (e.g. slow embedding round-trip) can never stall prompt preparation
            try:
                result = await asyncio.wait_for(task, timeout=RECALL_WAIT_TIMEOUT_S)
            except (asyncio.TimeoutError, TimeoutError):
                # raised either by this ceiling or by the task's own inner
                # SEARCH_TIMEOUT wait_for (see _50_recall_memories.py)
                self.agent.hist_add_warning(
                    "Memory recall timed out, continuing without memories."
                )
                return
            if self.agent.get_data(DATA_NAME_RESULT_SCOPE_MEMORIES) == get_recall_scope(
                self.agent
            ):
                apply_recall_result(loop_data, result)
            else:
                apply_recall_result(loop_data, {})
            self.agent.set_data(DATA_NAME_RESULT_MEMORIES, None)
            self.agent.set_data(DATA_NAME_RESULT_SCOPE_MEMORIES, None)
