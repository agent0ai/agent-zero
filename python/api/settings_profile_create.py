from python.helpers.api import ApiHandler, Request, Response
from python.helpers import settings


class SettingsProfileCreate(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        name = str((input or {}).get("name", "")).strip()
        if not name:
            raise ValueError("Profile name is required")
        settings.create_settings_profile(name)
        # Return effective settings for the newly selected profile
        effective = settings.get_effective_settings()
        set_out = settings.convert_out(effective)
        return {"settings": set_out}
