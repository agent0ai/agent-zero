# Project Scaffold Tool

The **project_scaffold** tool generates complete project structures from templates, with automatic app_spec.json generation and integration with portfolio management.

## Purpose

- Generate new projects from built-in or custom templates
- Support multiple project types: web apps, APIs, CLIs, microservices
- Auto-generate app_spec.json for project documentation
- Track generated projects for portfolio management
- Add components to existing projects

## Available Templates

### Web Applications

- `web_app/react` - React + Vite + TailwindCSS
- `web_app/nextjs` - Next.js 14 with App Router
- `web_app/vue` - Vue.js 3 with Vite

### APIs

- `api/fastapi` - Python FastAPI with SQLAlchemy
- `api/express` - Node.js Express with TypeScript

### CLI Applications

- `cli/python` - Python CLI with Click and Rich

### Microservices

- `microservice/python` - FastAPI microservice with Docker

## Available Actions

### 1. scaffold_project

**Generate a new project from a template**

```
{{project_scaffold(
  action="scaffold_project",
  template="api/fastapi",
  name="My API Project",
  output_path="/path/to/output",
  variables={
    "description": "A FastAPI REST API",
    "use_sqlalchemy": true,
    "database": "postgresql"
  },
  customer_id=5,
  generate_app_spec=true
)}}
```

**Parameters:**

- `template` (required): Template name (e.g., "web_app/react")
- `name` (required): Project name
- `output_path` (required): Where to create the project
- `variables` (optional): Template-specific variables
- `customer_id` (optional): Link to customer_lifecycle
- `generate_app_spec` (optional): Generate app_spec.json (default: true)

**Returns:** project_id, files_created, output_path

---

### 2. preview_scaffold

**Preview files that would be generated**

```
{{project_scaffold(
  action="preview_scaffold",
  template="web_app/react",
  variables={
    "use_typescript": true,
    "use_tailwind": true
  }
)}}
```

**Parameters:**

- `template` (required): Template name
- `variables` (optional): Template variables

**Returns:** List of files to be created, variable values

---

### 3. list_templates

**List available templates**

```
{{project_scaffold(
  action="list_templates",
  type="api",
  language="python"
)}}
```

**Parameters:**

- `type` (optional): Filter by type (web_app, api, cli, microservice)
- `language` (optional): Filter by language (python, javascript, typescript)
- `framework` (optional): Filter by framework (react, fastapi, express)

**Returns:** List of templates with descriptions

---

### 4. get_template

**Get detailed template information**

```
{{project_scaffold(
  action="get_template",
  name="api/fastapi"
)}}
```

**Parameters:**

- `name` (required): Template name

**Returns:** Template details including variables and configuration

---

### 5. create_template

**Create a template from an existing project**

```
{{project_scaffold(
  action="create_template",
  project_path="/path/to/existing/project",
  name="my_custom_template",
  description="Custom project template"
)}}
```

**Parameters:**

- `project_path` (required): Path to existing project
- `name` (required): Name for new template
- `description` (optional): Template description

**Returns:** template_id, detected type and language

---

### 6. generate_app_spec

**Generate app_spec.json for an existing project**

```
{{project_scaffold(
  action="generate_app_spec",
  project_path="/path/to/project",
  analyze_code=true
)}}
```

**Parameters:**

- `project_path` (required): Path to project
- `analyze_code` (optional): Analyze code for components (default: true)

**Returns:** Generated app_spec.json content

---

### 7. add_component

**Add a component to an existing project**

```
{{project_scaffold(
  action="add_component",
  project_path="/path/to/project",
  component_type="api_endpoint",
  name="users"
)}}
```

**Parameters:**

- `project_path` (required): Path to project
- `component_type` (required): page, api_endpoint, model, service, test
- `name` (required): Component name

**Returns:** List of created files

---

### 8. list_projects

**List generated projects**

```
{{project_scaffold(
  action="list_projects",
  customer_id=5
)}}
```

**Parameters:**

- `customer_id` (optional): Filter by customer
- `template_id` (optional): Filter by template

**Returns:** List of projects with paths and status

---

### 9. get_project

**Get project details**

```
{{project_scaffold(
  action="get_project",
  project_id=1
)}}
```

**Parameters:**

- `project_id` (required): Project ID

**Returns:** Project details, variables used, generated files

---

## Template Variables

### web_app/react

- `project_name` (required): Project name
- `description`: Project description
- `use_typescript` (default: true): Use TypeScript
- `use_tailwind` (default: true): Include TailwindCSS

### api/fastapi

- `project_name` (required): Project name
- `description`: Project description
- `use_sqlalchemy` (default: true): Include SQLAlchemy ORM
- `use_alembic` (default: true): Include Alembic migrations
- `database` (default: "sqlite"): Database type (sqlite, postgresql, mysql)

### cli/python

- `project_name` (required): Project name
- `description`: CLI description
- `use_rich` (default: true): Include rich console output

### microservice/python

- `service_name` (required): Service name
- `description`: Service description
- `port` (default: 8000): Service port

---

## Typical Workflows

### Create Project for Customer

```
# 1. Get customer requirements from customer_lifecycle
{{customer_lifecycle(action="get_customer_view", customer_id=5)}}

# 2. Scaffold project based on requirements
{{project_scaffold(
  action="scaffold_project",
  template="api/fastapi",
  name="CustomerAPI",
  output_path="/projects/customer-5/api",
  customer_id=5
)}}

# 3. Add to portfolio
{{portfolio_manager_tool(action="add", project_path="/projects/customer-5/api")}}
```

### Create Full-Stack Application

```
# 1. Create backend API
{{project_scaffold(
  action="scaffold_project",
  template="api/fastapi",
  name="MyApp-API",
  output_path="/projects/myapp/backend"
)}}

# 2. Create frontend
{{project_scaffold(
  action="scaffold_project",
  template="web_app/react",
  name="MyApp-Frontend",
  output_path="/projects/myapp/frontend"
)}}

# 3. Generate architecture diagrams
{{diagram_architect(
  action="analyze_architecture",
  project_path="/projects/myapp"
)}}
```

---

## Integration with Other Tools

### With Customer Lifecycle

Link projects to customers for tracking:

```
{{project_scaffold(action="scaffold_project", customer_id=5, ...)}}
```

### With Portfolio Manager

Generated projects can be added to portfolio:

```
{{portfolio_manager_tool(action="scan", folder="/projects")}}
```

### With Deployment Orchestrator

Generate CI/CD for scaffolded projects:

```
{{deployment_orchestrator(action="generate_cicd", project_path="/projects/myapp")}}
```

---

## Notes

- All templates include README.md, .gitignore, and .env.example
- app_spec.json is generated automatically unless disabled
- Custom templates can be created from existing projects
- Projects are tracked in SQLite database for reference
- Generated files use best practices for each framework
