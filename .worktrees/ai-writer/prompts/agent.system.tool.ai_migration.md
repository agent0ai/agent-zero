# AI Migration Tool

The **ai_migration** tool analyzes business processes, classifies tasks for automation potential, designs optimized human-AI workflows, and generates migration roadmaps with ROI projections.

## Purpose
- Assess business processes for AI automation potential
- Classify tasks as fully automatable, AI-assisted, or human-required
- Design optimized workflows that mesh AI agents with human workers
- Generate phased migration roadmaps with timelines
- Project ROI across conservative, moderate, and aggressive scenarios
- Identify quick wins for immediate automation

## Task Classification

Tasks are scored 0-100 based on automation potential:

| Score Range | Classification | Examples |
|-------------|----------------|----------|
| 80-100 | **Fully Automatable** | Data entry, calculations, report generation, scheduling, notifications |
| 40-79 | **AI-Assisted** | Pattern recognition, categorization, summarization, recommendations |
| 0-39 | **Human Required** | Strategic decisions, negotiations, creative design, relationship building |

---

## Available Actions

### 1. start_assessment
**Begin a new business process migration assessment**

```
{{ai_migration(
  action="start_assessment",
  business_name="Acme Corp",
  industry="manufacturing",
  description="Assessment of order processing workflows"
)}}
```

**Parameters:**
- `business_name` (required): Name of the business
- `industry` (optional): Industry sector
- `description` (optional): Assessment description

**Returns:** project_id, created timestamp

---

### 2. get_assessment
**Get assessment project details**

```
{{ai_migration(
  action="get_assessment",
  project_id=1
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID

**Returns:** Project details with processes and metrics

---

### 3. list_projects
**List all assessment projects**

```
{{ai_migration(
  action="list_projects",
  status="active"
)}}
```

**Parameters:**
- `status` (optional): Filter by status (active, completed, archived)

**Returns:** List of assessment projects

---

### 4. add_process
**Document a business process**

```
{{ai_migration(
  action="add_process",
  project_id=1,
  name="Order Processing",
  description="End-to-end order fulfillment workflow",
  current_duration_hours=4.5,
  frequency="daily",
  stakeholders=["sales", "warehouse", "shipping"]
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID
- `name` (required): Process name
- `description` (optional): Process description
- `current_duration_hours` (optional): Current time to complete
- `frequency` (optional): How often process runs (daily, weekly, etc.)
- `stakeholders` (optional): List of involved departments/roles

**Returns:** process_id, created timestamp

---

### 5. list_processes
**List processes in an assessment**

```
{{ai_migration(
  action="list_processes",
  project_id=1
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID

**Returns:** List of documented processes

---

### 6. get_process
**Get detailed process information**

```
{{ai_migration(
  action="get_process",
  process_id=1
)}}
```

**Parameters:**
- `process_id` (required): Process ID

**Returns:** Process details with tasks and analysis

---

### 7. add_task
**Add a task to a process**

```
{{ai_migration(
  action="add_task",
  process_id=1,
  name="Validate order data",
  task_type="data_validation",
  description="Check order fields for completeness",
  current_owner="data_clerk",
  avg_time_minutes=15,
  complexity="low",
  error_rate=0.05,
  decision_points=2
)}}
```

**Parameters:**
- `process_id` (required): Process ID
- `name` (required): Task name
- `task_type` (required): Type of task (see Task Types below)
- `description` (optional): Task description
- `current_owner` (optional): Current role performing task
- `avg_time_minutes` (optional): Average completion time
- `complexity` (optional): low, medium, high
- `error_rate` (optional): Current error rate (0.0-1.0)
- `decision_points` (optional): Number of decisions required

**Returns:** task_id, created timestamp

**Task Types:**
- `data_entry`, `data_validation`, `calculation`, `scheduling`
- `communication`, `document_processing`, `approval`, `analysis`
- `decision_making`, `creative_work`, `customer_interaction`

---

### 8. list_tasks
**List tasks in a process**

```
{{ai_migration(
  action="list_tasks",
  process_id=1
)}}
```

**Parameters:**
- `process_id` (required): Process ID

**Returns:** List of tasks with basic classification

---

### 9. analyze_process
**Analyze a process for automation potential**

```
{{ai_migration(
  action="analyze_process",
  process_id=1
)}}
```

**Parameters:**
- `process_id` (required): Process ID

**Returns:** Analysis with:
- Overall automation score
- Task-by-task classification
- Recommended automation targets
- Estimated time savings

---

### 10. classify_tasks
**Classify all tasks in a process**

```
{{ai_migration(
  action="classify_tasks",
  process_id=1
)}}
```

**Parameters:**
- `process_id` (required): Process ID

**Returns:** Task classification breakdown:
- Fully automatable tasks
- AI-assisted tasks
- Human-required tasks
- Recommended AI tools for each

---

### 11. design_workflow
**Design an optimized human-AI workflow**

```
{{ai_migration(
  action="design_workflow",
  process_id=1,
  optimization_level="balanced"
)}}
```

**Parameters:**
- `process_id` (required): Process ID
- `optimization_level` (optional): conservative, balanced, aggressive (default: balanced)

**Returns:** Optimized workflow design:
- New workflow steps (human, AI, handoff points)
- Role reassignments
- AI agent specifications
- Expected improvements

**Optimization Levels:**
- **Conservative**: Only automate 80+ score tasks, minimal disruption
- **Balanced**: Automate 60+ tasks, introduce AI assistance for 40-59
- **Aggressive**: Maximum automation, AI-first approach

---

### 12. list_workflows
**List designed workflows**

```
{{ai_migration(
  action="list_workflows",
  project_id=1
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID

**Returns:** List of workflow designs

---

### 13. get_workflow
**Get workflow design details**

```
{{ai_migration(
  action="get_workflow",
  workflow_id=1
)}}
```

**Parameters:**
- `workflow_id` (required): Workflow ID

**Returns:** Complete workflow specification

---

### 14. generate_roadmap
**Generate a phased migration roadmap**

```
{{ai_migration(
  action="generate_roadmap",
  project_id=1,
  phases=3,
  phase_duration_months=3
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID
- `phases` (optional): Number of phases (default: 3)
- `phase_duration_months` (optional): Months per phase (default: 3)

**Returns:** Migration roadmap:
- Phase breakdown with tasks
- Dependencies
- Resource requirements
- Milestones
- Risk mitigation

---

### 15. get_roadmap
**Get roadmap details**

```
{{ai_migration(
  action="get_roadmap",
  roadmap_id=1
)}}
```

**Parameters:**
- `roadmap_id` (required): Roadmap ID

**Returns:** Complete roadmap with phases

---

### 16. project_roi
**Calculate ROI projections**

```
{{ai_migration(
  action="project_roi",
  project_id=1,
  hourly_rate=75,
  implementation_cost=50000,
  years=3
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID
- `hourly_rate` (optional): Average hourly labor cost (default: 50)
- `implementation_cost` (optional): Estimated implementation cost
- `years` (optional): Projection years (default: 3)

**Returns:** ROI projections:
- Conservative scenario (50% of estimated savings)
- Moderate scenario (75% of estimated savings)
- Aggressive scenario (100% of estimated savings)
- Payback period for each scenario
- NPV and IRR calculations

---

### 17. identify_quick_wins
**Find immediate automation opportunities**

```
{{ai_migration(
  action="identify_quick_wins",
  project_id=1,
  min_score=80,
  max_complexity="medium"
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID
- `min_score` (optional): Minimum automation score (default: 80)
- `max_complexity` (optional): Maximum complexity (default: medium)

**Returns:** Quick wins list:
- High-impact, low-effort automation targets
- Estimated time savings per task
- Recommended AI tools
- Implementation priority

---

### 18. generate_report
**Generate comprehensive migration report**

```
{{ai_migration(
  action="generate_report",
  project_id=1,
  include_roi=true,
  include_roadmap=true,
  format="markdown"
)}}
```

**Parameters:**
- `project_id` (required): Assessment project ID
- `include_roi` (optional): Include ROI projections (default: true)
- `include_roadmap` (optional): Include roadmap (default: true)
- `format` (optional): Output format (markdown, json)

**Returns:** Complete migration report

---

## Typical Workflow

### Complete Assessment Flow
```
# 1. Start assessment
{{ai_migration(action="start_assessment", business_name="Acme Corp")}}

# 2. Document processes
{{ai_migration(action="add_process", project_id=1, name="Order Processing")}}

# 3. Add tasks to process
{{ai_migration(action="add_task", process_id=1, name="Validate order", task_type="data_validation")}}
{{ai_migration(action="add_task", process_id=1, name="Calculate pricing", task_type="calculation")}}
{{ai_migration(action="add_task", process_id=1, name="Approve discount", task_type="approval")}}

# 4. Analyze and classify
{{ai_migration(action="analyze_process", process_id=1)}}
{{ai_migration(action="classify_tasks", process_id=1)}}

# 5. Design optimized workflow
{{ai_migration(action="design_workflow", process_id=1, optimization_level="balanced")}}

# 6. Generate deliverables
{{ai_migration(action="identify_quick_wins", project_id=1)}}
{{ai_migration(action="generate_roadmap", project_id=1)}}
{{ai_migration(action="project_roi", project_id=1, hourly_rate=65)}}
{{ai_migration(action="generate_report", project_id=1)}}
```

---

## Integration with Other Tools

### With Customer Lifecycle
Track migration as a solution for a customer:
```
{{customer_lifecycle(action="add_solution", customer_id=5, name="AI Migration Project")}}
```

### With Diagram Tool
Visualize optimized workflows:
```
{{diagram_tool(action="create", type="flowchart", title="Optimized Order Processing")}}
```

### With Business X-Ray
Analyze broader business impact:
```
{{business_xray_tool(action="get_analysis", customer_id=5)}}
```

### With Virtual Team
Assign migration implementation tasks:
```
{{virtual_team(action="assign_task", description="Implement order validation automation")}}
```

---

## Output Examples

### Task Classification Output
```
Task: Validate Order Data
- Automation Score: 92
- Classification: Fully Automatable
- Recommended AI: Data validation agent
- Current Time: 15 min → Projected: 0.5 min
- Confidence: High

Task: Approve Large Discounts
- Automation Score: 35
- Classification: Human Required
- Reason: Strategic decision, relationship context
- Recommendation: AI-assisted prep, human approval
```

### ROI Projection Output
```
Conservative Scenario (50% savings):
- Year 1: $45,000 saved
- Year 3: $150,000 cumulative
- Payback: 14 months

Moderate Scenario (75% savings):
- Year 1: $67,500 saved
- Year 3: $225,000 cumulative
- Payback: 9 months

Aggressive Scenario (100% savings):
- Year 1: $90,000 saved
- Year 3: $300,000 cumulative
- Payback: 7 months
```

---

## Notes
- All assessments are stored in SQLite for tracking and reporting
- Task classification uses weighted scoring based on type, complexity, and decision points
- Workflow designs preserve necessary human touchpoints for quality and oversight
- ROI calculations include implementation costs and ongoing maintenance
- Quick wins prioritize high-impact, low-risk automation targets
