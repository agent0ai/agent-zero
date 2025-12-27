### component_generator

Generate React components with TypeScript, best practices, and modern patterns.
Includes shadcn/ui integration, accessibility attributes, and responsive design.
Outputs component code with kebab-case filename suggestion.

Args:
- name (required): Component name in PascalCase (e.g., "UserCard", "ProductList")
- props (optional): Array of prop definitions with name, type, and required fields
- features (optional): Array of features to include: "accessibility", "responsive", "shadcn-ui"
- library (optional): Component library to use (default: "shadcn-ui")

Generated components include:
- TypeScript interface for props
- Proper React component structure
- Accessibility attributes (if requested)
- Responsive classes (if requested)
- shadcn/ui utility integration

Usage example 1: Basic component with props

~~~json
{
    "thoughts": [
        "User needs a UserCard component",
        "Add props for name, email, and avatar",
        "Include accessibility features"
    ],
    "headline": "Generating UserCard component",
    "tool_name": "component_generator",
    "tool_args": {
        "name": "UserCard",
        "props": [
            {"name": "name", "type": "string", "required": true},
            {"name": "email", "type": "string", "required": true},
            {"name": "avatar", "type": "string", "required": false}
        ],
        "features": ["accessibility", "responsive"],
        "library": "shadcn-ui"
    }
}
~~~

Usage example 2: Simple component without props

~~~json
{
    "thoughts": [
        "Need a loading spinner component",
        "No props needed, just visual element"
    ],
    "headline": "Generating LoadingSpinner component",
    "tool_name": "component_generator",
    "tool_args": {
        "name": "LoadingSpinner",
        "features": ["accessibility"]
    }
}
~~~

File naming convention:
- Component name "UserCard" → filename "user-card.tsx"
- Component name "ProductList" → filename "product-list.tsx"
