from python.helpers.memory import Memory
from python.helpers import settings
from python.helpers.tool import Tool, Response
from python.helpers.strings import truncate_text as truncate_text_string

DEFAULT_THRESHOLD = 0.7
DEFAULT_LIMIT = 10


class MemoryLoad(Tool):

    async def execute(self, query="", threshold=DEFAULT_THRESHOLD, limit=DEFAULT_LIMIT, filter="", **kwargs):
        set = settings.get_settings()
        warnings: list[str] = []

        max_limit = int(set.get("memory_load_limit_max", 25))
        query_max_chars = int(set.get("memory_load_query_max_chars", 12000))
        response_max_chars = int(set.get("memory_load_response_max_chars", 24000))

        query = str(query or "")
        if query_max_chars > 0 and len(query) > query_max_chars:
            query = truncate_text_string(query, query_max_chars)
            warnings.append(
                f"Query truncated to {query_max_chars} chars by memory_load guardrail."
            )

        try:
            limit = int(limit)
        except Exception:
            limit = DEFAULT_LIMIT
        if limit < 1:
            limit = 1
        if max_limit > 0 and limit > max_limit:
            warnings.append(
                f"Limit reduced from {limit} to {max_limit} by memory_load guardrail."
            )
            limit = max_limit

        db = await Memory.get(self.agent)
        docs = await db.search_similarity_threshold(query=query, limit=limit, threshold=threshold, filter=filter)

        if len(docs) == 0:
            result = self.agent.read_prompt("fw.memories_not_found.md", query=query)
        else:
            text = "\n\n".join(Memory.format_docs_plain(docs))
            result = str(text)

        if response_max_chars > 0 and len(result) > response_max_chars:
            result = truncate_text_string(result, response_max_chars)
            warnings.append(
                f"Response truncated to {response_max_chars} chars by memory_load guardrail."
            )

        if warnings:
            result = result + "\n\n" + "\n".join(f"- {warning}" for warning in warnings)

        return Response(message=result, break_loop=False)
