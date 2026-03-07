from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skill_registry import get_registry


class SkillsSearch(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        registry = get_registry()
        query = input.get("query") or request.args.get("query", "")
        if not query:
            return Response(response="Missing 'query' parameter", status=400, mimetype="text/plain")

        results = registry.search(query)
        return {"results": [s.to_dict() for s in results]}
