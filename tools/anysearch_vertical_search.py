import asyncio

from helpers.anysearch import (
    ANYSEARCH_MAX_RESULTS,
    AnySearchError,
    search,
)
from helpers.errors import handle_error
from helpers.tool import Response, Tool


class AnySearchVerticalSearch(Tool):
    """Search a single vertical domain through AnySearch.

    Vertical domains are addressed with a ``tag`` such as ``code.doc`` or
    ``finance.news``. Some tags require extra ``params``, for example
    ``{"library": "golang"}``; those tags reject the request when the
    parameters are missing.

    Works anonymously: with no API key configured the request is rate
    limited per IP but otherwise succeeds.
    """

    async def execute(
        self,
        query="",
        tag="",
        params=None,
        max_results=ANYSEARCH_MAX_RESULTS,
        zone="",
        language="",
        **kwargs,
    ):
        result = await asyncio.to_thread(
            self._vertical_search,
            query,
            tag,
            params,
            max_results,
            zone,
            language,
        )

        await self.agent.handle_intervention(
            result
        )  # wait for intervention and handle it, if paused

        if isinstance(result, Exception):
            handle_error(result)
            return Response(
                message=f"AnySearch vertical search failed: {str(result)}",
                break_loop=False,
            )

        return Response(message=self.format_result(result), break_loop=False)

    def _vertical_search(
        self, query, tag, params, max_results, zone, language
    ):
        try:
            return search(
                query=query,
                max_results=max_results,
                tag=tag,
                params=params,
                zone=zone,
                language=language,
            )
        except Exception as e:
            return e

    def format_result(self, results, source="AnySearch"):
        if isinstance(results, Exception):
            return f"{source} vertical search failed: {str(results)}"

        if not results:
            return f"{source} vertical search returned no results."

        outputs = []
        for item in results:
            parts = [item["title"], item["url"]]
            body = item["content"] or item["snippet"]
            if body:
                parts.append(body)
            outputs.append("\n".join(parts))

        return "\n\n".join(outputs).strip()
