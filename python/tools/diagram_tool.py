from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
import json
import os
import subprocess
import tempfile
from pathlib import Path


class DiagramTool(Tool):
    """
    Comprehensive diagram generation tool supporting:
    - Mermaid (flowcharts, sequence diagrams, class diagrams, etc.)
    - Excalidraw (hand-drawn style diagrams)
    - Draw.io (professional technical diagrams)
    """

    async def execute(self, **kwargs):
        diagram_type = self.args.get("diagram_type", "mermaid")
        output_path = self.args.get("output_path")
        
        try:
            if diagram_type == "mermaid":
                return await self._generate_mermaid()
            elif diagram_type == "excalidraw":
                return await self._generate_excalidraw()
            elif diagram_type == "drawio":
                return await self._generate_drawio()
            else:
                return Response(
                    message=f"Unsupported diagram type: {diagram_type}. "
                           f"Supported types: mermaid, excalidraw, drawio",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Error generating {diagram_type} diagram: {str(e)}",
                break_loop=False
            )

    async def _generate_mermaid(self):
        """Generate Mermaid diagram"""
        code = self.args.get("code", "")
        output_path = self.args.get("output_path")
        format = self.args.get("format", "png")
        theme = self.args.get("theme", "default")
        
        if not code:
            return Response(
                message="Error: 'code' argument is required for Mermaid diagrams",
                break_loop=False
            )
        
        # Use the instrument script
        script_path = "/a0/instruments/custom/diagram_generator/generate_mermaid.py"
        
        if output_path:
            # Generate to file
            cmd = [
                "python3", script_path,
                "--output", output_path,
                "--code", code,
                "--format", format,
                "--theme", theme
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return Response(
                    message=f"Successfully generated Mermaid diagram: {output_path}\n\n"
                           f"View it with: ![Diagram](img://{output_path})",
                    break_loop=False
                )
            else:
                return Response(
                    message=f"Error generating Mermaid diagram:\n{result.stderr}",
                    break_loop=False
                )
        else:
            # Return code for inline rendering
            return Response(
                message=f"Mermaid diagram code:\n\n```mermaid\n{code}\n```",
                break_loop=False
            )

    async def _generate_excalidraw(self):
        """Generate Excalidraw diagram"""
        elements = self.args.get("elements", [])
        output_path = self.args.get("output_path")
        format = self.args.get("format", "json")
        template = self.args.get("template")
        
        script_path = "/a0/instruments/custom/diagram_generator/generate_excalidraw.py"
        
        cmd = ["python3", script_path, "--output", output_path, "--format", format]
        
        if template:
            cmd.extend(["--template", template])
        elif elements:
            cmd.extend(["--elements", json.dumps(elements)])
        else:
            return Response(
                message="Error: Either 'elements' or 'template' is required for Excalidraw diagrams",
                break_loop=False
            )
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            message = f"Successfully generated Excalidraw diagram: {output_path}"
            if format == "json" or output_path.endswith('.excalidraw'):
                message += f"\n\nOpen at: https://excalidraw.com"
            else:
                message += f"\n\nView it with: ![Diagram](img://{output_path})"
            
            return Response(message=message, break_loop=False)
        else:
            return Response(
                message=f"Error generating Excalidraw diagram:\n{result.stderr}",
                break_loop=False
            )

    async def _generate_drawio(self):
        """Generate Draw.io diagram"""
        xml = self.args.get("xml", "")
        output_path = self.args.get("output_path")
        format = self.args.get("format", "png")
        template = self.args.get("template")
        
        script_path = "/a0/instruments/custom/diagram_generator/generate_drawio.py"
        
        cmd = ["python3", script_path, "--output", output_path, "--format", format]
        
        if template:
            cmd.extend(["--template", template])
        elif xml:
            cmd.extend(["--xml", xml])
        else:
            return Response(
                message="Error: Either 'xml' or 'template' is required for Draw.io diagrams",
                break_loop=False
            )
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            message = f"Successfully generated Draw.io diagram: {output_path}"
            if format == "xml" or output_path.endswith('.drawio'):
                message += f"\n\nOpen at: https://app.diagrams.net"
            else:
                message += f"\n\nView it with: ![Diagram](img://{output_path})"
            
            return Response(message=message, break_loop=False)
        else:
            return Response(
                message=f"Error generating Draw.io diagram:\n{result.stderr}",
                break_loop=False
            )
