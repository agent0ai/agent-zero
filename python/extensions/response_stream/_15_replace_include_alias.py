from typing import Any
from python.helpers.extension import Extension
from python.helpers.strings import replace_file_includes


class ReplaceIncludeAlias(Extension):
    async def execute(
        self,
        loop_data=None,
        text: str = "",
        parsed: dict[str, Any] | None = None,
        **kwargs
    ):
        if not parsed or not isinstance(parsed, dict):
            return

        def replace_placeholders(value: Any) -> Any:
            if isinstance(value, str):
                new_val = value
                new_val = replace_file_includes(new_val, r"§§include\(([^)]+)\)")
                return new_val
            if isinstance(value, dict):
                return {k: replace_placeholders(v) for k, v in value.items()}
            if isinstance(value, list):
                return [replace_placeholders(v) for v in value]
            if isinstance(value, tuple):
                return tuple(replace_placeholders(v) for v in value)
            return value

        if "tool_args" in parsed and "tool_name" in parsed:
            parsed["tool_args"] = replace_placeholders(parsed["tool_args"])
