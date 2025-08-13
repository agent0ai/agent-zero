from python.helpers.api import ApiHandler, Request, Response

from python.helpers import settings

class GetSettings(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        # Use effective settings based on the currently selected profile
        effective = settings.get_effective_settings()
        set = settings.convert_out(effective)
        return {"settings": set, "selected_profile": settings.get_settings().get("selected_settings_profile", "default")}
