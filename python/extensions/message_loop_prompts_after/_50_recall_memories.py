import asyncio
from python.helpers.extension import Extension
from python.helpers.memory import Memory
from agent import LoopData
from python.helpers import dirty_json, errors, settings, log
from python.helpers.cognee_init import get_cognee_setting
from python.helpers.print_style import PrintStyle

DATA_NAME_TASK = "_recall_memories_task"
DATA_NAME_ITER = "_recall_memories_iter"
SEARCH_TIMEOUT = 30

_SLOW_SEARCH_NAMES = frozenset({
    "GRAPH_COMPLETION",
    "RAG_COMPLETION",
    "TRIPLET_COMPLETION",
    "GRAPH_SUMMARY_COMPLETION",
    "GRAPH_COMPLETION_COT",
    "GRAPH_COMPLETION_CONTEXT_EXTENSION",
    "NATURAL_LANGUAGE",
    "TEMPORAL",
    "FEELING_LUCKY",
})


class RecallMemories(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        set = settings.get_settings()

        if not set["memory_recall_enabled"]:
            return

        if loop_data.iteration % set["memory_recall_interval"] == 0:
            log_item = self.agent.context.log.log(
                type="util",
                heading="Searching memories...",
            )

            task = asyncio.create_task(
                asyncio.wait_for(
                    self.search_memories(loop_data=loop_data, log_item=log_item, **kwargs),
                    timeout=SEARCH_TIMEOUT,
                )
            )
        else:
            task = None

        self.agent.set_data(DATA_NAME_TASK, task)
        self.agent.set_data(DATA_NAME_ITER, loop_data.iteration)

    async def search_memories(self, log_item: log.LogItem, loop_data: LoopData, **kwargs):
        extras = loop_data.extras_persistent
        if "memories" in extras:
            del extras["memories"]
        if "solutions" in extras:
            del extras["solutions"]

        set = settings.get_settings()

        user_instruction = (
            loop_data.user_message.output_text() if loop_data.user_message else "None"
        )
        history = self.agent.history.output_text()[-set["memory_recall_history_len"]:]

        if set["memory_recall_query_prep"]:
            system = self.agent.read_prompt("memory.memories_query.sys.md")
            message = self.agent.read_prompt(
                "memory.memories_query.msg.md", history=history, message=user_instruction
            )
            try:
                query = await self.agent.call_utility_model(
                    system=system,
                    message=message,
                )
                query = query.strip()
                log_item.update(query=query)
            except Exception as e:
                err = errors.format_error(e)
                self.agent.context.log.log(
                    type="warning", heading="Recall memories extension error:", content=err
                )
                query = ""

            if not query:
                log_item.update(heading="Failed to generate memory query")
                return
        else:
            query = user_instruction + "\n\n" + history

        if not query or len(query) <= 3:
            log_item.update(
                query="No relevant memory query generated, skipping search",
            )
            return

        db = await Memory.get(self.agent)
        session_id = f"context_{id(self.agent.context)}"

        from python.helpers.memory import _get_cognee
        cognee, SearchType = _get_cognee()

        fast_types, slow_types = _resolve_search_types(SearchType)

        mem_datasets = [
            db._area_dataset(Memory.Area.MAIN.value),
            db._area_dataset(Memory.Area.FRAGMENTS.value),
        ]
        sol_datasets = [db._area_dataset(Memory.Area.SOLUTIONS.value)]
        mem_node_name = [Memory.Area.MAIN.value, Memory.Area.FRAGMENTS.value]
        sol_node_name = [Memory.Area.SOLUTIONS.value]

        # --- Phase 1: fast search (CHUNKS, CHUNKS_LEXICAL, etc.) ---
        memory_results, solution_results = await asyncio.gather(
            _multi_cognee_search(
                cognee, search_types=fast_types,
                query=query,
                top_k=set["memory_recall_memories_max_search"],
                datasets=mem_datasets,
                node_name=mem_node_name,
                session_id=session_id,
            ),
            _multi_cognee_search(
                cognee, search_types=fast_types,
                query=query,
                top_k=set["memory_recall_solutions_max_search"],
                datasets=sol_datasets,
                node_name=sol_node_name,
                session_id=session_id,
            ),
        )

        if memory_results is None:
            memory_results = await db.search_similarity_threshold(
                query=query,
                limit=set["memory_recall_memories_max_search"],
                threshold=set["memory_recall_similarity_threshold"],
                filter=f"area == '{Memory.Area.MAIN.value}' or area == '{Memory.Area.FRAGMENTS.value}'",
            )
        if solution_results is None:
            solution_results = await db.search_similarity_threshold(
                query=query,
                limit=set["memory_recall_solutions_max_search"],
                threshold=set["memory_recall_similarity_threshold"],
                filter=f"area == '{Memory.Area.SOLUTIONS.value}'",
            )

        memories = _extract_texts(memory_results, set["memory_recall_memories_max_result"])
        solutions = _extract_texts(solution_results, set["memory_recall_solutions_max_result"])

        if set["memory_recall_post_filter"] and (memories or solutions):
            memories, solutions = await self._post_filter(
                cognee, memories, solutions, history, user_instruction, session_id,
            )

        _write_extras(self.agent, extras, memories, solutions, log_item)

        # --- Phase 2: slow search in background (GRAPH_COMPLETION, etc.) ---
        if slow_types:
            asyncio.create_task(
                _slow_search_and_merge(
                    agent=self.agent,
                    cognee=cognee,
                    slow_types=slow_types,
                    query=query,
                    recall_settings=set,
                    mem_datasets=mem_datasets,
                    sol_datasets=sol_datasets,
                    mem_node_name=mem_node_name,
                    sol_node_name=sol_node_name,
                    session_id=session_id,
                    extras=extras,
                    log_item=log_item,
                    existing_memories=memories,
                    existing_solutions=solutions,
                )
            )

    async def _post_filter(self, cognee, memories, solutions, history, user_instruction, session_id):
        all_items = memories + solutions
        mems_list = {i: text for i, text in enumerate(all_items)}

        try:
            filter_response = await self.agent.call_utility_model(
                system=self.agent.read_prompt("memory.memories_filter.sys.md"),
                message=self.agent.read_prompt(
                    "memory.memories_filter.msg.md",
                    memories=mems_list,
                    history=history,
                    message=user_instruction,
                ),
            )
            filter_inds = dirty_json.try_parse(filter_response)

            if isinstance(filter_inds, list):
                filtered_memories = []
                filtered_solutions = []
                mem_len = len(memories)
                for idx in filter_inds:
                    if isinstance(idx, int):
                        if idx < mem_len:
                            filtered_memories.append(memories[idx])
                        else:
                            sol_idx = idx - mem_len
                            if sol_idx < len(solutions):
                                filtered_solutions.append(solutions[sol_idx])
                memories = filtered_memories
                solutions = filtered_solutions

                feedback_enabled = get_cognee_setting("cognee_feedback_enabled", True)
                if feedback_enabled:
                    try:
                        entries = await cognee.session.get_session(
                            session_id=session_id, last_n=1
                        )
                        if entries:
                            qa_id = entries[-1].qa_id
                            score = 5 if (memories or solutions) else 2
                            await cognee.session.add_feedback(
                                session_id=session_id,
                                qa_id=qa_id,
                                feedback_score=score,
                            )
                    except Exception as fb_err:
                        PrintStyle.error(f"Cognee feedback failed: {fb_err}")

        except Exception as e:
            err = errors.format_error(e)
            self.agent.context.log.log(
                type="warning", heading="Failed to filter relevant memories", content=err
            )

        return memories, solutions


def _write_extras(agent, extras, memories, solutions, log_item):
    if not memories and not solutions:
        log_item.update(heading="No memories or solutions found")
        return

    log_item.update(
        heading=f"{len(memories)} memories and {len(solutions)} relevant solutions found",
    )

    memories_txt = "\n\n".join(memories) if memories else ""
    solutions_txt = "\n\n".join(solutions) if solutions else ""

    if memories_txt:
        log_item.update(memories=memories_txt)
    if solutions_txt:
        log_item.update(solutions=solutions_txt)

    if memories_txt:
        extras["memories"] = agent.parse_prompt(
            "agent.system.memories.md", memories=memories_txt
        )
    if solutions_txt:
        extras["solutions"] = agent.parse_prompt(
            "agent.system.solutions.md", solutions=solutions_txt
        )


async def _slow_search_and_merge(
    *, agent, cognee, slow_types, query, recall_settings,
    mem_datasets, sol_datasets, mem_node_name, sol_node_name,
    session_id, extras, log_item, existing_memories, existing_solutions,
):
    try:
        slow_mem, slow_sol = await asyncio.gather(
            _multi_cognee_search(
                cognee, search_types=slow_types,
                query=query,
                top_k=recall_settings["memory_recall_memories_max_search"],
                datasets=mem_datasets,
                node_name=mem_node_name,
                session_id=session_id,
            ),
            _multi_cognee_search(
                cognee, search_types=slow_types,
                query=query,
                top_k=recall_settings["memory_recall_solutions_max_search"],
                datasets=sol_datasets,
                node_name=sol_node_name,
                session_id=session_id,
            ),
        )

        new_memories = _extract_texts(
            slow_mem, recall_settings["memory_recall_memories_max_result"]
        )
        new_solutions = _extract_texts(
            slow_sol, recall_settings["memory_recall_solutions_max_result"]
        )

        existing_mem_keys = frozenset(existing_memories) if existing_memories else frozenset()
        existing_sol_keys = frozenset(existing_solutions) if existing_solutions else frozenset()
        merged_memories = list(existing_memories) + [
            m for m in new_memories if m not in existing_mem_keys
        ]
        merged_solutions = list(existing_solutions) + [
            s for s in new_solutions if s not in existing_sol_keys
        ]

        if merged_memories != existing_memories or merged_solutions != existing_solutions:
            _write_extras(agent, extras, merged_memories, merged_solutions, log_item)

    except Exception as e:
        PrintStyle.error(f"Background memory search failed: {e}")


def _extract_texts(results, limit: int) -> list[str]:
    texts = []
    if not results:
        return texts

    for result in results:
        if len(texts) >= limit:
            break

        raw = result
        if hasattr(result, "search_result"):
            raw = result.search_result

        if isinstance(raw, str):
            text = raw
            if text.startswith("[META:"):
                try:
                    meta_end = text.index("]\n")
                    text = text[meta_end + 2:]
                except ValueError:
                    pass
            texts.append(text)
        elif hasattr(raw, "page_content"):
            texts.append(raw.page_content)
        elif hasattr(raw, "text"):
            texts.append(str(raw.text))
        elif isinstance(raw, dict):
            texts.append(raw.get("text", raw.get("content", str(raw))))
        else:
            texts.append(str(raw))

    return texts


def _resolve_search_types(SearchType):
    """Returns (fast_types, slow_types) tuple."""
    multi_enabled = get_cognee_setting("cognee_multi_search_enabled", True)
    if multi_enabled:
        type_names = get_cognee_setting("cognee_search_types", "GRAPH_COMPLETION,CHUNKS_LEXICAL")
        all_types = []
        for name in type_names.split(","):
            name = name.strip()
            if hasattr(SearchType, name):
                all_types.append(getattr(SearchType, name))
        if not all_types:
            all_types = [SearchType.CHUNKS]
    else:
        name = get_cognee_setting("cognee_search_type", "GRAPH_COMPLETION")
        try:
            all_types = [getattr(SearchType, name)]
        except AttributeError:
            all_types = [SearchType.CHUNKS]

    fast = [t for t in all_types if t.name not in _SLOW_SEARCH_NAMES]
    slow = [t for t in all_types if t.name in _SLOW_SEARCH_NAMES]

    if not fast:
        fast = [SearchType.CHUNKS]

    return fast, slow


async def _multi_cognee_search(
    cognee, *, search_types, query, top_k, datasets, node_name, session_id
):
    all_results = []
    for st in search_types:
        try:
            results = await cognee.search(
                query_text=query,
                query_type=st,
                top_k=top_k,
                datasets=datasets,
                node_name=node_name,
                session_id=session_id,
            )
            if results:
                all_results.extend(results)
        except Exception as e:
            PrintStyle.error(f"Cognee search ({st.name}) failed: {e}")

    if all_results:
        seen = {}
        unique = []
        for r in all_results:
            raw = r.search_result if hasattr(r, "search_result") else r
            key = str(raw)[:200]
            if key not in seen:
                seen[key] = True
                unique.append(r)
        return unique
    return None
