### mermaid_diagram

Generate Mermaid diagrams for component architecture, data flow, and user flows.
Supports flowchart and graph diagram types.

Args:
- type (optional): "flowchart" or "graph" (default: "flowchart")
- components (required): Array of component objects with name, type, uses, children
- title (optional): Diagram title

Component types:
- page: Rendered as rectangle [name]
- component: Rendered as rounded (name)
- hook: Rendered as hexagon {name}

Usage example:

~~~json
{
    "thoughts": [
        "User wants to see component hierarchy",
        "I'll create a flowchart showing the structure"
    ],
    "headline": "Creating component architecture diagram",
    "tool_name": "mermaid_diagram",
    "tool_args": {
        "type": "flowchart",
        "title": "App Component Structure",
        "components": [
            {
                "name": "App",
                "type": "page",
                "uses": ["Header", "Content", "Footer"]
            },
            {
                "name": "Header",
                "type": "component",
                "uses": ["Logo", "Navigation"]
            },
            {
                "name": "Content",
                "type": "component",
                "uses": []
            }
        ]
    }
}
~~~
