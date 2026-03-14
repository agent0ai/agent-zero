from python.helpers.errors import RepairableException
from python.helpers.extension import Extension
from python.helpers.secrets import get_secrets_manager


class UnmaskToolSecrets(Extension):
    async def execute(self, **kwargs):
        # Get tool args from kwargs
        tool_args = kwargs.get("tool_args")
        if not tool_args:
            return
        tool_name = (kwargs.get("tool_name") or "").strip().lower()
        # `response` is a meta tool for final text output; secret expansion here
        # is unnecessary and can cause avoidable failures.
        if tool_name == "response":
            return

        secrets_mgr = get_secrets_manager(self.agent.context)

        # Unmask placeholders in args for actual tool execution
        for k, v in tool_args.items():
            if isinstance(v, str):
                try:
                    tool_args[k] = secrets_mgr.replace_placeholders(v)
                except RepairableException:
                    # Bubble up as repairable so Tool.handle_exception can provide
                    # a clean, user-facing guidance message.
                    raise
