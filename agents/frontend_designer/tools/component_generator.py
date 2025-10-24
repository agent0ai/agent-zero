from python.helpers.tool import Tool, Response
import re


class ComponentGeneratorTool(Tool):
    """Generate React components with TypeScript and best practices."""

    async def execute(self, **kwargs) -> Response:
        # Extract arguments
        name = self.args.get("name", "")
        props = self.args.get("props", [])
        features = self.args.get("features", [])
        library = self.args.get("library", "shadcn-ui")

        if not name:
            return Response(
                message="Error: Component name is required",
                break_loop=False
            )

        # Generate component code
        component_code = self._generate_component(name, props, features, library)

        # Generate filename (kebab-case)
        filename = self._to_kebab_case(name)

        # Build response message
        message = f"Generated React component: {name}\n\n"
        message += f"Suggested filename: {filename}.tsx\n\n"
        message += "Component code:\n\n```typescript\n"
        message += component_code
        message += "\n```"

        return Response(message=message, break_loop=False)

    def _generate_component(self, name: str, props: list, features: list, library: str) -> str:
        """Generate the component code."""
        code_parts = []

        # Imports
        imports = ['import React from "react"']

        if library == "shadcn-ui":
            imports.append('import { cn } from "@/lib/utils"')

        code_parts.append('\n'.join(imports))
        code_parts.append('')

        # Props interface
        if props:
            interface_lines = [f'interface {name}Props {{']
            for prop in props:
                prop_name = prop.get('name', '')
                prop_type = prop.get('type', 'string')
                required = prop.get('required', True)
                optional_marker = '' if required else '?'
                interface_lines.append(f'  {prop_name}{optional_marker}: {prop_type}')
            interface_lines.append('}')
            code_parts.append('\n'.join(interface_lines))
            code_parts.append('')

        # Component function
        props_param = f'{{ {", ".join(p.get("name", "") for p in props)} }}' if props else ''
        props_type = f': {name}Props' if props else ''

        code_parts.append(f'export function {name}({props_param}{props_type}) {{')
        code_parts.append('  return (')

        # Component JSX
        accessibility = 'accessibility' in features
        responsive = 'responsive' in features

        # Build className
        classes = []
        if responsive:
            classes.append('w-full md:w-auto')

        class_attr = f' className="{" ".join(classes)}"' if classes else ''
        aria_attr = f' role="region" aria-label="{name}"' if accessibility else ''

        code_parts.append(f'    <div{class_attr}{aria_attr}>')
        code_parts.append(f'      {/* Component content */}')

        # Add prop display if props exist
        if props:
            for prop in props:
                prop_name = prop.get('name', '')
                code_parts.append(f'      <div>{{{prop_name}}}</div>')

        code_parts.append('    </div>')
        code_parts.append('  )')
        code_parts.append('}')

        return '\n'.join(code_parts)

    def _to_kebab_case(self, text: str) -> str:
        """Convert PascalCase or camelCase to kebab-case."""
        # Insert hyphen before capital letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
        # Insert hyphen before capital letters in acronyms
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
        return s2.lower()
