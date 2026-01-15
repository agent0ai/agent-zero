"""
Workflow Engine Tool - Orchestrate structured workflows with stages, gates, and training
Manages workflow execution from design through production and support phases
"""

from python.helpers.tool import Tool, Response
from python.helpers import files
from typing import Any


class WorkflowEngine(Tool):
    """
    Tool for managing structured workflows with defined stages and training paths.

    Supports complete product lifecycles: design → poc → mvp → production → support → upgrade
    Includes skill tracking, learning paths, and progress monitoring.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data: Any | None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        from instruments.custom.workflow_engine.workflow_manager import WorkflowEngineManager

        db_path = files.get_abs_path("./instruments/custom/workflow_engine/data/workflow.db")
        self.manager = WorkflowEngineManager(db_path)

    async def execute(self, **kwargs):
        action = self.args.get("action", "").lower()

        action_map = {
            # Workflow Management
            "create_workflow": self._create_workflow,
            "get_workflow": self._get_workflow,
            "list_workflows": self._list_workflows,
            "delete_workflow": self._delete_workflow,
            "clone_workflow": self._clone_workflow,
            "get_version_history": self._get_workflow_history,
            "rollback_workflow": self._rollback_workflow,

            # Workflow Execution
            "start_workflow": self._start_workflow,
            "get_status": self._get_status,
            "advance_stage": self._advance_stage,
            "approve_stage": self._approve_stage,
            "complete_criterion": self._complete_criterion,
            "complete_deliverable": self._complete_deliverable,

            # Task Execution
            "start_task": self._start_task,
            "complete_task": self._complete_task,
            "fail_task": self._fail_task,
            "get_next_task": self._get_next_task,

            # Templates
            "list_templates": self._list_templates,
            "load_template": self._load_template,
            "create_from_template": self._create_from_template,

            # Skills & Training
            "register_skill": self._register_skill,
            "get_skill": self._get_skill,
            "list_skills": self._list_skills,
            "track_skill": self._track_skill,
            "get_agent_skills": self._get_agent_skills,

            # Learning Paths
            "create_learning_path": self._create_learning_path,
            "get_learning_path": self._get_learning_path,
            "list_learning_paths": self._list_learning_paths,

            # History & Stats
            "get_execution_history": self._get_history,
            "get_events": self._get_events,
            "get_stats": self._get_stats,

            # Visualization
            "visualize_workflow": self._visualize_workflow,
            "visualize_progress": self._visualize_progress,
            "visualize_tasks": self._visualize_tasks,
            "visualize_timeline": self._visualize_timeline,
            "visualize_gantt": self._visualize_gantt,
            "dashboard": self._dashboard,
        }

        handler = action_map.get(action)
        if handler:
            return await handler()

        return Response(
            message=self._format_help(),
            break_loop=False
        )

    # ========== Workflow Management ==========

    async def _create_workflow(self):
        """Create a new workflow definition"""
        result = self.manager.create_workflow(
            name=self.args.get("name"),
            stages=self.args.get("stages", []),
            description=self.args.get("description"),
            version=self.args.get("version", "1.0.0"),
            global_context=self.args.get("global_context"),
            settings=self.args.get("settings"),
            is_template=self.args.get("is_template", False),
            required_secrets=self.args.get("required_secrets"),
            changed_by=self.args.get("changed_by", "agent"),
            change_notes=self.args.get("change_notes")
        )
        return Response(
            message=self._format_result(result, "Create Workflow"),
            break_loop=False
        )

    async def _get_workflow(self):
        """Get workflow details"""
        result = self.manager.get_workflow(
            workflow_id=self.args.get("workflow_id"),
            name=self.args.get("name")
        )
        return Response(
            message=self._format_result(result, "Workflow Details"),
            break_loop=False
        )

    async def _list_workflows(self):
        """List all workflows"""
        result = self.manager.list_workflows(
            workflow_type=self.args.get("workflow_type"),
            templates_only=self.args.get("templates_only", False)
        )
        return Response(
            message=self._format_list(result, "Workflows", ["name", "version", "workflow_type", "is_active"]),
            break_loop=False
        )

    async def _delete_workflow(self):
        """Delete a workflow"""
        result = self.manager.delete_workflow(
            workflow_id=self.args.get("workflow_id")
        )
        return Response(
            message=self._format_result(result, "Delete Workflow"),
            break_loop=False
        )

    async def _clone_workflow(self):
        """Clone a workflow"""
        result = self.manager.clone_workflow(
            workflow_id=self.args.get("workflow_id"),
            new_name=self.args.get("new_name")
        )
        return Response(
            message=self._format_result(result, "Clone Workflow"),
            break_loop=False
        )

    async def _get_workflow_history(self):
        """Get history of a workflow"""
        result = self.manager.get_workflow_history(
            name=self.args.get("name")
        )
        return Response(
            message=self._format_list(result, f"History for {self.args.get('name')}", ["version", "created_at", "is_active"]),
            break_loop=False
        )

    async def _rollback_workflow(self):
        """Rollback to a specific version"""
        result = self.manager.rollback_workflow(
            name=self.args.get("name"),
            version=self.args.get("version"),
            changed_by=self.args.get("changed_by", "agent")
        )
        return Response(
            message=self._format_result(result, "Rollback Workflow"),
            break_loop=False
        )

    # ========== Workflow Execution ==========

    async def _start_workflow(self):
        """Start executing a workflow"""
        result = self.manager.start_workflow(
            workflow_id=self.args.get("workflow_id"),
            workflow_name=self.args.get("workflow_name"),
            execution_name=self.args.get("execution_name"),
            context=self.args.get("context")
        )
        return Response(
            message=self._format_result(result, "Start Workflow"),
            break_loop=False
        )

    async def _get_status(self):
        """Get execution status"""
        result = self.manager.get_execution_status(
            execution_id=self.args.get("execution_id")
        )
        return Response(
            message=self._format_execution_status(result),
            break_loop=False
        )

    async def _advance_stage(self):
        """Advance to next stage"""
        result = self.manager.advance_stage(
            execution_id=self.args.get("execution_id"),
            force=self.args.get("force", False)
        )
        return Response(
            message=self._format_result(result, "Advance Stage"),
            break_loop=False
        )

    async def _approve_stage(self):
        """Approve a stage"""
        result = self.manager.approve_stage(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            approved_by=self.args.get("approved_by", "agent"),
            notes=self.args.get("notes")
        )
        return Response(
            message=self._format_result(result, "Approve Stage"),
            break_loop=False
        )

    async def _complete_criterion(self):
        """Mark a criterion as met"""
        result = self.manager.complete_criterion(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            criterion_id=self.args.get("criterion_id"),
            criterion_type=self.args.get("criterion_type", "exit")
        )
        return Response(
            message=self._format_result(result, "Complete Criterion"),
            break_loop=False
        )

    async def _complete_deliverable(self):
        """Mark a deliverable as completed"""
        result = self.manager.complete_deliverable(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            deliverable_id=self.args.get("deliverable_id"),
            artifact_path=self.args.get("artifact_path")
        )
        return Response(
            message=self._format_result(result, "Complete Deliverable"),
            break_loop=False
        )

    # ========== Task Execution ==========

    async def _start_task(self):
        """Start a task"""
        result = self.manager.start_task(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            task_id=self.args.get("task_id"),
            input_data=self.args.get("input_data"),
            assigned_to=self.args.get("assigned_to")
        )
        return Response(
            message=self._format_result(result, "Start Task"),
            break_loop=False
        )

    async def _complete_task(self):
        """Complete a task"""
        result = self.manager.complete_task(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            task_id=self.args.get("task_id"),
            output_data=self.args.get("output_data")
        )
        return Response(
            message=self._format_result(result, "Complete Task"),
            break_loop=False
        )

    async def _fail_task(self):
        """Mark a task as failed"""
        result = self.manager.fail_task(
            execution_id=self.args.get("execution_id"),
            stage_id=self.args.get("stage_id"),
            task_id=self.args.get("task_id"),
            error=self.args.get("error"),
            retry=self.args.get("retry", False)
        )
        return Response(
            message=self._format_result(result, "Fail Task"),
            break_loop=False
        )

    async def _get_next_task(self):
        """Get next task to execute"""
        result = self.manager.get_next_task(
            execution_id=self.args.get("execution_id")
        )
        return Response(
            message=self._format_result(result, "Next Task"),
            break_loop=False
        )

    # ========== Templates ==========

    async def _list_templates(self):
        """List available templates"""
        result = self.manager.list_templates()
        return Response(
            message=self._format_list(result, "Workflow Templates", ["name", "description", "stages"]),
            break_loop=False
        )

    async def _load_template(self):
        """Load a template"""
        result = self.manager.load_template(
            template_path=self.args.get("template_path")
        )
        return Response(
            message=self._format_result(result, "Load Template"),
            break_loop=False
        )

    async def _create_from_template(self):
        """Create workflow from template"""
        result = self.manager.create_from_template(
            template_path=self.args.get("template_path"),
            name=self.args.get("name"),
            customizations=self.args.get("customizations")
        )
        return Response(
            message=self._format_result(result, "Create from Template"),
            break_loop=False
        )

    # ========== Skills & Training ==========

    async def _register_skill(self):
        """Register a skill"""
        result = self.manager.register_skill(
            skill_id=self.args.get("skill_id"),
            name=self.args.get("name"),
            category=self.args.get("category"),
            description=self.args.get("description"),
            proficiency_levels=self.args.get("proficiency_levels"),
            prerequisites=self.args.get("prerequisites"),
            related_tools=self.args.get("related_tools")
        )
        return Response(
            message=self._format_result(result, "Register Skill"),
            break_loop=False
        )

    async def _get_skill(self):
        """Get skill details"""
        result = self.manager.get_skill(
            skill_id=self.args.get("skill_id")
        )
        return Response(
            message=self._format_result(result, "Skill Details"),
            break_loop=False
        )

    async def _list_skills(self):
        """List all skills"""
        result = self.manager.list_skills(
            category=self.args.get("category")
        )
        return Response(
            message=self._format_list(result, "Skills", ["skill_id", "name", "category"]),
            break_loop=False
        )

    async def _track_skill(self):
        """Track skill usage"""
        result = self.manager.track_skill_usage(
            agent_id=self.args.get("agent_id", "default"),
            skill_id=self.args.get("skill_id"),
            success=self.args.get("success", True),
            assessment_score=self.args.get("assessment_score")
        )
        return Response(
            message=self._format_result(result, "Track Skill"),
            break_loop=False
        )

    async def _get_agent_skills(self):
        """Get agent's skills"""
        result = self.manager.get_agent_skills(
            agent_id=self.args.get("agent_id", "default")
        )
        return Response(
            message=self._format_list(result, "Agent Skills", ["skill_id", "name", "current_level", "completions"]),
            break_loop=False
        )

    # ========== Learning Paths ==========

    async def _create_learning_path(self):
        """Create a learning path"""
        result = self.manager.create_learning_path(
            path_id=self.args.get("path_id"),
            name=self.args.get("name"),
            target_role=self.args.get("target_role"),
            description=self.args.get("description"),
            modules=self.args.get("modules"),
            estimated_hours=self.args.get("estimated_hours"),
            certification=self.args.get("certification")
        )
        return Response(
            message=self._format_result(result, "Create Learning Path"),
            break_loop=False
        )

    async def _get_learning_path(self):
        """Get learning path details"""
        result = self.manager.get_learning_path(
            path_id=self.args.get("path_id")
        )
        return Response(
            message=self._format_result(result, "Learning Path Details"),
            break_loop=False
        )

    async def _list_learning_paths(self):
        """List learning paths"""
        result = self.manager.list_learning_paths(
            target_role=self.args.get("target_role")
        )
        return Response(
            message=self._format_list(result, "Learning Paths", ["path_id", "name", "target_role"]),
            break_loop=False
        )

    # ========== History & Stats ==========

    async def _get_history(self):
        """Get execution history"""
        result = self.manager.get_execution_history(
            workflow_id=self.args.get("workflow_id"),
            status=self.args.get("status"),
            limit=self.args.get("limit", 50)
        )
        return Response(
            message=self._format_list(result, "Execution History", ["execution_id", "workflow_name", "status", "started_at"]),
            break_loop=False
        )

    async def _get_events(self):
        """Get execution events"""
        result = self.manager.get_execution_events(
            execution_id=self.args.get("execution_id")
        )
        return Response(
            message=self._format_list(result, "Execution Events", ["event_type", "stage_id", "task_id", "timestamp"]),
            break_loop=False
        )

    async def _get_stats(self):
        """Get workflow engine statistics"""
        result = self.manager.get_stats()
        return Response(
            message=self._format_stats(result),
            break_loop=False
        )

    # ========== Visualization ==========

    async def _visualize_workflow(self):
        """Generate workflow diagram"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        workflow = self.manager.get_workflow(
            workflow_id=self.args.get("workflow_id"),
            name=self.args.get("name")
        )

        if "error" in workflow:
            return Response(message=f"**Error:** {workflow['error']}", break_loop=False)

        execution_status = None
        if self.args.get("execution_id"):
            execution_status = self.manager.get_execution_status(self.args["execution_id"])

        diagram = visualizer.generate_workflow_diagram(workflow, execution_status)

        return Response(
            message=f"## Workflow: {workflow['name']}\n\n{diagram}",
            break_loop=False
        )

    async def _visualize_progress(self):
        """Visualize execution progress"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        execution_id = self.args.get("execution_id")
        execution_status = self.manager.get_execution_status(execution_id)

        if "error" in execution_status:
            return Response(message=f"**Error:** {execution_status['error']}", break_loop=False)

        workflow = self.manager.get_workflow(workflow_id=execution_status.get('workflow_id'))
        stages = workflow.get('definition', {}).get('stages', [])

        progress_viz = visualizer.generate_stage_progress(stages, execution_status)
        progress_bar = visualizer.generate_progress_bar(
            execution_status['progress']['stages_completed'],
            execution_status['progress']['stages_total']
        )

        return Response(
            message=f"## Execution Progress\n\n**Overall:** {progress_bar}\n\n{progress_viz}",
            break_loop=False
        )

    async def _visualize_tasks(self):
        """Visualize tasks within a stage"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        workflow = self.manager.get_workflow(
            workflow_id=self.args.get("workflow_id"),
            name=self.args.get("workflow_name")
        )

        if "error" in workflow:
            return Response(message=f"**Error:** {workflow['error']}", break_loop=False)

        stage_id = self.args.get("stage_id")
        stages = workflow.get('definition', {}).get('stages', [])
        stage = next((s for s in stages if s['id'] == stage_id), None)

        if not stage:
            return Response(message=f"**Error:** Stage not found: {stage_id}", break_loop=False)

        task_status = None
        if self.args.get("execution_id"):
            task_status = self.manager.db.get_task_executions(
                self.args["execution_id"], stage_id
            )

        diagram = visualizer.generate_task_diagram(stage, task_status)

        return Response(
            message=f"## Tasks: {stage['name']}\n\n{diagram}",
            break_loop=False
        )

    async def _visualize_timeline(self):
        """Visualize execution timeline"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        execution_id = self.args.get("execution_id")
        execution = self.manager.db.get_execution(execution_id)

        if not execution:
            return Response(message="**Error:** Execution not found", break_loop=False)

        events = self.manager.get_execution_events(execution_id)
        timeline = visualizer.generate_timeline(execution, events)

        return Response(
            message=f"## Execution Timeline\n\n{timeline}",
            break_loop=False
        )

    async def _visualize_gantt(self):
        """Generate Gantt chart for workflow"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        workflow = self.manager.get_workflow(
            workflow_id=self.args.get("workflow_id"),
            name=self.args.get("name")
        )

        if "error" in workflow:
            return Response(message=f"**Error:** {workflow['error']}", break_loop=False)

        gantt = visualizer.generate_gantt(
            workflow,
            start_date=self.args.get("start_date")
        )

        return Response(
            message=f"## Gantt Chart: {workflow['name']}\n\n{gantt}",
            break_loop=False
        )

    async def _dashboard(self):
        """Generate comprehensive dashboard"""
        from instruments.custom.workflow_engine.workflow_visualizer import WorkflowVisualizer
        visualizer = WorkflowVisualizer()

        stats = self.manager.get_stats()
        recent = self.manager.get_execution_history(limit=5)
        skills = self.manager.get_agent_skills(
            agent_id=self.args.get("agent_id", "default")
        )

        dashboard = visualizer.generate_dashboard(stats, recent, skills)

        return Response(
            message=dashboard,
            break_loop=False
        )

    # ========== Formatting Helpers ==========

    def _format_result(self, result: dict, title: str) -> str:
        """Format a result dictionary"""
        if "error" in result:
            return f"## {title}\n\n**Error:** {result['error']}"

        lines = [f"## {title}\n"]
        for key, value in result.items():
            if isinstance(value, dict):
                lines.append(f"**{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"**{key}:** {len(value)} items")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)

    def _format_list(self, items: list, title: str, columns: list) -> str:
        """Format a list of items as a table"""
        if not items:
            return f"## {title}\n\nNo items found."

        lines = [f"## {title}\n"]
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join(["---"] * len(columns)) + " |")

        for item in items:
            row = []
            for col in columns:
                val = item.get(col, "")
                if isinstance(val, list):
                    val = f"{len(val)} items"
                elif isinstance(val, dict):
                    val = "..."
                row.append(str(val)[:50])
            lines.append("| " + " | ".join(row) + " |")

        lines.append(f"\n*Total: {len(items)} items*")
        return "\n".join(lines)

    def _format_execution_status(self, status: dict) -> str:
        """Format execution status with progress visualization"""
        if "error" in status:
            return f"## Execution Status\n\n**Error:** {status['error']}"

        progress = status.get('progress', {})
        pct = progress.get('percentage', 0)
        bar_filled = int(pct / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)

        lines = [
            "## Execution Status\n",
            f"**Workflow:** {status.get('workflow_name')}",
            f"**Status:** {status.get('status')}",
            f"**Current Stage:** {status.get('current_stage')}",
            f"**Current Task:** {status.get('current_task', 'None')}",
            "",
            f"**Progress:** [{bar}] {pct}%",
            f"Stages: {progress.get('stages_completed', 0)}/{progress.get('stages_total', 0)}",
            "",
            f"**Started:** {status.get('started_at')}"
        ]

        # Add stage details
        if status.get('stage_details'):
            lines.append("\n### Stage Progress")
            for stage in status['stage_details']:
                icon = "✓" if stage['status'] == 'completed' else ("▶" if stage['status'] == 'in_progress' else "○")
                lines.append(f"{icon} {stage['stage_id']}: {stage['status']}")

        return "\n".join(lines)

    def _format_stats(self, stats: dict) -> str:
        """Format statistics"""
        lines = [
            "## Workflow Engine Statistics\n",
            f"**Total Workflows:** {stats.get('total_workflows', 0)}",
            f"**Workflow Templates:** {stats.get('workflow_templates', 0)}",
            f"**Total Executions:** {stats.get('total_executions', 0)}",
            f"**Total Skills:** {stats.get('total_skills', 0)}",
            f"**Learning Paths:** {stats.get('total_learning_paths', 0)}",
        ]

        if stats.get('executions_by_status'):
            lines.append("\n### Executions by Status")
            for status, count in stats['executions_by_status'].items():
                lines.append(f"- {status}: {count}")

        return "\n".join(lines)

    def _format_help(self) -> str:
        """Format help message"""
        return """## Workflow Engine Tool

Orchestrate structured workflows with stages, gates, and training paths.

### Workflow Management
- `create_workflow` - Create a new workflow definition
- `get_workflow` - Get workflow details
- `list_workflows` - List all workflows
- `delete_workflow` - Delete a workflow
- `clone_workflow` - Clone a workflow
- `get_version_history` - Get workflow version history
- `rollback_workflow` - Rollback to a previous version

### Workflow Execution
- `start_workflow` - Start executing a workflow
- `get_status` - Get current execution status
- `advance_stage` - Advance to next stage
- `approve_stage` - Approve a stage
- `complete_criterion` - Mark criterion as met
- `complete_deliverable` - Mark deliverable complete

### Task Execution
- `start_task` - Start a task
- `complete_task` - Complete a task
- `fail_task` - Mark task as failed
- `get_next_task` - Get next available task

### Templates
- `list_templates` - List available templates
- `load_template` - Load a template file
- `create_from_template` - Create workflow from template

### Skills & Training
- `register_skill` - Register a new skill
- `get_skill` - Get skill details
- `list_skills` - List all skills
- `track_skill` - Track skill usage
- `get_agent_skills` - Get agent's skill progress

### Learning Paths
- `create_learning_path` - Create a learning path
- `get_learning_path` - Get learning path details
- `list_learning_paths` - List all learning paths

### History & Stats
- `get_execution_history` - Get execution history
- `get_events` - Get execution events
- `get_stats` - Get workflow engine statistics

### Visualization
- `visualize_workflow` - Generate workflow diagram (Mermaid)
- `visualize_progress` - Visualize stage progress
- `visualize_tasks` - Visualize task dependencies
- `visualize_timeline` - Execution timeline
- `visualize_gantt` - Generate Gantt chart
- `dashboard` - Comprehensive dashboard view
"""
