# Virtual Team Tool

The **virtual_team** tool coordinates specialized AI agents for collaborative software development workflows.

## Purpose

Orchestrate a virtual team of specialized agents including:

- **Architect**: System design, architecture patterns, cloud design
- **Developer**: Backend/frontend development, API design
- **DBA**: Database schema design, optimization, migrations
- **QA**: Test automation, quality assurance, testing
- **DevOps**: CI/CD, containerization, infrastructure
- **Security**: Security reviews, threat modeling, compliance
- **PM**: Project management, planning, stakeholder coordination

## Available Actions

### 1. route_task

**Automatically route task to best-suited agent based on task type**

```
{{virtual_team(
  action="route_task",
  task_name="Design microservices architecture",
  task_type="architecture_design",
  description="Design scalable microservices architecture for e-commerce platform",
  context={"customer_id": 5, "requirements": "high_availability"},
  priority="high",
  complexity="high"
)}}
```

**Parameters:**

- `task_name` (required): Task name/title
- `task_type` (required): Type of task (see task types below)
- `description` (optional): Detailed description
- `context` (optional): Additional context data
- `priority` (optional): "low", "medium", "high" (default: "medium")
- `complexity` (optional): Complexity level

**Task Type → Agent Role Mapping:**

- `architecture_design`, `system_design`, `api_design` → architect
- `backend_development`, `frontend_development`, `implementation`, `code_review` → developer
- `schema_design`, `database_optimization`, `migration_planning` → dba
- `test_development`, `testing`, `quality_assurance` → qa
- `deployment_setup`, `ci_cd_setup`, `infrastructure` → devops
- `security_review`, `security_testing`, `threat_modeling` → security
- `project_planning`, `stakeholder_management` → pm

**Returns:** Task ID, assignment ID, assigned agent, status

---

### 2. delegate_to_specialist

**Explicitly delegate task to specific specialist role**

```
{{virtual_team(
  action="delegate_to_specialist",
  task_name="Optimize database queries",
  specialist_role="dba",
  description="Optimize slow queries in orders table",
  context={"table": "orders", "avg_query_time": "5s"},
  priority="high"
)}}
```

**Parameters:**

- `task_name` (required): Task name
- `specialist_role` (required): Target role (architect, developer, dba, qa, devops, security, pm)
- `description` (optional): Task description
- `context` (optional): Context data
- `priority` (optional): Priority level

**Returns:** Task ID, assignment details

**Available Specialist Roles:**

- `architect`: System architecture, design patterns, scalability
- `developer`: Software engineering, coding, APIs
- `dba`: Database design, optimization, migrations
- `qa`: Testing, quality assurance, automation
- `devops`: Infrastructure, CI/CD, deployment
- `security`: Security analysis, penetration testing
- `pm`: Project coordination, planning

---

### 3. start_workflow

**Start multi-agent workflow using template or custom tasks**

```
{{virtual_team(
  action="start_workflow",
  workflow_name="Build Customer Portal",
  workflow_type="custom",
  template="full_stack_development",
  customer_id=5,
  project_id=10
)}}
```

**Parameters:**

- `workflow_name` (required): Workflow name
- `workflow_type` (optional): Type of workflow (default: "custom")
- `template` (optional): Use predefined template (see templates below)
- `custom_tasks` (optional): Custom task sequence if not using template
- `customer_id` (optional): Link to customer
- `project_id` (optional): Link to project

**Available Workflow Templates:**

**full_stack_development:**

1. Architect → Architecture design
2. **Parallel:** DBA → Schema design, Developer → Backend, Developer → Frontend
3. **Parallel:** QA → Testing, Security → Security review
4. DevOps → Deployment setup

**api_development:**

1. Architect → API design
2. Developer → Implementation
3. **Parallel:** QA → API testing, Security → Security testing
4. DevOps → Deployment

**database_migration:**

1. DBA → Migration planning
2. DBA → Schema migration
3. Developer → Code updates
4. QA → Validation testing
5. DevOps → Rollback plan

**Custom Task Sequence Format:**

```python
custom_tasks=[
  {"role": "architect", "task_type": "architecture_design", "parallel_group": None},
  {"role": "developer", "task_type": "backend_development", "parallel_group": 1},
  {"role": "qa", "task_type": "testing", "parallel_group": 1}
]
```

**Returns:** Workflow ID, tasks created, status

---

### 4. get_workflow_progress

**Get workflow progress and status**

```
{{virtual_team(
  action="get_workflow_progress",
  workflow_id=1
)}}
```

**Parameters:**

- `workflow_id` (required): Workflow ID

**Returns:** Workflow status, task list with statuses, progress percentage

---

### 5. coordinate_parallel_tasks

**Coordinate multiple tasks to run in parallel**

```
{{virtual_team(
  action="coordinate_parallel_tasks",
  task_specs=[
    {
      "task_name": "Build API endpoints",
      "task_type": "backend_development",
      "priority": "high"
    },
    {
      "task_name": "Create UI mockups",
      "task_type": "frontend_development",
      "priority": "high"
    },
    {
      "task_name": "Design database schema",
      "task_type": "schema_design",
      "priority": "high"
    }
  ]
)}}
```

**Parameters:**

- `task_specs` (required): Array of task specifications

**Returns:** Parallel task count, assignment details

---

### 6. escalate_task

**Escalate task to different agent or higher tier**

```
{{virtual_team(
  action="escalate_task",
  task_id=5,
  reason="Requires architectural expertise",
  target_role="architect"
)}}
```

**Parameters:**

- `task_id` (required): Task ID to escalate
- `reason` (required): Escalation reason
- `target_role` (optional): Target role (defaults to architect)

**Returns:** New assignment details, escalation status

---

### 7. get_task_queue

**Get pending task queue, optionally filtered by role**

```
{{virtual_team(
  action="get_task_queue",
  role="developer"
)}}
```

**Parameters:**

- `role` (optional): Filter by specific role

**Returns:** Total pending, tasks grouped by role

---

### 8. get_agent_workload

**Get current workload for specific agent or role**

```
{{virtual_team(
  action="get_agent_workload",
  role="developer"
)}}
```

**Parameters:**

- `agent_id` (optional): Specific agent ID
- `role` (optional): Role to check (must provide agent_id OR role)

**Returns:** Workload by status, total active tasks

---

### 9. get_team_dashboard

**Get team-wide analytics and metrics**

```
{{virtual_team(
  action="get_team_dashboard"
)}}
```

**Returns:** Active agents, task stats, workload by role, recent completions, pending queue size

---

### 10. update_task_status

**Update task status and progress**

```
{{virtual_team(
  action="update_task_status",
  task_id=5,
  status="in_progress",
  progress_percentage=50
)}}
```

**Parameters:**

- `task_id` (required): Task ID
- `status` (required): New status ("pending", "assigned", "in_progress", "completed", "escalated")
- `progress_percentage` (optional): Progress 0-100

**Returns:** Success status

---

### 11. get_task_details

**Get detailed task information**

```
{{virtual_team(
  action="get_task_details",
  task_id=5
)}}
```

**Parameters:**

- `task_id` (required): Task ID

**Returns:** Complete task details including assignment info

---

### 12. list_agents

**List all agents with optional filters**

```
{{virtual_team(
  action="list_agents",
  role="developer",
  status="active"
)}}
```

**Parameters:**

- `role` (optional): Filter by role
- `status` (optional): Filter by status (default: "active")

**Returns:** Agent list with capabilities

---

### 13. get_available_workflows

**Get list of available workflow templates**

```
{{virtual_team(
  action="get_available_workflows"
)}}
```

**Returns:** Workflow template names

---

### 14. get_available_roles

**Get all available agent roles with capabilities**

```
{{virtual_team(
  action="get_available_roles"
)}}
```

**Returns:** Roles with specializations, expertise areas, available tools

---

## Typical Workflows

### Software Development Workflow

1. **Route architecture task** to architect
2. **Start full_stack_development workflow**
3. **Monitor workflow progress**
4. **Escalate if needed**
5. **Check team dashboard** for overall status

### Example Complete Flow

```
# Step 1: Design system architecture
{{virtual_team(action="route_task", task_name="Design payment system", task_type="architecture_design")}}
# Returns: task_id = 1, assigned to architect

# Step 2: Start full development workflow
{{virtual_team(action="start_workflow", workflow_name="Payment System Implementation", template="full_stack_development", project_id=5)}}
# Returns: workflow_id = 1, tasks_created = 7

# Step 3: Check workflow progress
{{virtual_team(action="get_workflow_progress", workflow_id=1)}}
# Returns: progress_percentage = 42, task statuses

# Step 4: Coordinate parallel security tasks
{{virtual_team(action="coordinate_parallel_tasks", task_specs=[
  {"task_name": "Penetration testing", "task_type": "security_testing"},
  {"task_name": "Code security audit", "task_type": "security_review"}
])}}

# Step 5: Monitor team workload
{{virtual_team(action="get_team_dashboard")}}
# Returns: active_agents, workload_by_role, task_stats
```

---

## Integration with Other Tools

### With Customer Lifecycle

```
# Customer requirements gathered
{{customer_lifecycle(action="design_solution", customer_id=5)}}

# Start virtual team workflow for implementation
{{virtual_team(action="start_workflow", workflow_name="Customer Portal", template="full_stack_development", customer_id=5)}}
```

### With Portfolio Manager

```
# Create project
{{portfolio_manager_tool(action="create_project", project_name="E-Commerce Platform")}}
# Returns: project_id = 10

# Assign virtual team
{{virtual_team(action="start_workflow", workflow_name="E-Commerce Build", template="full_stack_development", project_id=10)}}
```

---

## Agent Role Capabilities

### Architect

- **Expertise**: Architecture patterns, scalability, cloud design, security architecture
- **Tools**: Diagram tools, documentation, code review
- **Task Types**: architecture_design, system_design, api_design

### Developer

- **Expertise**: Backend, frontend, API design, testing, refactoring
- **Tools**: Code generation, debugging, refactoring
- **Task Types**: backend_development, frontend_development, implementation, code_review

### DBA

- **Expertise**: Schema design, query optimization, migrations, indexing
- **Tools**: Database tools, performance monitoring
- **Task Types**: schema_design, database_optimization, migration_planning

### QA

- **Expertise**: Test automation, manual testing, performance testing, security testing
- **Tools**: Testing frameworks, bug tracking
- **Task Types**: test_development, testing, quality_assurance

### DevOps

- **Expertise**: CI/CD, containerization, orchestration, monitoring
- **Tools**: Docker, Kubernetes, Terraform, CI/CD pipelines
- **Task Types**: deployment_setup, ci_cd_setup, infrastructure

### Security

- **Expertise**: Threat modeling, penetration testing, compliance, encryption
- **Tools**: Security scanners, audit tools
- **Task Types**: security_review, security_testing, threat_modeling

### PM

- **Expertise**: Agile, planning, stakeholder management, risk management
- **Tools**: Project tracking, reporting
- **Task Types**: project_planning, stakeholder_management

---

## Best Practices

1. **Use workflows for complex projects** - Templates handle task sequencing automatically
2. **Route simple tasks directly** - Single tasks don't need full workflows
3. **Monitor team dashboard** - Check workload balance regularly
4. **Escalate blockers quickly** - Don't let tasks stall
5. **Coordinate parallel work** - Use parallel task groups for efficiency
6. **Link to customers/projects** - Maintain context for reporting
7. **Update task status** - Keep progress tracking accurate

---

## Notes

- Database auto-creates standard agents on initialization
- Workflow templates handle task dependencies automatically
- Parallel task groups (same parallel_group number) run concurrently
- Task routing is automatic based on task_type
- Escalation defaults to architect if no target_role specified
