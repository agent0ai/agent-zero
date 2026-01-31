import uuid
from datetime import datetime
from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings
from python.helpers.settings import ModelGroupConfig


class ModelGroupsCreate(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        name = input.get("name", "").strip()
        description = input.get("description", "").strip()
        
        if not name:
            return {"ok": False, "error": "Name is required"}
        
        # Create new model group
        group = ModelGroupConfig(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            chat_model_provider=input.get("chat_model_provider", ""),
            chat_model_name=input.get("chat_model_name", ""),
            chat_model_api_base=input.get("chat_model_api_base", ""),
            util_model_provider=input.get("util_model_provider", ""),
            util_model_name=input.get("util_model_name", ""),
            util_model_api_base=input.get("util_model_api_base", ""),
            browser_model_provider=input.get("browser_model_provider", ""),
            browser_model_name=input.get("browser_model_name", ""),
            browser_model_api_base=input.get("browser_model_api_base", ""),
            embed_model_provider=input.get("embed_model_provider", ""),
            embed_model_name=input.get("embed_model_name", ""),
            embed_model_api_base=input.get("embed_model_api_base", ""),
        )
        
        current = settings.get_settings()
        groups = current.get("model_groups", [])
        groups.append(group)
        current["model_groups"] = groups
        settings.set_settings(current, apply=False)
        
        return {"ok": True, "group": group}