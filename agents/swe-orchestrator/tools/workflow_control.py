"""
Workflow Control Tool for SWE Orchestrator Agent
Provides workflow management and control operations
"""

from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState

class WorkflowControl(Tool):
    """
    Tool for controlling and managing SWE workflows
    """
    
    async def execute(self, **kwargs):
        """Execute workflow control operations"""
        
        operation = kwargs.get("operation", "pause")
        
        if operation == "pause":
            return await self.pause_workflow()
        elif operation == "resume":
            return await self.resume_workflow()
        elif operation == "reset":
            return await self.reset_workflow()
        elif operation == "skip_task":
            return await self.skip_task(**kwargs)
        elif operation == "retry_task":
            return await self.retry_task(**kwargs)
        elif operation == "set_priority":
            return await self.set_task_priority(**kwargs)
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: pause, resume, reset, skip_task, retry_task, set_priority",
                break_loop=False
            )
    
    async def pause_workflow(self) -> Response:
        """Pause the current workflow"""
        state = self.get_or_create_state()
        
        if not state.plan.tasks:
            return Response(
                message="No active workflow to pause",
                break_loop=False
            )
        
        state.scratchpad["workflow_paused"] = True
        state.add_history("Workflow paused by orchestrator")
        self.save_state(state)
        
        return Response(
            message="⏸️ Workflow paused. Use workflow_control(operation='resume') to continue.",
            break_loop=False
        )
    
    async def resume_workflow(self) -> Response:
        """Resume a paused workflow"""
        state = self.get_or_create_state()
        
        if not state.scratchpad.get("workflow_paused"):
            return Response(
                message="Workflow is not currently paused",
                break_loop=False
            )
        
        state.scratchpad["workflow_paused"] = False
        state.add_history("Workflow resumed by orchestrator")
        self.save_state(state)
        
        return Response(
            message="▶️ Workflow resumed. You can now continue with task execution.",
            break_loop=False
        )
    
    async def reset_workflow(self, **kwargs) -> Response:
        """Reset the workflow state (clears all progress)"""
        confirm = kwargs.get("confirm", "").lower()
        
        if confirm != "yes":
            return Response(
                message="⚠️ This will reset ALL workflow progress. To confirm, use: workflow_control(operation='reset', confirm='yes')",
                break_loop=False
            )
        
        # Clear the workflow state
        self.agent.set_data("swe_state", None)
        self.agent.set_data("swe_state_dict", None)
        
        return Response(
            message="🔄 Workflow state has been reset. You can start a new workflow with swe_orchestrator tool.",
            break_loop=False
        )
    
    async def skip_task(self, **kwargs) -> Response:
        """Skip a specific task (marks it as completed without execution)"""
        task_id = kwargs.get("task_id")
        reason = kwargs.get("reason", "Skipped by orchestrator")
        
        if not task_id:
            return Response(
                message="Error: task_id parameter required for skip_task operation",
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
                message=f"Task {task_id} not found in current workflow",
                break_loop=False
            )
        
        if task.status == "completed":
            return Response(
                message=f"Task {task_id} is already completed",
                break_loop=False
            )
        
        # Mark task as completed with skip reason
        task.status = "completed"
        task.revisions.append(f"SKIPPED: {reason}")
        task.artifacts["skip_reason"] = reason
        
        from datetime import datetime
        task.completed_at = datetime.now()
        
        state.add_history(f"Task {task_id} skipped by orchestrator: {reason}")
        self.save_state(state)
        
        return Response(
            message=f"⏭️ Task {task_id} has been skipped: {reason}",
            break_loop=False
        )
    
    async def retry_task(self, **kwargs) -> Response:
        """Reset a failed task to pending status for retry"""
        task_id = kwargs.get("task_id")
        
        if not task_id:
            return Response(
                message="Error: task_id parameter required for retry_task operation", 
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
                message=f"Task {task_id} not found in current workflow",
                break_loop=False
            )
        
        if task.status != "failed":
            return Response(
                message=f"Task {task_id} status is '{task.status}' - only failed tasks can be retried",
                break_loop=False
            )
        
        # Reset task for retry
        task.status = "pending"
        task.error_message = None
        task.started_at = None
        task.completed_at = None
        
        state.add_history(f"Task {task_id} reset for retry by orchestrator")
        self.save_state(state)
        
        return Response(
            message=f"🔄 Task {task_id} has been reset to pending status for retry",
            break_loop=False
        )
    
    async def set_task_priority(self, **kwargs) -> Response:
        """Set priority for task execution (reorders tasks)"""
        task_id = kwargs.get("task_id")
        priority = kwargs.get("priority", "normal")  # high, normal, low
        
        if not task_id:
            return Response(
                message="Error: task_id parameter required for set_priority operation",
                break_loop=False
            )
        
        state = self.get_or_create_state()
        
        # Find the task
        task = None
        task_index = -1
        for i, t in enumerate(state.plan.tasks):
            if t.id == task_id:
                task = t
                task_index = i
                break
        
        if not task:
            return Response(
                message=f"Task {task_id} not found in current workflow",
                break_loop=False
            )
        
        # Store priority in task artifacts
        task.artifacts["priority"] = priority
        
        # Reorder tasks based on priority (high priority tasks moved up)
        if priority == "high" and task_index > 0:
            # Move task towards the beginning
            state.plan.tasks.pop(task_index)
            # Insert after any already completed tasks
            completed_count = len([t for t in state.plan.tasks if t.status == "completed"])
            state.plan.tasks.insert(completed_count, task)
        elif priority == "low":
            # Move task towards the end
            state.plan.tasks.pop(task_index)
            state.plan.tasks.append(task)
        
        state.add_history(f"Task {task_id} priority set to {priority} by orchestrator")
        self.save_state(state)
        
        return Response(
            message=f"📋 Task {task_id} priority set to {priority}",
            break_loop=False
        )
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            # Try to restore from dict format
            state_dict = self.agent.get_data("swe_state_dict") 
            if state_dict and isinstance(state_dict, dict):
                from python.helpers.swe_graph_state import GraphState
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-orchestrator"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.agent.set_data("swe_state", state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())