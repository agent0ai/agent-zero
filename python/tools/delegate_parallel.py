"""
Parallel Delegation Tool

Allows agents to delegate multiple tasks to subordinate agents in parallel.
"""

from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
from python.helpers.task_queue import TaskQueue
from initialize import initialize_agent
from typing import Any, Dict, List, Optional


class DelegateParallel(Tool):
    """
    Tool for parallel agent delegation with dependency management.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create or reuse task queue for this agent context
        # Set higher concurrency limit for true parallel execution
        if not hasattr(self.agent.context, '_task_queue'):
            self.agent.context._task_queue = TaskQueue(max_concurrent=10)
        self.task_queue = self.agent.context._task_queue
        # Track agent numbers for unique numbering
        if not hasattr(self.agent.context, '_parallel_agent_counter'):
            self.agent.context._parallel_agent_counter = 0

    async def execute(self, **kwargs) -> Response:
        """
        Execute multiple tasks in parallel using subordinate agents.

        Args (from kwargs or self.args):
            tasks: List of task dictionaries, each with:
                - id: Unique task identifier
                - message: Task description
                - profile: Optional agent profile (developer, researcher, etc.)
                - dependencies: Optional list of task IDs this depends on
                - metadata: Optional additional metadata
            wait_for_all: Whether to wait for all tasks to complete (default: True)
            timeout: Maximum time to wait in seconds (default: None)

        Returns:
            Response with aggregated results
        """
        # Extract from kwargs (passed from tool_args) or self.args (for compatibility)
        tasks = kwargs.get("tasks") or self.args.get("tasks", [])
        wait_for_all = kwargs.get("wait_for_all", self.args.get("wait_for_all", True))
        timeout = kwargs.get("timeout", self.args.get("timeout", None))
        
        # Handle boolean strings from JSON
        if isinstance(wait_for_all, str):
            wait_for_all = wait_for_all.lower() in ("true", "1", "yes")
        if isinstance(timeout, str):
            try:
                timeout = float(timeout)
            except ValueError:
                timeout = None
        if not tasks:
            return Response(
                message="No tasks provided for parallel delegation.",
                break_loop=False
            )

        # Validate tasks
        for task in tasks:
            if "message" not in task:
                return Response(
                    message=f"Task {task.get('id', 'unknown')} missing required 'message' field.",
                    break_loop=False
                )

        # Add task group to queue
        try:
            group = self.task_queue.add_task_group(
                tasks=tasks,
                wait_for_all=wait_for_all,
                timeout=timeout,
            )
        except Exception as e:
            return Response(
                message=f"Failed to create task group: {str(e)}",
                break_loop=False
            )

        # Log delegation start
        self.agent.context.log.log(
            type="tool",
            heading=f"{self.agent.agent_name}: Parallel Delegation Started",
            content=f"Delegating {len(tasks)} tasks in parallel",
            kvps={
                "group_id": group.id,
                "task_count": len(tasks),
                "wait_for_all": wait_for_all,
            }
        )

        # Execute task group
        try:
            results = await self.task_queue.execute_group(
                group_id=group.id,
                agent_factory=self._create_agent,
                execute_func=self._execute_task,
            )

            # Aggregate results
            aggregated = self._aggregate_results(results, group)

            # Log completion
            self.agent.context.log.log(
                type="tool",
                heading=f"{self.agent.agent_name}: Parallel Delegation Completed",
                content=f"Completed {len([r for r in results.values() if r.get('status') == 'completed'])}/{len(tasks)} tasks",
                kvps={
                    "group_id": group.id,
                    "results": results,
                }
            )

            return Response(
                message=aggregated,
                break_loop=False,
                additional={
                    "group_id": group.id,
                    "results": results,
                    "task_count": len(tasks),
                }
            )

        except Exception as e:
            error_msg = f"Parallel delegation failed: {str(e)}"
            self.agent.context.log.log(
                type="error",
                heading="Parallel Delegation Error",
                content=error_msg,
            )
            return Response(
                message=error_msg,
                break_loop=False
            )

    def _create_agent(self, profile: Optional[str] = None) -> Agent:
        """
        Create a subordinate agent for task execution with isolated context.

        Args:
            profile: Optional agent profile name

        Returns:
            Agent instance
        """
        from agent import AgentContext, AgentContextType
        
        config = initialize_agent()
        if profile:
            config.profile = profile

        # Create isolated context for parallel execution
        # This ensures agents don't interfere with each other
        isolated_context = AgentContext(
            config=config,
            type=AgentContextType.TASK,  # Mark as task context
            name=f"Parallel Task Agent ({profile or 'default'})",
        )

        # Create subordinate agent with isolated context
        # Use unique agent number for each parallel agent
        self.agent.context._parallel_agent_counter += 1
        sub_number = self.agent.number + self.agent.context._parallel_agent_counter
        sub = Agent(sub_number, config, isolated_context)

        # Register superior/subordinate relationship (but keep contexts separate)
        sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
        # Store reference to parent context for coordination if needed
        sub.set_data("_parent_context_id", self.agent.context.id)

        return sub

    async def _execute_task(self, agent: Agent, message: str) -> str:
        """
        Execute a task on an agent.

        Args:
            agent: Agent instance
            message: Task message

        Returns:
            Task result
        """
        import time
        start_time = time.time()
        
        # Log task start
        agent.context.log.log(
            type="tool",
            heading=f"{agent.agent_name}: Starting Parallel Task",
            content=f"Task: {message[:100]}...",
        )
        
        # Add user message to agent
        agent.hist_add_user_message(UserMessage(message=message, attachments=[]))

        # Run agent monologue - this should run independently in parallel
        result = await agent.monologue()
        
        duration = time.time() - start_time
        agent.context.log.log(
            type="tool",
            heading=f"{agent.agent_name}: Completed Parallel Task",
            content=f"Completed in {duration:.2f}s",
        )

        return result

    def _aggregate_results(
        self,
        results: Dict[str, Any],
        group: Any
    ) -> str:
        """
        Aggregate results from multiple tasks into a coherent response.

        Args:
            results: Dictionary mapping task IDs to results
            group: TaskGroup object

        Returns:
            Aggregated result string
        """
        completed = []
        failed = []

        for task in group.tasks:
            task_result = results.get(task.id, {})
            status = task_result.get("status", "unknown")

            if status == "completed":
                completed.append({
                    "id": task.id,
                    "message": task.message,
                    "result": task_result.get("result", ""),
                })
            elif status == "failed":
                failed.append({
                    "id": task.id,
                    "message": task.message,
                    "error": task_result.get("error", ""),
                })

        # Build aggregated response
        parts = []

        if completed:
            parts.append(f"## Completed Tasks ({len(completed)}/{len(group.tasks)})\n")
            for task_result in completed:
                parts.append(f"### Task: {task_result['message']}\n")
                parts.append(f"{task_result['result']}\n\n")

        if failed:
            parts.append(f"## Failed Tasks ({len(failed)}/{len(group.tasks)})\n")
            for task_result in failed:
                parts.append(f"### Task: {task_result['message']}\n")
                parts.append(f"Error: {task_result['error']}\n\n")

        if not completed and not failed:
            return "No tasks completed successfully."

        return "\n".join(parts)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"{self.agent.agent_name}: Parallel Delegation",
            content="",
            kvps=self.args,
        )

