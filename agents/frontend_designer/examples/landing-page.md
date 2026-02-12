# Example: Landing Page Creation

## User Request

"Create a modern SaaS landing page with hero section, feature cards, and pricing table"

## Agent Workflow

### Step 1: Project Setup

```json
{
  "tool_name": "code_project",
  "tool_args": {
    "project_id": "saas-landing",
    "framework": "nextjs",
    "styling": "tailwind",
    "files": [...]
  }
}
```

### Step 2: Generate Hero Component

```json
{
  "tool_name": "component_generator",
  "tool_args": {
    "name": "Hero",
    "props": [
      {"name": "title", "type": "string", "required": true},
      {"name": "description", "type": "string", "required": true},
      {"name": "ctaText", "type": "string", "required": true}
    ],
    "features": ["accessibility", "responsive"]
  }
}
```

### Step 3: Generate Feature Cards

```json
{
  "tool_name": "component_generator",
  "tool_args": {
    "name": "FeatureCard",
    "props": [
      {"name": "icon", "type": "React.ReactNode", "required": true},
      {"name": "title", "type": "string", "required": true},
      {"name": "description", "type": "string", "required": true}
    ],
    "features": ["accessibility", "responsive", "shadcn-ui"]
  }
}
```

### Step 4: Create Architecture Diagram

```json
{
  "tool_name": "mermaid_diagram",
  "tool_args": {
    "type": "flowchart",
    "title": "Landing Page Structure",
    "components": [
      {"name": "Home", "type": "page", "uses": ["Hero", "Features", "Pricing"]},
      {"name": "Hero", "type": "component"},
      {"name": "Features", "type": "component", "uses": ["FeatureCard"]},
      {"name": "Pricing", "type": "component", "uses": ["PricingCard"]}
    ]
  }
}
```

## Result

Complete Next.js landing page with:
- Responsive hero section
- Feature cards grid
- Pricing table
- Full TypeScript types
- WCAG AA accessibility
- Tailwind CSS styling
