### code_project

Generate Next.js/React code projects with proper file structure.
Creates files using tsx/jsx syntax with TypeScript support.
Handles component scaffolding, routing, and configuration.

Args:
- project_id (required): Unique identifier for the project (used as directory name)
- files (required): Array of file objects with 'path' and 'content' properties
- framework (optional): "nextjs" or "react" (default: "nextjs")
- styling (optional): "tailwind", "css-modules", or "styled-components" (default: "tailwind")

Files are created in tmp/{project_id}/ directory.

Usage example 1: Create Next.js landing page

~~~json
{
    "thoughts": [
        "User wants a landing page with hero section",
        "I'll create a Next.js app with Tailwind CSS",
        "Need page.tsx, layout.tsx, and components"
    ],
    "headline": "Creating Next.js landing page project",
    "tool_name": "code_project",
    "tool_args": {
        "project_id": "landing-page",
        "framework": "nextjs",
        "styling": "tailwind",
        "files": [
            {
                "path": "app/page.tsx",
                "content": "export default function Home() {\n  return (\n    <main className=\"min-h-screen\">\n      <h1>Welcome</h1>\n    </main>\n  )\n}"
            },
            {
                "path": "app/layout.tsx",
                "content": "export default function RootLayout({ children }) {\n  return (\n    <html lang=\"en\">\n      <body>{children}</body>\n    </html>\n  )\n}"
            },
            {
                "path": "package.json",
                "content": "{\"name\": \"landing-page\", \"version\": \"1.0.0\"}"
            }
        ]
    }
}
~~~

Usage example 2: Create React component library

~~~json
{
    "thoughts": [
        "User needs a component library",
        "I'll create reusable components with TypeScript"
    ],
    "headline": "Creating React component library",
    "tool_name": "code_project",
    "tool_args": {
        "project_id": "component-lib",
        "framework": "react",
        "styling": "css-modules",
        "files": [
            {
                "path": "src/components/Button/Button.tsx",
                "content": "interface ButtonProps {\n  children: React.ReactNode\n}\n\nexport function Button({ children }: ButtonProps) {\n  return <button>{children}</button>\n}"
            },
            {
                "path": "src/components/Button/Button.module.css",
                "content": ".button {\n  padding: 0.5rem 1rem;\n}"
            }
        ]
    }
}
~~~
