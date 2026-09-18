from typing import Any

from helpers.extension import Extension
from helpers.secrets import get_secrets_manager


def _replace_placeholders(value: Any, secrets_mgr) -> Any:
    if isinstance(value, str):
        return secrets_mgr.replace_placeholders(value)
    if isinstance(value, dict):
        return {k: _replace_placeholders(v, secrets_mgr) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(v, secrets_mgr) for v in value]
    if isinstance(value, tuple):
        return tuple(_replace_placeholders(v, secrets_mgr) for v in value)
    return value


class UnmaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        if not self.agent:
            return

        # Get tool args from kwargs
        tool_args = kwargs.get("tool_args")
        if not tool_args:
            return

        secrets_mgr = get_secrets_manager(self.agent.context)

        # Unmask placeholders in args for actual tool execution, recursing
        # into dicts/lists/tuples so nested calls (e.g. the `parallel` tool's
        # tool_calls list) get their secrets substituted too.
        for k, v in tool_args.items():
            tool_args[k] = _replace_placeholders(v, secrets_mgr)
