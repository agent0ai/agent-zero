"""
Virtual Team Tool for Agent Jumbo
Enables AI-driven multi-agent collaboration
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class VirtualTeam(Tool):
    """
    Agent Jumbo tool for virtual team orchestration.
    Coordinates specialized AI agents (architect, developer, DBA, QA, DevOps, etc.)
    for collaborative software development workflows.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import orchestrator here to avoid circular imports
        from instruments.custom.virtual_team.team_orchestrator import VirtualTeamOrchestrator

        # Initialize orchestrator
        db_path = files.get_abs_path("./instruments/custom/virtual_team/data/virtual_team.db")
        self.orchestrator = VirtualTeamOrchestrator(db_path)

    async def execute(self, **kwargs):
        """Execute virtual team action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        if action == "route_task":
            return await self._route_task()
        elif action == "delegate_to_specialist":
            return await self._delegate_to_specialist()
        elif action == "start_workflow":
            return await self._start_workflow()
        elif action == "get_workflow_progress":
            return await self._get_workflow_progress()
        elif action == "coordinate_parallel_tasks":
            return await self._coordinate_parallel_tasks()
        elif action == "escalate_task":
            return await self._escalate_task()
        elif action == "get_task_queue":
            return await self._get_task_queue()
        elif action == "get_agent_workload":
            return await self._get_agent_workload()
        elif action == "get_team_dashboard":
            return await self._get_team_dashboard()
        elif action == "update_task_status":
            return await self._update_task_status()
        elif action == "get_task_details":
            return await self._get_task_details()
        elif action == "list_agents":
            return await self._list_agents()
        elif action == "get_available_workflows":
            return await self._get_available_workflows()
        elif action == "get_available_roles":
            return await self._get_available_roles()
        else:
            return Response(message=f"Unknown action: {action}", break_loop=False)

    async def _route_task(self):
        """Automatically route task to best-suited agent"""
        result = self.orchestrator.route_task(
            task_name=self.args.get("task_name"),
            task_type=self.args.get("task_type"),
            description=self.args.get("description"),
            context=self.args.get("context"),
            priority=self.args.get("priority", "medium"),
            complexity=self.args.get("complexity"),
        )

        return Response(message=self._format_result(result, "Task Routed"), break_loop=False)

    async def _delegate_to_specialist(self):
        """Delegate task to specific specialist role"""
        result = self.orchestrator.delegate_to_specialist(
            task_name=self.args.get("task_name"),
            specialist_role=self.args.get("specialist_role"),
            description=self.args.get("description"),
            context=self.args.get("context"),
            priority=self.args.get("priority", "medium"),
        )

        return Response(message=self._format_result(result, "Task Delegated"), break_loop=False)

    async def _start_workflow(self):
        """Start multi-agent workflow"""
        result = self.orchestrator.start_workflow(
            workflow_name=self.args.get("workflow_name"),
            workflow_type=self.args.get("workflow_type", "custom"),
            customer_id=self.args.get("customer_id"),
            project_id=self.args.get("project_id"),
            template=self.args.get("template"),
            custom_tasks=self.args.get("custom_tasks"),
        )

        return Response(message=self._format_result(result, "Workflow Started"), break_loop=False)

    async def _get_workflow_progress(self):
        """Get workflow progress"""
        workflow_id = self.args.get("workflow_id")
        result = self.orchestrator.get_workflow_progress(workflow_id)

        return Response(message=self._format_result(result, "Workflow Progress"), break_loop=False)

    async def _coordinate_parallel_tasks(self):
        """Coordinate parallel task execution"""
        task_specs = self.args.get("task_specs", [])
        result = self.orchestrator.coordinate_parallel_tasks(task_specs)

        return Response(message=self._format_result(result, "Parallel Tasks Coordinated"), break_loop=False)

    async def _escalate_task(self):
        """Escalate task to different agent"""
        result = self.orchestrator.escalate_task(
            task_id=self.args.get("task_id"),
            escalation_reason=self.args.get("reason"),
            target_role=self.args.get("target_role"),
        )

        return Response(message=self._format_result(result, "Task Escalated"), break_loop=False)

    async def _get_task_queue(self):
        """Get pending task queue"""
        result = self.orchestrator.get_task_queue(role=self.args.get("role"))

        return Response(message=self._format_result(result, "Task Queue"), break_loop=False)

    async def _get_agent_workload(self):
        """Get agent workload"""
        result = self.orchestrator.get_agent_workload(agent_id=self.args.get("agent_id"), role=self.args.get("role"))

        return Response(message=self._format_result(result, "Agent Workload"), break_loop=False)

    async def _get_team_dashboard(self):
        """Get team dashboard"""
        result = self.orchestrator.get_team_dashboard()

        return Response(message=self._format_result(result, "Team Dashboard"), break_loop=False)

    async def _update_task_status(self):
        """Update task status"""
        success = self.orchestrator.db.update_task_status(
            task_id=self.args.get("task_id"),
            status=self.args.get("status"),
            progress_percentage=self.args.get("progress_percentage"),
        )

        result = {"success": success, "task_id": self.args.get("task_id"), "new_status": self.args.get("status")}

        return Response(message=self._format_result(result, "Task Status Updated"), break_loop=False)

    async def _get_task_details(self):
        """Get task details"""
        task_id = self.args.get("task_id")
        result = self.orchestrator.db.get_task(task_id)

        return Response(message=self._format_result(result, "Task Details"), break_loop=False)

    async def _list_agents(self):
        """List all agents"""
        agents = self.orchestrator.db.list_agents(role=self.args.get("role"), status=self.args.get("status", "active"))

        result = {"agents": agents, "count": len(agents)}

        return Response(message=self._format_result(result, "Agent List"), break_loop=False)

    async def _get_available_workflows(self):
        """Get available workflow templates"""
        workflows = self.orchestrator.get_available_workflows()

        result = {"workflows": workflows, "count": len(workflows)}

        return Response(message=self._format_result(result, "Available Workflows"), break_loop=False)

    async def _get_available_roles(self):
        """Get available agent roles"""
        roles = self.orchestrator.get_available_roles()

        result = {"roles": roles, "count": len(roles)}

        return Response(message=self._format_result(result, "Available Roles"), break_loop=False)

    def _format_result(self, result: dict, title: str) -> str:
        """Format result for display"""
        if not result:
            return f"**{title}**: No data"

        if "error" in result:
            return f"**{title} - Error**: {result['error']}"

        # Pretty print JSON result
        formatted = f"**{title}**:\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
        return formatted
