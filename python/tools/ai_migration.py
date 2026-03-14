"""
AI Migration Tool for Agent Jumbo
Analyze business processes and design human-AI collaboration workflows
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class AIMigration(Tool):
    """
    Agent Jumbo tool for AI business migration.
    Analyze processes, classify tasks, design workflows, and generate roadmaps.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        from instruments.custom.ai_migration.migration_manager import MigrationManager

        db_path = files.get_abs_path("./instruments/custom/ai_migration/data/ai_migration.db")
        self.manager = MigrationManager(db_path)

    async def execute(self, **kwargs):
        """Execute AI migration action"""

        action = self.args.get("action", "").lower()

        action_handlers = {
            # Assessment
            "start_assessment": self._start_assessment,
            "get_assessment": self._get_assessment,
            "list_projects": self._list_projects,
            # Process management
            "add_process": self._add_process,
            "list_processes": self._list_processes,
            "get_process": self._get_process,
            # Task management
            "add_task": self._add_task,
            "list_tasks": self._list_tasks,
            # Analysis
            "analyze_process": self._analyze_process,
            "classify_tasks": self._classify_tasks,
            # Workflow design
            "design_workflow": self._design_workflow,
            "list_workflows": self._list_workflows,
            "get_workflow": self._get_workflow,
            # Roadmap
            "generate_roadmap": self._generate_roadmap,
            "get_roadmap": self._get_roadmap,
            # ROI
            "project_roi": self._project_roi,
            # Quick wins
            "identify_quick_wins": self._identify_quick_wins,
            # Reporting
            "generate_report": self._generate_report,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Assessment ==========

    async def _start_assessment(self):
        """Start a new business migration assessment"""
        business_name = self.args.get("business_name")
        customer_id = self.args.get("customer_id")
        industry = self.args.get("industry")

        if not business_name:
            return Response(message="Error: business_name is required", break_loop=False)

        # Get optional fields
        kwargs = {
            "company_size": self.args.get("company_size"),
            "current_tech_stack": self.args.get("current_tech_stack", []),
            "pain_points": self.args.get("pain_points", []),
            "goals": self.args.get("goals", []),
            "budget_range": self.args.get("budget_range"),
            "timeline": self.args.get("timeline"),
        }

        result = self.manager.start_assessment(
            business_name=business_name, customer_id=customer_id, industry=industry, **kwargs
        )

        lines = [f"## Assessment Started: {result['business_name']}\n"]
        lines.append(f"**Project ID:** {result['project_id']}")
        lines.append(f"**Status:** {result['status']}")
        lines.append("\n### Next Steps:")
        for step in result["next_steps"]:
            lines.append(f"1. {step}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_assessment(self):
        """Get assessment summary"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.get_assessment_summary(project_id)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Assessment: {result['business_name']}\n"]
        lines.append(f"**Industry:** {result.get('industry', 'N/A')}")
        lines.append(f"**Status:** {result['status']}")
        lines.append(f"**Assessment Score:** {result.get('assessment_score', 'N/A')}/100")

        lines.append("\n### Summary")
        s = result["summary"]
        lines.append(f"- Processes: {s['total_processes']}")
        lines.append(f"- Tasks: {s['total_tasks']}")
        lines.append(f"- Current Hours/Month: {s['total_current_hours_monthly']}")
        lines.append(f"- Avg Automation Score: {s['average_automation_score']}/100")

        lines.append("\n### Task Breakdown")
        tb = result["task_breakdown"]
        lines.append(f"- Fully Automatable: {tb['fully_automatable']}")
        lines.append(f"- AI-Assisted: {tb['ai_assisted']}")
        lines.append(f"- Human Required: {tb['human_required']}")
        lines.append(f"- Unanalyzed: {tb['unanalyzed']}")

        if result["processes"]:
            lines.append("\n### Processes")
            for p in result["processes"]:
                score = p.get("automation_score", "N/A")
                lines.append(f"- **{p['name']}** ({p.get('department', 'N/A')}) - Score: {score}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_projects(self):
        """List migration projects"""
        customer_id = self.args.get("customer_id")
        status = self.args.get("status")

        projects = self.manager.db.list_projects(customer_id=customer_id, status=status)

        if not projects:
            return Response(message="No migration projects found.", break_loop=False)

        lines = ["## Migration Projects\n"]
        for p in projects:
            lines.append(f"### {p['business_name']} (ID: {p['project_id']})")
            lines.append(f"- Industry: {p.get('industry', 'N/A')}")
            lines.append(f"- Status: {p.get('status')}")
            lines.append(f"- Created: {p['created_at']}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Process Management ==========

    async def _add_process(self):
        """Add a business process"""
        project_id = self.args.get("project_id")
        name = self.args.get("name")

        if not project_id or not name:
            return Response(message="Error: project_id and name are required", break_loop=False)

        kwargs = {
            "description": self.args.get("description"),
            "department": self.args.get("department"),
            "owner": self.args.get("owner"),
            "frequency": self.args.get("frequency"),
            "volume_per_period": self.args.get("volume_per_period"),
            "current_time_hours": self.args.get("current_time_hours"),
            "current_cost": self.args.get("current_cost"),
            "pain_points": self.args.get("pain_points", []),
            "systems_used": self.args.get("systems_used", []),
            "priority": self.args.get("priority", "medium"),
        }

        result = self.manager.add_process(project_id, name, **kwargs)

        return Response(message=self._format_result(result, "Process Added"), break_loop=False)

    async def _list_processes(self):
        """List processes for a project"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        processes = self.manager.db.list_processes(project_id)

        if not processes:
            return Response(message="No processes found.", break_loop=False)

        lines = ["## Business Processes\n"]
        for p in processes:
            score = p.get("automation_score")
            score_str = f"{score}/100" if score else "Not analyzed"
            lines.append(f"### {p['name']} (ID: {p['process_id']})")
            lines.append(f"- Department: {p.get('department', 'N/A')}")
            lines.append(f"- Automation Score: {score_str}")
            lines.append(f"- Current Time: {p.get('current_time_hours', 0)} hours/month")
            lines.append(f"- Status: {p.get('status')}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_process(self):
        """Get process details"""
        process_id = self.args.get("process_id")

        if not process_id:
            return Response(message="Error: process_id is required", break_loop=False)

        process = self.manager.db.get_process(process_id)
        if not process:
            return Response(message=f"Process not found: {process_id}", break_loop=False)

        tasks = self.manager.db.list_tasks(process_id)

        lines = [f"## Process: {process['name']}\n"]
        lines.append(f"**Department:** {process.get('department', 'N/A')}")
        lines.append(f"**Owner:** {process.get('owner', 'N/A')}")
        lines.append(f"**Frequency:** {process.get('frequency', 'N/A')}")
        lines.append(f"**Current Time:** {process.get('current_time_hours', 0)} hours/month")
        lines.append(f"**Automation Score:** {process.get('automation_score', 'N/A')}/100")

        if process.get("pain_points"):
            lines.append("\n**Pain Points:**")
            for pp in process["pain_points"]:
                lines.append(f"- {pp}")

        if tasks:
            lines.append(f"\n### Tasks ({len(tasks)})")
            for t in tasks:
                category = t.get("automation_category", "unanalyzed")
                lines.append(f"- {t['name']} [{category}]")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Task Management ==========

    async def _add_task(self):
        """Add a task to a process"""
        process_id = self.args.get("process_id")
        name = self.args.get("name")

        if not process_id or not name:
            return Response(message="Error: process_id and name are required", break_loop=False)

        kwargs = {
            "description": self.args.get("description"),
            "task_type": self.args.get("task_type"),
            "current_owner": self.args.get("current_owner"),
            "time_minutes": self.args.get("time_minutes"),
            "complexity": self.args.get("complexity", "medium"),
            "data_inputs": self.args.get("data_inputs", []),
            "data_outputs": self.args.get("data_outputs", []),
            "tools_used": self.args.get("tools_used", []),
            "decision_points": self.args.get("decision_points", []),
            "error_rate": self.args.get("error_rate"),
            "sequence_order": self.args.get("sequence_order", 0),
        }

        result = self.manager.add_task(process_id, name, **kwargs)

        return Response(message=self._format_result(result, "Task Added"), break_loop=False)

    async def _list_tasks(self):
        """List tasks for a process"""
        process_id = self.args.get("process_id")

        if not process_id:
            return Response(message="Error: process_id is required", break_loop=False)

        tasks = self.manager.db.list_tasks(process_id)

        if not tasks:
            return Response(message="No tasks found.", break_loop=False)

        lines = ["## Process Tasks\n"]
        for t in tasks:
            category = t.get("automation_category", "unanalyzed")
            score = t.get("automation_score", "-")
            lines.append(f"### {t['name']} (ID: {t['task_id']})")
            lines.append(f"- Type: {t.get('task_type', 'N/A')}")
            lines.append(f"- Time: {t.get('time_minutes', 0)} min")
            lines.append(f"- Category: {category}")
            lines.append(f"- Automation Score: {score}/100")
            if t.get("ai_tools_suggested"):
                lines.append(f"- Suggested Tools: {', '.join(t['ai_tools_suggested'][:3])}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Analysis ==========

    async def _analyze_process(self):
        """Analyze a process for automation potential"""
        process_id = self.args.get("process_id")

        if not process_id:
            return Response(message="Error: process_id is required", break_loop=False)

        result = self.manager.analyze_process(process_id)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Analysis: {result['process_name']}\n"]
        lines.append(f"**Automation Score:** {result['automation_score']}/100")
        lines.append(f"**Automation Potential:** {result['automation_percentage']}%")
        lines.append(f"**Total Time:** {result['total_time_minutes']} minutes")
        lines.append(f"**Potential Savings:** {result['potential_savings_minutes']} minutes")

        lines.append("\n### Task Breakdown")
        tb = result["task_breakdown"]
        lines.append(f"- Fully Automatable: {tb['fully_automatable']}")
        lines.append(f"- AI-Assisted: {tb['ai_assisted']}")
        lines.append(f"- Human Required: {tb['human_required']}")

        if result.get("recommendations"):
            lines.append("\n### Recommendations")
            for rec in result["recommendations"]:
                lines.append(f"- {rec}")

        lines.append("\n### Task Analysis")
        for task in result.get("tasks", [])[:10]:
            lines.append(f"- **{task['name']}**: {task['category']} (Score: {task['automation_score']})")
            if task.get("ai_tools"):
                lines.append(f"  Tools: {', '.join(task['ai_tools'][:2])}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _classify_tasks(self):
        """Alias for analyze_process"""
        return await self._analyze_process()

    # ========== Workflow Design ==========

    async def _design_workflow(self):
        """Design an optimized human-AI workflow"""
        process_id = self.args.get("process_id")
        automation_level = self.args.get("automation_level", "balanced")

        if not process_id:
            return Response(message="Error: process_id is required", break_loop=False)

        result = self.manager.design_workflow(process_id, automation_level)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Workflow: {result['name']}\n"]
        lines.append(f"**Process:** {result['process_name']}")
        lines.append(f"**Automation Level:** {result['automation_level']}")

        lines.append("\n### Original vs Optimized")
        orig = result["original_process"]
        opt = result["optimized_workflow"]
        lines.append("| Metric | Original | Optimized |")
        lines.append("|--------|----------|-----------|")
        lines.append(f"| Time (hours) | {orig['time_hours']} | {opt['time_hours']} |")
        if orig.get("cost"):
            lines.append(f"| Cost | ${orig['cost']:.0f} | ${opt['cost']:.0f} |")
        lines.append(f"| Human Touchpoints | - | {opt['human_touchpoints']} |")
        lines.append(f"| AI Touchpoints | 0 | {opt['ai_touchpoints']} |")

        savings = result["savings"]
        lines.append("\n### Savings")
        lines.append(f"- Time: {savings['time_hours']} hours ({savings['time_percentage']}%)")
        if savings.get("cost"):
            lines.append(f"- Cost: ${savings['cost']:.0f}")

        lines.append("\n### Workflow Steps")
        for step in result.get("steps", []):
            owner_icon = "🤖" if step["owner"] == "ai" else "👤" if step["owner"] == "human" else "🤝"
            lines.append(f"{step['step']}. {owner_icon} **{step['name']}** ({step['owner']})")
            if step.get("ai_tools"):
                lines.append(f"   Tools: {', '.join(step['ai_tools'][:2])}")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_workflows(self):
        """List designed workflows"""
        project_id = self.args.get("project_id")
        process_id = self.args.get("process_id")

        workflows = self.manager.db.list_workflows(process_id=process_id, project_id=project_id)

        if not workflows:
            return Response(message="No workflows found.", break_loop=False)

        lines = ["## Designed Workflows\n"]
        for w in workflows:
            lines.append(f"### {w['name']} (ID: {w['workflow_id']})")
            lines.append(f"- Type: {w.get('workflow_type', 'N/A')}")
            lines.append(f"- Automation: {w.get('automation_percentage', 0):.1f}%")
            lines.append(f"- Human/AI Touchpoints: {w.get('human_touchpoints', 0)}/{w.get('ai_touchpoints', 0)}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_workflow(self):
        """Get workflow details"""
        workflow_id = self.args.get("workflow_id")

        if not workflow_id:
            return Response(message="Error: workflow_id is required", break_loop=False)

        workflow = self.manager.db.get_workflow(workflow_id)
        if not workflow:
            return Response(message=f"Workflow not found: {workflow_id}", break_loop=False)

        return Response(message=self._format_result(workflow, f"Workflow: {workflow['name']}"), break_loop=False)

    # ========== Roadmap ==========

    async def _generate_roadmap(self):
        """Generate migration roadmap"""
        project_id = self.args.get("project_id")
        timeline_months = self.args.get("timeline_months", 12)
        budget = self.args.get("budget")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.generate_roadmap(project_id, timeline_months, budget)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Migration Roadmap\n"]
        lines.append(f"**Project:** {result['project_name']}")
        lines.append(f"**Timeline:** {result['timeline_months']} months")

        lines.append("\n### Investment")
        inv = result["investment"]
        lines.append(f"**Total:** ${inv['total']:,.0f}")

        lines.append("\n### Projected ROI")
        roi = result["projected_roi"]
        lines.append(f"- Annual Savings: ${roi['annual_savings']:,.0f}")
        lines.append(f"- Payback Period: {roi['payback_months']} months")
        lines.append(f"- 3-Year ROI: {roi['roi_3_year']}")

        lines.append("\n### Phases")
        for phase in result["phases"]:
            lines.append(f"\n**Phase {phase['phase']}: {phase['name']}** ({phase['duration_months']} months)")
            lines.append(f"{phase['description']}")

        if result.get("quick_wins"):
            lines.append("\n### Quick Wins to Start")
            for qw in result["quick_wins"][:5]:
                lines.append(f"- {qw['name']} ({qw['process']}) - {qw['savings_minutes']} min/month saved")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_roadmap(self):
        """Get roadmap details"""
        roadmap_id = self.args.get("roadmap_id")

        if not roadmap_id:
            return Response(message="Error: roadmap_id is required", break_loop=False)

        roadmap = self.manager.db.get_roadmap(roadmap_id)
        if not roadmap:
            return Response(message=f"Roadmap not found: {roadmap_id}", break_loop=False)

        return Response(message=self._format_result(roadmap, f"Roadmap: {roadmap['name']}"), break_loop=False)

    # ========== ROI ==========

    async def _project_roi(self):
        """Calculate ROI projections"""
        project_id = self.args.get("project_id")
        scenarios = self.args.get("scenarios", ["conservative", "moderate", "aggressive"])

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.project_roi(project_id, scenarios)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## ROI Projections\n"]

        for scenario, data in result["scenarios"].items():
            lines.append(f"### {scenario.title()} Scenario")
            lines.append(f"- Implementation Cost: ${data['implementation_cost']:,.0f}")
            lines.append(f"- Annual Savings: ${data['annual_savings']:,.0f}")
            lines.append(f"- Payback: {data['payback_months']} months")
            lines.append(f"- 3-Year ROI: {data['roi_3_year']}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Quick Wins ==========

    async def _identify_quick_wins(self):
        """Identify quick win opportunities"""
        project_id = self.args.get("project_id")
        max_effort = self.args.get("max_effort", "medium")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.identify_quick_wins(project_id, max_effort)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Quick Wins\n"]
        lines.append(f"**Total Found:** {result['total_quick_wins']}")
        lines.append(f"**Max Effort Filter:** {result['max_effort_filter']}")
        lines.append(f"**Total Potential Savings:** {result['estimated_total_savings_minutes']} min/month")

        lines.append("\n### Top Opportunities")
        for qw in result["quick_wins"][:10]:
            lines.append(f"\n**{qw['name']}** (Process: {qw['process']})")
            lines.append(f"- Score: {qw['automation_score']}/100")
            lines.append(f"- Effort: {qw['effort']}")
            lines.append(f"- Monthly Savings: {qw['savings_minutes']} min")
            if qw.get("ai_tools"):
                lines.append(f"- Tools: {', '.join(qw['ai_tools'][:2])}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Reporting ==========

    async def _generate_report(self):
        """Generate comprehensive report"""
        project_id = self.args.get("project_id")
        format = self.args.get("format", "markdown")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        result = self.manager.generate_report(project_id, format)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        return Response(message=result["report"], break_loop=False)

    # ========== Helpers ==========

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary"""
        lines = [f"## {title}\n"]

        for key, value in data.items():
            if isinstance(value, dict | list):
                lines.append(f"**{key}:** {json.dumps(value, indent=2)}")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)
