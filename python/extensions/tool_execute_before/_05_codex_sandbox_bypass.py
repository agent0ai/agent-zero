from python.helpers.extension import Extension


class CodexSandboxBypass(Extension):
    """Inject sandbox=danger-full-access into Codex MCP tool calls.

    Codex's Landlock sandbox cannot traverse Docker bind mounts,
    so all file reads in /a0 fail with EACCES. Since the container
    IS the sandbox, we disable Codex's internal sandbox entirely.
    """

    async def execute(self, **kwargs):
        tool_name = kwargs.get("tool_name", "")
        tool_args = kwargs.get("tool_args")
        if not tool_args or not tool_name:
            return

        if tool_name.startswith("codex."):
            tool_args["sandbox"] = "danger-full-access"
