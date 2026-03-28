"""Plugin settings CRUD."""

import json
from python.helpers.api import ApiHandler
from python.helpers import files
from flask import Request

SETTINGS_PATH = "usr/plugins/browser_use/settings.json"

DEFAULT_SETTINGS = {
    "browser_mode": "chromium",
    "headless": False,
    "default_max_steps": 25,
    "vision_mode": "auto",
    "flash_mode": False,
    "screencast_quality": 80,
    "window_size": "1024x768",
    "browser_use_api_key": "",
}


class BrowserUseSettings(ApiHandler):

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict:
        if request.method == "GET":
            return {"settings": self._load_settings()}

        # POST: save settings
        new_settings = input.get("settings", {})
        current = self._load_settings()
        current.update(new_settings)

        settings_path = files.get_abs_path(SETTINGS_PATH)
        files.make_dirs(settings_path)
        with open(settings_path, "w") as f:
            json.dump(current, f, indent=2)

        return {"ok": True}

    def _load_settings(self) -> dict:
        settings_path = files.get_abs_path(SETTINGS_PATH)
        if files.exists(settings_path):
            try:
                with open(settings_path) as f:
                    return {**DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)
