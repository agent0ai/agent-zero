from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skill_registry import get_registry


class SkillsList(ApiHandler):
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        registry = get_registry()
        category = input.get("category") or request.args.get("category")
        skills = registry.list(category=category)
        return {"skills": [s.to_dict() for s in skills]}
