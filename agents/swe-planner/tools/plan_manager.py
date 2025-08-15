"""
Plan Manager Tool for SWE Planner Agent
Manages development plans within the GraphState
"""

from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, Plan, Task
from datetime import datetime
import json

class PlanManager(Tool):
    """
    Tool for creating and managing development plans in the SWE workflow
    """
    
    async def execute(self, **kwargs):
        """Execute plan management operations"""
        
        # Get the operation type
        operation = kwargs.get("operation", "create")
        
        if operation == "create":
            return await self.create_plan(**kwargs)
        elif operation == "add_task":
            return await self.add_task(**kwargs)
        elif operation == "update_task":
            return await self.update_task(**kwargs)
        elif operation == "estimate_complexity":
            return await self.estimate_complexity(**kwargs)
        elif operation == "get_status":
            return await self.get_plan_status(**kwargs)
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: create, add_task, update_task, estimate_complexity, get_status",
                break_loop=False
            )
    
    async def create_plan(self, **kwargs) -> Response:
        """Create a new development plan"""
        goal = kwargs.get("goal")
        if not goal:
            return Response(
                message="Error: 'goal' parameter is required for creating a plan",
                break_loop=False
            )
        
        # Get or create state
        state = self.get_or_create_state()
        
        # Create new plan
        state.plan = Plan(
            goal=goal,
            created_at=datetime.now(),
            complexity_estimate=kwargs.get("complexity", "moderate")
        )
        
        # Add to history
        state.add_history(f"Plan created by {state.current_agent or 'swe-planner'}: {goal}")
        
        # Store state
        self.save_state(state)
        
        return Response(
            message=f"Successfully created development plan with goal: '{goal}'",
            break_loop=False
        )
    
    async def add_task(self, **kwargs) -> Response:
        """Add a task to the existing plan"""
        description = kwargs.get("description")
        if not description:
            return Response(
                message="Error: 'description' parameter is required for adding a task",
                break_loop=False
            )
        
        # Get state
        state = self.get_or_create_state()
        
        if not state.plan or not state.plan.goal:
            return Response(
                message="Error: A plan must be created before adding tasks. Use operation='create' first.",
                break_loop=False
            )
        
        # Create new task
        task_id = len(state.plan.tasks) + 1
        new_task = Task(
            id=task_id,
            description=description,
            status="pending"
        )
        
        # Add optional task metadata
        if "artifacts" in kwargs:
            new_task.artifacts = kwargs["artifacts"]
        
        state.plan.tasks.append(new_task)
        state.add_history(f"Task {task_id} added: {description}")
        
        # Store updated state
        self.save_state(state)
        
        return Response(
            message=f"Successfully added task {task_id}: {description}",
            break_loop=False
        )
    
    async def update_task(self, **kwargs) -> Response:
        """Update an existing task's status or details"""
        task_id = kwargs.get("task_id")
        if not task_id:
            return Response(
                message="Error: 'task_id' parameter is required for updating a task",
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
                message=f"Error: Task with ID {task_id} not found",
                break_loop=False
            )
        
        # Update task fields
        updates = []
        if "status" in kwargs:
            old_status = task.status
            task.status = kwargs["status"]
            updates.append(f"status: {old_status} -> {task.status}")
            
            if task.status == "in-progress" and not task.started_at:
                task.started_at = datetime.now()
            elif task.status == "completed" and not task.completed_at:
                task.completed_at = datetime.now()
        
        if "description" in kwargs:
            task.description = kwargs["description"]
            updates.append("description updated")
        
        if "artifacts" in kwargs:
            task.artifacts.update(kwargs["artifacts"])
            updates.append("artifacts updated")
        
        if "error_message" in kwargs:
            task.error_message = kwargs["error_message"]
            updates.append("error message set")
        
        state.add_history(f"Task {task_id} updated: {', '.join(updates)}")
        self.save_state(state)
        
        return Response(
            message=f"Task {task_id} updated: {', '.join(updates)}",
            break_loop=False
        )
    
    async def estimate_complexity(self, **kwargs) -> Response:
        """Estimate the complexity of the current plan"""
        state = self.get_or_create_state()
        
        if not state.plan or not state.plan.tasks:
            return Response(
                message="No plan or tasks available to estimate complexity",
                break_loop=False
            )
        
        task_count = len(state.plan.tasks)
        
        # Simple heuristic for complexity
        if task_count <= 3:
            complexity = "simple"
        elif task_count <= 7:
            complexity = "moderate"
        else:
            complexity = "complex"
        
        state.plan.complexity_estimate = complexity
        self.save_state(state)
        
        return Response(
            message=f"Plan complexity estimated as '{complexity}' based on {task_count} tasks",
            break_loop=False
        )
    
    async def get_plan_status(self, **kwargs) -> Response:
        """Get the current status of the plan"""
        state = self.get_or_create_state()
        
        if not state.plan or not state.plan.goal:
            return Response(
                message="No active plan found",
                break_loop=False
            )
        
        total_tasks = len(state.plan.tasks)
        pending = sum(1 for t in state.plan.tasks if t.status == "pending")
        in_progress = sum(1 for t in state.plan.tasks if t.status == "in-progress")
        completed = sum(1 for t in state.plan.tasks if t.status == "completed")
        failed = sum(1 for t in state.plan.tasks if t.status == "failed")
        
        status_msg = f"""Plan Status:
Goal: {state.plan.goal}
Total Tasks: {total_tasks}
- Pending: {pending}
- In Progress: {in_progress}
- Completed: {completed}
- Failed: {failed}
Complexity: {state.plan.complexity_estimate or 'not estimated'}
Complete: {state.plan.all_tasks_complete()}"""
        
        return Response(
            message=status_msg,
            break_loop=False
        )
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            # Try to restore from dict if stored as dict
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict and isinstance(state_dict, dict):
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-planner"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.save_state(state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())