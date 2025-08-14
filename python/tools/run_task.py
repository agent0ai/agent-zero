import asyncio
import uuid
import json
from datetime import datetime
from typing import Any, Dict
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from agent import Agent, AgentContext, AgentContextType, LoopData


class RunTask(Tool):
    """
    Wrapper tool for executing other tools in background contexts.

    This tool accepts a mapping 'tool_calls' from call IDs (no whitespace) to tool-call JSON objects.
    """

    async def execute(self, tool_calls: str = "", **kwargs) -> Response:
        if not tool_calls or not str(tool_calls).strip():
            return Response(message="Error: 'tool_calls' (JSON mapping) is required", break_loop=False)
        return await self._execute_batch(tool_calls)

    async def _execute_batch(self, tool_calls: str) -> Response:
        # Parse mapping of call_id -> tool call JSON
        try:
            calls_obj = json.loads(tool_calls)
            if not isinstance(calls_obj, dict):
                return Response(message="Error: tool_calls must be a JSON object (mapping)", break_loop=False)
        except json.JSONDecodeError as e:
            return Response(message=f"Error: Invalid JSON in tool_calls: {str(e)}", break_loop=False)

        results: Dict[str, str] = {}

        for call_id, call in calls_obj.items():
            call_id_str = str(call_id)
            if not call_id_str or any(c.isspace() for c in call_id_str):
                results[call_id_str] = "Error: Invalid call id (must not contain whitespace)"
                continue
            if not isinstance(call, dict):
                results[call_id_str] = "Error: Tool call must be an object"
                continue

            tool_name = str(call.get("tool_name", "")).strip()
            method = str(call.get("method", "")).strip()
            message = str(call.get("message", ""))
            raw_args: Any = call.get("args", {})
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args) if raw_args else {}
                except json.JSONDecodeError as e:
                    results[call_id_str] = f"Error: Invalid JSON in args: {str(e)}"
                    continue
            elif isinstance(raw_args, dict):
                tool_args = raw_args
            else:
                results[call_id_str] = "Error: args must be an object or JSON string"
                continue

            if not tool_name:
                results[call_id_str] = "Error: tool_name is required"
                continue

            # Start task
            task_id = str(uuid.uuid4())

            async def execute_tool_async(_tool_name: str, _method: str, _tool_args: dict, _message: str, _task_id: str):
                temp_context = AgentContext(
                    config=self.agent.config,
                    type=AgentContextType.BACKGROUND
                )
                temp_agent = Agent(self.agent.number + 1000, self.agent.config, temp_context)
                temp_agent.config.profile = self.agent.config.profile
                try:
                    if not hasattr(temp_agent, 'loop_data') or temp_agent.loop_data is None:
                        temp_agent.loop_data = LoopData()
                    # Ensure message is available in tool_args if provided separately
                    merged_args = dict(_tool_args or {})
                    if _message and "message" not in merged_args:
                        merged_args["message"] = _message
                    # Build a tool request that Agent.process_tools can understand (supports MCP lookup)
                    raw_tool_name = _tool_name + (f":{_method}" if _method else "")
                    request_obj = {"tool_name": raw_tool_name, "tool_args": merged_args}
                    await temp_agent.handle_intervention()
                    tool_result = await temp_agent.process_tools(json.dumps(request_obj))
                    # process_tools now returns a mapping {message,error,break_loop,tool}
                    final_text = ""
                    if isinstance(tool_result, dict):
                        final_text = str(tool_result.get("message") or tool_result.get("error") or "No result")
                    else:
                        final_text = str(tool_result or "No result")
                    await temp_agent.handle_intervention()
                    completed_tasks = self.agent.get_data("completed_tool_tasks") or {}
                    completed_tasks[_task_id] = {
                        "tool_name": _tool_name + (f":{_method}" if _method else ""),
                        "result": final_text,
                        "success": True,
                        "started_at": datetime.now().isoformat(),
                        "context_id": temp_context.id
                    }
                    self.agent.set_data("completed_tool_tasks", completed_tasks)
                    return Response(message=final_text, break_loop=False)
                except Exception as e:
                    completed_tasks = self.agent.get_data("completed_tool_tasks") or {}
                    completed_tasks[_task_id] = {
                        "tool_name": _tool_name + (f":{_method}" if _method else ""),
                        "result": f"Tool execution failed: {str(e)}",
                        "success": False,
                        "started_at": datetime.now().isoformat(),
                        "context_id": temp_context.id
                    }
                    self.agent.set_data("completed_tool_tasks", completed_tasks)
                    PrintStyle(font_color="red", padding=True).print(
                        f"Tool execution failed in task {_task_id}: {str(e)}"
                    )
                finally:
                    # Remove from active tasks when done (success or failure)
                    try:
                        active_tasks_local = self.agent.get_data("active_tool_tasks") or {}
                        if _task_id in active_tasks_local:
                            active_tasks_local.pop(_task_id, None)
                            self.agent.set_data("active_tool_tasks", active_tasks_local)
                    except Exception:
                        pass
                    try:
                        temp_context.reset()
                        AgentContext.remove(temp_context.id)
                    except Exception as cleanup_error:
                        PrintStyle(font_color="red", padding=True).print(
                            f"Warning: Failed to clean up temporary context {temp_context.id}: {cleanup_error}"
                        )

            asyncio_task = asyncio.create_task(execute_tool_async(tool_name, method, tool_args, message, task_id))
            active_tasks = self.agent.get_data("active_tool_tasks") or {}
            active_tasks[task_id] = {
                "tool_name": tool_name + (f":{method}" if method else ""),
                "task": asyncio_task,
                "started_at": datetime.now().isoformat(),
                "args": tool_args
            }
            self.agent.set_data("active_tool_tasks", active_tasks)

        # Build response: one pair per line "call_id: <task_id or Error: ...>"
        response_lines = [f"{cid}: {res}" for cid, res in results.items()]
        return Response(message="\n".join(response_lines), break_loop=False)
