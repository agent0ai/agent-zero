"""
SWE Orchestrator Tool for Agent Zero
Coordinates the multi-agent software engineering workflow
"""

import json
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState, Plan

class SWEOrchestrator(Tool):
    """
    Orchestrates the SWE agent workflow by calling planner, programmer, and reviewer agents in sequence
    """
    
    async def execute(self, **kwargs):
        """Execute the complete SWE workflow"""
        
        user_request = kwargs.get("user_request")
        max_iterations = kwargs.get("max_iterations", 3)
        
        if not user_request:
            return Response(
                message="Error: 'user_request' parameter is required for SWE workflow",
                break_loop=False
            )
        
        try:
            # Initialize the workflow
            workflow_result = await self.run_swe_workflow(user_request, max_iterations)
            return Response(message=workflow_result, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"SWE Workflow failed with error: {str(e)}",
                break_loop=False
            )
    
    async def run_swe_workflow(self, user_request: str, max_iterations: int) -> str:
        """Run the complete SWE workflow"""
        
        # Initialize shared state
        initial_state = GraphState()
        initial_state.plan = Plan(goal=user_request)
        initial_state.current_agent = "orchestrator"
        initial_state.add_history(f"SWE workflow started: {user_request}")
        
        self.agent.set_data("swe_state", initial_state)
        
        results = []
        
        # Step 1: Planning Phase
        results.append("🔍 **Planning Phase**")
        planning_result = await self.run_planner(user_request)
        results.append(planning_result)
        
        # Get updated state after planning
        state = self.agent.get_data("swe_state")
        if not state or not state.plan.tasks:
            return "❌ Planning failed - no tasks generated"
        
        results.append(f"📋 Generated {len(state.plan.tasks)} tasks")
        
        # Step 2: Implementation Phase
        results.append("\n💻 **Implementation Phase**")
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            state = self.agent.get_data("swe_state")
            
            # Check if all tasks are complete
            if state.plan.all_tasks_complete():
                results.append("✅ All tasks completed successfully")
                break
            
            # Find next task to implement
            next_task = state.plan.get_next_pending_task()
            if not next_task:
                # Check for failed tasks
                failed_tasks = [t for t in state.plan.tasks if t.status == "failed"]
                if failed_tasks:
                    results.append(f"❌ Implementation blocked by {len(failed_tasks)} failed task(s)")
                    break
                else:
                    results.append("✅ No more pending tasks")
                    break
            
            results.append(f"\n**Iteration {iteration}: Task {next_task.id}**")
            programming_result = await self.run_programmer(next_task.id, next_task.description)
            results.append(programming_result)
        
        # Step 3: Review Phase
        results.append("\n🔍 **Review Phase**")
        review_result = await self.run_reviewer()
        results.append(review_result)
        
        # Final status
        final_state = self.agent.get_data("swe_state")
        if final_state and final_state.review_feedback.passed:
            results.append("\n🎉 **SWE Workflow Completed Successfully!**")
        else:
            results.append("\n⚠️ **SWE Workflow Completed with Issues**")
        
        return "\n".join(results)
    
    async def run_planner(self, user_request: str) -> str:
        """Run the SWE Planner agent"""
        try:
            # Call planner agent
            planner_message = f"""
Please analyze this software engineering request and create a detailed development plan:

**Request**: {user_request}

Tasks to complete:
1. Parse any project rules from the user message or from files (AGENTS.md, CLAUDE.md, etc.) - use the rules_parser tool with user_message parameter
   - If rules_parser fails, try the diagnostic tool to identify issues: diagnostic(operation="tools")
2. Analyze the current codebase structure using code_execution_tool if needed
3. Create a step-by-step development plan using the plan_manager tool
4. Estimate complexity and identify dependencies

Use your tools to gather context and create a comprehensive plan stored in the GraphState.

**Original User Message** (may contain project rules): {user_request}

**Available Tools**: rules_parser, plan_manager, diagnostic, code_execution_tool, response
"""
            
            # Create subordinate planner agent
            from agent import Agent, UserMessage
            planner = Agent(self.agent.number + 1, self.agent.config, self.agent.context)
            planner.config.profile = "swe-planner"
            
            # Transfer state to planner - serialize to ensure clean copy
            current_state = self.agent.get_data("swe_state")
            if current_state:
                # Convert to dict for clean transfer
                state_dict = current_state.to_dict() if hasattr(current_state, 'to_dict') else current_state
                planner.set_data("swe_state_dict", state_dict)
                # Also set the object for direct access
                planner.set_data("swe_state", current_state)
            
            # Run planner
            planner.hist_add_user_message(UserMessage(message=planner_message))
            result = await planner.monologue()
            
            # Get updated state from planner - try both formats
            updated_state = planner.get_data("swe_state")
            if not updated_state:
                # Try to restore from dict format
                state_dict = planner.get_data("swe_state_dict")
                if state_dict:
                    from python.helpers.swe_graph_state import GraphState
                    updated_state = GraphState.from_dict(state_dict)
            
            if updated_state:
                self.agent.set_data("swe_state", updated_state)
                # Also store as dict for backup
                if hasattr(updated_state, 'to_dict'):
                    self.agent.set_data("swe_state_dict", updated_state.to_dict())
            
            return f"Planning completed: {len(updated_state.plan.tasks) if updated_state else 0} tasks generated"
            
        except Exception as e:
            return f"Planning failed: {str(e)}"
    
    async def run_programmer(self, task_id: int, task_description: str) -> str:
        """Run the SWE Programmer agent for a specific task"""
        try:
            # Call programmer agent  
            programmer_message = f"""
Please implement the following task from the development plan:

**Task {task_id}**: {task_description}

Steps to follow:
1. Update task status to 'in-progress' using task_manager
2. Use file_operations and grep tools to understand the codebase
3. Implement the required functionality
4. Run tests to validate the implementation
5. Mark the task as 'completed' with artifacts

The GraphState contains the full context and plan. Focus only on this specific task.
"""
            
            # Create subordinate programmer agent
            from agent import Agent, UserMessage
            programmer = Agent(self.agent.number + 1, self.agent.config, self.agent.context)
            programmer.config.profile = "swe-programmer"
            
            # Transfer state to programmer - serialize to ensure clean copy
            current_state = self.agent.get_data("swe_state")
            if current_state:
                # Convert to dict for clean transfer
                state_dict = current_state.to_dict() if hasattr(current_state, 'to_dict') else current_state
                programmer.set_data("swe_state_dict", state_dict)
                # Also set the object for direct access
                programmer.set_data("swe_state", current_state)
            
            # Run programmer
            programmer.hist_add_user_message(UserMessage(message=programmer_message))
            result = await programmer.monologue()
            
            # Get updated state from programmer - try both formats
            updated_state = programmer.get_data("swe_state")
            if not updated_state:
                # Try to restore from dict format
                state_dict = programmer.get_data("swe_state_dict")
                if state_dict:
                    from python.helpers.swe_graph_state import GraphState
                    updated_state = GraphState.from_dict(state_dict)
            
            if updated_state:
                self.agent.set_data("swe_state", updated_state)
                # Also store as dict for backup
                if hasattr(updated_state, 'to_dict'):
                    self.agent.set_data("swe_state_dict", updated_state.to_dict())
                
                # Check task status
                task = None
                for t in updated_state.plan.tasks:
                    if t.id == task_id:
                        task = t
                        break
                
                if task:
                    if task.status == "completed":
                        return f"✅ Task {task_id} completed successfully"
                    elif task.status == "failed":
                        return f"❌ Task {task_id} failed: {task.error_message or 'Unknown error'}"
                    else:
                        return f"⚠️ Task {task_id} status: {task.status}"
            
            return f"Task {task_id} processing completed"
            
        except Exception as e:
            return f"❌ Task {task_id} failed with exception: {str(e)}"
    
    async def run_reviewer(self) -> str:
        """Run the SWE Reviewer agent"""
        try:
            # Get current state for context
            state = self.agent.get_data("swe_state")
            completed_tasks = [t for t in state.plan.tasks if t.status == "completed"] if state else []
            
            # Call reviewer agent
            reviewer_message = f"""
Please review the implemented software changes and validate quality:

**Original Goal**: {state.plan.goal if state else 'Unknown'}
**Completed Tasks**: {len(completed_tasks)}

Review checklist:
1. Verify all requirements are implemented correctly
2. Run tests and check coverage
3. Review code quality and standards compliance
4. Check for security vulnerabilities
5. Validate documentation
6. Assess performance implications

The GraphState contains all implementation details. Provide a comprehensive review with pass/fail status and specific feedback.
"""
            
            # Create subordinate reviewer agent
            from agent import Agent, UserMessage
            reviewer = Agent(self.agent.number + 1, self.agent.config, self.agent.context)
            reviewer.config.profile = "swe-reviewer"
            
            # Transfer state to reviewer - serialize to ensure clean copy
            current_state = self.agent.get_data("swe_state")
            if current_state:
                # Convert to dict for clean transfer
                state_dict = current_state.to_dict() if hasattr(current_state, 'to_dict') else current_state
                reviewer.set_data("swe_state_dict", state_dict)
                # Also set the object for direct access
                reviewer.set_data("swe_state", current_state)
            
            # Run reviewer
            reviewer.hist_add_user_message(UserMessage(message=reviewer_message))
            result = await reviewer.monologue()
            
            # Get updated state from reviewer - try both formats
            updated_state = reviewer.get_data("swe_state")
            if not updated_state:
                # Try to restore from dict format
                state_dict = reviewer.get_data("swe_state_dict")
                if state_dict:
                    from python.helpers.swe_graph_state import GraphState
                    updated_state = GraphState.from_dict(state_dict)
            
            if updated_state:
                self.agent.set_data("swe_state", updated_state)
                # Also store as dict for backup
                if hasattr(updated_state, 'to_dict'):
                    self.agent.set_data("swe_state_dict", updated_state.to_dict())
                
                if updated_state.review_feedback.passed:
                    return "✅ Code review passed - implementation meets quality standards"
                else:
                    issues = len(updated_state.review_feedback.issues)
                    return f"⚠️ Code review identified {issues} issue(s) requiring attention"
            
            return "Code review completed"
            
        except Exception as e:
            return f"Code review failed: {str(e)}"
    
    def get_workflow_summary(self) -> str:
        """Generate a summary of the workflow execution"""
        state = self.agent.get_data("swe_state")
        if not state:
            return "No workflow state available"
        
        summary = []
        summary.append(f"**Goal**: {state.plan.goal}")
        summary.append(f"**Total Tasks**: {len(state.plan.tasks)}")
        
        if state.plan.tasks:
            completed = sum(1 for t in state.plan.tasks if t.status == "completed")
            failed = sum(1 for t in state.plan.tasks if t.status == "failed")
            pending = sum(1 for t in state.plan.tasks if t.status == "pending")
            
            summary.append(f"**Completed**: {completed}")
            summary.append(f"**Failed**: {failed}")
            summary.append(f"**Pending**: {pending}")
        
        if state.review_feedback:
            summary.append(f"**Review Status**: {'Passed' if state.review_feedback.passed else 'Issues Found'}")
            if state.review_feedback.issues:
                summary.append(f"**Issues**: {len(state.review_feedback.issues)}")
        
        summary.append(f"**Iterations**: {state.iteration_count}")
        
        return "\n".join(summary)