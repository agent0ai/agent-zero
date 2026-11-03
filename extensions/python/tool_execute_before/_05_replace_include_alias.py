from typing import Any

from helpers.extension import Extension
from helpers.strings import replace_file_includes


class ReplaceIncludeAlias(Extension):
    async def execute(self, tool_args: dict[str, Any] | None = None, **kwargs):
        if not tool_args:
            return

        def replace_placeholders(value: Any) -> Any:
            if isinstance(value, str):
                return replace_file_includes(value)
            if isinstance(value, dict):
                return {k: replace_placeholders(v) for k, v in value.items()}
            if isinstance(value, list):
                return [replace_placeholders(v) for v in value]
            if isinstance(value, tuple):
                return tuple(replace_placeholders(v) for v in value)
            return value

        for key, value in tool_args.items():
            tool_args[key] = replace_placeholders(value)
