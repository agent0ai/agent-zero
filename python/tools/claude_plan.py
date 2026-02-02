import asyncio
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle


class ClaudePlan(Tool):
    """Delegate planning tasks to Claude Code CLI with extended thinking."""

    TIMEOUT_SECONDS = 600  # 10 minutes

    async def execute(self, **kwargs) -> Response:
        await self.agent.handle_intervention()

        task = self.args.get("task", "")
        working_dir = self.args.get("working_dir", None)

        if not task:
            return Response(
                message="Error: No task provided. Please specify a 'task' argument.",
                break_loop=False
            )

        try:
            process = await asyncio.create_subprocess_exec(
                "claude", "--think", "--print",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )

            self.log.update(content="Starting Claude Plan with extended thinking...")
            output = await self._stream_output(process, task)

            return Response(message=output, break_loop=False)

        except FileNotFoundError:
            return Response(
                message="Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
                break_loop=False
            )
        except asyncio.TimeoutError:
            return Response(
                message=f"Claude Plan timed out after {self.TIMEOUT_SECONDS // 60} minutes.",
                break_loop=False
            )
        except Exception as e:
            return Response(message=f"Claude Plan error: {str(e)}", break_loop=False)

    async def _stream_output(self, process, task: str) -> str:
        full_output = ""

        if process.stdin:
            process.stdin.write(task.encode())
            await process.stdin.drain()
            process.stdin.close()

        async def read_stream():
            nonlocal full_output
            while True:
                await self.agent.handle_intervention()
                if process.stdout:
                    chunk = await asyncio.wait_for(process.stdout.read(1024), timeout=60)
                    if not chunk:
                        break
                    decoded = chunk.decode('utf-8', errors='replace')
                    full_output += decoded
                    PrintStyle(font_color="#82E0AA").stream(decoded)
                    self.log.update(content=full_output[-50000:])
                else:
                    break

        try:
            await asyncio.wait_for(read_stream(), timeout=self.TIMEOUT_SECONDS)
            await process.wait()

            if process.returncode != 0 and process.stderr:
                stderr = await process.stderr.read()
                if stderr.strip():
                    full_output += f"\n[stderr]: {stderr.decode()}"
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise

        self.log.update(heading=self.get_heading(done=True))
        return full_output.strip() or "Claude Plan completed with no output."

    def get_heading(self, done: bool = False) -> str:
        icon = " icon://done_all" if done else ""
        return f"icon://psychology {self.agent.agent_name}: Claude Plan{icon}"

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=self.get_heading(),
            content="",
            kvps=self.args,
        )
