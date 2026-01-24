"""
OpenCode Bridge - Integrate OpenCode AI coding agent as a tool
Delegates specialized coding tasks to OpenCode CLI

Security: Uses asyncio.create_subprocess_exec() with list args
to prevent command injection. Never uses shell=True.
"""

import asyncio

from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool


class OpenCodeBridge(Tool):
    async def execute(self, **kwargs) -> Response:
        """
        Execute OpenCode for specialized coding tasks

        Args:
            task: Coding task description
            context: Optional code context
            model: Optional model override (default: qwen2.5-coder:7b)
        """
        task = self.args.get("task", "")
        context = self.args.get("context", "")
        model = self.args.get("model", "qwen2.5-coder:7b")

        if not task:
            return Response(message="Error: task parameter required", break_loop=False)

        # Build OpenCode command - using list args (safe from injection)
        # No shell=True, all parameters are separate list elements
        cmd = [
            "npx",
            "-y",
            "@opencode-ai/cli",
            "--model",
            model,
            "--provider",
            "ollama",
            "--api-base",
            "http://localhost:11434",
            "--prompt",
            task,
        ]

        if context:
            cmd.extend(["--context", context])

        try:
            PrintStyle.hint(f"Invoking OpenCode for: {task}")
            # Using asyncio.create_subprocess_exec (not shell=True) - safe
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                return Response(message=f"OpenCode Result:\n```\n{output}\n```", break_loop=False)
            else:
                error = stderr.decode()
                return Response(message=f"OpenCode Error: {error}", break_loop=False)
        except Exception as e:
            return Response(message=f"Failed to invoke OpenCode: {e!s}", break_loop=False)
