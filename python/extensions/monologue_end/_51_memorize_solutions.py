import asyncio
from python.helpers import settings, errors
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from python.helpers.dirty_json import DirtyJson
from agent import LoopData
from python.helpers.log import LogItem
from python.tools.memory_load import DEFAULT_THRESHOLD as DEFAULT_MEMORY_THRESHOLD
from python.helpers.defer import DeferredTask, THREAD_BACKGROUND


class MemorizeSolutions(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        set = settings.get_settings()

        if not set["memory_memorize_enabled"]:
            return

        log_item = self.agent.context.log.log(
            type="util",
            heading="Memorizing succesful solutions...",
        )

        task = DeferredTask(thread_name=THREAD_BACKGROUND)
        task.start_task(self.memorize, loop_data, log_item)
        return task

    async def memorize(self, loop_data: LoopData, log_item: LogItem, **kwargs):
        try:
            set = settings.get_settings()
            db = await Memory.get(self.agent)

            system = self.agent.read_prompt("memory.solutions_sum.sys.md")
            msgs_text = self.agent.concat_messages(self.agent.history)

            solutions_json = await self.agent.call_utility_model(
                system=system,
                message=msgs_text,
                background=True,
            )

            log_item.update(content=solutions_json)

            if not solutions_json or not isinstance(solutions_json, str):
                log_item.update(heading="No response from utility model.")
                return

            solutions_json = solutions_json.strip()

            if not solutions_json:
                log_item.update(heading="Empty response from utility model.")
                return

            try:
                solutions = DirtyJson.parse_string(solutions_json)
            except Exception as e:
                log_item.update(heading=f"Failed to parse solutions response: {str(e)}")
                return

            if solutions is None:
                log_item.update(heading="No valid solutions found in response.")
                return

            if not isinstance(solutions, list):
                if isinstance(solutions, (str, dict)):
                    solutions = [solutions]
                else:
                    log_item.update(heading="Invalid solutions format received.")
                    return

            if not isinstance(solutions, list) or len(solutions) == 0:
                log_item.update(heading="No successful solutions to memorize.")
                return
            else:
                solutions_txt = "\n\n".join([str(solution) for solution in solutions]).strip()
                log_item.update(
                    heading=f"{len(solutions)} successful solutions to memorize.", solutions=solutions_txt
                )

            rem = []

            for solution in solutions:
                if isinstance(solution, dict):
                    problem = solution.get("problem", "Unknown problem")
                    solution_text = solution.get("solution", "Unknown solution")
                    txt = f"# Problem\n {problem}\n# Solution\n {solution_text}"
                else:
                    txt = f"# Solution\n {str(solution)}"

                if set["memory_memorize_replace_threshold"] > 0:
                    rem += await db.delete_documents_by_query(
                        query=txt,
                        threshold=set["memory_memorize_replace_threshold"],
                        filter=f"area=='{Memory.Area.SOLUTIONS.value}'",
                    )
                    if rem:
                        rem_txt = "\n\n".join(Memory.format_docs_plain(rem))
                        log_item.update(replaced=rem_txt)

                await db.insert_text(text=txt, metadata={"area": Memory.Area.SOLUTIONS.value})

            log_item.update(
                result=f"{len(solutions)} solutions memorized.",
                heading=f"{len(solutions)} solutions memorized.",
            )
            if rem:
                log_item.stream(result=f"\nReplaced {len(rem)} previous solutions.")

        except Exception as e:
            err = errors.format_error(e)
            self.agent.context.log.log(
                type="warning", heading="Memorize solutions extension error", content=err
            )
