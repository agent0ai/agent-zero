import uuid
import copy
from datetime import datetime
from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings


class ModelGroupsDuplicate(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        group_id = input.get("group_id")
        if not group_id:
            return {"ok": False, "error": "Missing group_id"}
        
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        
        source_group = None
        for group in groups:
            if group["id"] == group_id:
                source_group = group
                break
        
        if not source_group:
            return {"ok": False, "error": "Model group not found"}
        
        # Create copy
        new_group = copy.deepcopy(source_group)
        new_group["id"] = str(uuid.uuid4())
        new_group["name"] = f"{source_group['name']} (Copy)"
        new_group["created_at"] = datetime.now().isoformat()
        
        groups.append(new_group)
        current["model_groups"] = groups
        settings.set_settings(current, apply=False)
        
        return {"ok": True, "group": new_group}