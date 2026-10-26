import asyncio

from helpers.anysearch import (
    ANYSEARCH_MAX_RESULTS,
    AnySearchError,
    search,
)
from helpers.errors import handle_error
from helpers.tool import Response, Tool


class AnySearchSearch(Tool):
    """Web search through AnySearch, including vertical domain search.

    Works anonymously: with no API key configured the request is rate
    limited per IP but otherwise succeeds.
    """

    async def execute(
        self,
        query="",
        max_results=ANYSEARCH_MAX_RESULTS,
        tag="",
        zone="",
        language="",
        **kwargs,
    ):
        result = await asyncio.to_thread(
            self._search, query, max_results, tag, zone, language
        )

        await self.agent.handle_intervention(
            result
        )  # wait for intervention and handle it, if paused

        if isinstance(result, Exception):
            handle_error(result)
            return Response(
                message=f"AnySearch search failed: {str(result)}",
                break_loop=False,
            )

        return Response(message=self.format_result(result), break_loop=False)

    def _search(self, query, max_results, tag, zone, language):
        try:
            return search(
                query=query,
                max_results=max_results,
                tag=tag,
                zone=zone,
                language=language,
            )
        except Exception as e:
            return e

    def format_result(self, results, source="AnySearch"):
        if isinstance(results, Exception):
            return f"{source} search failed: {str(results)}"

        if not results:
            return f"{source} search returned no results."

        outputs = []
        for item in results:
            parts = [item["title"], item["url"]]
            body = item["content"] or item["snippet"]
            if body:
                parts.append(body)
            outputs.append("\n".join(parts))

        return "\n\n".join(outputs).strip()
