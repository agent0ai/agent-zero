# 🔄 Workflow Engine - Quick Reference

## ✅ What's Available

- **Workflow Lifecycle Management** - Design → POC → MVP → Production → Support
- **Skill Tracking** - 5 proficiency levels with automatic progression
- **Learning Paths** - Structured curricula with certifications
- **Visual Dashboards** - Mermaid diagrams and ASCII visualizations
- **UI Integration** - Settings → Workflows tab

---

## 🚀 Quick Start

### 1. Create a Workflow

```
{{workflow_engine(
  action="create_workflow",
  name="My Project",
  stages=[
    {"id": "design", "name": "Design Phase", "type": "design"},
    {"id": "build", "name": "Build Phase", "type": "poc"},
    {"id": "deploy", "name": "Deployment", "type": "production"}
  ],
  description="Project workflow"
)}}
```

### 2. Start Execution

```
{{workflow_engine(
  action="start_workflow",
  workflow_name="My Project",
  execution_name="Sprint 1",
  context={"team": "alpha", "priority": "high"}
)}}
```

### 3. Track Progress

```
{{workflow_engine(action="get_status", execution_id=1)}}
```

### 4. View in UI

**Settings → Workflows tab → Dashboard**

---

## 📚 Available Actions

### Workflow Management

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `create_workflow` | Create new workflow | `name`, `stages`, `description` |
| `list_workflows` | List all workflows | `workflow_type` (optional) |
| `get_workflow` | Get workflow details | `workflow_id` or `name` |
| `delete_workflow` | Delete workflow | `workflow_id` |
| `clone_workflow` | Clone existing | `workflow_id`, `new_name` |

### Execution Control

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `start_workflow` | Begin execution | `workflow_id/name`, `context` |
| `get_status` | Current status | `execution_id` |
| `advance_stage` | Move to next stage | `execution_id`, `force` |
| `approve_stage` | Approve for advancement | `execution_id`, `stage_id`, `approved_by` |
| `complete_criterion` | Mark criterion met | `execution_id`, `stage_id`, `criterion_id` |

### Task Execution

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `start_task` | Start a task | `execution_id`, `stage_id`, `task_id` |
| `complete_task` | Mark task done | `execution_id`, `stage_id`, `task_id`, `output_data` |
| `fail_task` | Mark task failed | `execution_id`, `stage_id`, `task_id`, `error`, `retry` |
| `get_next_task` | Get next available task | `execution_id` |

### Training & Skills

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `define_skill` | Create skill definition | `skill_id`, `name`, `category` |
| `assess_skill` | Record skill practice | `agent_id`, `skill_id`, `success` |
| `get_proficiency` | Check skill levels | `agent_id` |
| `create_path` | Create learning path | `path_id`, `name`, `target_role`, `modules` |
| `list_paths` | List learning paths | `target_role` (optional) |

### Visualization

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `visualize_workflow` | Mermaid flowchart | `workflow_id`, `execution_id` |
| `visualize_gantt` | Gantt timeline | `workflow_id`, `start_date` |
| `visualize_tasks` | Task dependency graph | `workflow_id`, `stage_id` |
| `get_dashboard` | ASCII dashboard | (none) |

---

## 🎯 Stage Types

| Type | Description | Use Case |
|------|-------------|----------|
| `design` | Initial planning | Requirements, wireframes |
| `poc` | Proof of concept | Technical validation |
| `mvp` | Minimum viable product | Core feature development |
| `production` | Production release | Deployment, go-live |
| `support` | Ongoing support | Bug fixes, maintenance |
| `upgrade` | Version upgrade | Major updates, migrations |
| `custom` | Generic stage | Anything else |

---

## 📊 Skill Levels

| Level | Name | Typical Completions |
|-------|------|---------------------|
| 1 | Novice | 0 |
| 2 | Beginner | 5+ |
| 3 | Intermediate | 15+ |
| 4 | Advanced | 30+ |
| 5 | Expert | 50+ |

---

## 🔧 Stage Configuration

### Exit Criteria

```json
{
  "id": "design",
  "name": "Design Phase",
  "exit_criteria": [
    {"id": "wireframes", "name": "Wireframes complete"},
    {"id": "spec", "name": "Tech spec approved"}
  ]
}
```

### Tasks with Dependencies

```json
{
  "id": "build",
  "name": "Build Phase",
  "tasks": [
    {"id": "setup", "name": "Setup Environment", "dependencies": []},
    {"id": "develop", "name": "Develop Features", "dependencies": ["setup"]},
    {"id": "test", "name": "Run Tests", "dependencies": ["develop"]}
  ]
}
```

### Approval Gates

```json
{
  "id": "production",
  "name": "Production Release",
  "approval_required": true
}
```

---

## 📋 Common Workflows

### Product Development

```
{{workflow_engine(
  action="create_workflow",
  name="Product Development",
  stages=[
    {"id": "discovery", "name": "Discovery", "type": "design"},
    {"id": "design", "name": "Design", "type": "design", "approval_required": true},
    {"id": "poc", "name": "POC", "type": "poc"},
    {"id": "mvp", "name": "MVP", "type": "mvp"},
    {"id": "production", "name": "Production", "type": "production", "approval_required": true},
    {"id": "support", "name": "Support", "type": "support"}
  ]
)}}
```

### Client Project

```
{{workflow_engine(
  action="create_workflow",
  name="Client Integration",
  stages=[
    {"id": "kickoff", "name": "Project Kickoff", "type": "custom"},
    {"id": "analysis", "name": "Requirements", "type": "design"},
    {"id": "development", "name": "Development", "type": "custom"},
    {"id": "uat", "name": "UAT", "type": "custom", "approval_required": true},
    {"id": "golive", "name": "Go Live", "type": "production"},
    {"id": "hypercare", "name": "Hypercare", "type": "support"}
  ]
)}}
```

---

## 📈 Learning Paths

### Create Path with Modules

```
{{workflow_engine(
  action="create_path",
  path_id="python_dev",
  name="Python Developer",
  target_role="developer",
  modules=[
    {"module_id": "basics", "name": "Python Basics", "required": true},
    {"module_id": "advanced", "name": "Advanced Python", "required": true, "prerequisites": ["basics"]},
    {"module_id": "testing", "name": "Testing", "required": true}
  ],
  certification={"name": "Certified Python Developer", "badge": "py_dev"}
)}}
```

---

## 🖥️ UI Dashboard

### Access

1. Open Agent Jumbo web interface
2. Click **Settings** (gear icon)
3. Select **Workflows** tab

### Dashboard Views

- **Dashboard** - Overview stats, recent executions
- **Workflows** - List and visualize workflows
- **Training** - Learning paths and progress
- **Skills** - Skill proficiency tracking

### Features

- Real-time polling (every 5 seconds)
- Mermaid diagram rendering
- Tab-based navigation
- Refresh button for manual updates

---

## 🐛 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty dashboard | No data | Create workflows and skills first |
| Stage won't advance | Exit criteria not met | Complete required criteria or use `force=true` |
| Stage won't advance | Approval required | Use `approve_stage` action first |
| Skills not tracking | Wrong action | Use `assess_skill` not `define_skill` |
| Mermaid not rendering | JavaScript error | Check browser console, refresh page |
| API returns error | Database path issue | Ensure data directory exists |

---

## 🧪 Testing

### Run Unit Tests

```bash
# Database tests
pytest tests/test_workflow_db.py -v

# Manager tests
pytest tests/test_workflow_manager.py -v

# Visualizer tests
pytest tests/test_workflow_visualizer.py -v

# All workflow tests
pytest tests/test_workflow*.py -v
```

### Run API Tests

```bash
pytest tests/test_workflow_api.py -v
```

### Run E2E Tests

```bash
pytest tests/test_workflow_e2e.py -v
```

### Run UI Tests (requires Playwright)

```bash
pytest tests/ui/test_workflow_ui.py -v
```

### Generate Sample Data

```bash
python tests/fixtures/workflow_sample_data.py
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `python/tools/workflow_engine.py` | Main workflow tool |
| `python/tools/workflow_training.py` | Training tool |
| `instruments/custom/workflow_engine/workflow_db.py` | Database layer |
| `instruments/custom/workflow_engine/workflow_manager.py` | Business logic |
| `instruments/custom/workflow_engine/workflow_visualizer.py` | Visualizations |
| `python/api/workflow_dashboard.py` | Dashboard API |
| `python/api/workflow_engine_api.py` | Engine API |
| `python/api/workflow_training_api.py` | Training API |
| `webui/components/settings/workflow/` | UI components |

---

## 📊 API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/workflow_dashboard` | Dashboard data (stats, recent, top skills) |
| `/workflow_engine_api` | Workflow operations |
| `/workflow_training_api` | Training operations |

---

## 🔗 Related Tools

- **customer_lifecycle** - Customer journey tracking
- **portfolio_manager** - Project portfolio management
- **diagram_tool** - General diagram generation
- **virtual_team** - Task assignment and delegation
