import os
import asyncio
from python.helpers import dotenv, memory, perplexity_search, duckduckgo_search
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error
from python.helpers.searxng import search as searxng
from python.helpers.citations_br import (
    format_brazil_citations_markdown,
    select_sources_official_first,
)

SEARCH_ENGINE_RESULTS = 10


class SearchEngine(Tool):
    async def execute(self, query="", **kwargs):


        searxng_result = await self.searxng_search(query)

        await self.agent.handle_intervention(
            searxng_result
        )  # wait for intervention and handle it, if paused

        return Response(message=searxng_result, break_loop=False)


    async def searxng_search(self, question):
        results = await searxng(question)
        return self.format_result_searxng(results, "Search Engine")

    def format_result_searxng(self, result, source):
        if isinstance(result, Exception):
            handle_error(result)
            return f"{source} search failed: {str(result)}"

        if not result or "results" not in result:
            return ""

        selected = select_sources_official_first(
            result.get("results", []), limit=SEARCH_ENGINE_RESULTS
        )
        return format_brazil_citations_markdown(
            selected, heading="Fontes (priorizando oficiais)"
        )
