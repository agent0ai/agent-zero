from helpers.extension import Extension
from helpers.secrets import get_secrets_manager
from helpers.team_access import is_team_chat


class UnmaskToolSecrets(Extension):

    async def execute(self, **kwargs):
        if not self.agent or is_team_chat(self.agent.context):
            return

        # Get tool args from kwargs
        tool_args = kwargs.get("tool_args")
        if not tool_args:
            return

        secrets_mgr = get_secrets_manager(self.agent.context)

        # Unmask placeholders in args for actual tool execution
        for k, v in tool_args.items():
            if isinstance(v, str):
                tool_args[k] = secrets_mgr.replace_placeholders(v)
