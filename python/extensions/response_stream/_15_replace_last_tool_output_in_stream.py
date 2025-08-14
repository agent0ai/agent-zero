from typing import Any
from python.helpers.extension import Extension


class ReplaceLastToolOutputInStream(Extension):
    async def execute(self, loop_data=None, text: str = "", parsed: dict[str, Any] | None = None, **kwargs):
        if not parsed or not isinstance(parsed, dict):
            return

        last_call = self.agent.get_data("last_tool_call") or {}
        last_output = last_call.get("last_tool_output", "")
        if not last_output:
            return

        tokens = ("{last_tool_output}", "{{last_tool_output}}")

        def replace_placeholders(value: Any) -> Any:
            if isinstance(value, str):
                new_val = value
                for token in tokens:
                    new_val = new_val.replace(token, last_output)
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
