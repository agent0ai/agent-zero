from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings


class ModelGroupsDelete(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        group_id = input.get("group_id")
        if not group_id:
            return {"ok": False, "error": "Missing group_id"}
        
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        
        new_groups = [g for g in groups if g["id"] != group_id]
        
        if len(new_groups) == len(groups):
            return {"ok": False, "error": "Model group not found"}
        
        current["model_groups"] = new_groups
        
        # If deleted group was active, clear active state
        if current.get("active_model_group_id") == group_id:
            current["active_model_group_id"] = ""
        
        settings.set_settings(current, apply=False)
        
        return {"ok": True, "message": "Model group deleted"}