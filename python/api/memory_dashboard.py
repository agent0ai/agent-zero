from python.helpers.api import ApiHandler, Request, Response
from python.helpers.memory import Memory, get_existing_memory_subdirs, get_context_memory_subdir
from python.helpers import files
from langchain_core.documents import Document
from agent import AgentContext


class MemoryDashboard(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = input.get("action", "search")
            if action == "get_memory_subdirs":
                return await self._get_memory_subdirs()
            elif action == "get_current_memory_subdir":
                return await self._get_current_memory_subdir(input)
            elif action == "search":
                return await self._search_memories(input)
            elif action == "delete":
                return await self._delete_memory(input)
            elif action == "bulk_delete":
                return await self._bulk_delete_memories(input)
            elif action == "update":
                return await self._update_memory(input)
            elif action == "cognify_status":
                return await self._get_cognify_status()
            elif action == "knowledge_graph":
                return await self._get_knowledge_graph()
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "memories": [],
                    "total_count": 0,
                }
        except Exception as e:
            return {"success": False, "error": str(e), "memories": [], "total_count": 0}

    async def _delete_memory(self, input: dict) -> dict:
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_id = input.get("memory_id")

            if not memory_id:
                return {"success": False, "error": "Memory ID is required for deletion"}

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
            rem = await memory.delete_documents_by_ids([memory_id])

            if len(rem) == 0:
                return {
                    "success": False,
                    "error": f"Memory with ID '{memory_id}' not found",
                }
            else:
                return {
                    "success": True,
                    "message": f"Memory {memory_id} deleted successfully",
                }
        except Exception as e:
            return {"success": False, "error": f"Failed to delete memory: {str(e)}"}

    async def _bulk_delete_memories(self, input: dict) -> dict:
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_ids = input.get("memory_ids", [])

            if not memory_ids:
                return {
                    "success": False,
                    "error": "No memory IDs provided for bulk deletion",
                }

            if not isinstance(memory_ids, list):
                return {
                    "success": False,
                    "error": "Memory IDs must be provided as a list",
                }

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
            rem = await memory.delete_documents_by_ids(memory_ids)

            if len(rem) == len(memory_ids):
                return {
                    "success": True,
                    "message": f"Successfully deleted {len(memory_ids)} memories",
                }
            elif len(rem) > 0:
                return {
                    "success": True,
                    "message": f"Successfully deleted {len(rem)} memories. {len(memory_ids) - len(rem)} failed.",
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete any memories.",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to bulk delete memories: {str(e)}",
            }

    async def _get_current_memory_subdir(self, input: dict) -> dict:
        try:
            context_id = input.get("context_id", None)
            if not context_id:
                return {"success": True, "memory_subdir": "default"}

            context = AgentContext.use(context_id)
            if not context:
                return {"success": True, "memory_subdir": "default"}

            memory_subdir = get_context_memory_subdir(context)
            return {"success": True, "memory_subdir": memory_subdir or "default"}
        except Exception:
            return {"success": True, "memory_subdir": "default"}

    async def _get_memory_subdirs(self) -> dict:
        try:
            subdirs = get_existing_memory_subdirs()
            return {"success": True, "subdirs": subdirs}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get memory subdirectories: {str(e)}",
                "subdirs": ["default"],
            }

    async def _search_memories(self, input: dict) -> dict:
        try:
            memory_subdir = input.get("memory_subdir", "default")
            area_filter = input.get("area", "")
            search_query = input.get("search", "")
            limit = input.get("limit", 100)
            threshold = input.get("threshold", 0.6)

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

            memories = []

            if search_query:
                docs = await memory.search_similarity_threshold(
                    query=search_query,
                    limit=limit,
                    threshold=threshold,
                    filter=f"area == '{area_filter}'" if area_filter else "",
                )
                memories = docs
            else:
                try:
                    import cognee
                    datasets_to_check = []
                    if area_filter:
                        datasets_to_check.append(memory._area_dataset(area_filter))
                    else:
                        for area in Memory.Area:
                            datasets_to_check.append(memory._area_dataset(area.value))

                    all_datasets = await cognee.datasets.list_datasets()
                    for ds in all_datasets:
                        if ds.name in datasets_to_check:
                            data_items = await cognee.datasets.list_data(ds.id)
                            for item in data_items:
                                content = self._read_data_item_content(item)
                                from python.helpers.memory import _extract_metadata_from_text
                                text, meta = _extract_metadata_from_text(content)
                                if not meta.get("id"):
                                    from python.helpers import guids
                                    meta["id"] = guids.generate_id(10)
                                if not meta.get("area"):
                                    meta["area"] = Memory.Area.MAIN.value
                                memories.append(Document(page_content=text, metadata=meta))
                except Exception:
                    pass

                def get_sort_key(m):
                    return m.metadata.get("timestamp", "0000-00-00 00:00:00")

                memories.sort(key=get_sort_key, reverse=True)

                if limit and len(memories) > limit:
                    memories = memories[:limit]

            formatted_memories = [self._format_memory_for_dashboard(m) for m in memories]

            total_memories = len(formatted_memories)
            knowledge_count = sum(
                1 for m in formatted_memories if m["knowledge_source"]
            )
            conversation_count = total_memories - knowledge_count

            return {
                "success": True,
                "memories": formatted_memories,
                "total_count": total_memories,
                "total_db_count": total_memories,
                "knowledge_count": knowledge_count,
                "conversation_count": conversation_count,
                "search_query": search_query,
                "area_filter": area_filter,
                "memory_subdir": memory_subdir,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "memories": [], "total_count": 0}

    @staticmethod
    def _read_data_item_content(item) -> str:
        raw_location = getattr(item, "raw_data_location", None)
        if raw_location:
            import os
            from urllib.parse import urlparse, unquote
            path = raw_location
            if path.startswith("file://"):
                path = unquote(urlparse(path).path)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
        return str(getattr(item, "name", ""))

    def _format_memory_for_dashboard(self, m: Document) -> dict:
        metadata = m.metadata
        return {
            "id": metadata.get("id", "unknown"),
            "area": metadata.get("area", "unknown"),
            "timestamp": metadata.get("timestamp", "unknown"),
            "content_full": m.page_content,
            "knowledge_source": metadata.get("knowledge_source", False),
            "source_file": metadata.get("source_file", ""),
            "file_type": metadata.get("file_type", ""),
            "consolidation_action": metadata.get("consolidation_action", ""),
            "tags": metadata.get("tags", []),
            "metadata": metadata,
        }

    async def _update_memory(self, input: dict) -> dict:
        try:
            memory_subdir = input.get("memory_subdir")
            original = input.get("original")
            edited = input.get("edited")

            if not memory_subdir or not original or not edited:
                return {"success": False, "error": "Missing required parameters"}

            doc = Document(
                page_content=edited["content_full"],
                metadata=edited["metadata"],
            )

            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)
            result = await memory.update_documents([doc])
            if result:
                formatted_doc = self._format_memory_for_dashboard(doc)
                return {"success": True, "memory": formatted_doc}
            return {"success": False, "error": "Update failed", "memory": None}
        except Exception as e:
            return {"success": False, "error": str(e), "memory": None}

    async def _get_cognify_status(self) -> dict:
        try:
            from python.helpers.cognee_background import CogneeBackgroundWorker
            status = CogneeBackgroundWorker.get_instance().get_status()
            return {"success": True, **status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_knowledge_graph(self) -> dict:
        try:
            import cognee
            html = await cognee.visualize_graph()
            return {"success": True, "html": html}
        except Exception as e:
            return {"success": False, "error": str(e)}
