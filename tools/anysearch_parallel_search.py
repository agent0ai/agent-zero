import asyncio

from helpers.anysearch import (
    ANYSEARCH_MAX_RESULTS,
    AnySearchError,
    search_parallel,
)
from helpers.errors import handle_error
from helpers.tool import Response, Tool


class AnySearchParallelSearch(Tool):
    """Run several AnySearch queries concurrently.

    AnySearch exposes no batch endpoint, so parallel search issues one
    request per query from a thread pool and returns a mapping from query
    to results. A query that fails maps to an empty list, so one bad query
    never destroys the results of the others.

    Accepts a list of queries or a newline separated string, because the
    model will happily pass either.

    Works anonymously: with no API key configured requests are rate
    limited per IP but otherwise succeed.
    """

    async def execute(
        self,
        queries=None,
        max_results=ANYSEARCH_MAX_RESULTS,
        max_workers=4,
        tag="",
        zone="",
        language="",
        **kwargs,
    ):
        result = await asyncio.to_thread(
            self._parallel_search,
            queries,
            max_results,
            max_workers,
            tag,
            zone,
            language,
        )

        await self.agent.handle_intervention(
            result
        )  # wait for intervention and handle it, if paused

        if isinstance(result, Exception):
            handle_error(result)
            return Response(
                message=f"AnySearch parallel search failed: {str(result)}",
                break_loop=False,
            )

        return Response(message=self.format_result(result), break_loop=False)

    def _parallel_search(
        self, queries, max_results, max_workers, tag, zone, language
    ):
        try:
            normalized = self._normalize_queries(queries)
            if not normalized:
                raise ValueError("no query given")

            return search_parallel(
                queries=normalized,
                max_results=max_results,
                max_workers=max_workers,
                tag=tag,
                zone=zone,
                language=language,
            )
        except Exception as e:
            return e

    def _normalize_queries(self, queries):
        """Accept a list, a tuple, or a newline separated string."""
        if queries is None:
            return []
        if isinstance(queries, str):
            raw = queries.splitlines()
        elif isinstance(queries, (list, tuple, set)):
            raw = [str(item) for item in queries]
        else:
            raw = [str(queries)]

        seen = []
        for item in raw:
            entry = item.strip()
            if entry and entry not in seen:
                seen.append(entry)
        return seen

    def format_result(self, batches, source="AnySearch"):
        if isinstance(batches, Exception):
            return f"{source} parallel search failed: {str(batches)}"

        if not batches:
            return f"{source} parallel search returned no results."

        outputs = []
        for query, results in batches.items():
            outputs.append(f"Query: {query}")
            if not results:
                outputs.append("(no results)")
                continue
            for item in results:
                outputs.append(item["title"])
                outputs.append(item["url"])
                body = item["content"] or item["snippet"]
                if body:
                    outputs.append(body)
            outputs.append("")

        return "\n".join(outputs).strip()
