"""
Task Manager Tool for SWE Programmer Agent
Manages task status and progress within the GraphState
"""

from datetime import datetime
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState

class TaskManager(Tool):
    """
    Tool for managing task status and progress in the SWE workflow
    """
    
    async def execute(self, **kwargs):
        """Execute task management operations"""
        
        operation = kwargs.get("operation", "update_status")
        
        if operation == "update_status":
            return await self.update_task_status(**kwargs)
        elif operation == "start_task":
            return await self.start_task(**kwargs)
        elif operation == "complete_task":
            return await self.complete_task(**kwargs)
        elif operation == "fail_task":
            return await self.fail_task(**kwargs)
        elif operation == "get_current":
            return await self.get_current_task(**kwargs)
        elif operation == "get_next":
            return await self.get_next_task(**kwargs)
        elif operation == "add_artifact":
            return await self.add_artifact(**kwargs)
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: update_status, start_task, complete_task, fail_task, get_current, get_next, add_artifact",
                break_loop=False
            )
    
    async def update_task_status(self, **kwargs) -> Response:
        """Update the status of a specific task"""
        task_id = kwargs.get("task_id")
        status = kwargs.get("status")
        
        if not task_id or not status:
            return Response(
                message="Error: Both 'task_id' and 'status' are required",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find the task
        task = None
        for t in state.plan.tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return Response(
                message=f"Task with ID {task_id} not found",
                break_loop=False
            )
        
        old_status = task.status
        task.status = status
        
        # Update timestamps
        if status == "in-progress" and not task.started_at:
            task.started_at = datetime.now()
        elif status == "completed" and not task.completed_at:
            task.completed_at = datetime.now()
        
        # Add error message if provided
        if "error_message" in kwargs:
            task.error_message = kwargs["error_message"]
        
        state.add_history(f"Task {task_id} status: {old_status} → {status}")
        self.save_state(state)
        
        return Response(
            message=f"Task {task_id} status updated: {old_status} → {status}",
            break_loop=False
        )
    
    async def start_task(self, **kwargs) -> Response:
        """Start working on a specific task"""
        task_id = kwargs.get("task_id")
        
        if not task_id:
            return Response(
                message="Error: 'task_id' is required to start a task",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find and start the task
        task = None
        for t in state.plan.tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return Response(
                message=f"Task with ID {task_id} not found",
                break_loop=False
            )
        
        task.status = "in-progress"
        task.started_at = datetime.now()
        task.assigned_to = "swe-programmer"
        
        state.current_agent = "swe-programmer"
        state.add_history(f"Started task {task_id}: {task.description}")
        self.save_state(state)
        
        return Response(
            message=f"Started task {task_id}: {task.description}",
            break_loop=False
        )
    
    async def complete_task(self, **kwargs) -> Response:
        """Mark a task as completed"""
        task_id = kwargs.get("task_id")
        summary = kwargs.get("summary", "")
        
        if not task_id:
            return Response(
                message="Error: 'task_id' is required to complete a task",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find and complete the task
        task = None
        for t in state.plan.tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return Response(
                message=f"Task with ID {task_id} not found",
                break_loop=False
            )
        
        task.status = "completed"
        task.completed_at = datetime.now()
        
        if summary:
            if "completion_summary" not in task.artifacts:
                task.artifacts["completion_summary"] = []
            task.artifacts["completion_summary"] = summary
        
        state.add_history(f"Completed task {task_id}: {task.description}")
        
        # Check if all tasks are complete
        if state.plan.all_tasks_complete():
            state.plan.is_complete = True
            state.add_history("All tasks completed - plan finished")
        
        self.save_state(state)
        
        return Response(
            message=f"Task {task_id} completed successfully",
            break_loop=False
        )
    
    async def fail_task(self, **kwargs) -> Response:
        """Mark a task as failed"""
        task_id = kwargs.get("task_id")
        error_message = kwargs.get("error_message", "Task failed")
        
        if not task_id:
            return Response(
                message="Error: 'task_id' is required to fail a task",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find and fail the task
        task = None
        for t in state.plan.tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return Response(
                message=f"Task with ID {task_id} not found",
                break_loop=False
            )
        
        task.status = "failed"
        task.error_message = error_message
        
        state.add_history(f"Task {task_id} failed: {error_message}")
        self.save_state(state)
        
        return Response(
            message=f"Task {task_id} marked as failed: {error_message}",
            break_loop=False
        )
    
    async def get_current_task(self, **kwargs) -> Response:
        """Get the currently active task"""
        state = self.get_or_create_state()
        
        current_task = None
        for task in state.plan.tasks:
            if task.status == "in-progress":
                current_task = task
                break
        
        if not current_task:
            return Response(
                message="No task currently in progress",
                break_loop=False
            )
        
        message = f"Current task: {current_task.id} - {current_task.description}\nStatus: {current_task.status}\nStarted: {current_task.started_at}"
        
        return Response(message=message, break_loop=False)
    
    async def get_next_task(self, **kwargs) -> Response:
        """Get the next pending task to work on"""
        state = self.get_or_create_state()
        
        next_task = state.plan.get_next_pending_task()
        
        if not next_task:
            return Response(
                message="No pending tasks found",
                break_loop=False
            )
        
        message = f"Next task: {next_task.id} - {next_task.description}"
        
        return Response(message=message, break_loop=False)
    
    async def add_artifact(self, **kwargs) -> Response:
        """Add an artifact to a task"""
        task_id = kwargs.get("task_id")
        artifact_key = kwargs.get("key")
        artifact_value = kwargs.get("value")
        
        if not all([task_id, artifact_key, artifact_value]):
            return Response(
                message="Error: 'task_id', 'key', and 'value' are all required for adding artifacts",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find the task
        task = None
        for t in state.plan.tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return Response(
                message=f"Task with ID {task_id} not found",
                break_loop=False
            )
        
        task.artifacts[artifact_key] = artifact_value
        state.add_history(f"Added artifact '{artifact_key}' to task {task_id}")
        self.save_state(state)
        
        return Response(
            message=f"Added artifact '{artifact_key}' to task {task_id}",
            break_loop=False
        )
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict and isinstance(state_dict, dict):
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-programmer"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.save_state(state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())