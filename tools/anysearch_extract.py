import asyncio

from helpers.anysearch import AnySearchError, extract
from helpers.errors import handle_error
from helpers.tool import Response, Tool

ANYSEARCH_EXTRACT_LIMIT = 8000


class AnySearchExtract(Tool):
    """Fetch a web page and return its parsed, readable content.

    Complements the search tool: search results already carry a parsed
    ``content`` field, and this tool parses an arbitrary URL on demand.
    """

    async def execute(self, url="", **kwargs):
        result = await asyncio.to_thread(self._extract, url)

        await self.agent.handle_intervention(
            result
        )  # wait for intervention and handle it, if paused

        if isinstance(result, Exception):
            handle_error(result)
            return Response(
                message=f"AnySearch extract failed: {str(result)}",
                break_loop=False,
            )

        return Response(message=self.format_result(result), break_loop=False)

    def _extract(self, url):
        try:
            return extract(url)
        except Exception as e:
            return e

    def format_result(self, page, source="AnySearch"):
        if isinstance(page, Exception):
            return f"{source} extract failed: {str(page)}"

        title = page.get("title", "")
        content = (page.get("content", "") or "").strip()
        if len(content) > ANYSEARCH_EXTRACT_LIMIT:
            content = content[:ANYSEARCH_EXTRACT_LIMIT] + "\n...(truncated)"

        head = f"{title}\n{page.get('url', '')}" if title else page.get(
            "url", ""
        )
        return f"{head}\n\n{content}".strip()
