from python.helpers.api import ApiHandler, Request, Response
from python.helpers.memory import Memory
from python.helpers import files
from models import ModelConfig, ModelType


class MemoryDashboard(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            action = input.get("action", "search")
            if action == "get_memory_subdirs":
                return await self._get_memory_subdirs()
            elif action == "get_current_memory_subdir":
                return await self._get_current_memory_subdir(request)
            elif action == "search":
                return await self._search_memories(input)
            elif action == "delete":
                return await self._delete_memory(input)
            elif action == "bulk_delete":
                return await self._bulk_delete_memories(input)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "memories": [],
                    "total_count": 0
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memories": [],
                "total_count": 0
            }

    async def _delete_memory(self, input: dict) -> dict:
        """Delete a memory by ID from the specified subdirectory."""
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_id = input.get("memory_id")

            if not memory_id:
                return {
                    "success": False,
                    "error": "Memory ID is required for deletion"
                }

            # Check if memory database exists
            if Memory.index.get(memory_subdir) is None:
                return {
                    "success": False,
                    "error": f"Memory database '{memory_subdir}' not initialized"
                }

            # Get the MyFaiss database directly
            myFaiss_db = Memory.index[memory_subdir]

            # Delete the memory by ID (replicate logic from Memory.delete_documents_by_ids)
            rem_docs = await myFaiss_db.aget_by_ids([memory_id])
            if rem_docs:
                rem_ids = [doc.metadata["id"] for doc in rem_docs]
                await myFaiss_db.adelete(ids=rem_ids)
                # Persist changes to disk
                Memory._save_db_file(myFaiss_db, memory_subdir)
            else:
                return {
                    "success": False,
                    "error": f"Memory with ID '{memory_id}' not found"
                }

            return {
                "success": True,
                "message": f"Memory {memory_id} deleted successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete memory: {str(e)}"
            }

    async def _bulk_delete_memories(self, input: dict) -> dict:
        """Delete multiple memories by IDs from the specified subdirectory."""
        try:
            memory_subdir = input.get("memory_subdir", "default")
            memory_ids = input.get("memory_ids", [])

            if not memory_ids:
                return {
                    "success": False,
                    "error": "No memory IDs provided for bulk deletion"
                }

            if not isinstance(memory_ids, list):
                return {
                    "success": False,
                    "error": "Memory IDs must be provided as a list"
                }

            # Check if memory database exists
            if Memory.index.get(memory_subdir) is None:
                return {
                    "success": False,
                    "error": f"Memory database '{memory_subdir}' not initialized"
                }

            # Get the MyFaiss database directly
            myFaiss_db = Memory.index[memory_subdir]

            # Delete memories in batch
            deleted_count = 0
            failed_ids = []

            for memory_id in memory_ids:
                try:
                    # Get memory to check if it exists
                    rem_docs = await myFaiss_db.aget_by_ids([memory_id])
                    if rem_docs:
                        rem_ids = [doc.metadata["id"] for doc in rem_docs]
                        await myFaiss_db.adelete(ids=rem_ids)
                        deleted_count += 1
                    else:
                        failed_ids.append(memory_id)
                except Exception:
                    failed_ids.append(memory_id)

            # Persist changes to disk if any deletions were successful
            if deleted_count > 0:
                Memory._save_db_file(myFaiss_db, memory_subdir)

            if deleted_count == len(memory_ids):
                return {
                    "success": True,
                    "message": f"Successfully deleted {deleted_count} memories"
                }
            elif deleted_count > 0:
                return {
                    "success": True,
                    "message": f"Successfully deleted {deleted_count} memories. {len(failed_ids)} failed: {failed_ids[:5]}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to delete any memories. Not found: {failed_ids[:10]}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to bulk delete memories: {str(e)}"
            }

    async def _get_current_memory_subdir(self, request: Request) -> dict:
        """Get the current memory subdirectory from the active context."""
        try:
            # Try to get the context from the request
            context_id = getattr(request, 'context_id', None)
            if not context_id:
                # Fallback to default if no context available
                return {
                    "success": True,
                    "memory_subdir": "default"
                }

            # Import AgentContext here to avoid circular imports
            from agent import AgentContext

            # Get the context and extract memory subdirectory
            context = AgentContext.get(context_id)
            if context and hasattr(context, 'config') and hasattr(context.config, 'memory_subdir'):
                memory_subdir = context.config.memory_subdir or "default"
                return {
                    "success": True,
                    "memory_subdir": memory_subdir
                }
            else:
                return {
                    "success": True,
                    "memory_subdir": "default"
                }

        except Exception:
            return {
                "success": True,  # Still success, just fallback to default
                "memory_subdir": "default"
            }

    async def _get_memory_subdirs(self) -> dict:
        """Get available memory subdirectories."""
        try:
            # Get subdirectories from memory folder
            subdirs = files.get_subdirectories("memory")

            # Ensure 'default' is always available
            if "default" not in subdirs:
                subdirs.insert(0, "default")

            return {
                "success": True,
                "subdirs": subdirs
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get memory subdirectories: {str(e)}",
                "subdirs": ["default"]
            }

    async def _search_memories(self, input: dict) -> dict:
        """Search memories in the specified subdirectory."""
        try:
            # Get search parameters
            memory_subdir = input.get("memory_subdir", "default")
            area_filter = input.get("area", "")  # Filter by memory area
            search_query = input.get("search", "")  # Full-text search query
            limit = input.get("limit", 100)  # Number of results to return

            # Initialize memory if not already done
            if Memory.index.get(memory_subdir) is None:
                # Create default embeddings model config
                embeddings_config = ModelConfig(
                    type=ModelType.EMBEDDING,
                    provider="huggingface",
                    name="sentence-transformers/all-MiniLM-L6-v2",
                    ctx_length=512,
                    limit_requests=0,
                    limit_input=0,
                    limit_output=0,
                    vision=False,
                    kwargs={}
                )

                # Initialize memory database (with log_item=None to prevent status blinking)
                db, created = Memory.initialize(
                    log_item=None,
                    model_config=embeddings_config,
                    memory_subdir=memory_subdir,
                    in_memory=False
                )

                # Store in the Memory index
                Memory.index[memory_subdir] = db

            # Get the MyFaiss database directly
            myFaiss_db = Memory.index[memory_subdir]

            memories = []

            if search_query:
                # If search query provided, use similarity search
                threshold = 0.6  # Lower threshold for broader search in dashboard
                comparator = Memory._get_comparator(f"area == '{area_filter}'") if area_filter else None

                # Get ALL matching results, don't limit in query
                docs = await myFaiss_db.asearch(
                    search_query,
                    search_type="similarity_score_threshold",
                    k=10000,  # Get all matches up to reasonable max
                    score_threshold=threshold,
                    filter=comparator,
                )
                memories = docs
            else:
                # If no search query, get all memories from specified area(s)
                all_docs = myFaiss_db.get_all_docs()

                for doc_id, doc in all_docs.items():
                    # Apply area filter if specified
                    if area_filter and doc.metadata.get("area", "") != area_filter:
                        continue

                    memories.append(doc)

            # Format memories for the dashboard
            formatted_memories: list[dict] = []
            for memory in memories:
                metadata = memory.metadata

                # Extract key information
                memory_data = {
                    "id": metadata.get("id", "unknown"),
                    "area": metadata.get("area", "unknown"),
                    "timestamp": metadata.get("timestamp", "unknown"),
                    "content_preview": memory.page_content[:200] + ("..." if len(memory.page_content) > 200 else ""),
                    "content_full": memory.page_content,
                    "knowledge_source": metadata.get("knowledge_source", False),
                    "source_file": metadata.get("source_file", ""),
                    "file_type": metadata.get("file_type", ""),
                    "consolidation_action": metadata.get("consolidation_action", ""),
                    "tags": metadata.get("tags", []),
                    "metadata": metadata  # Include full metadata for advanced users
                }

                formatted_memories.append(memory_data)

            # Sort ALL results by timestamp (newest first) - handle "unknown" timestamps
            def get_sort_key(memory):
                timestamp = memory["timestamp"]
                if timestamp == "unknown" or not timestamp:
                    return "0000-00-00 00:00:00"  # Put unknown timestamps at the end
                return timestamp

            formatted_memories.sort(key=get_sort_key, reverse=True)

            # Apply limit AFTER sorting to get the newest entries
            if limit and len(formatted_memories) > limit:
                formatted_memories = formatted_memories[:limit]

            # Get summary statistics
            total_memories = len(formatted_memories)
            knowledge_count = sum(1 for m in formatted_memories if m["knowledge_source"])
            conversation_count = total_memories - knowledge_count

            # Get total count of all memories in database (unfiltered)
            all_docs = myFaiss_db.get_all_docs()
            total_db_count = len(all_docs)

            areas_count: dict[str, int] = {}
            for memory_dict in formatted_memories:
                area = memory_dict["area"]
                areas_count[area] = areas_count.get(area, 0) + 1

            return {
                "success": True,
                "memories": formatted_memories,
                "total_count": total_memories,
                "total_db_count": total_db_count,
                "knowledge_count": knowledge_count,
                "conversation_count": conversation_count,
                "areas_count": areas_count,
                "search_query": search_query,
                "area_filter": area_filter,
                "memory_subdir": memory_subdir
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memories": [],
                "total_count": 0
            }
