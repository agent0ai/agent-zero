from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings


class ModelGroupsList(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        active_group_id = current.get("active_model_group_id", "")
        
        return {
            "ok": True,
            "groups": groups,
            "active_group_id": active_group_id
        }
