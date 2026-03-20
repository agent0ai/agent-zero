from helpers.api import ApiHandler, Request, Response
from plugins._model_config.helpers import model_config


class ModelPresets(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "get")

        if action == "get":
            presets = model_config.get_presets()
            return {"ok": True, "presets": presets}

        elif action == "save":
            presets = input.get("presets")
            if not isinstance(presets, list):
                return Response(status=400, response="presets must be an array")
            model_config.save_presets(presets)
            return {"ok": True, "presets": presets}

        elif action == "reset":
            presets = model_config.reset_presets()
            return {"ok": True, "presets": presets}

        return Response(status=400, response=f"Unknown action: {action}")
