from helpers import settings
from helpers.extension import Extension


_TOKEN_KEY = "_prompt_settings_snapshot_token"


class RestorePromptSettings(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        token = data.pop(_TOKEN_KEY, None) if isinstance(data, dict) else None
        if token is not None:
            settings.end_prompt_settings_snapshot(token)
