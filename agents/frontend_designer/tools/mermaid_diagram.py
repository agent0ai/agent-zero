from python.helpers.tool import Tool, Response


class MermaidDiagramTool(Tool):
    """Generate Mermaid diagrams for component architecture and flows."""

    async def execute(self, **kwargs) -> Response:
        diagram_type = self.args.get("type", "flowchart")
        components = self.args.get("components", [])
        title = self.args.get("title", "Component Architecture")

        if not components:
            return Response(
                message="Error: components array is required",
                break_loop=False
            )

        # Generate Mermaid diagram
        diagram = self._generate_diagram(diagram_type, components, title)

        message = f"{title}\n\n"
        message += "```mermaid\n"
        message += diagram
        message += "\n```"

        return Response(message=message, break_loop=False)

    def _generate_diagram(self, diagram_type: str, components: list, title: str) -> str:
        """Generate Mermaid diagram syntax."""
        lines = []

        if diagram_type == "flowchart":
            lines.append("flowchart TD")

            # Add nodes
            for idx, component in enumerate(components):
                name = component.get("name", f"Component{idx}")
                comp_type = component.get("type", "component")

                # Sanitize name for Mermaid (no special chars)
                node_id = self._sanitize_id(name)
                node_label = f'"{name}"'

                if comp_type == "page":
                    lines.append(f"    {node_id}[{node_label}]")
                elif comp_type == "component":
                    lines.append(f"    {node_id}({node_label})")
                elif comp_type == "hook":
                    lines.append(f"    {node_id}{{{node_label}}}")
                else:
                    lines.append(f"    {node_id}[{node_label}]")

            # Add relationships
            for component in components:
                name = component.get("name", "")
                uses = component.get("uses", [])

                if uses:
                    node_id = self._sanitize_id(name)
                    for used in uses:
                        used_id = self._sanitize_id(used)
                        lines.append(f"    {node_id} --> {used_id}")

        elif diagram_type == "graph":
            lines.append("graph LR")

            for idx, component in enumerate(components):
                name = component.get("name", f"Component{idx}")
                node_id = self._sanitize_id(name)
                lines.append(f'    {node_id}["{name}"]')

                children = component.get("children", [])
                for child in children:
                    child_id = self._sanitize_id(child)
                    lines.append(f'    {node_id} --> {child_id}["{child}"]')

        return '\n'.join(lines)

    def _sanitize_id(self, text: str) -> str:
        """Sanitize text to be Mermaid-safe ID."""
        # Remove special characters, keep alphanumeric
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', text)
        return sanitized or "node"
