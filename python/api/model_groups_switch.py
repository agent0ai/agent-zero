from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings
from python.api.model_groups import MODEL_GROUP_FIELDS


class ModelGroupsSwitch(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        group_id = input.get("group_id")  # Can be empty or null, meaning switch to default/manual config
        
        current = settings.get_settings()
        
        if not group_id:
            # Switch to default config (clear model group activation)
            current["active_model_group_id"] = ""
            settings.set_settings(current, apply=False)
            return {"ok": True, "message": "Switched to default configuration"}
        
        # Find model group
        groups = current.get("model_groups", [])
        target_group = None
        for group in groups:
            if group["id"] == group_id:
                target_group = group
                break
        
        if not target_group:
            return {"ok": False, "error": "Model group not found"}
        
        # Apply model group config
        for field in MODEL_GROUP_FIELDS:
            if field in target_group:
                current[field] = target_group[field]
        
        current["active_model_group_id"] = group_id
        settings.set_settings(current)  # apply=True triggers model reinitialization
        
        return {"ok": True, "message": f"Switched to model group: {target_group['name']}"}