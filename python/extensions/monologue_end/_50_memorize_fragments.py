import asyncio
from python.helpers import settings, errors
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from python.helpers.dirty_json import DirtyJson
from agent import LoopData
from python.helpers.log import LogItem
from python.tools.memory_load import DEFAULT_THRESHOLD as DEFAULT_MEMORY_THRESHOLD
from python.helpers.defer import DeferredTask, THREAD_BACKGROUND


class MemorizeMemories(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        set = settings.get_settings()

        if not set["memory_memorize_enabled"]:
            return

        log_item = self.agent.context.log.log(
            type="util",
            heading="Memorizing new information...",
        )

        task = DeferredTask(thread_name=THREAD_BACKGROUND)
        task.start_task(self.memorize, loop_data, log_item)
        return task

    async def memorize(self, loop_data: LoopData, log_item: LogItem, **kwargs):
        try:
            set = settings.get_settings()
            db = await Memory.get(self.agent)

            system = self.agent.read_prompt("memory.memories_sum.sys.md")
            msgs_text = self.agent.concat_messages(self.agent.history)

            memories_json = await self.agent.call_utility_model(
                system=system,
                message=msgs_text,
                background=True,
            )

            log_item.update(content=memories_json)

            if not memories_json or not isinstance(memories_json, str):
                log_item.update(heading="No response from utility model.")
                return

            memories_json = memories_json.strip()

            if not memories_json:
                log_item.update(heading="Empty response from utility model.")
                return

            try:
                memories = DirtyJson.parse_string(memories_json)
            except Exception as e:
                log_item.update(heading=f"Failed to parse memories response: {str(e)}")
                return

            if memories is None:
                log_item.update(heading="No valid memories found in response.")
                return

            if not isinstance(memories, list):
                if isinstance(memories, (str, dict)):
                    memories = [memories]
                else:
                    log_item.update(heading="Invalid memories format received.")
                    return

            if not isinstance(memories, list) or len(memories) == 0:
                log_item.update(heading="No useful information to memorize.")
                return
            else:
                memories_txt = "\n\n".join([str(memory) for memory in memories]).strip()
                log_item.update(heading=f"{len(memories)} entries to memorize.", memories=memories_txt)

            rem = []

            for memory in memories:
                txt = f"{memory}"

                if set["memory_memorize_replace_threshold"] > 0:
                    rem += await db.delete_documents_by_query(
                        query=txt,
                        threshold=set["memory_memorize_replace_threshold"],
                        filter=f"area=='{Memory.Area.FRAGMENTS.value}'",
                    )
                    if rem:
                        rem_txt = "\n\n".join(Memory.format_docs_plain(rem))
                        log_item.update(replaced=rem_txt)

                await db.insert_text(text=txt, metadata={"area": Memory.Area.FRAGMENTS.value})

            log_item.update(
                result=f"{len(memories)} entries memorized.",
                heading=f"{len(memories)} entries memorized.",
            )
            if rem:
                log_item.stream(result=f"\nReplaced {len(rem)} previous memories.")

        except Exception as e:
            err = errors.format_error(e)
            self.agent.context.log.log(
                type="warning", heading="Memorize memories extension error", content=err
            )
