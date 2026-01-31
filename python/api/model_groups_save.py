from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings
from python.api.model_groups import create_model_group_from_current


class ModelGroupsSave(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        name = input.get("name", "").strip()
        description = input.get("description", "").strip()
        
        if not name:
            return {"ok": False, "error": "Name is required"}
        
        # Create model group from current settings
        group = create_model_group_from_current()
        group["name"] = name
        group["description"] = description
        
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        groups.append(group)
        current["model_groups"] = groups
        current["active_model_group_id"] = group["id"]
        settings.set_settings(current, apply=False)
        
        return {"ok": True, "group": group}