from helpers.tool import Response, Tool
from plugins._searxng.helpers.searxng import search as searxng


class SearchEngine(Tool):
    async def execute(self, query: str = "", **kwargs) -> Response:
        del kwargs
        return Response(message=await searxng(query), break_loop=False)
