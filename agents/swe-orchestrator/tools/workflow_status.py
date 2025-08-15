"""
Workflow Status Tool for SWE Orchestrator Agent
Provides comprehensive status reporting and workflow monitoring
"""

from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState

class WorkflowStatus(Tool):
    """
    Tool for monitoring and reporting on SWE workflow status
    """
    
    async def execute(self, **kwargs):
        """Execute workflow status operations"""
        
        operation = kwargs.get("operation", "summary")
        
        if operation == "summary":
            return await self.get_workflow_summary()
        elif operation == "detailed":
            return await self.get_detailed_status()
        elif operation == "progress":
            return await self.get_progress_percentage()
        elif operation == "next_steps":
            return await self.get_next_steps()
        elif operation == "issues":
            return await self.get_blocking_issues()
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: summary, detailed, progress, next_steps, issues",
                break_loop=False
            )
    
    async def get_workflow_summary(self) -> Response:
        """Get a high-level workflow summary"""
        state = self.get_state()
        
        if not state or not state.plan.tasks:
            return Response(
                message="No active workflow found. Use the swe_orchestrator tool to start a new workflow.",
                break_loop=False
            )
        
        total_tasks = len(state.plan.tasks)
        completed_tasks = len([t for t in state.plan.tasks if t.status == "completed"])
        in_progress_tasks = len([t for t in state.plan.tasks if t.status == "in-progress"])
        failed_tasks = len([t for t in state.plan.tasks if t.status == "failed"])
        
        progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        summary = f"""
🎯 **SWE Workflow Summary**

**Goal**: {state.plan.goal}
**Progress**: {completed_tasks}/{total_tasks} tasks complete ({progress_percent}%)

**Task Status**:
- ✅ Completed: {completed_tasks}
- 🔄 In Progress: {in_progress_tasks}  
- ❌ Failed: {failed_tasks}
- ⏳ Pending: {total_tasks - completed_tasks - in_progress_tasks - failed_tasks}

**Review Status**: {"✅ Passed" if state.review_feedback.passed else "⏳ Pending" if not state.review_feedback.issues else "❌ Issues Found"}
"""
        
        return Response(message=summary.strip(), break_loop=False)
    
    async def get_detailed_status(self) -> Response:
        """Get detailed status of all tasks"""
        state = self.get_state()
        
        if not state or not state.plan.tasks:
            return Response(
                message="No active workflow found.",
                break_loop=False
            )
        
        status_report = [f"📋 **Detailed Task Status for**: {state.plan.goal}\n"]
        
        for task in state.plan.tasks:
            status_icon = {
                "completed": "✅",
                "in-progress": "🔄", 
                "failed": "❌",
                "pending": "⏳"
            }.get(task.status, "❓")
            
            task_line = f"{status_icon} **Task {task.id}**: {task.description}"
            if task.error_message:
                task_line += f" (Error: {task.error_message})"
                
            status_report.append(task_line)
        
        return Response(message="\n".join(status_report), break_loop=False)
    
    async def get_progress_percentage(self) -> Response:
        """Get workflow progress as percentage"""
        state = self.get_state()
        
        if not state or not state.plan.tasks:
            return Response(message="0% - No active workflow", break_loop=False)
        
        completed = len([t for t in state.plan.tasks if t.status == "completed"])
        total = len(state.plan.tasks)
        percentage = int((completed / total) * 100) if total > 0 else 0
        
        return Response(message=f"{percentage}% complete ({completed}/{total} tasks)", break_loop=False)
    
    async def get_next_steps(self) -> Response:
        """Get recommended next steps"""
        state = self.get_state()
        
        if not state or not state.plan.tasks:
            return Response(
                message="**Next Steps**: Start a workflow using the swe_orchestrator tool",
                break_loop=False
            )
        
        # Check for failed tasks first
        failed_tasks = [t for t in state.plan.tasks if t.status == "failed"]
        if failed_tasks:
            return Response(
                message=f"**Next Steps**: Address {len(failed_tasks)} failed task(s) before continuing",
                break_loop=False
            )
        
        # Check for next pending task
        next_task = state.plan.get_next_pending_task()
        if next_task:
            return Response(
                message=f"**Next Steps**: Execute Task {next_task.id} - {next_task.description}",
                break_loop=False
            )
        
        # Check if review is needed
        completed_tasks = [t for t in state.plan.tasks if t.status == "completed"]
        if completed_tasks and not state.review_feedback.passed:
            return Response(
                message="**Next Steps**: Run code review to validate completed implementation",
                break_loop=False
            )
        
        return Response(
            message="**Next Steps**: All tasks complete! 🎉",
            break_loop=False
        )
    
    async def get_blocking_issues(self) -> Response:
        """Get any blocking issues in the workflow"""
        state = self.get_state()
        
        if not state or not state.plan.tasks:
            return Response(message="No workflow active", break_loop=False)
        
        issues = []
        
        # Check for failed tasks
        failed_tasks = [t for t in state.plan.tasks if t.status == "failed"]
        if failed_tasks:
            for task in failed_tasks:
                issues.append(f"❌ Task {task.id} failed: {task.error_message or 'Unknown error'}")
        
        # Check for review issues
        if state.review_feedback.issues:
            issues.extend([f"🔍 Review issue: {issue}" for issue in state.review_feedback.issues])
        
        if not issues:
            return Response(message="✅ No blocking issues found", break_loop=False)
        
        return Response(
            message="🚫 **Blocking Issues**:\n" + "\n".join(issues),
            break_loop=False
        )
    
    def get_state(self) -> GraphState:
        """Get current workflow state"""
        state = self.agent.get_data("swe_state")
        if not state:
            # Try to restore from dict format
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict:
                from python.helpers.swe_graph_state import GraphState
                state = GraphState.from_dict(state_dict)
        return state