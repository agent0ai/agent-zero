from helpers import settings
from helpers.extension import Extension


_TOKEN_KEY = "_prompt_settings_snapshot_token"


class SnapshotPromptSettings(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        if isinstance(data, dict):
            data[_TOKEN_KEY] = settings.begin_prompt_settings_snapshot()
