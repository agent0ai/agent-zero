from typing import Any
from helpers.extension import Extension
from helpers import cache


class SaveToolCallFile(Extension):
    def execute(self, data: dict[str, Any] | None = None, **kwargs):
        # trim unused cache entries
        cache.trim_cache("*", seconds=300)
