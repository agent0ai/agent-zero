import asyncio
import time
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from agent import LoopData
from python.helpers import dirty_json, errors, settings, log


DATA_NAME_TASK = "_recall_memories_task"
DATA_NAME_ITER = "_recall_memories_iter"


class RecallMemories(Extension):
    """Periodic memory recall extension with optional query preparation and post-filtering.

    - Every N iterations, generate a memory query (optionally with a utility LLM),
      search memory DB for memories and solutions, optionally post-filter via LLM,
      and expose results in `loop_data.extras_persistent`.
    - Logs timing metrics (ms): query_ms, db_ms, post_filter_ms, total_ms.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        cfg = settings.get_settings()

        # Disabled in settings?
        if not cfg["memory_recall_enabled"]:
            return

        # Run every cfg["memory_recall_interval"] iterations
        if loop_data.iteration % cfg["memory_recall_interval"] == 0:
            # Show util message immediately
            log_item = self.agent.context.log.log(
                type="util",
                heading="Searching memories...",
            )
            task = asyncio.create_task(
                self.search_memories(loop_data=loop_data, log_item=log_item, **kwargs)
            )
        else:
            task = None

        # Save task for external waiting
        self.agent.set_data(DATA_NAME_TASK, task)
        self.agent.set_data(DATA_NAME_ITER, loop_data.iteration)

    async def search_memories(self, log_item: log.LogItem, loop_data: LoopData, **kwargs):
        t_start = time.time()
        query_ms = 0.0
        db_ms = 0.0
        filter_ms = 0.0

        # Cleanup previous extras
        extras = loop_data.extras_persistent
        extras.pop("memories", None)
        extras.pop("solutions", None)

        cfg = settings.get_settings()

        # System message and history for utility LLM
        system = self.agent.read_prompt("memory.memories_query.sys.md")

        # Stream utility LLM output into the log
        async def log_callback(content):
            log_item.stream(query=content)

        # Prepare conversation context
        user_instruction = (
            loop_data.user_message.output_text() if loop_data.user_message else "None"
        )
        history = self.agent.history.output_text()[-cfg["memory_recall_history_len"]:]
        message = self.agent.read_prompt(
            "memory.memories_query.msg.md", history=history, message=user_instruction
        )

        # Optionally let utility LLM prepare the search query
        if cfg["memory_recall_query_prep"]:
            try:
                t0 = time.time()
                query = await self.agent.call_utility_model(
                    system=system,
                    message=message,
                    callback=log_callback,
                )
                query = query.strip()
                query_ms = (time.time() - t0) * 1000
            except Exception as e:
                err = errors.format_error(e)
                self.agent.context.log.log(
                    type="error", heading="Recall memories extension error:", content=err
                )
                query = ""

            if not query:
                log_item.update(heading="Failed to generate memory query")
                return
        else:
            # Use the message and history directly as query
            query = user_instruction + "\n\n" + history

        # If we have no meaningful query, skip search
        if not query or len(query) <= 3:
            log_item.update(query="No relevant memory query generated, skipping search")
            return

        # Query the memory database
        db = await Memory.get(self.agent)

        # Search memories (MAIN, FRAGMENTS)
        t1 = time.time()
        memories = await db.search_similarity_threshold(
            query=query,
            limit=cfg["memory_recall_memories_max_search"],
            threshold=cfg["memory_recall_similarity_threshold"],
            filter=f"area == '{Memory.Area.MAIN.value}' or area == '{Memory.Area.FRAGMENTS.value}'",
        )

        # Search solutions
        solutions = await db.search_similarity_threshold(
            query=query,
            limit=cfg["memory_recall_solutions_max_search"],
            threshold=cfg["memory_recall_similarity_threshold"],
            filter=f"area == '{Memory.Area.SOLUTIONS.value}'",
        )
        db_ms = (time.time() - t1) * 1000

        if not memories and not solutions:
            log_item.update(heading="No memories or solutions found")
            return

        # Optional post-filtering via utility LLM
        if cfg["memory_recall_post_filter"]:
            mems_list = {i: m.page_content for i, m in enumerate(memories + solutions)}
            try:
                t2 = time.time()
                filter_resp = await self.agent.call_utility_model(
                    system=self.agent.read_prompt("memory.memories_filter.sys.md"),
                    message=self.agent.read_prompt(
                        "memory.memories_filter.msg.md",
                        memories=mems_list,
                        history=history,
                        message=user_instruction,
                    ),
                )
                filter_inds = dirty_json.try_parse(filter_resp)
                filter_ms = (time.time() - t2) * 1000

                filtered_memories = []
                filtered_solutions = []
                mem_len = len(memories)

                if isinstance(filter_inds, list):
                    for idx in filter_inds:
                        if isinstance(idx, int):
                            if idx < mem_len:
                                filtered_memories.append(memories[idx])
                            else:
                                sol_idx = idx - mem_len
                                if 0 <= sol_idx < len(solutions):
                                    filtered_solutions.append(solutions[sol_idx])

                memories = filtered_memories
                solutions = filtered_solutions

            except Exception as e:
                err = errors.format_error(e)
                self.agent.context.log.log(
                    type="error", heading="Failed to filter relevant memories", content=err
                )

        # Limit final counts
        memories = memories[: cfg["memory_recall_memories_max_result"]]
        solutions = solutions[: cfg["memory_recall_solutions_max_result"]]

        # Log search result and timing metrics (ms)
        log_item.update(
            heading=f"{len(memories)} memories and {len(solutions)} relevant solutions found",
            query_ms=f"{query_ms:.0f}",
            db_ms=f"{db_ms:.0f}",
            post_filter_ms=f"{filter_ms:.0f}",
            total_ms=f"{(time.time() - t_start) * 1000:.0f}",
        )

        memories_txt = "\n\n".join([mem.page_content for mem in memories]) if memories else ""
        solutions_txt = "\n\n".join([sol.page_content for sol in solutions]) if solutions else ""

        # Log full results
        if memories_txt:
            log_item.update(memories=memories_txt)
        if solutions_txt:
            log_item.update(solutions=solutions_txt)

        # Expose prompts for agent system
        if memories_txt:
            extras["memories"] = self.agent.parse_prompt(
                "agent.system.memories.md", memories=memories_txt
            )
        if solutions_txt:
            extras["solutions"] = self.agent.parse_prompt(
                "agent.system.solutions.md", solutions=solutions_txt
            )
