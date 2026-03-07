from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skill_registry import get_registry


class SkillsUninstall(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        registry = get_registry()
        name = input.get("name", "")
        if not name:
            return Response(response="Missing 'name' parameter", status=400, mimetype="text/plain")

        skill = registry.get(name)
        if skill is None:
            return Response(response=f"Skill '{name}' not found", status=404, mimetype="text/plain")

        registry.uninstall(name)
        return {"uninstalled": name}
