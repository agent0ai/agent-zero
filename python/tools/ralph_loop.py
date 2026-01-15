"""
Ralph Loop Tool - Autonomous iterative task execution

Implements the Ralph Wiggum technique for iterative AI development loops.
Tasks continue until completion promise is detected or max iterations reached.
"""

from python.helpers.tool import Tool, Response
from python.helpers import files


class RalphLoop(Tool):
    """
    Tool for autonomous iterative task execution using Ralph Loop methodology.

    Start a loop with a prompt and completion criteria. The agent will
    iterate on the task until the completion promise is output or
    max iterations is reached.
    """

    def __init__(self, agent, name: str, args: dict, message: str, **kwargs):
        super().__init__(agent, name, args, message, **kwargs)

        from instruments.custom.ralph_loop.ralph_manager import RalphLoopManager

        db_path = files.get_abs_path("./instruments/custom/ralph_loop/data/ralph_loop.db")
        self.manager = RalphLoopManager(db_path)

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower()

        action_map = {
            # Loop Lifecycle
            "start_loop": self._start_loop,
            "get_status": self._get_status,
            "cancel_loop": self._cancel_loop,
            "list_loops": self._list_loops,
            "get_loop_history": self._get_loop_history,

            # Workflow Integration
            "start_task_loop": self._start_task_loop,
            "link_to_workflow": self._link_to_workflow,

            # Configuration
            "set_completion_promise": self._set_completion_promise,
            "set_max_iterations": self._set_max_iterations,
            "pause_loop": self._pause_loop,
            "resume_loop": self._resume_loop,

            # Statistics
            "get_stats": self._get_stats,
        }

        handler = action_map.get(action)
        if handler:
            return await handler()

        return Response(
            message=self._format_help(),
            break_loop=False
        )

    # ========== Loop Lifecycle ==========

    async def _start_loop(self):
        """Start a new Ralph loop"""
        prompt = self.args.get("prompt")
        if not prompt:
            return Response(
                message="❌ Error: `prompt` is required to start a Ralph loop.",
                break_loop=False
            )

        result = self.manager.start_loop(
            prompt=prompt,
            name=self.args.get("name"),
            completion_promise=self.args.get("completion_promise"),
            max_iterations=self.args.get("max_iterations", 50),
            agent_id=str(self.agent.number) if self.agent else None
        )

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=self._format_loop_started(result),
            break_loop=False
        )

    async def _get_status(self):
        """Get current status of a loop"""
        loop_id = self.args.get("loop_id")
        if not loop_id:
            # Try to get active loop for this agent
            agent_id = str(self.agent.number) if self.agent else None
            if agent_id:
                loop = self.manager.get_active_loop(agent_id)
                if loop:
                    loop_id = loop['loop_id']

        if not loop_id:
            return Response(
                message="❌ Error: `loop_id` is required or no active loop found.",
                break_loop=False
            )

        result = self.manager.get_status(loop_id)
        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=self._format_status(result),
            break_loop=False
        )

    async def _cancel_loop(self):
        """Cancel an active loop"""
        loop_id = self.args.get("loop_id")
        if not loop_id:
            agent_id = str(self.agent.number) if self.agent else None
            if agent_id:
                loop = self.manager.get_active_loop(agent_id)
                if loop:
                    loop_id = loop['loop_id']

        if not loop_id:
            return Response(
                message="❌ Error: `loop_id` is required or no active loop found.",
                break_loop=False
            )

        result = self.manager.cancel_loop(
            loop_id=loop_id,
            reason=self.args.get("reason")
        )

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"""
🛑 **Ralph Loop Cancelled**
- Loop ID: {result['loop_id']}
- Iterations completed: {result['iterations_completed']}
- Reason: {result['reason']}
""",
            break_loop=False
        )

    async def _list_loops(self):
        """List Ralph loops"""
        loops = self.manager.list_loops(
            status=self.args.get("status"),
            agent_id=self.args.get("agent_id") or (str(self.agent.number) if self.agent else None),
            limit=self.args.get("limit", 20)
        )

        if not loops:
            return Response(
                message="📋 No Ralph loops found.",
                break_loop=False
            )

        return Response(
            message=self._format_loop_list(loops),
            break_loop=False
        )

    async def _get_loop_history(self):
        """Get iteration history for a loop"""
        loop_id = self.args.get("loop_id")
        if not loop_id:
            return Response(
                message="❌ Error: `loop_id` is required.",
                break_loop=False
            )

        iterations = self.manager.get_iteration_history(loop_id)
        loop = self.manager.get_status(loop_id)

        if "error" in loop:
            return Response(
                message=f"❌ Error: {loop['error']}",
                break_loop=False
            )

        return Response(
            message=self._format_iteration_history(loop, iterations),
            break_loop=False
        )

    # ========== Workflow Integration ==========

    async def _start_task_loop(self):
        """Start a Ralph loop for a workflow task"""
        workflow_execution_id = self.args.get("workflow_execution_id")
        task_id = self.args.get("task_id")
        prompt = self.args.get("prompt")

        if not all([workflow_execution_id, task_id, prompt]):
            return Response(
                message="❌ Error: `workflow_execution_id`, `task_id`, and `prompt` are required.",
                break_loop=False
            )

        result = self.manager.start_task_loop(
            workflow_execution_id=workflow_execution_id,
            task_id=task_id,
            prompt=prompt,
            name=self.args.get("name"),
            completion_promise=self.args.get("completion_promise"),
            max_iterations=self.args.get("max_iterations", 30),
            agent_id=str(self.agent.number) if self.agent else None
        )

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=self._format_loop_started(result, is_task=True),
            break_loop=False
        )

    async def _link_to_workflow(self):
        """Link an existing loop to a workflow"""
        loop_id = self.args.get("loop_id")
        workflow_execution_id = self.args.get("workflow_execution_id")

        if not all([loop_id, workflow_execution_id]):
            return Response(
                message="❌ Error: `loop_id` and `workflow_execution_id` are required.",
                break_loop=False
            )

        result = self.manager.link_to_workflow(
            loop_id=loop_id,
            workflow_execution_id=workflow_execution_id,
            task_id=self.args.get("task_id")
        )

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"✅ Loop {loop_id} linked to workflow execution {workflow_execution_id}",
            break_loop=False
        )

    # ========== Configuration ==========

    async def _set_completion_promise(self):
        """Update completion promise for a loop"""
        loop_id = self.args.get("loop_id")
        completion_promise = self.args.get("completion_promise")

        if not all([loop_id, completion_promise]):
            return Response(
                message="❌ Error: `loop_id` and `completion_promise` are required.",
                break_loop=False
            )

        result = self.manager.update_completion_promise(loop_id, completion_promise)

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"✅ Completion promise updated: `<promise>{completion_promise}</promise>`",
            break_loop=False
        )

    async def _set_max_iterations(self):
        """Update max iterations for a loop"""
        loop_id = self.args.get("loop_id")
        max_iterations = self.args.get("max_iterations")

        if not all([loop_id, max_iterations]):
            return Response(
                message="❌ Error: `loop_id` and `max_iterations` are required.",
                break_loop=False
            )

        result = self.manager.update_max_iterations(loop_id, max_iterations)

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"✅ Max iterations updated to {max_iterations}",
            break_loop=False
        )

    async def _pause_loop(self):
        """Pause an active loop"""
        loop_id = self.args.get("loop_id")
        if not loop_id:
            agent_id = str(self.agent.number) if self.agent else None
            if agent_id:
                loop = self.manager.get_active_loop(agent_id)
                if loop:
                    loop_id = loop['loop_id']

        if not loop_id:
            return Response(
                message="❌ Error: `loop_id` is required or no active loop found.",
                break_loop=False
            )

        result = self.manager.pause_loop(loop_id)

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"⏸️ Loop {loop_id} paused at iteration {result['current_iteration']}",
            break_loop=False
        )

    async def _resume_loop(self):
        """Resume a paused loop"""
        loop_id = self.args.get("loop_id")
        if not loop_id:
            return Response(
                message="❌ Error: `loop_id` is required.",
                break_loop=False
            )

        result = self.manager.resume_loop(loop_id)

        if "error" in result:
            return Response(
                message=f"❌ Error: {result['error']}",
                break_loop=False
            )

        return Response(
            message=f"""
▶️ **Loop Resumed**
- Loop ID: {result['loop_id']}
- Current iteration: {result['current_iteration']}
- Completion promise: {result.get('completion_promise') or 'None'}

The loop will continue from where it left off.
""",
            break_loop=False
        )

    # ========== Statistics ==========

    async def _get_stats(self):
        """Get Ralph loop statistics"""
        agent_id = self.args.get("agent_id")
        if not agent_id and self.agent:
            agent_id = str(self.agent.number)

        stats = self.manager.get_stats(agent_id)

        return Response(
            message=f"""
📊 **Ralph Loop Statistics**

| Metric | Value |
|--------|-------|
| Total Loops | {stats['total_loops']} |
| Active | {stats['active_loops']} |
| Completed | {stats['completed_loops']} |
| Cancelled | {stats['cancelled_loops']} |
| Total Iterations | {stats['total_iterations']} |
| Avg per Loop | {stats['avg_iterations_per_loop']} |
""",
            break_loop=False
        )

    # ========== Formatting Helpers ==========

    def _format_loop_started(self, result: dict, is_task: bool = False) -> str:
        """Format loop started message"""
        source = "Workflow Task" if is_task else "Ralph"
        return f"""
🚀 **{source} Loop Started**

| Property | Value |
|----------|-------|
| Loop ID | {result['loop_id']} |
| Name | {result['name']} |
| Status | {result['status']} |
| Iteration | {result['current_iteration']} |
| Max Iterations | {result['max_iterations']} |
| Completion Promise | {result.get('completion_promise') or 'None'} |

**How it works:**
1. Work on the task described in the prompt
2. Your changes persist in files between iterations
3. When done, output: `<promise>{result.get('completion_promise') or 'DONE'}</promise>`
4. The loop will automatically continue until completion or max iterations

**Controls:**
- Check status: `{{ralph_loop(action="get_status", loop_id={result['loop_id']})}}`
- Cancel: `{{ralph_loop(action="cancel_loop", loop_id={result['loop_id']})}}`
- Pause: `{{ralph_loop(action="pause_loop", loop_id={result['loop_id']})}}`
"""

    def _format_status(self, result: dict) -> str:
        """Format status message"""
        status_emoji = {
            "active": "🔄",
            "completed": "✅",
            "cancelled": "🛑",
            "paused": "⏸️",
            "max_iterations": "📊"
        }.get(result['status'], "❓")

        return f"""
{status_emoji} **Ralph Loop Status**

| Property | Value |
|----------|-------|
| Loop ID | {result['loop_id']} |
| Name | {result['name']} |
| Status | {result['status']} |
| Current Iteration | {result['current_iteration']} |
| Max Iterations | {result['max_iterations']} |
| Completion Promise | {result.get('completion_promise') or 'None'} |
| Started | {result['started_at']} |
| Completed | {result.get('completed_at') or '-'} |
| Workflow Execution | {result.get('workflow_execution_id') or '-'} |
| Task ID | {result.get('task_id') or '-'} |
"""

    def _format_loop_list(self, loops: list) -> str:
        """Format loop list"""
        lines = ["📋 **Ralph Loops**\n"]
        lines.append("| ID | Name | Status | Iteration | Started |")
        lines.append("|---|---|---|---|---|")

        for loop in loops:
            status_emoji = {
                "active": "🔄",
                "completed": "✅",
                "cancelled": "🛑",
                "paused": "⏸️"
            }.get(loop['status'], "❓")

            lines.append(
                f"| {loop['loop_id']} | {loop['name'][:30]} | "
                f"{status_emoji} {loop['status']} | "
                f"{loop['current_iteration']}/{loop['max_iterations']} | "
                f"{loop['started_at'][:10]} |"
            )

        return "\n".join(lines)

    def _format_iteration_history(self, loop: dict, iterations: list) -> str:
        """Format iteration history"""
        lines = [f"📜 **Iteration History: {loop['name']}**\n"]
        lines.append(f"Loop ID: {loop['loop_id']} | Status: {loop['status']}\n")
        lines.append("| # | Started | Completed | Success | Files |")
        lines.append("|---|---|---|---|---|")

        for it in iterations:
            success = "✅" if it.get('success') else ("❌" if it.get('success') is False else "⏳")
            files_count = len(it.get('files_modified', []))
            lines.append(
                f"| {it['iteration_number']} | "
                f"{it['started_at'][:19] if it.get('started_at') else '-'} | "
                f"{it['completed_at'][:19] if it.get('completed_at') else '-'} | "
                f"{success} | {files_count} |"
            )

        return "\n".join(lines)

    def _format_help(self) -> str:
        """Format help message"""
        return """
🔄 **Ralph Loop Tool**

Autonomous iterative task execution using the Ralph Wiggum technique.

## Actions

### Loop Lifecycle
- `start_loop` - Start a new Ralph loop
- `get_status` - Get current loop status
- `cancel_loop` - Cancel an active loop
- `list_loops` - List all loops
- `get_loop_history` - View iteration history

### Workflow Integration
- `start_task_loop` - Start loop for workflow task
- `link_to_workflow` - Link loop to workflow

### Configuration
- `set_completion_promise` - Update completion criteria
- `set_max_iterations` - Update iteration limit
- `pause_loop` - Pause a loop
- `resume_loop` - Resume paused loop

### Statistics
- `get_stats` - View loop statistics

## Quick Start

```
{{ralph_loop(
  action="start_loop",
  name="Build Feature",
  prompt="Implement user authentication with tests.",
  completion_promise="ALL_TESTS_PASS",
  max_iterations=30
)}}
```
"""
