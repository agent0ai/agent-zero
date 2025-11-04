from typing import Any
from python.helpers.extension import Extension


class ReplaceLastToolOutput(Extension):
    async def execute(self, tool_args: dict[str, Any] | None = None, tool_name: str = "", **kwargs):
        if not tool_args:
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

        updated_args = replace_placeholders(tool_args)
        tool_args.clear()
        tool_args.update(updated_args)
