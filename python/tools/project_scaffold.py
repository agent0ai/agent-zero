"""
Project Scaffold Tool for Agent Jumbo
Generate complete project structures from templates
"""

import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class ProjectScaffold(Tool):
    """
    Agent Jumbo tool for project scaffolding.
    Generate complete project structures from templates with app_spec integration.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.project_scaffold.scaffold_manager import ScaffoldManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/project_scaffold/data/project_scaffold.db")
        templates_dir = files.get_abs_path("./instruments/custom/project_scaffold/templates")
        self.manager = ScaffoldManager(db_path, templates_dir)

    async def execute(self, **kwargs):
        """Execute project scaffold action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Project generation
            "scaffold_project": self._scaffold_project,
            "preview_scaffold": self._preview_scaffold,
            # Template management
            "list_templates": self._list_templates,
            "get_template": self._get_template,
            "create_template": self._create_template,
            # App spec
            "generate_app_spec": self._generate_app_spec,
            # Components
            "add_component": self._add_component,
            # Project tracking
            "list_projects": self._list_projects,
            "get_project": self._get_project,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Project Generation ==========

    async def _scaffold_project(self):
        """Generate a new project from a template"""
        template_name = self.args.get("template")
        project_name = self.args.get("name")
        output_path = self.args.get("output_path")
        variables = self.args.get("variables", {})
        customer_id = self.args.get("customer_id")
        generate_app_spec = self.args.get("generate_app_spec", True)

        if not template_name:
            return Response(message="Error: template is required", break_loop=False)
        if not project_name:
            return Response(message="Error: name is required", break_loop=False)
        if not output_path:
            return Response(message="Error: output_path is required", break_loop=False)

        result = self.manager.scaffold_project(
            template_name=template_name,
            project_name=project_name,
            output_path=output_path,
            variables=variables,
            customer_id=customer_id,
            generate_app_spec=generate_app_spec,
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        # Format success response
        lines = [f"## Project Created: {result['project_name']}\n"]
        lines.append(f"**Location:** {result['output_path']}")
        lines.append(f"**Template:** {result['template']}")
        lines.append(f"**Files Created:** {result['files_created']}")

        if result.get("app_spec_path"):
            lines.append(f"**App Spec:** {result['app_spec_path']}")

        lines.append("\n### Files:")
        for f in result.get("files", [])[:15]:
            lines.append(f"- {f}")
        if result["files_created"] > 15:
            lines.append(f"... and {result['files_created'] - 15} more")

        return Response(message="\n".join(lines), break_loop=False)

    async def _preview_scaffold(self):
        """Preview what files would be generated"""
        template_name = self.args.get("template")
        variables = self.args.get("variables", {})

        if not template_name:
            return Response(message="Error: template is required", break_loop=False)

        result = self.manager.preview_scaffold(template_name, variables)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Scaffold Preview: {result['template']}\n"]
        lines.append(f"**Type:** {result['type']}")
        lines.append(f"**Framework:** {result.get('framework', 'N/A')}")

        lines.append("\n### Variables:")
        for key, value in result.get("variables", {}).items():
            lines.append(f"- {key}: {value}")

        lines.append("\n### Files to be created:")
        for f in result.get("files", []):
            lines.append(f"- {f}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Template Management ==========

    async def _list_templates(self):
        """List available templates"""
        template_type = self.args.get("type")
        language = self.args.get("language")
        framework = self.args.get("framework")

        templates = self.manager.list_templates(template_type=template_type, language=language, framework=framework)

        if not templates:
            return Response(message="No templates found.", break_loop=False)

        lines = ["## Available Templates\n"]

        # Group by type
        by_type = {}
        for t in templates:
            ttype = t["type"]
            if ttype not in by_type:
                by_type[ttype] = []
            by_type[ttype].append(t)

        for ttype, tlist in by_type.items():
            lines.append(f"### {ttype.replace('_', ' ').title()}")
            for t in tlist:
                builtin = " (built-in)" if t.get("builtin") else ""
                lines.append(f"- **{t['name']}**{builtin}")
                lines.append(f"  {t['language']}/{t.get('framework', 'generic')} - {t.get('description', '')[:60]}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_template(self):
        """Get template details"""
        name = self.args.get("name")

        if not name:
            return Response(message="Error: name is required", break_loop=False)

        template = self.manager.get_template(name)
        if not template:
            return Response(message=f"Template not found: {name}", break_loop=False)

        lines = [f"## Template: {template['name']}\n"]
        lines.append(f"**Type:** {template['type']}")
        lines.append(f"**Language:** {template['language']}")
        lines.append(f"**Framework:** {template.get('framework', 'N/A')}")
        lines.append(f"**Description:** {template.get('description', '')}")

        if template.get("tags"):
            lines.append(f"**Tags:** {', '.join(template['tags'])}")

        if template.get("variables"):
            lines.append("\n### Variables:")
            for key, config in template["variables"].items():
                if isinstance(config, dict):
                    required = "(required)" if config.get("required") else "(optional)"
                    default = f" [default: {config.get('default')}]" if "default" in config else ""
                    lines.append(f"- `{key}` {required}{default}")
                else:
                    lines.append(f"- `{key}`")

        return Response(message="\n".join(lines), break_loop=False)

    async def _create_template(self):
        """Create a template from an existing project"""
        project_path = self.args.get("project_path")
        template_name = self.args.get("name")
        description = self.args.get("description", "")

        if not project_path:
            return Response(message="Error: project_path is required", break_loop=False)
        if not template_name:
            return Response(message="Error: name is required", break_loop=False)

        result = self.manager.create_template_from_project(
            project_path=project_path, template_name=template_name, description=description
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        return Response(message=self._format_result(result, "Template Created"), break_loop=False)

    # ========== App Spec ==========

    async def _generate_app_spec(self):
        """Generate app_spec.json for a project"""
        project_path = self.args.get("project_path")
        analyze_code = self.args.get("analyze_code", True)

        if not project_path:
            return Response(message="Error: project_path is required", break_loop=False)

        result = self.manager.generate_app_spec(project_path, analyze_code)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## App Spec Generated\n"]
        lines.append(f"**Path:** {result['app_spec_path']}")
        lines.append("\n### Content:")
        lines.append(f"```json\n{json.dumps(result['content'], indent=2)}\n```")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Components ==========

    async def _add_component(self):
        """Add a component to an existing project"""
        project_path = self.args.get("project_path")
        component_type = self.args.get("component_type")
        name = self.args.get("name")

        if not project_path:
            return Response(message="Error: project_path is required", break_loop=False)
        if not component_type:
            return Response(
                message="Error: component_type is required (page, api_endpoint, model, service, test)", break_loop=False
            )
        if not name:
            return Response(message="Error: name is required", break_loop=False)

        # Get extra args
        extra_args = {
            k: v for k, v in self.args.items() if k not in ["action", "project_path", "component_type", "name"]
        }

        result = self.manager.add_component(
            project_path=project_path, component_type=component_type, name=name, **extra_args
        )

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        return Response(message=self._format_result(result, "Component Added"), break_loop=False)

    # ========== Project Tracking ==========

    async def _list_projects(self):
        """List generated projects"""
        customer_id = self.args.get("customer_id")
        template_id = self.args.get("template_id")

        projects = self.manager.db.list_projects(customer_id=customer_id, template_id=template_id)

        if not projects:
            return Response(message="No projects found.", break_loop=False)

        lines = ["## Generated Projects\n"]
        for p in projects:
            lines.append(f"### {p['name']} (ID: {p['project_id']})")
            lines.append(f"- Path: {p['output_path']}")
            lines.append(f"- Status: {p.get('status', 'created')}")
            lines.append(f"- Created: {p['created_at']}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_project(self):
        """Get project details"""
        project_id = self.args.get("project_id")

        if not project_id:
            return Response(message="Error: project_id is required", break_loop=False)

        project = self.manager.db.get_project(project_id)
        if not project:
            return Response(message=f"Project not found: {project_id}", break_loop=False)

        # Get files
        project_files = self.manager.db.get_project_files(project_id)

        lines = [f"## Project: {project['name']}\n"]
        lines.append(f"**ID:** {project['project_id']}")
        lines.append(f"**Path:** {project['output_path']}")
        lines.append(f"**Status:** {project.get('status', 'created')}")
        lines.append(f"**Created:** {project['created_at']}")

        if project.get("variables_used"):
            lines.append("\n### Variables Used:")
            for key, value in project["variables_used"].items():
                lines.append(f"- {key}: {value}")

        if project_files:
            lines.append(f"\n### Files ({len(project_files)}):")
            for f in project_files[:20]:
                lines.append(f"- {f['file_path']}")
            if len(project_files) > 20:
                lines.append(f"... and {len(project_files) - 20} more")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Helpers ==========

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary as readable output"""
        lines = [f"## {title}\n"]

        for key, value in data.items():
            if isinstance(value, dict | list):
                lines.append(f"**{key}:** {json.dumps(value, indent=2)}")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)
