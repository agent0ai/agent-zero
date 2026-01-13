import asyncio
import urllib.parse

import aiohttp

from python.helpers.dotenv import get_dotenv_value
from python.helpers.tool import Tool, Response


S2_API_KEY = get_dotenv_value("S2_API_KEY") or ""


class SemanticScholar(Tool):
    """Search Semantic Scholar for academic papers."""

    async def execute(self, **kwargs) -> Response:
        """
        Search Semantic Scholar for papers matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results (default 10)
            fields: Comma-separated fields to return
        """
        query = kwargs.get("query", "")
        limit = kwargs.get("limit", 10)
        fields = kwargs.get("fields", "title,authors,year,abstract,citationCount")

        if not query:
            return Response(
                message="Error: no query provided",
                break_loop=False,
            )

        # Log the search operation
        self.agent.context.log.log(
            type="tool",
            heading="Semantic Scholar Search",
            content=f"Searching for: {query}",
            kvps={"query": query, "limit": limit},
        )

        try:
            results = await self._search(query, limit, fields)

            if not results:
                return Response(
                    message="No papers found matching the query.",
                    break_loop=False,
                )

            # Format results
            formatted = self._format_results(results)

            return Response(
                message=f"Found {len(results)} papers:\n\n{formatted}",
                break_loop=False,
            )

        except Exception as e:
            return Response(
                message=f"Semantic Scholar search failed: {str(e)}",
                break_loop=False,
            )

    async def _search(self, query: str, limit: int, fields: str) -> list[dict]:
        """Execute the search API call."""
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={limit}&fields={fields}"

        headers = {}
        if S2_API_KEY:
            headers["x-api-key"] = S2_API_KEY

        # Rate limiting
        await asyncio.sleep(1.0 if not S2_API_KEY else 0.1)

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 429:
                    # Rate limited, wait and retry
                    await asyncio.sleep(5)
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as retry_response:
                        retry_response.raise_for_status()
                        data = await retry_response.json()
                        return data.get("data", [])

                response.raise_for_status()
                data = await response.json()

        return data.get("data", [])

    def _format_results(self, results: list[dict]) -> str:
        """Format search results for display."""
        formatted = []
        for i, paper in enumerate(results, 1):
            title = paper.get("title", "Unknown")
            authors = paper.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors[:3])
            if len(authors) > 3:
                author_str += " et al."
            year = paper.get("year", "Unknown")
            citations = paper.get("citationCount", 0)
            abstract = paper.get("abstract", "")
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + "..."

            formatted.append(
                f"{i}. **{title}**\n"
                f"   Authors: {author_str}\n"
                f"   Year: {year} | Citations: {citations}\n"
                f"   Abstract: {abstract}\n"
            )

        return "\n".join(formatted)
