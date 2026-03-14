"""
Claude SDK Bridge Tool for Agent Jumbo
Integrates Claude Agent SDK for Python, enabling bidirectional tool sharing
"""

from python.helpers import files
from python.helpers.tool import Response, Tool


class ClaudeSDKBridge(Tool):
    """
    Agent Jumbo tool for Claude Agent SDK integration.
    Enables session management, queries, and tool bridging with Claude Code.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.claude_sdk.sdk_manager import ClaudeSDKManager

        self.manager = ClaudeSDKManager()

    async def execute(self, **kwargs):
        """Execute Claude SDK bridge action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Status
            "get_status": self._get_status,
            "install_sdk": self._install_sdk,
            # Session management
            "init_sdk": self._init_sdk,
            "close_sdk": self._close_sdk,
            # Query operations
            "query": self._query,
            "session_query": self._session_query,
            "cli_query": self._cli_query,
            # Tool operations
            "list_tools": self._list_tools,
            "export_tool": self._export_tool,
            # MCP operations
            "get_mcp_config": self._get_mcp_config,
            "bridge_mcp": self._bridge_mcp,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Status ==========

    async def _get_status(self):
        """Get SDK availability and session status"""
        status = self.manager.get_status()

        lines = ["## Claude SDK Status\n"]

        sdk_icon = "✅" if status["sdk_available"] else "❌"
        cli_icon = "✅" if status["cli_available"] else "❌"
        session_icon = "✅" if status["session_active"] else "⏳"

        lines.append(f"**SDK Available:** {sdk_icon}")
        lines.append(f"**CLI Available:** {cli_icon}")
        lines.append(f"**Session Active:** {session_icon}")

        if status.get("sdk_version"):
            lines.append(f"**SDK Version:** {status['sdk_version']}")

        if not status["sdk_available"]:
            lines.append("")
            lines.append('To install SDK: `{{claude_sdk_bridge(action="install_sdk")}}`')

        return Response(message="\n".join(lines), break_loop=False)

    async def _install_sdk(self):
        """Install Claude Agent SDK"""
        result = self.manager.install_sdk()

        if "error" in result:
            return Response(message=f"Installation failed: {result['error']}", break_loop=False)

        return Response(
            message="## SDK Installed\n\nClaude Agent SDK has been installed. You can now use SDK features.",
            break_loop=False,
        )

    # ========== Session Management ==========

    async def _init_sdk(self):
        """Initialize SDK session"""
        system_prompt = self.args.get("system_prompt")
        allowed_tools = self.args.get("allowed_tools")
        permission_mode = self.args.get("permission_mode", "acceptEdits")
        max_turns = self.args.get("max_turns", 10)
        mcp_servers = self.args.get("mcp_servers")
        cwd = self.args.get("cwd")

        result = await self.manager.initialize_session(
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
            max_turns=max_turns,
            mcp_servers=mcp_servers,
            cwd=cwd,
        )

        if "error" in result:
            return Response(message=f"Session initialization failed: {result['error']}", break_loop=False)

        lines = ["## SDK Session Initialized\n"]
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Allowed Tools:** {', '.join(result['allowed_tools'])}")
        lines.append(f"**Max Turns:** {result['max_turns']}")
        lines.append(f"**Permission Mode:** {result['permission_mode']}")
        lines.append("")
        lines.append("Use `session_query` to send queries through this session.")

        return Response(message="\n".join(lines), break_loop=False)

    async def _close_sdk(self):
        """Close SDK session"""
        result = await self.manager.close_session()

        return Response(message=f"SDK session {result['status']}.", break_loop=False)

    # ========== Query Operations ==========

    async def _query(self):
        """Send a simple stateless query"""
        prompt = self.args.get("prompt")

        if not prompt:
            return Response(message="Error: prompt is required", break_loop=False)

        # Build options from args if provided
        options = {}
        if self.args.get("system_prompt"):
            options["system_prompt"] = self.args["system_prompt"]
        if self.args.get("allowed_tools"):
            options["allowed_tools"] = self.args["allowed_tools"]

        result = await self.manager.simple_query(prompt, options if options else None)

        if "error" in result:
            return Response(message=f"Query failed: {result['error']}", break_loop=False)

        lines = ["## Query Result\n"]

        for i, response in enumerate(result.get("responses", []), 1):
            lines.append(f"### Response {i}")
            lines.append(f"**Type:** {response.get('type', 'unknown')}")
            content = response.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "...(truncated)"
            lines.append(content)
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _session_query(self):
        """Send query through active session"""
        prompt = self.args.get("prompt")

        if not prompt:
            return Response(message="Error: prompt is required", break_loop=False)

        result = await self.manager.session_query(prompt)

        if "error" in result:
            return Response(message=f"Query failed: {result['error']}", break_loop=False)

        lines = ["## Session Query Result\n"]

        for i, response in enumerate(result.get("responses", []), 1):
            lines.append(f"### Response {i}")
            lines.append(f"**Type:** {response.get('type', 'unknown')}")
            content = response.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "...(truncated)"
            lines.append(content)
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _cli_query(self):
        """Run query through Claude Code CLI directly"""
        prompt = self.args.get("prompt")
        working_dir = self.args.get("working_dir")
        timeout = self.args.get("timeout", 300)

        if not prompt:
            return Response(message="Error: prompt is required", break_loop=False)

        result = self.manager.run_cli_command(prompt, working_dir, timeout)

        if "error" in result:
            return Response(message=f"CLI query failed: {result['error']}", break_loop=False)

        lines = ["## CLI Query Result\n"]
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Exit Code:** {result['exit_code']}")

        if result.get("output"):
            lines.append("")
            lines.append("### Output")
            output = result["output"]
            if len(output) > 2000:
                output = output[:2000] + "...(truncated)"
            lines.append(f"```\n{output}\n```")

        if result.get("error"):
            lines.append("")
            lines.append("### Error")
            lines.append(f"```\n{result['error']}\n```")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Tool Operations ==========

    async def _list_tools(self):
        """List available SDK tools"""
        tools = self.manager.get_available_tools()

        lines = ["## Available SDK Tools\n"]
        for tool in tools:
            lines.append(f"- {tool}")

        lines.append("")
        lines.append("These tools can be enabled when initializing an SDK session.")

        return Response(message="\n".join(lines), break_loop=False)

    async def _export_tool(self):
        """Export an Agent Jumbo tool for SDK use"""
        tool_name = self.args.get("tool_name")

        if not tool_name:
            return Response(message="Error: tool_name is required", break_loop=False)

        # Try to get the tool class
        try:
            from python.helpers.extract_tools import load_classes_from_folder

            tool_classes = load_classes_from_folder(files.get_abs_path("python/tools"), name_pattern=f"*{tool_name}*")

            if not tool_classes:
                return Response(message=f"Tool not found: {tool_name}", break_loop=False)

            tool_class = next(iter(tool_classes.values()))
            result = self.manager.export_agent_jumbo_tool(tool_name, tool_class)

            if "error" in result:
                return Response(message=f"Export failed: {result['error']}", break_loop=False)

            return Response(
                message=f"## Tool Exported\n\n**Original:** {result['original_name']}\n**SDK Name:** {result['sdk_name']}\n\nThis tool can now be used in SDK sessions via MCP.",
                break_loop=False,
            )

        except Exception as e:
            return Response(message=f"Export failed: {e!s}", break_loop=False)

    # ========== MCP Operations ==========

    async def _get_mcp_config(self):
        """Generate MCP server configuration"""
        server_name = self.args.get("server_name")
        command = self.args.get("command")
        args = self.args.get("args", [])
        env = self.args.get("env", {})

        if not server_name or not command:
            return Response(message="Error: server_name and command are required", break_loop=False)

        config = self.manager.get_mcp_server_config(server_name, command, args, env)

        import json

        config_json = json.dumps(config, indent=2)

        return Response(
            message=f"## MCP Server Config\n\n```json\n{config_json}\n```\n\nUse this config with `init_sdk` mcp_servers parameter.",
            break_loop=False,
        )

    async def _bridge_mcp(self):
        """Bridge an external MCP server"""
        server_name = self.args.get("server_name")
        server_type = self.args.get("server_type", "stdio")
        config = self.args.get("config", {})

        if not server_name:
            return Response(message="Error: server_name is required", break_loop=False)

        result = self.manager.bridge_external_mcp(server_name, server_type, config)

        if "error" in result:
            return Response(message=f"Bridge failed: {result['error']}", break_loop=False)

        import json

        config_json = json.dumps(result, indent=2)

        return Response(
            message=f"## MCP Server Bridged\n\n**Server:** {server_name}\n**Type:** {server_type}\n\n```json\n{config_json}\n```",
            break_loop=False,
        )
