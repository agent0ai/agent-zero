from python.helpers.extension import Extension
from python.helpers.secrets import SecretsManager


class UnmaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        # Get tool args from kwargs
        tool_args = kwargs.get("tool_args")
        if not tool_args:
            return

        secrets_mgr = SecretsManager.get_instance()

        # Unmask placeholders in args for actual tool execution
        for k, v in tool_args.items():
            if isinstance(v, str):
                tool_args[k] = secrets_mgr.replace_placeholders(v)
