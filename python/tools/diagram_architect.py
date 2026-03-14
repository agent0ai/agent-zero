"""
Diagram Architect Tool for Agent Jumbo
Auto-generate architecture diagrams from codebase analysis
"""

from python.helpers import files
from python.helpers.tool import Response, Tool


class DiagramArchitect(Tool):
    """
    Agent Jumbo tool for architecture analysis and diagram generation.
    Analyzes codebases to detect components, relationships, and generates
    architecture diagrams in Mermaid format.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.diagram_architect.architect_manager import DiagramArchitectManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/diagram_architect/data/diagram_architect.db")
        self.manager = DiagramArchitectManager(db_path)

    async def execute(self, **kwargs):
        """Execute diagram architect action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        action_handlers = {
            # Analysis actions
            "analyze_architecture": self._analyze_architecture,
            "get_analysis": self._get_analysis,
            "list_analyses": self._list_analyses,
            "get_analysis_summary": self._get_analysis_summary,
            # Diagram generation
            "generate_system_diagram": self._generate_system_diagram,
            "generate_data_flow": self._generate_data_flow,
            "generate_integration_map": self._generate_integration_map,
            "generate_deployment": self._generate_deployment,
            "generate_from_app_spec": self._generate_from_app_spec,
            "export_all": self._export_all,
            # Diagram retrieval
            "get_diagram": self._get_diagram,
            "list_diagrams": self._list_diagrams,
        }

        handler = action_handlers.get(action)
        if handler:
            return await handler()

        return Response(
            message=f"Unknown action: {action}. Available: {', '.join(action_handlers.keys())}", break_loop=False
        )

    # ========== Analysis Actions ==========

    async def _analyze_architecture(self):
        """Perform full architecture analysis of a project"""
        project_path = self.args.get("project_path")
        analysis_type = self.args.get("analysis_type", "full")

        if not project_path:
            return Response(message="Error: project_path is required", break_loop=False)

        result = self.manager.analyze_architecture(project_path, analysis_type)

        if "error" in result:
            return Response(message=f"Analysis failed: {result['error']}", break_loop=False)

        lines = ["## Architecture Analysis Complete\n"]
        lines.append(f"**Project:** {result['project_name']}")
        lines.append(f"**Analysis ID:** {result['analysis_id']}")
        lines.append(f"**Status:** {result['status']}")
        lines.append("")
        lines.append("### Detected")
        lines.append(f"- Components: {result['components']}")
        lines.append(f"- Relationships: {result['relationships']}")
        lines.append(f"- External Integrations: {result['integrations']}")
        lines.append(f"- Data Flows: {result['data_flows']}")
        lines.append("")
        lines.append("Use `generate_system_diagram`, `generate_data_flow`, etc. to create diagrams.")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_analysis(self):
        """Get analysis details"""
        analysis_id = self.args.get("analysis_id")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.get_analysis(analysis_id)

        if not result:
            return Response(message=f"Analysis not found: {analysis_id}", break_loop=False)

        return Response(message=self._format_result(result, f"Analysis: {result['project_name']}"), break_loop=False)

    async def _list_analyses(self):
        """List all analyses"""
        project_path = self.args.get("project_path")

        analyses = self.manager.list_analyses(project_path)

        if not analyses:
            return Response(message="No analyses found.", break_loop=False)

        lines = ["## Architecture Analyses\n"]
        for a in analyses:
            lines.append(f"### {a['project_name']} (ID: {a['analysis_id']})")
            lines.append(f"- Status: {a['status']}")
            lines.append(f"- Created: {a['created_at']}")
            lines.append(f"- Path: {a['project_path']}")
            lines.append("")

        return Response(message="\n".join(lines), break_loop=False)

    async def _get_analysis_summary(self):
        """Get comprehensive analysis summary"""
        analysis_id = self.args.get("analysis_id")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.get_analysis_summary(analysis_id)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = [f"## Analysis Summary: {result['project_name']}\n"]
        lines.append(f"**Status:** {result['status']}")
        lines.append("")

        lines.append("### Totals")
        for key, value in result["summary"].items():
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")

        lines.append("")
        lines.append("### Component Breakdown")
        for comp_type, count in result["component_breakdown"].items():
            lines.append(f"- {comp_type}: {count}")

        if result["integration_breakdown"]:
            lines.append("")
            lines.append("### Integration Breakdown")
            for int_type, count in result["integration_breakdown"].items():
                lines.append(f"- {int_type}: {count}")

        if result["diagram_types"]:
            lines.append("")
            lines.append(f"### Diagrams Generated: {', '.join(result['diagram_types'])}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Diagram Generation ==========

    async def _generate_system_diagram(self):
        """Generate system/component architecture diagram"""
        analysis_id = self.args.get("analysis_id")
        title = self.args.get("title")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.generate_system_diagram(analysis_id, title)
        return self._format_diagram_response(result, "System Architecture")

    async def _generate_data_flow(self):
        """Generate data flow diagram"""
        analysis_id = self.args.get("analysis_id")
        title = self.args.get("title")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.generate_data_flow_diagram(analysis_id, title)
        return self._format_diagram_response(result, "Data Flow")

    async def _generate_integration_map(self):
        """Generate external integrations diagram"""
        analysis_id = self.args.get("analysis_id")
        title = self.args.get("title")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.generate_integration_diagram(analysis_id, title)
        return self._format_diagram_response(result, "External Integrations")

    async def _generate_deployment(self):
        """Generate deployment/infrastructure diagram"""
        analysis_id = self.args.get("analysis_id")
        title = self.args.get("title")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.generate_deployment_diagram(analysis_id, title)
        return self._format_diagram_response(result, "Deployment")

    async def _generate_from_app_spec(self):
        """Generate diagram from app_spec.json"""
        app_spec_path = self.args.get("app_spec_path")
        diagram_type = self.args.get("diagram_type", "system")

        if not app_spec_path:
            return Response(message="Error: app_spec_path is required", break_loop=False)

        result = self.manager.generate_from_app_spec(app_spec_path, diagram_type)
        return self._format_diagram_response(result, "App Spec Diagram")

    async def _export_all(self):
        """Generate and export all diagram types"""
        analysis_id = self.args.get("analysis_id")
        output_dir = self.args.get("output_dir")

        if not analysis_id:
            return Response(message="Error: analysis_id is required", break_loop=False)

        result = self.manager.export_all_diagrams(analysis_id, output_dir)

        if "error" in result:
            return Response(message=f"Error: {result['error']}", break_loop=False)

        lines = ["## Diagrams Exported\n"]
        lines.append(f"**Output Directory:** {result['output_dir']}")
        lines.append("")

        for d in result["diagrams"]:
            lines.append(f"- **{d['type']}**: {d['mermaid_file']}")

        lines.append(f"\n**Total:** {len(result['diagrams'])} diagrams exported")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Diagram Retrieval ==========

    async def _get_diagram(self):
        """Get a specific diagram"""
        diagram_id = self.args.get("diagram_id")

        if not diagram_id:
            return Response(message="Error: diagram_id is required", break_loop=False)

        result = self.manager.get_diagram(diagram_id)

        if not result:
            return Response(message=f"Diagram not found: {diagram_id}", break_loop=False)

        lines = [f"## Diagram: {result['title']}\n"]
        lines.append(f"**Type:** {result['diagram_type']}")
        lines.append(f"**Created:** {result['created_at']}")
        lines.append("")
        lines.append("### Mermaid Code")
        lines.append("```mermaid")
        lines.append(result["mermaid_code"])
        lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    async def _list_diagrams(self):
        """List diagrams"""
        analysis_id = self.args.get("analysis_id")
        diagram_type = self.args.get("diagram_type")

        diagrams = self.manager.list_diagrams(analysis_id, diagram_type)

        if not diagrams:
            return Response(message="No diagrams found.", break_loop=False)

        lines = ["## Generated Diagrams\n"]
        for d in diagrams:
            lines.append(f"- **{d['title']}** (ID: {d['diagram_id']})")
            lines.append(f"  Type: {d['diagram_type']}, Created: {d['created_at']}")

        return Response(message="\n".join(lines), break_loop=False)

    # ========== Helpers ==========

    def _format_diagram_response(self, result: dict, diagram_name: str) -> Response:
        """Format diagram generation response"""
        if "error" in result:
            return Response(message=f"Error generating {diagram_name}: {result['error']}", break_loop=False)

        lines = [f"## {diagram_name} Diagram Generated\n"]
        lines.append(f"**Diagram ID:** {result['diagram_id']}")
        lines.append(f"**Title:** {result['title']}")
        lines.append("")
        lines.append("### Mermaid Code")
        lines.append("```mermaid")
        lines.append(result["mermaid_code"])
        lines.append("```")

        return Response(message="\n".join(lines), break_loop=False)

    def _format_result(self, data: dict, title: str) -> str:
        """Format result dictionary as readable output"""
        lines = [f"## {title}\n"]

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"**{key}:**")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"**{key}:** ({len(value)} items)")
                for item in value[:5]:
                    if isinstance(item, dict):
                        lines.append(f"  - {item.get('name', item)}")
                    else:
                        lines.append(f"  - {item}")
                if len(value) > 5:
                    lines.append(f"  ... and {len(value) - 5} more")
            else:
                lines.append(f"**{key}:** {value}")

        return "\n".join(lines)
