from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings
from python.api.model_groups import MODEL_GROUP_FIELDS


class ModelGroupsUpdate(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        group_id = input.get("group_id")
        if not group_id:
            return {"ok": False, "error": "Missing group_id"}
        
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        active_group_id = current.get("active_model_group_id", "")
        
        for i, group in enumerate(groups):
            if group["id"] == group_id:
                # Update fields
                if "name" in input:
                    group["name"] = input["name"].strip()
                if "description" in input:
                    group["description"] = input["description"].strip()
                
                for field in MODEL_GROUP_FIELDS:
                    if field in input:
                        group[field] = input[field]
                
                groups[i] = group
                current["model_groups"] = groups
                
                # If this is the active group, also update current settings
                if group_id == active_group_id:
                    for field in MODEL_GROUP_FIELDS:
                        if field in group:
                            current[field] = group[field]
                    settings.set_settings(current, apply=True)
                else:
                    settings.set_settings(current, apply=False)
                
                return {"ok": True, "group": group}
        
        return {"ok": False, "error": "Model group not found"}